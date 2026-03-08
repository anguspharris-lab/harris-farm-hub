"""
Harris Farm Hub — Conversational Survey Engine
Stateless state machine that drives WhatsApp, SMS, and simulator conversations.
Reads questions dynamically from survey_config.py so all channels stay in sync.

Usage:
    from shared.conversation_engine import ConversationEngine
    engine = ConversationEngine()
    reply = engine.process_message(session, user_input, "whatsapp")
"""

import os
import re
import uuid
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple, List, Dict, Any

import requests

from shared.survey_config import (
    SECTIONS, DEPARTMENTS, ROLE_LEVELS,
    FIELD_TO_BQ, build_field_sequence, score_label,
)

_log = logging.getLogger(__name__)

# Cloud Function endpoint for submitting completed surveys
_SUBMIT_URL = os.getenv(
    "SCR_SUBMIT_URL",
    "https://australia-southeast1-oval-blend-488902-p2"
    ".cloudfunctions.net/hfm-scr-insert",
)
_API_KEY = os.getenv("SCR_API_KEY", "hfm-scr-2026")

# Build the field sequence once at import time
FIELD_SEQUENCE = build_field_sequence()

# States before the dynamic ADKAR fields
_PRE_STATES = ["GREETING", "EMAIL", "FIRST_NAME", "DEPARTMENT", "ROLE"]
_POST_STATES = ["SUMMARY", "COMPLETE"]

# Session TTL
_SESSION_TTL_SECS = 86400  # 24 hours


# ---------------------------------------------------------------------------
# Input parsers
# ---------------------------------------------------------------------------

def parse_score_and_text(text):
    # type: (str) -> Tuple[Optional[int], Optional[str]]
    """Parse '7 - waste is an issue' -> (7, 'waste is an issue').
    Also handles '7' alone -> (7, None)."""
    cleaned = text.strip()
    # Score + text: "7 - reason" or "7, reason" or "7: reason"
    m = re.match(r'^(\d{1,2})\s*[-:,.]\s*(.+)$', cleaned, re.DOTALL)
    if m:
        score = int(m.group(1))
        if 1 <= score <= 10:
            return score, m.group(2).strip()
    # Score only
    m = re.match(r'^(\d{1,2})$', cleaned)
    if m:
        score = int(m.group(1))
        if 1 <= score <= 10:
            return score, None
    return None, None


def parse_number_selection(text, max_val):
    # type: (str, int) -> Optional[int]
    """Parse a number selection (1-based). Returns 0-based index or None."""
    cleaned = text.strip()
    m = re.match(r'^(\d{1,2})$', cleaned)
    if m:
        val = int(m.group(1))
        if 1 <= val <= max_val:
            return val - 1  # 0-based
    return None


def parse_email(text):
    # type: (str) -> Optional[str]
    """Validate and return email or None."""
    cleaned = text.strip().lower()
    if re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', cleaned):
        return cleaned
    return None


def parse_confirmation(text):
    # type: (str) -> bool
    """Check if user confirmed."""
    cleaned = text.strip().lower()
    return cleaned in (
        "yes", "y", "yep", "yeah", "submit", "send", "go", "done", "ok"
    )


def parse_restart(text):
    # type: (str) -> bool
    """Check if user wants to restart."""
    cleaned = text.strip().lower()
    return cleaned in ("restart", "start over", "reset", "new")


# ---------------------------------------------------------------------------
# Session helpers
# ---------------------------------------------------------------------------

def new_session(channel, identifier):
    # type: (str, str) -> Dict[str, Any]
    """Create a fresh session dict."""
    now = datetime.utcnow().isoformat()
    return {
        "session_id": str(uuid.uuid4())[:8],
        "channel": channel,
        "identifier": identifier,
        "current_state": "GREETING",
        "current_field_idx": 0,
        "waiting_for_text": False,
        "answers": {},
        "started_at": now,
        "updated_at": now,
        "completed": False,
        "submitted_to_bq": False,
        "test_mode": False,
    }


