"""
Harris Farm Hub — Growing Legends Academy

Pillar 3: Growing Legendary Leadership
A self-learning destination that ties together the Learning Centre, Rubric,
Prompt Builder, Arena, and Showcase into a single inspiring page.

6-level maturity model: Seed → Sprout → Grower → Harvester → Cultivator → Legend
"""

import streamlit as st

from shared.styles import render_header, render_footer, HFM_GREEN
from shared.goals_config import goal_badge_html
from shared.voice_realtime import render_voice_data_box
from shared.academy_content import (
    MATURITY_LEVELS,
    PROMPT_PATTERNS,
    RUBRIC_TIER_BREAKDOWN,
    SCORE_THIS_EXERCISES,
    LEARNING_PATHS,
    ARENA_CHALLENGES,
    TOP_SHOWCASE,
    DASHBOARD_QUALITY_RUBRIC,
    PAGE_CONTENT_RUBRIC,
    ACADEMY_SELF_SCORE,
)
from shared.training_content import BUILDING_BLOCKS, RUBRIC_CRITERIA

user = st.session_state.get("auth_user")
_pages = st.session_state.get("_pages", {})

render_header(
    "Growing Legends Academy",
    "Your AI capability journey | From Seed to Legend | Learn, Practice, Build",
    goals=["G3"],
    strategy_context="Famous for attracting, developing, and retaining exceptional people \u2014 Pillar 3 in action.",
)

# ---------------------------------------------------------------------------
# HERO BANNER — People pillar green (#059669)
# ---------------------------------------------------------------------------

st.markdown(
    "<div style='background:linear-gradient(135deg, #059669 0%, #047857 50%, #065f46 100%);"
    "color:white;padding:36px 32px;border-radius:14px;margin-bottom:24px;'>"
    "<div style='font-size:2.2em;font-weight:800;margin-bottom:8px;'>"
    "\U0001f331 Growing Legends Academy</div>"
    "<div style='font-size:1.15em;opacity:0.95;max-width:800px;line-height:1.6;'>"
    "Every expert was once a beginner. This Academy maps your journey from first "
    "AI prompt to leading transformation across the business. Six levels, seven "
    "prompt patterns, real Harris Farm examples, and a community of learners."
    "</div>"
    "<div style='margin-top:16px;font-size:0.9em;opacity:0.8;'>"
    "Pillar 3: Growing Legendary Leadership &mdash; "
    "Part of the Fewer, Bigger, Better strategy</div>"
    "</div>",
    unsafe_allow_html=True,
)

# Goal connection callout
st.markdown(
    f"<div style='background:#faf5ff;border:1px solid #d8b4fe;border-radius:10px;"
    f"padding:14px 18px;margin-bottom:16px;display:flex;align-items:center;gap:12px;'>"
    f"<span style='font-size:1.3em;'>\U0001f31f</span>"
    f"<div>"
    f"<strong style='color:#7c3aed;'>Goal 3: Train Our Superstars</strong>"
    f"<span style='color:#6b7280;font-size:0.9em;'> &mdash; "
    f"Making every Harris Farmer more capable with AI, at their own pace.</span>"
    f"</div>"
    f"<div>{goal_badge_html('G3')}</div>"
    f"</div>",
    unsafe_allow_html=True,
)


# ============================================================================
# 8 TABS
# ============================================================================

tabs = st.tabs([
    "\U0001f331 Journey",
    "\U0001f9e0 Patterns",
    "\u2696\ufe0f Rubric",
    "\U0001f4da Paths",
    "\U0001f3c6 Arena",
    "\U0001f4a1 Showcase",
    "\U0001f4cf Site Quality",
    "\U0001f517 Links",
])


# ────────────────────────────────────────────────────────────────────────────
# TAB 1: CAPABILITY JOURNEY
# ────────────────────────────────────────────────────────────────────────────

