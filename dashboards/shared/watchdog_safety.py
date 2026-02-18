"""
Harris Farm Hub — WATCHDOG Safety Service
Every agent proposal, suggestion, or action MUST pass through WATCHDOG
before reaching humans. No exceptions. No bypasses.

Risk Levels:
    SAFE (Green)     — No issues, low impact, easily reversible
    LOW (Yellow)     — Minor concerns, requires human review
    MEDIUM (Orange)  — Significant concerns, careful review needed
    HIGH (Red)       — Critical concerns, senior approval required
    BLOCKED (Black)  — Unsafe, violates policy, must not proceed
"""

import hashlib
import json
import logging
import re
import sqlite3
from datetime import datetime

logger = logging.getLogger("watchdog_safety")


# ---------------------------------------------------------------------------
# RISK LEVELS
# ---------------------------------------------------------------------------

RISK_SAFE = "SAFE"
RISK_LOW = "LOW"
RISK_MEDIUM = "MEDIUM"
RISK_HIGH = "HIGH"
RISK_BLOCKED = "BLOCKED"

RISK_LEVELS = [RISK_SAFE, RISK_LOW, RISK_MEDIUM, RISK_HIGH, RISK_BLOCKED]

RISK_COLORS = {
    RISK_SAFE: "#22c55e",
    RISK_LOW: "#eab308",
    RISK_MEDIUM: "#f97316",
    RISK_HIGH: "#ef4444",
    RISK_BLOCKED: "#1f2937",
}

RISK_ICONS = {
    RISK_SAFE: "✅",
    RISK_LOW: "⚠️",
    RISK_MEDIUM: "🟠",
    RISK_HIGH: "🔴",
    RISK_BLOCKED: "⛔",
}


# ---------------------------------------------------------------------------
# SAFETY PATTERNS — what WATCHDOG scans for
# ---------------------------------------------------------------------------

SQL_INJECTION_PATTERNS = [
    r";\s*(DROP|DELETE|UPDATE|INSERT|ALTER|CREATE|TRUNCATE)\s",
    r"'\s*OR\s+'?\d*'?\s*=\s*'?\d*",
    r"UNION\s+SELECT",
    r"--\s*$",
    r"/\*.*\*/",
    r"xp_cmdshell",
    r"EXEC\s*\(",
    r"EXECUTE\s*\(",
    r"INTO\s+OUTFILE",
    r"LOAD_FILE\s*\(",
]

UNSAFE_FILE_PATTERNS = [
    r"os\.system\s*\(",
    r"subprocess\.(call|run|Popen)\s*\(",
    r"eval\s*\(",
    r"exec\s*\(",
    r"__import__\s*\(",
    r"open\s*\([^)]*['\"]w['\"]",
    r"shutil\.rmtree\s*\(",
    r"os\.remove\s*\(",
    r"os\.unlink\s*\(",
    r"pathlib.*\.unlink\s*\(",
]

CREDENTIAL_PATTERNS = [
    r"password\s*=\s*['\"][^'\"]+['\"]",
    r"api_key\s*=\s*['\"][^'\"]+['\"]",
    r"secret\s*=\s*['\"][^'\"]+['\"]",
    r"token\s*=\s*['\"][A-Za-z0-9+/=]{20,}['\"]",
    r"AWS_SECRET",
    r"PRIVATE_KEY",
]

PII_PATTERNS = [
    r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",  # Phone numbers
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email
    r"\b\d{3}-\d{2}-\d{4}\b",  # SSN-like
    r"\bTFN\b.*\d{8,9}",  # Tax file number
    r"\bABN\b.*\d{11}",  # Business number
]

RESOURCE_PATTERNS = [
    r"while\s+True\s*:",
    r"for\s+.*\s+in\s+range\s*\(\s*\d{7,}",  # Very large ranges
    r"\.read\(\s*\)",  # Reading entire files without limits
    r"SELECT\s+\*\s+FROM\s+(?!.*LIMIT)",  # SELECT * without LIMIT
]