def is_expired(session):
    # type: (Dict[str, Any]) -> bool
    """Check if session has expired (24hr TTL)."""
    updated = session.get("updated_at", "")
    if not updated:
        return True
    try:
        dt = datetime.fromisoformat(updated)
        return (datetime.utcnow() - dt).total_seconds() > _SESSION_TTL_SECS
    except (ValueError, TypeError):
        return True


# ---------------------------------------------------------------------------
# Message formatting
# ---------------------------------------------------------------------------

def _fmt(text, channel):
    # type: (str, str) -> str
    """Format text for the channel. WhatsApp supports *bold*, SMS is plain."""
    if channel == "sms":
        # Strip markdown bold markers
        return text.replace("*", "")
    return text


def _numbered_list(items, channel):
    # type: (List[str], str) -> str
    """Format a numbered list."""
    lines = []
    for i, item in enumerate(items, 1):
        lines.append(f"{i}. {item}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Conversation Engine
# ---------------------------------------------------------------------------

class ConversationEngine:
    """Stateless conversation engine. Call process_message with a session dict,
    user input, and channel. Returns the bot's reply text. Mutates session
    in-place."""

    def process_message(self, session, user_input, channel):
        # type: (Dict[str, Any], str, str) -> str
        """Process one user message. Updates session in-place. Returns reply."""
        session["updated_at"] = datetime.utcnow().isoformat()

        # Check for restart command
        if parse_restart(user_input):
            self._reset(session)
            return self._greeting_prompt(channel)

        state = session["current_state"]

        if state == "GREETING":
            return self._handle_greeting(session, user_input, channel)
        elif state == "EMAIL":
            return self._handle_email(session, user_input, channel)
        elif state == "FIRST_NAME":
            return self._handle_first_name(session, user_input, channel)
        elif state == "DEPARTMENT":
            return self._handle_department(session, user_input, channel)
        elif state == "ROLE":
            return self._handle_role(session, user_input, channel)
        elif state == "FIELD":
            return self._handle_field(session, user_input, channel)
        elif state == "SUMMARY":
            return self._handle_summary(session, user_input, channel)
        elif state == "COMPLETE":
            return _fmt(
                "You've already submitted! Reply *restart* to begin a new survey.",
                channel,
            )
        else:
            return "Something went wrong. Reply RESTART to begin again."

    # -- State handlers -------------------------------------------------------

    def _handle_greeting(self, session, user_input, channel):
        # type: (Dict[str, Any], str, str) -> str
        """Handle workstream selection."""
        # Try to match a workstream code (SCR2026, AIVISION, etc.)
        try:
            from config.workstreams import (
                get_active_workstreams, get_workstream_by_code,
            )
            ws = get_workstream_by_code(user_input.strip().upper())
            if ws:
                session["answers"]["workstream_id"] = ws["id"]
                session["answers"]["workstream_name"] = ws["name"]
                session["current_state"] = "EMAIL"
                return _fmt(
                    f"Great \u2014 *{ws['name']}* it is!\n\n"
                    f"What's your email address?\n"
                    f"(So we can share your personal results back with you "
                    f"\u2014 no spam, promise.)",
                    channel,
                )

            # Try number selection
            active = get_active_workstreams()
            idx = parse_number_selection(user_input, len(active))
            if idx is not None:
                ws = active[idx]
                session["answers"]["workstream_id"] = ws["id"]
                session["answers"]["workstream_name"] = ws["name"]
                session["current_state"] = "EMAIL"
                return _fmt(
                    f"Great \u2014 *{ws['name']}* it is!\n\n"
                    f"What's your email address?\n"
                    f"(So we can share your personal results back with you "
                    f"\u2014 no spam, promise.)",
                    channel,
                )
        except ImportError:
            pass

        # Unrecognised input — show the full greeting so the user
        # always knows what to do (especially after WhatsApp sandbox join)
        return self._greeting_prompt(channel)

    def _handle_email(self, session, user_input, channel):
        # type: (Dict[str, Any], str, str) -> str
        email = parse_email(user_input)
        if email is None:
            return "That doesn't look like a valid email. Please try again."
        session["answers"]["email"] = email
        session["current_state"] = "FIRST_NAME"
        return "Thanks! And what's your first name?"

    def _handle_first_name(self, session, user_input, channel):
        # type: (Dict[str, Any], str, str) -> str
        name = user_input.strip()
        if not name or len(name) < 1:
            return "Please enter your first name."
        session["answers"]["first_name"] = name
        session["current_state"] = "DEPARTMENT"
        return _fmt(
            f"Nice to meet you, *{name}*!\n\n"
            f"Which department are you in?\n\n"
            f"{_numbered_list(DEPARTMENTS, channel)}\n\n"
            f"Reply with the number.",
            channel,
        )

    def _handle_department(self, session, user_input, channel):
        # type: (Dict[str, Any], str, str) -> str
        idx = parse_number_selection(user_input, len(DEPARTMENTS))
        if idx is None:
            return (
                f"Please reply with a number from 1 to {len(DEPARTMENTS)}."
            )
        session["answers"]["department"] = DEPARTMENTS[idx]
        session["current_state"] = "ROLE"
        return _fmt(
            f"Got it \u2014 *{DEPARTMENTS[idx]}*.\n\n"
            f"What's your role level?\n\n"
            f"{_numbered_list(ROLE_LEVELS, channel)}\n\n"
            f"Reply with the number.",
            channel,
        )

    def _handle_role(self, session, user_input, channel):
        # type: (Dict[str, Any], str, str) -> str
        idx = parse_number_selection(user_input, len(ROLE_LEVELS))
        if idx is None:
            return f"Please reply with a number from 1 to {len(ROLE_LEVELS)}."
        session["answers"]["role_level"] = ROLE_LEVELS[idx]
        session["current_state"] = "FIELD"
        session["current_field_idx"] = 0
        session["waiting_for_text"] = False

        total = len(FIELD_SEQUENCE)
        return _fmt(
            f"Alright *{session['answers'].get('first_name', '')}*, "
            f"now the good stuff. {total} quick questions about where we "
            f"are today.\n\n"
            + self._field_prompt(0, channel),
            channel,
        )

    def _handle_field(self, session, user_input, channel):
        # type: (Dict[str, Any], str, str) -> str
        """Handle dynamic ADKAR field questions."""
        idx = session["current_field_idx"]
        if idx >= len(FIELD_SEQUENCE):
            session["current_state"] = "SUMMARY"
            return self._summary_prompt(session, channel)

        _si, _fi, field, section = FIELD_SEQUENCE[idx]

        # If we're waiting for the text part of a score+text field
        if session.get("waiting_for_text"):
            session["answers"][field["key"] + "_text_part"] = user_input.strip()
            # Combine: the score was already saved under field["key"]
            # Save the text under the original text field key
            # But we need to figure out which text field follows this slider
            # Actually, the "waiting_for_text" means user gave score-only
            # on a slider, and we asked for the reason.
            # The text goes into the NEXT field's key if it's a text field,
            # OR as a suffix to the slider key.
            # Simpler: for sliders, the text reason is stored as
            # "{field_key}_reason" in answers, and mapped at submit time.
            session["waiting_for_text"] = False
            # Move to next field
            return self._advance_field(session, channel)

        if field["type"] == "slider":
            score, text = parse_score_and_text(user_input)
            if score is None:
                return (
                    "Please reply with a score from 1 to 10.\n"
                    "e.g. '7 - your reason here'"
                )
            session["answers"][field["key"]] = score
            if text:
                # Got both score and text in one message
                session["answers"][field["key"] + "_reason"] = text
                return self._advance_field(session, channel)
            else:
                # Score only — ask for the reason
                session["waiting_for_text"] = True
                lbl, _ = score_label(score)
                return _fmt(
                    f"Score of *{score}/10* ({lbl}) recorded.\n\n"
                    f"Now tell me briefly \u2014 why that score? "
                    f"A few words is perfect.",
                    channel,
                )
        else:
            # Text field — just store it
            val = user_input.strip()
            if not val:
                return "Please share your thoughts \u2014 even a few words helps."
            session["answers"][field["key"]] = val
            return self._advance_field(session, channel)

    def _handle_summary(self, session, user_input, channel):
        # type: (Dict[str, Any], str, str) -> str
        if parse_confirmation(user_input):
            success = self.submit(session)
            if success:
                session["current_state"] = "COMPLETE"
                session["completed"] = True
                session["submitted_to_bq"] = True
                name = session["answers"].get("first_name", "")
                return _fmt(
                    f"Submitted! Thank you, *{name}*.\n\n"
                    f"Your voice is shaping our future. "
                    f"If you want to share this with a colleague, "
                    f"send them this link:\n\n"
                    f"https://harris-farm-hub.onrender.com/hfw-landing\n\n"
                    f"Or tell them to text the workstream code to this number.",
                    channel,
                )
            else:
                return (
                    "Something went wrong submitting your response. "
                    "Please try again \u2014 reply YES to retry."
                )
        elif parse_restart(user_input):
            self._reset(session)
            return self._greeting_prompt(channel)
        else:
            return _fmt(
                "Reply *yes* to submit your response, or *restart* to "
                "start over.",
                channel,
            )

    # -- Helpers --------------------------------------------------------------

    def _reset(self, session):
        # type: (Dict[str, Any]) -> None
        """Reset session to start."""
        channel = session["channel"]
        identifier = session["identifier"]
        sid = session["session_id"]
        session.clear()
        session.update(new_session(channel, identifier))
        session["session_id"] = sid

    def _advance_field(self, session, channel):
        # type: (Dict[str, Any], str) -> str
        """Move to next field or to summary if done."""
        session["current_field_idx"] += 1
        idx = session["current_field_idx"]
        if idx >= len(FIELD_SEQUENCE):
            session["current_state"] = "SUMMARY"
            return self._summary_prompt(session, channel)
        return self._field_prompt(idx, channel)

    def _field_prompt(self, idx, channel):
        # type: (int, str) -> str
        """Generate the question prompt for field at index idx."""
        _si, _fi, field, section = FIELD_SEQUENCE[idx]
        total = len(FIELD_SEQUENCE)

        # Section header — show when entering a new section
        prev_section = FIELD_SEQUENCE[idx - 1][3] if idx > 0 else None
        header = ""
        if prev_section is None or prev_section["key"] != section["key"]:
            header = _fmt(
                f"*{section['label'].upper()}* \u2014 {section['question']}\n\n",
                channel,
            )

        num = idx + 1

        if field["type"] == "slider":
            return (
                f"{header}"
                f"Question {num}/{total}\n"
                f"{field['label']}\n\n"
                f"Reply with a score from 1-10 and a quick reason.\n"
                f"e.g. '7 - your reason here'\n\n"
                f"({field.get('help', '')})"
            )
        else:
            return (
                f"{header}"
                f"Question {num}/{total}\n"
                f"{field['label']}\n\n"
                f"{field.get('help', '')}"
            )

    def _summary_prompt(self, session, channel):
        # type: (Dict[str, Any], str) -> str
        """Build the summary message."""
        answers = session["answers"]
        name = answers.get("first_name", "")
        dept = answers.get("department", "")
        role = answers.get("role_level", "")
        ws = answers.get("workstream_name", "")

        lines = [
            _fmt(f"Here's your summary, *{name}*:\n", channel),
            f"{dept} | {role}",
            f"Workstream: {ws}\n",
        ]

        scores = []
        for _si, _fi, field, section in FIELD_SEQUENCE:
            if field["type"] == "slider":
                val = answers.get(field["key"], "?")
                reason = answers.get(field["key"] + "_reason", "")
                lbl, _ = score_label(int(val)) if isinstance(val, int) else ("?", "")
                reason_txt = f" \u2014 {reason}" if reason else ""
                lines.append(
                    f"{section['label']}: {val}/10 ({lbl}){reason_txt}"
                )
                if isinstance(val, int):
                    scores.append(val)

        if scores:
            avg = sum(scores) / len(scores)
            lines.append(f"\nAverage: {avg:.1f}/10")
            best_idx = scores.index(max(scores))
            worst_idx = scores.index(min(scores))
            slider_fields = [
                (s, f) for _si, _fi, f, s in FIELD_SEQUENCE
                if f["type"] == "slider"
            ]
            if slider_fields:
                lines.append(
                    f"Strongest: {slider_fields[best_idx][0]['label']} "
                    f"({max(scores)}/10)"
                )
                lines.append(
                    f"Growth area: {slider_fields[worst_idx][0]['label']} "
                    f"({min(scores)}/10)"
                )

        lines.append("")
        lines.append(
            _fmt("Reply *yes* to submit, or *restart* to start over.", channel)
        )
        return "\n".join(lines)

    def _greeting_prompt(self, channel):
        # type: (str) -> str
        """Generate the greeting/workstream selection message."""
        try:
            from config.workstreams import get_active_workstreams
            active = get_active_workstreams()
            ws_list = _numbered_list(
                [ws["name"] for ws in active], channel
            )
        except ImportError:
            ws_list = "1. Supply Chain Review\n2. AI Vision 2026"

        return _fmt(
            "G'day! I'm the Harris Farm Transformation survey bot. "
            "This takes about 5 minutes and your answers help shape "
            "our future.\n\n"
            "Which survey are you here for?\n\n"
            f"{ws_list}\n\n"
            "Reply with the number.",
            channel,
        )

    def get_greeting(self, channel):
        # type: (str) -> str
        """Public method to get the initial greeting message."""
        return self._greeting_prompt(channel)

    def build_payload(self, session):
        # type: (Dict[str, Any]) -> Dict[str, Any]
        """Build the hfm-scr-insert payload from session answers."""
        answers = session["answers"]

        payload = {
            "meeting_type": "TRANSFORMATION_READINESS",
            "name": answers.get("first_name", ""),
            "first_name": answers.get("first_name", ""),
            "email": answers.get("email", ""),
            "department": answers.get("department", ""),
            "role_level": answers.get("role_level", ""),
            "role": answers.get("role_level", ""),
            "transformation_focus": answers.get("workstream_name", ""),
            "initiative_name": answers.get("workstream_name", ""),
            "session_id": session.get("session_id", ""),
            "channel": session.get("channel", "whatsapp"),
        }

        # Map form field keys to BQ column names
        for field_key, bq_col in FIELD_TO_BQ.items():
            val = answers.get(field_key)
            if val is not None:
                payload[bq_col] = val

        # For slider fields, also map the reason text
        # The conversation stores reasons as {key}_reason
        # We need to map these to the appropriate BQ text columns
        _slider_to_text = {
            "awareness_score": "adkar_awareness_text",
            "desire_score": "adkar_desire_text",
            "knowledge_score": "adkar_knowledge_text",
            "capability_score": "adkar_ability_text",
            "reinforcement_score": "adkar_reinforcement_text",
        }
        for slider_key, text_col in _slider_to_text.items():
            reason = answers.get(slider_key + "_reason", "")
            if reason and text_col not in payload:
                payload[text_col] = reason

        # Also map the explicit text fields that may have been answered
        # after a slider (e.g. why_transform follows awareness_score)
        for field_key, bq_col in FIELD_TO_BQ.items():
            if bq_col not in payload:
                val = answers.get(field_key, "")
                if val:
                    payload[bq_col] = val

        # Fill biggest_blocker from ability text
        if "biggest_blocker" not in payload:
            payload["biggest_blocker"] = payload.get("adkar_ability_text", "")

        return payload

    def submit(self, session):
        # type: (Dict[str, Any]) -> bool
        """POST completed survey to hfm-scr-insert Cloud Function."""
        payload = self.build_payload(session)
        url = f"{_SUBMIT_URL}?api_key={_API_KEY}"
        if session.get("test_mode"):
            url += "&test=true"
        try:
            resp = requests.post(url, json=payload, timeout=15)
            if resp.ok:
                _log.info("Survey submitted: %s", payload.get("email", ""))
                return True
            _log.error("Submit failed: %s %s", resp.status_code, resp.text[:200])
            return False
        except Exception as e:
            _log.exception("Submit error: %s", e)
            return False