with tabs[0]:
    st.markdown("### Your Capability Journey")
    st.markdown(
        "Six levels from your first AI conversation to leading transformation. "
        "Every level has clear skills, exercises, and a rubric score target."
    )

    # Progress bar showing all 6 levels
    level_names = [lv["name"] for lv in MATURITY_LEVELS]
    level_icons = [lv["icon"] for lv in MATURITY_LEVELS]
    bar_html = "".join(
        f"<div style='flex:1;text-align:center;padding:8px 4px;"
        f"background:{lv['color']};color:{lv['text_color']};"
        f"font-weight:600;font-size:0.85em;"
        f"{'border-radius:10px 0 0 10px;' if i == 0 else ''}"
        f"{'border-radius:0 10px 10px 0;' if i == len(MATURITY_LEVELS) - 1 else ''}'>"
        f"{lv['icon']} {lv['name']}</div>"
        for i, lv in enumerate(MATURITY_LEVELS)
    )
    st.markdown(
        f"<div style='display:flex;border-radius:10px;overflow:hidden;"
        f"margin-bottom:24px;box-shadow:0 2px 8px rgba(0,0,0,0.08);'>"
        f"{bar_html}</div>",
        unsafe_allow_html=True,
    )

    # 3x2 card grid
    for row_start in (0, 3):
        cols = st.columns(3)
        for j, col in enumerate(cols):
            idx = row_start + j
            if idx >= len(MATURITY_LEVELS):
                break
            lv = MATURITY_LEVELS[idx]
            with col:
                st.markdown(
                    f"<div style='background:{lv['color']};color:{lv['text_color']};"
                    f"border-radius:14px;padding:20px;min-height:180px;"
                    f"box-shadow:0 2px 8px rgba(0,0,0,0.06);'>"
                    f"<div style='font-size:2em;'>{lv['icon']}</div>"
                    f"<div style='font-size:1.2em;font-weight:700;'>{lv['name']}</div>"
                    f"<div style='font-size:0.85em;opacity:0.85;font-style:italic;'>"
                    f"\"{lv['tagline']}\"</div>"
                    f"<div style='margin-top:8px;font-size:0.9em;'>{lv['description']}</div>"
                    f"<div style='margin-top:10px;font-size:0.8em;font-weight:600;'>"
                    f"Rubric Score: {lv['rubric_threshold']}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
                with st.expander(f"Skills, exercises & modules"):
                    st.markdown("**Skills to demonstrate:**")
                    for skill in lv["skills"]:
                        st.markdown(f"- {skill}")
                    st.markdown("**Exercises:**")
                    for ex in lv["exercises"]:
                        st.markdown(f"- {ex}")
                    mods = lv["learning_centre_modules"]
                    if mods != ["All"]:
                        st.markdown(f"**Modules:** {', '.join(mods)}")
                    else:
                        st.markdown("**Modules:** All Learning Centre modules")
                    st.markdown(f"**Recommended path:** {lv['recommended_path']}")


# ────────────────────────────────────────────────────────────────────────────
# TAB 2: PROMPT MASTERY — 7 Patterns
# ────────────────────────────────────────────────────────────────────────────

with tabs[1]:
    st.markdown("### Prompt Mastery")
    st.markdown(
        "Seven proven patterns that transform basic prompts into powerful ones. "
        "Each pattern includes a Harris Farm example and a scored comparison."
    )

    # Quick reference: 5 Building Blocks
    st.markdown("#### The 5 Building Blocks (Quick Reference)")
    bb_cols = st.columns(5)
    for i, block in enumerate(BUILDING_BLOCKS):
        with bb_cols[i]:
            st.markdown(
                f"<div style='background:#f0fdf4;border-radius:10px;padding:12px;"
                f"text-align:center;border:1px solid #bbf7d0;min-height:100px;'>"
                f"<div style='font-size:1.4em;font-weight:700;color:#059669;'>"
                f"{block['icon']}</div>"
                f"<div style='font-weight:600;'>{block['name']}</div>"
                f"<div style='font-size:0.8em;color:#555;'>{block['short']}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

    st.markdown("---")
    st.markdown("#### The 7 Advanced Patterns")

    for pattern in PROMPT_PATTERNS:
        with st.expander(
            f"{pattern['icon']} {pattern['name']}  |  Level: {pattern['level']}"
        ):
            st.info(f"**Why this works:** {pattern['why']}")
            st.markdown(f"**{pattern['description']}**")

            st.markdown("**Harris Farm Example:**")
            st.markdown(
                f"<div style='background:#f0fdf4;border-left:4px solid #059669;"
                f"padding:12px 16px;border-radius:0 8px 8px 0;margin:8px 0;'>"
                f"{pattern['hfm_example']}</div>",
                unsafe_allow_html=True,
            )

            st.markdown("**Score 6 vs Score 9 — Side by Side:**")
            c1, c2 = st.columns(2)
            with c1:
                st.error(f"**Score ~6/25**\n\n{pattern['scored_6_prompt']}")
                st.caption(pattern["scored_6_explanation"])
            with c2:
                st.success(f"**Score ~9/9 per criterion**\n\n{pattern['scored_9_prompt']}")
                st.caption(pattern["scored_9_explanation"])

    # Footer link
    if "prompt-builder" in _pages:
        st.page_link(_pages["prompt-builder"], label="Practice now in the Prompt Builder \u2192", icon="\U0001f527")


# ────────────────────────────────────────────────────────────────────────────
# TAB 3: THE RUBRIC EXPLAINED
# ────────────────────────────────────────────────────────────────────────────

with tabs[2]:
    st.markdown("### The Rubric Explained")
    st.markdown(
        "Two rubric systems power the Hub: a **Prompt Quality Rubric** (25 pts) "
        "for evaluating individual prompts, and a **5-Tier Strategic Rubric** "
        "(130 pts) for evaluating AI initiatives."
    )

    # Section A: Prompt Quality Rubric
    st.markdown("#### A. Prompt Quality Rubric (25 points)")
    st.markdown(
        "Each prompt is scored on 5 criteria, each worth 1-5 points. "
        "Used in The Rubric dashboard and the Arena."
    )

    for crit in RUBRIC_CRITERIA:
        with st.expander(f"{crit['name']} — {crit['description']}"):
            for score, desc in crit["guide"].items():
                icon = "\U0001f7e2" if score >= 4 else ("\U0001f7e1" if score >= 3 else "\U0001f534")
                st.markdown(f"{icon} **{score}/5** — {desc}")

    st.markdown("---")

    # Section B: 5-Tier Strategic Evaluation Rubric
    st.markdown("#### B. 5-Tier Strategic Evaluation Rubric (130 points)")
    st.markdown(
        "Used by the Arena to evaluate AI initiative proposals. "
        "Five expert panels, each scoring different dimensions. "
        "**Implementation threshold: 110/130 (85%).**"
    )

    for tier in RUBRIC_TIER_BREAKDOWN:
        with st.expander(
            f"{tier['name']} — {tier['max_points']} pts "
            f"({tier['criteria_count']} criteria)"
        ):
            st.markdown(f"**Panelists:** {tier['panelists']}")
            st.markdown(
                f"<div style='display:flex;gap:12px;margin:12px 0;'>"
                f"<div style='flex:1;background:#f0fdf4;border-left:4px solid #22c55e;"
                f"padding:12px;border-radius:0 8px 8px 0;'>"
                f"<strong>What 8+ looks like:</strong><br>{tier['what_8_looks_like']}</div>"
                f"<div style='flex:1;background:#fef2f2;border-left:4px solid #ef4444;"
                f"padding:12px;border-radius:0 8px 8px 0;'>"
                f"<strong>What 5 looks like:</strong><br>{tier['what_5_looks_like']}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # Section C: "Score This" Interactive Exercise
    st.markdown("#### C. Score This! (Interactive Exercise)")
    st.markdown(
        "Look at each prompt below and guess its score before revealing the answer."
    )

    for ex in SCORE_THIS_EXERCISES:
        st.markdown(f"**{ex['label']}**")
        st.markdown(
            f"<div style='background:#f8fafc;border:1px solid #e2e8f0;padding:14px;"
            f"border-radius:8px;font-family:monospace;margin:8px 0;'>"
            f"{ex['prompt']}</div>",
            unsafe_allow_html=True,
        )
        with st.expander("Reveal score and explanation"):
            st.markdown(f"**Expected Score:** {ex['expected_score']}")
            st.markdown(ex["explanation"])


# ────────────────────────────────────────────────────────────────────────────
# TAB 4: LEARNING PATHS
# ────────────────────────────────────────────────────────────────────────────

with tabs[3]:
    st.markdown("### Learning Paths")
    st.markdown(
        "Not sure where to start? Pick the path that matches your role and level."
    )

    # "Where should I start?" guide
    st.markdown(
        "<div style='background:#f0fdf4;border:2px solid #bbf7d0;border-radius:12px;"
        "padding:16px;margin-bottom:20px;'>"
        "<strong>Where should I start?</strong><br>"
        "\U0001f331 Never used AI? \u2192 <strong>AI Foundations</strong><br>"
        "\U0001f33f Using AI sometimes? \u2192 <strong>Prompt Craft</strong><br>"
        "\U0001f4ca Work with data? \u2192 <strong>Data Intelligence</strong><br>"
        "\U0001f527 Want advanced techniques? \u2192 <strong>Prompt Engineering</strong><br>"
        "\U0001f4bb On the IT team? \u2192 <strong>Building with Claude Code</strong><br>"
        "\U0001f3c6 Leading a team? \u2192 <strong>AI Leadership</strong>"
        "</div>",
        unsafe_allow_html=True,
    )

    # 3x2 grid of path cards
    for row_start in (0, 3):
        cols = st.columns(3)
        for j, col in enumerate(cols):
            idx = row_start + j
            if idx >= len(LEARNING_PATHS):
                break
            path = LEARNING_PATHS[idx]
            with col:
                path_badges = " ".join(
                    goal_badge_html(g) for g in path.get("goal_tags", [])
                )
                st.markdown(
                    f"<div style='background:{path['color']};color:{path['text_color']};"
                    f"border-radius:14px;padding:20px;min-height:200px;"
                    f"box-shadow:0 2px 8px rgba(0,0,0,0.06);'>"
                    f"<div style='font-size:1.15em;font-weight:700;'>{path['name']}</div>"
                    f"<div style='display:flex;gap:8px;margin:6px 0;flex-wrap:wrap;'>"
                    f"<span style='background:rgba(255,255,255,0.3);padding:2px 8px;"
                    f"border-radius:20px;font-size:0.75em;'>{path['audience']}</span>"
                    f"<span style='background:rgba(255,255,255,0.3);padding:2px 8px;"
                    f"border-radius:20px;font-size:0.75em;'>{path['levels']}</span>"
                    f"<span style='background:rgba(255,255,255,0.3);padding:2px 8px;"
                    f"border-radius:20px;font-size:0.75em;'>{path['hours']}</span>"
                    f"</div>"
                    f"<div style='font-style:italic;font-size:0.9em;margin:6px 0;'>"
                    f"\"{path['tagline']}\"</div>"
                    f"<div style='font-size:0.85em;margin-top:8px;'>"
                    f"{path['description']}</div>"
                    f"<div style='margin-top:8px;'>{path_badges}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
                with st.expander("View modules"):
                    for mod in path["modules"]:
                        st.markdown(
                            f"- **{mod['id']}**: {mod['name']} "
                            f"*({mod['type']})*"
                        )

    if "learning-centre" in _pages:
        st.page_link(
            _pages["learning-centre"],
            label="Go to Learning Centre \u2192",
            icon="\U0001f393",
        )


# ────────────────────────────────────────────────────────────────────────────
# TAB 5: THE ARENA
# ────────────────────────────────────────────────────────────────────────────

with tabs[4]:
    st.markdown("### The Arena")
    st.markdown(
        "Weekly prompt challenges that test your skills against real Harris Farm "
        "scenarios. Submit your best prompt and see how it scores."
    )

    # Active challenge hero card
    active = [c for c in ARENA_CHALLENGES if c["status"] == "active"]
    if active:
        ch = active[0]
        ch_badges = " ".join(goal_badge_html(g) for g in ch.get("goal_tags", []))
        st.markdown(
            f"<div style='background:#f0fdf4;border:3px solid #22c55e;"
            f"border-radius:14px;padding:24px;margin-bottom:20px;'>"
            f"<div style='display:flex;justify-content:space-between;align-items:center;'>"
            f"<div style='font-size:1.3em;font-weight:700;color:#166534;'>"
            f"\U0001f525 Active Challenge: {ch['title']}</div>"
            f"<span style='background:#22c55e;color:white;padding:4px 12px;"
            f"border-radius:20px;font-size:0.8em;font-weight:600;'>"
            f"{ch['difficulty']}</span>"
            f"</div>"
            f"<div style='margin-top:12px;color:#374151;line-height:1.6;'>"
            f"{ch['description']}</div>"
            f"<div style='margin-top:10px;'>{ch_badges}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    # Past challenges
    past = [c for c in ARENA_CHALLENGES if c["status"] == "past"]
    if past:
        with st.expander(f"Past challenges ({len(past)})"):
            for ch in past:
                past_badges = " ".join(goal_badge_html(g) for g in ch.get("goal_tags", []))
                st.markdown(
                    f"**{ch['week']}: {ch['title']}** "
                    f"({ch['difficulty']})"
                )
                st.markdown(f"_{ch['description']}_")
                if past_badges:
                    st.markdown(past_badges, unsafe_allow_html=True)
                st.markdown("---")

    if "agent-hub" in _pages:
        st.page_link(
            _pages["agent-hub"],
            label="View Arena Leaderboard in Agent Hub \u2192",
            icon="\U0001f916",
        )


# ────────────────────────────────────────────────────────────────────────────
# TAB 6: SHOWCASE HIGHLIGHTS
# ────────────────────────────────────────────────────────────────────────────

with tabs[5]:
    st.markdown("### Showcase Highlights")
    st.markdown(
        "Real AI implementations built by the Harris Farm team. "
        "These started as ideas and became tools that run the business."
    )

    for item in TOP_SHOWCASE:
        sc_badges = " ".join(goal_badge_html(g) for g in item.get("goal_tags", []))
        st.markdown(
            f"<div style='border-left:4px solid #059669;padding:12px 16px;"
            f"margin:12px 0;border-radius:0 8px 8px 0;"
            f"background:#f8fafc;'>"
            f"<div style='font-weight:700;font-size:1.05em;'>{item['name']}</div>"
            f"<div style='color:#059669;font-weight:600;font-size:0.9em;'>"
            f"{item['stat']}</div>"
            f"<div style='font-size:0.9em;color:#555;margin-top:4px;'>"
            f"{item['description']}</div>"
            f"<div style='margin-top:6px;'>{sc_badges}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    if "mission-control" in _pages:
        st.page_link(
            _pages["mission-control"],
            label="See all implementations in Mission Control \u2192",
            icon="\U0001f3af",
        )


# ────────────────────────────────────────────────────────────────────────────
# TAB 7: SITE QUALITY RUBRICS
# ────────────────────────────────────────────────────────────────────────────

with tabs[6]:
    st.markdown("### Site Quality Rubrics")
    st.markdown(
        "Use these rubrics to evaluate **any page in the Hub**. They drive "
        "continuous improvement and help us maintain quality as we grow."
    )

    # Dashboard Quality Rubric
    st.markdown(f"#### {DASHBOARD_QUALITY_RUBRIC['name']} ({DASHBOARD_QUALITY_RUBRIC['max_points']} pts)")
    st.markdown(f"*{DASHBOARD_QUALITY_RUBRIC['description']}*")

    for crit in DASHBOARD_QUALITY_RUBRIC["criteria"]:
        st.markdown(
            f"<div style='display:flex;align-items:center;padding:8px 0;"
            f"border-bottom:1px solid #f1f5f9;'>"
            f"<div style='width:180px;font-weight:600;'>{crit['name']}</div>"
            f"<div style='width:40px;text-align:center;color:#059669;"
            f"font-weight:700;'>/{crit['max']}</div>"
            f"<div style='flex:1;color:#555;font-size:0.9em;'>"
            f"{crit['description']}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Page Content Rubric
    st.markdown(f"#### {PAGE_CONTENT_RUBRIC['name']} ({PAGE_CONTENT_RUBRIC['max_points']} pts)")
    st.markdown(f"*{PAGE_CONTENT_RUBRIC['description']}*")

    for crit in PAGE_CONTENT_RUBRIC["criteria"]:
        st.markdown(
            f"<div style='display:flex;align-items:center;padding:8px 0;"
            f"border-bottom:1px solid #f1f5f9;'>"
            f"<div style='width:180px;font-weight:600;'>{crit['name']}</div>"
            f"<div style='width:40px;text-align:center;color:#059669;"
            f"font-weight:700;'>/{crit['max']}</div>"
            f"<div style='flex:1;color:#555;font-size:0.9em;'>"
            f"{crit['description']}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Academy self-score
    st.markdown("#### Walking the Talk: Academy Self-Score")
    st.markdown(
        "We scored this page against our own Page Content Rubric. "
        "Here's how we rate ourselves — and why."
    )

    scores = ACADEMY_SELF_SCORE["content_rubric"]
    for name, data in scores.items():
        bar_pct = data["score"] / 5 * 100
        bar_color = "#22c55e" if data["score"] >= 4 else ("#eab308" if data["score"] >= 3 else "#ef4444")
        st.markdown(
            f"<div style='margin:8px 0;'>"
            f"<div style='display:flex;justify-content:space-between;'>"
            f"<strong>{name}</strong>"
            f"<span style='color:{bar_color};font-weight:700;'>{data['score']}/5</span>"
            f"</div>"
            f"<div style='background:#e2e8f0;border-radius:4px;height:8px;margin:4px 0;'>"
            f"<div style='background:{bar_color};width:{bar_pct}%;height:100%;"
            f"border-radius:4px;'></div></div>"
            f"<div style='font-size:0.8em;color:#666;'>{data['rationale']}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.markdown(f"**Total: {ACADEMY_SELF_SCORE['content_total']}**")

    # ── Interactive page scoring ──────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### Score a Hub Page")
    st.caption(
        "Pick any page and score it against the appropriate rubric. "
        "Scores are stored and feed into the self-improvement loop."
    )

    _DATA_DASHBOARDS = {
        "Sales Dashboard", "Profitability Dashboard", "Transport Dashboard",
        "Store Operations", "Product Intelligence", "Revenue Bridge",
        "Buying Hub", "Customer Analytics", "Market Share", "Trending",
        "PLU Intelligence",
    }
    _ALL_PAGES = sorted([
        "Landing Page", "Sales Dashboard", "Profitability Dashboard",
        "Transport Dashboard", "Store Operations", "Product Intelligence",
        "Revenue Bridge", "Buying Hub", "Customer Analytics",
        "Market Share", "Trending", "The Rubric", "Prompt Builder",
        "Learning Centre", "Growing Legends Academy", "Mission Control",
        "Agent Hub", "Analytics Engine", "Agent Operations",
        "Hub Assistant", "Greater Goodness", "PLU Intelligence",
        "AI Adoption",
    ])

    _sel_page = st.selectbox("Select page to score", _ALL_PAGES,
                             key="quality_page_select")

    _is_data = _sel_page in _DATA_DASHBOARDS
    _rubric = DASHBOARD_QUALITY_RUBRIC if _is_data else PAGE_CONTENT_RUBRIC
    _rubric_type = "dashboard" if _is_data else "content"

    st.markdown(f"**Scoring against: {_rubric['name']} ({_rubric['max_points']} pts)**")

    _quality_scores = {}
    _cols = st.columns(min(len(_rubric["criteria"]), 4))
    for i, crit in enumerate(_rubric["criteria"]):
        with _cols[i % len(_cols)]:
            _quality_scores[crit["name"]] = st.slider(
                crit["name"],
                min_value=0, max_value=crit["max"],
                value=crit["max"] // 2,
                key=f"quality_{_rubric_type}_{crit['name'].lower().replace(' ', '_')}",
                help=crit["description"],
            )

    _total = sum(_quality_scores.values())
    _pct = round(_total / _rubric["max_points"] * 100, 1)
    _color = "#22c55e" if _pct >= 80 else ("#eab308" if _pct >= 60 else "#ef4444")
    st.markdown(
        f"**Total: <span style='color:{_color}'>{_total}/{_rubric['max_points']}"
        f" ({_pct}%)</span>**",
        unsafe_allow_html=True,
    )

    if st.button("Submit Score", key="quality_submit"):
        import json as _json
        _db = Path(__file__).resolve().parent.parent / "backend" / "hub_data.db"
        _scorer = (user or {}).get("email", "anonymous") if "user" in dir() else "anonymous"
        if _db.exists():
            import sqlite3 as _sql
            _conn = _sql.connect(str(_db))
            _conn.execute(
                "CREATE TABLE IF NOT EXISTS page_quality_scores "
                "(id INTEGER PRIMARY KEY AUTOINCREMENT, page_name TEXT NOT NULL, "
                "rubric_type TEXT NOT NULL, scorer TEXT DEFAULT 'anonymous', "
                "scores_json TEXT NOT NULL, total_score INTEGER NOT NULL, "
                "max_score INTEGER NOT NULL, "
                "created_at TEXT DEFAULT (datetime('now')))",
            )
            _conn.execute(
                "INSERT INTO page_quality_scores "
                "(page_name, rubric_type, scorer, scores_json, total_score, max_score) "
                "VALUES (?,?,?,?,?,?)",
                (_sel_page, _rubric_type, _scorer,
                 _json.dumps(_quality_scores), _total, _rubric["max_points"]),
            )
            _conn.commit()
            _conn.close()
            st.success(f"Score submitted: {_total}/{_rubric['max_points']} ({_pct}%)")
        else:
            st.warning("Database not found — score not saved.")

    # ── Score history ──────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### Score History")
    try:
        import json as _json
        _db = Path(__file__).resolve().parent.parent / "backend" / "hub_data.db"
        if _db.exists():
            import sqlite3 as _sql
            _conn = _sql.connect(str(_db))
            _conn.row_factory = _sql.Row
            _rows = _conn.execute(
                "SELECT page_name, rubric_type, total_score, max_score, "
                "scorer, created_at FROM page_quality_scores "
                "ORDER BY created_at DESC LIMIT 20"
            ).fetchall()
            _conn.close()
            if _rows:
                import pandas as pd
                _df = pd.DataFrame([dict(r) for r in _rows])
                _df["pct"] = (_df["total_score"] / _df["max_score"] * 100).round(1)
                st.dataframe(
                    _df.rename(columns={
                        "page_name": "Page", "rubric_type": "Rubric",
                        "total_score": "Score", "max_score": "Max",
                        "pct": "%", "scorer": "Scorer", "created_at": "Date",
                    }),
                    use_container_width=True, hide_index=True,
                )

                # Leaderboard (lowest first)
                _avg = _df.groupby("page_name").agg(
                    avg_pct=("pct", "mean"), reviews=("pct", "count"),
                ).sort_values("avg_pct").reset_index()
                st.markdown("**Pages needing most improvement (lowest first):**")
                st.dataframe(
                    _avg.rename(columns={
                        "page_name": "Page", "avg_pct": "Avg %",
                        "reviews": "Reviews",
                    }),
                    use_container_width=True, hide_index=True,
                )
            else:
                st.info("No scores recorded yet. Be the first to score a page!")
    except Exception:
        st.caption("Score history will appear after the first submission.")


# ────────────────────────────────────────────────────────────────────────────
# TAB 8: QUICK LINKS
# ────────────────────────────────────────────────────────────────────────────

with tabs[7]:
    st.markdown("### Quick Links")

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("#### Learn & Practice")
        links_learn = [
            ("learning-centre", "Learning Centre", "\U0001f393",
             "12 modules across AI, Data, and Company Knowledge"),
            ("the-rubric", "The Rubric", "\u2696\ufe0f",
             "Practice prompts, compare AI models, score responses"),
            ("prompt-builder", "Prompt Builder", "\U0001f527",
             "Design and test analytical prompts"),
            ("hub-assistant", "Hub Assistant", "\U0001f4ac",
             "Ask questions about Harris Farm data and operations"),
        ]
        for slug, label, icon, desc in links_learn:
            if slug in _pages:
                st.page_link(_pages[slug], label=f"{icon} {label}", icon=None)
                st.caption(desc)

    with c2:
        st.markdown("#### Build & Explore")
        links_build = [
            ("mission-control", "Mission Control", "\U0001f3af",
             "Documentation, data catalog, AI showcase, and governance"),
            ("ai-adoption", "AI Adoption Tracker", "\U0001f4ca",
             "Organisation-wide AI platform usage stats"),
            ("greater-goodness", "Greater Goodness", "\U0001f331",
             "Our purpose, sustainability, and community impact"),
            ("customers", "Customer Intelligence", "\U0001f465",
             "Customer insights, trends, and loyalty data"),
        ]
        for slug, label, icon, desc in links_build:
            if slug in _pages:
                st.page_link(_pages[slug], label=f"{icon} {label}", icon=None)
                st.caption(desc)


# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown(
    "<div style='background:linear-gradient(135deg, #f0fdf4, #dcfce7);"
    "border-radius:12px;padding:20px;text-align:center;margin:16px 0;'>"
    "<div style='font-size:1.3em;font-weight:700;color:#166534;'>"
    "\"Every expert was once a beginner.\"</div>"
    "<div style='font-size:0.95em;color:#059669;margin-top:8px;'>"
    "Start where you are. Use what you have. Do what you can. "
    "The journey from Seed to Legend starts with a single prompt.</div>"
    "</div>",
    unsafe_allow_html=True,
)

render_voice_data_box("general")

render_footer("Growing Legends Academy", user=user)