EXTERNAL_CALL_PATTERNS = [
    r"requests\.(get|post|put|delete|patch)\s*\(",
    r"httpx\.(get|post|put|delete|patch)\s*\(",
    r"urllib\.request\.urlopen\s*\(",
    r"aiohttp\.ClientSession\s*\(",
]


# ---------------------------------------------------------------------------
# POLICY RULES
# ---------------------------------------------------------------------------

BLOCKED_ACTIONS = [
    "delete_database",
    "drop_table",
    "modify_watchdog",
    "disable_safety",
    "bypass_approval",
    "modify_audit_log",
    "access_credentials",
    "external_data_export",
    "modify_pricing_live",
    "bulk_delete_products",
]

REQUIRES_SENIOR_APPROVAL = [
    "pricing_change",
    "product_delist",
    "supplier_change",
    "financial_adjustment",
    "data_schema_change",
    "production_deployment",
    "customer_data_access",
]


# ---------------------------------------------------------------------------
# WATCHDOG SERVICE
# ---------------------------------------------------------------------------

class WatchdogService:
    """Core safety gatekeeper. All agent proposals must pass through here."""

    def __init__(self, db_path=None):
        self.db_path = db_path

    def analyze_proposal(self, proposal):
        """Main entry point. Analyze a proposal and return safety report.

        Args:
            proposal: dict with keys:
                agent_id, proposal_type, title, description,
                code_changes (optional), data_access (optional),
                expected_impact (optional), implementation_plan (optional)

        Returns:
            dict with: proposal_id, risk_level, findings, report,
                       recommendation, approved (always False initially)
        """
        tracking_id = self._generate_tracking_id(proposal)

        # Run all safety scans
        findings = []
        findings.extend(self.security_scan(proposal))
        findings.extend(self.safety_scan(proposal))
        findings.extend(self.privacy_scan(proposal))
        findings.extend(self.business_validation(proposal))
        findings.extend(self.compliance_check(proposal))

        # Calculate risk
        risk_level = self.calculate_risk_score(findings)

        # Generate report
        report = self.generate_report(proposal, findings, risk_level)

        # Generate recommendation
        recommendation = self.recommend_action(risk_level, findings)

        result = {
            "tracking_id": tracking_id,
            "agent_id": proposal.get("agent_id", "unknown"),
            "title": proposal.get("title", "Untitled"),
            "risk_level": risk_level,
            "risk_color": RISK_COLORS.get(risk_level, "#666"),
            "risk_icon": RISK_ICONS.get(risk_level, "?"),
            "findings": findings,
            "finding_count": len(findings),
            "report": report,
            "recommendation": recommendation,
            "approved": False,
            "approval_required": risk_level != RISK_BLOCKED,
            "senior_approval_required": risk_level == RISK_HIGH,
            "blocked": risk_level == RISK_BLOCKED,
            "analyzed_at": datetime.utcnow().isoformat(),
        }

        # Log to audit trail
        if self.db_path:
            self._log_analysis(result, proposal)

        return result

    # ------------------------------------------------------------------
    # SCANNING FUNCTIONS
    # ------------------------------------------------------------------

    def security_scan(self, proposal):
        """Check for security vulnerabilities."""
        findings = []
        content = self._extract_scannable_content(proposal)

        # SQL injection
        for pattern in SQL_INJECTION_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                findings.append({
                    "category": "security",
                    "severity": "critical",
                    "title": "Potential SQL injection detected",
                    "detail": "Pattern '{}' matched in proposal content".format(
                        pattern[:40]),
                    "recommendation": "Use parameterised queries. Never "
                                      "concatenate user input into SQL.",
                })

        # Unsafe file operations
        for pattern in UNSAFE_FILE_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                findings.append({
                    "category": "security",
                    "severity": "high",
                    "title": "Unsafe operation detected: {}".format(
                        matches[0][:30]),
                    "detail": "Code contains potentially dangerous operation "
                              "that could modify or delete files.",
                    "recommendation": "Use safe alternatives. Avoid eval/exec. "
                                      "Restrict file operations to project dir.",
                })

        # Hardcoded credentials
        for pattern in CREDENTIAL_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                findings.append({
                    "category": "security",
                    "severity": "critical",
                    "title": "Hardcoded credentials detected",
                    "detail": "Credential pattern found in proposal. "
                              "Secrets must never be in code.",
                    "recommendation": "Use environment variables via .env file. "
                                      "Never commit secrets to code.",
                })

        # External API calls without validation
        for pattern in EXTERNAL_CALL_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                findings.append({
                    "category": "security",
                    "severity": "medium",
                    "title": "External API call detected",
                    "detail": "Proposal makes external network calls. "
                              "Verify target domains are authorised.",
                    "recommendation": "Validate all external URLs against "
                                      "allowlist. Add timeout and error handling.",
                })

        return findings

    def safety_scan(self, proposal):
        """Check for code safety issues."""
        findings = []
        content = self._extract_scannable_content(proposal)

        # Resource exhaustion
        for pattern in RESOURCE_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                findings.append({
                    "category": "safety",
                    "severity": "high",
                    "title": "Potential resource exhaustion",
                    "detail": "Code may consume excessive resources: "
                              "{}".format(matches[0][:50]),
                    "recommendation": "Add limits, timeouts, and bounds "
                                      "checks to prevent runaway execution.",
                })

        # Blocked actions
        proposal_text = json.dumps(proposal).lower()
        for action in BLOCKED_ACTIONS:
            if action.replace("_", " ") in proposal_text:
                findings.append({
                    "category": "safety",
                    "severity": "critical",
                    "title": "Blocked action: {}".format(action),
                    "detail": "This action is prohibited by WATCHDOG policy.",
                    "recommendation": "This action cannot proceed. Contact "
                                      "system administrator if this is needed.",
                })

        # Check proposal type for high-risk actions
        proposal_type = proposal.get("proposal_type", "").lower()
        if proposal_type in ("code_change", "deployment", "schema_change"):
            findings.append({
                "category": "safety",
                "severity": "medium",
                "title": "Code/infrastructure change proposed",
                "detail": "Proposal involves changes to production code "
                          "or infrastructure. Requires careful review.",
                "recommendation": "Review all code changes line by line. "
                                  "Ensure tests pass before deployment.",
            })

        return findings

    def privacy_scan(self, proposal):
        """Check for privacy violations."""
        findings = []
        content = self._extract_scannable_content(proposal)

        # PII detection
        for pattern in PII_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                findings.append({
                    "category": "privacy",
                    "severity": "high",
                    "title": "Potential PII detected",
                    "detail": "Personal information pattern found. "
                              "Ensure data is properly anonymised.",
                    "recommendation": "Remove or mask PII. Use anonymised "
                                      "identifiers instead of real data.",
                })

        # Customer data access
        data_keywords = [
            "customer_name", "customer_email", "customer_phone",
            "customer_address", "credit_card", "payment_details",
        ]
        for keyword in data_keywords:
            if keyword in content.lower():
                findings.append({
                    "category": "privacy",
                    "severity": "high",
                    "title": "Customer data access: {}".format(keyword),
                    "detail": "Proposal accesses customer personal data. "
                              "Requires data protection review.",
                    "recommendation": "Ensure data access follows privacy "
                                      "policy. Use aggregated data where possible.",
                })

        return findings

    def business_validation(self, proposal):
        """Validate business logic and alignment."""
        findings = []

        # Check for financial impact
        impact = proposal.get("estimated_impact_aud", 0)
        if isinstance(impact, (int, float)):
            if impact > 1000000:
                findings.append({
                    "category": "business",
                    "severity": "medium",
                    "title": "High financial impact: ${:,.0f}".format(impact),
                    "detail": "Proposal claims significant financial impact. "
                              "Verify assumptions and methodology.",
                    "recommendation": "Request supporting data and sensitivity "
                                      "analysis for high-impact claims.",
                })

        # Check complexity vs effort
        effort = proposal.get("estimated_effort_weeks", 0)
        complexity = proposal.get("complexity", "medium").lower()
        if complexity == "high" and effort and effort < 4:
            findings.append({
                "category": "business",
                "severity": "low",
                "title": "Complexity/effort mismatch",
                "detail": "High complexity rated at only {} weeks. "
                          "May be underestimated.".format(effort),
                "recommendation": "Review effort estimate. High complexity "
                                  "tasks typically need 6+ weeks.",
            })

        # Check for senior approval requirement
        category = proposal.get("category", "").lower()
        for action in REQUIRES_SENIOR_APPROVAL:
            if action.replace("_", " ") in json.dumps(proposal).lower():
                findings.append({
                    "category": "business",
                    "severity": "medium",
                    "title": "Requires senior approval: {}".format(action),
                    "detail": "This action type requires approval from "
                              "senior leadership.",
                    "recommendation": "Escalate to department head or "
                                      "executive team for review.",
                })

        return findings

    def compliance_check(self, proposal):
        """Check regulatory compliance."""
        findings = []
        content = self._extract_scannable_content(proposal)

        # Food safety keywords
        food_safety_keywords = [
            "temperature", "cold chain", "expiry", "best before",
            "shelf life", "allergen", "contamination", "recall",
        ]
        for keyword in food_safety_keywords:
            if keyword in content.lower():
                findings.append({
                    "category": "compliance",
                    "severity": "medium",
                    "title": "Food safety topic: {}".format(keyword),
                    "detail": "Proposal involves food safety considerations. "
                              "Ensure compliance with food safety regulations.",
                    "recommendation": "Review against Food Standards Australia "
                                      "New Zealand (FSANZ) requirements.",
                })
                break  # One finding is enough for food safety flag

        # Financial reporting
        financial_keywords = [
            "revenue recognition", "tax", "gst", "bas",
            "financial report", "p&l", "balance sheet",
        ]
        for keyword in financial_keywords:
            if keyword in content.lower():
                findings.append({
                    "category": "compliance",
                    "severity": "medium",
                    "title": "Financial compliance: {}".format(keyword),
                    "detail": "Proposal involves financial data or reporting. "
                              "Ensure compliance with AASB standards.",
                    "recommendation": "Review with finance team for "
                                      "regulatory compliance.",
                })
                break

        return findings

    # ------------------------------------------------------------------
    # RISK SCORING
    # ------------------------------------------------------------------

    def calculate_risk_score(self, findings):
        """Calculate overall risk level from findings.

        Rules:
        - Any critical finding → BLOCKED or HIGH
        - Any critical security finding → BLOCKED
        - Multiple high findings → HIGH
        - Any high finding → MEDIUM
        - Only medium/low findings → LOW
        - No findings → SAFE
        """
        if not findings:
            return RISK_SAFE

        severities = [f.get("severity", "low") for f in findings]
        categories = [f.get("category", "") for f in findings]

        critical_count = severities.count("critical")
        high_count = severities.count("high")
        medium_count = severities.count("medium")

        # Blocked actions are always BLOCKED
        blocked = any(
            f.get("title", "").startswith("Blocked action")
            for f in findings
        )
        if blocked:
            return RISK_BLOCKED

        # Critical security findings → BLOCKED
        critical_security = sum(
            1 for f in findings
            if f.get("severity") == "critical"
            and f.get("category") == "security"
        )
        if critical_security > 0:
            return RISK_BLOCKED

        # Other critical findings → HIGH
        if critical_count > 0:
            return RISK_HIGH

        # Multiple high findings → HIGH
        if high_count >= 3:
            return RISK_HIGH

        # Any high finding → MEDIUM
        if high_count > 0:
            return RISK_MEDIUM

        # Multiple medium → LOW
        if medium_count > 0:
            return RISK_LOW

        return RISK_SAFE

    # ------------------------------------------------------------------
    # REPORT GENERATION
    # ------------------------------------------------------------------

    def generate_report(self, proposal, findings, risk_level):
        """Create human-readable safety report."""
        lines = []

        # Executive Summary
        lines.append("# WATCHDOG Safety Report")
        lines.append("")
        lines.append("## Executive Summary")
        lines.append("")
        lines.append("**Proposal:** {}".format(
            proposal.get("title", "Untitled")))
        lines.append("**Agent:** {}".format(
            proposal.get("agent_id", "Unknown")))
        lines.append("**Risk Level:** {} {}".format(
            RISK_ICONS.get(risk_level, ""), risk_level))
        lines.append("**Findings:** {} issues identified".format(
            len(findings)))
        lines.append("")

        # What the agent wants to do
        lines.append("**What:** {}".format(
            proposal.get("description", "No description provided.")))
        if proposal.get("expected_impact"):
            lines.append("**Expected Impact:** {}".format(
                proposal["expected_impact"]))
        lines.append("")

        # Detailed findings
        if findings:
            lines.append("## Detailed Findings")
            lines.append("")

            by_category = {}
            for f in findings:
                cat = f.get("category", "other")
                if cat not in by_category:
                    by_category[cat] = []
                by_category[cat].append(f)

            for cat, cat_findings in by_category.items():
                lines.append("### {} ({} issues)".format(
                    cat.title(), len(cat_findings)))
                for f in cat_findings:
                    sev = f.get("severity", "low")
                    sev_icon = {
                        "critical": "🔴", "high": "🟠",
                        "medium": "🟡", "low": "🟢",
                    }.get(sev, "⚪")
                    lines.append("- {} **{}** [{}]".format(
                        sev_icon, f["title"], sev.upper()))
                    lines.append("  - {}".format(f["detail"]))
                    lines.append("  - *Recommendation:* {}".format(
                        f["recommendation"]))
                lines.append("")
        else:
            lines.append("## Findings")
            lines.append("")
            lines.append("No safety issues detected.")
            lines.append("")

        # Recommendation
        lines.append("## WATCHDOG Recommendation")
        lines.append("")
        rec = self.recommend_action(risk_level, findings)
        lines.append("**Decision:** {}".format(rec["decision"]))
        lines.append("")
        lines.append(rec["reasoning"])
        lines.append("")

        if rec.get("modifications"):
            lines.append("**Required Modifications:**")
            for mod in rec["modifications"]:
                lines.append("- {}".format(mod))
            lines.append("")

        if rec.get("required_approvers"):
            lines.append("**Required Approvers:** {}".format(
                ", ".join(rec["required_approvers"])))

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # RECOMMENDATION
    # ------------------------------------------------------------------

    def recommend_action(self, risk_level, findings):
        """Generate WATCHDOG recommendation."""
        if risk_level == RISK_BLOCKED:
            return {
                "decision": "REJECT — Do not proceed",
                "reasoning": (
                    "This proposal contains critical safety violations that "
                    "cannot be approved. The identified issues pose "
                    "unacceptable risk to the system."
                ),
                "modifications": [],
                "required_approvers": [],
                "can_approve": False,
            }

        if risk_level == RISK_HIGH:
            mods = [f["recommendation"] for f in findings
                    if f.get("severity") in ("critical", "high")]
            return {
                "decision": "ESCALATE — Requires senior approval",
                "reasoning": (
                    "This proposal has significant risk factors that require "
                    "senior leadership review. {} critical/high issues must "
                    "be addressed.".format(len(mods))
                ),
                "modifications": mods[:5],
                "required_approvers": ["Senior Leadership", "Department Head"],
                "can_approve": True,
            }

        if risk_level == RISK_MEDIUM:
            mods = [f["recommendation"] for f in findings
                    if f.get("severity") in ("high", "medium")]
            return {
                "decision": "REVIEW — Approve with careful review",
                "reasoning": (
                    "This proposal has moderate risk factors. Review the "
                    "identified concerns before approving."
                ),
                "modifications": mods[:3],
                "required_approvers": ["Operator"],
                "can_approve": True,
            }

        if risk_level == RISK_LOW:
            return {
                "decision": "APPROVE — Low risk, minor concerns noted",
                "reasoning": (
                    "WATCHDOG has identified minor concerns. The proposal is "
                    "generally safe but review the noted items."
                ),
                "modifications": [],
                "required_approvers": ["Operator"],
                "can_approve": True,
            }

        return {
            "decision": "APPROVE — No safety concerns",
            "reasoning": (
                "WATCHDOG found no safety issues with this proposal. "
                "It appears safe to proceed after human confirmation."
            ),
            "modifications": [],
            "required_approvers": ["Operator"],
            "can_approve": True,
        }

    # ------------------------------------------------------------------
    # AUDIT LOGGING
    # ------------------------------------------------------------------

    def _log_analysis(self, result, proposal):
        """Log WATCHDOG analysis to audit database."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute(
                "INSERT INTO watchdog_audit "
                "(tracking_id, agent_id, title, risk_level, finding_count, "
                "report, proposal_json, analyzed_at) "
                "VALUES (?,?,?,?,?,?,?,?)",
                (
                    result["tracking_id"],
                    result["agent_id"],
                    result["title"],
                    result["risk_level"],
                    result["finding_count"],
                    result["report"],
                    json.dumps(proposal),
                    result["analyzed_at"],
                ),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error("WATCHDOG audit log failed: %s", e)

    def log_decision(self, tracking_id, decision, approver, comments=""):
        """Log human approval/rejection decision."""
        if not self.db_path:
            return
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute(
                "INSERT INTO watchdog_decisions "
                "(tracking_id, decision, approver, comments, decided_at) "
                "VALUES (?,?,?,?,?)",
                (tracking_id, decision, approver, comments,
                 datetime.utcnow().isoformat()),
            )

            # Update the proposal status
            conn.execute(
                "UPDATE watchdog_proposals SET status = ?, "
                "reviewed_by = ?, reviewed_at = datetime('now') "
                "WHERE tracking_id = ?",
                (decision, approver, tracking_id),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error("WATCHDOG decision log failed: %s", e)

    # ------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------

    def _extract_scannable_content(self, proposal):
        """Extract all text content from proposal for scanning."""
        parts = [
            str(proposal.get("title", "")),
            str(proposal.get("description", "")),
            str(proposal.get("implementation_plan", "")),
            str(proposal.get("expected_impact", "")),
        ]
        code_changes = proposal.get("code_changes", [])
        if isinstance(code_changes, list):
            parts.extend(str(c) for c in code_changes)
        elif isinstance(code_changes, str):
            parts.append(code_changes)

        data_access = proposal.get("data_access", "")
        if data_access:
            parts.append(str(data_access))

        return "\n".join(parts)

    def _generate_tracking_id(self, proposal):
        """Generate unique tracking ID for a proposal."""
        content = json.dumps(proposal, sort_keys=True)
        ts = datetime.utcnow().isoformat()
        raw = "{}:{}".format(ts, content)
        return "WD-" + hashlib.sha256(raw.encode()).hexdigest()[:12].upper()


# ---------------------------------------------------------------------------
# SYSTEM STATUS
# ---------------------------------------------------------------------------

SYSTEM_STATUS = {
    "watchdog_active": True,
    "human_in_loop_required": True,
    "auto_implementation_disabled": True,
    "audit_logging_active": True,
}


def get_system_status():
    """Return current WATCHDOG system status."""
    return dict(SYSTEM_STATUS)


def is_safe_to_proceed(tracking_id, db_path):
    """Check if a proposal has been approved by both WATCHDOG and a human.

    Returns (bool, str) — (can_proceed, reason)
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row

        # Check WATCHDOG analysis exists
        audit = conn.execute(
            "SELECT * FROM watchdog_audit WHERE tracking_id = ?",
            (tracking_id,),
        ).fetchone()
        if not audit:
            conn.close()
            return False, "No WATCHDOG analysis found"

        audit = dict(audit)
        if audit["risk_level"] == RISK_BLOCKED:
            conn.close()
            return False, "Proposal blocked by WATCHDOG"

        # Check human approval
        decision = conn.execute(
            "SELECT * FROM watchdog_decisions WHERE tracking_id = ? "
            "ORDER BY decided_at DESC LIMIT 1",
            (tracking_id,),
        ).fetchone()
        conn.close()

        if not decision:
            return False, "Awaiting human approval"

        decision = dict(decision)
        if decision["decision"] == "approved":
            return True, "Approved by {} on {}".format(
                decision["approver"], decision["decided_at"])
        else:
            return False, "Rejected by {} — {}".format(
                decision["approver"], decision.get("comments", ""))

    except Exception as e:
        return False, "Safety check failed: {}".format(e)
