"""Safety Bot — runs all validation checks between phases."""
import subprocess
import re
import json
import time
import os
from pathlib import Path
from typing import List
from .models import SafetyCheckResult, SafetyReport, SafetyVerdict, WorkerResult
from .audit import log_safety, log_error

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Individual safety checks
# ---------------------------------------------------------------------------

def run_pytest() -> SafetyCheckResult:
    """Run the full pytest suite. HARD GATE."""
    start = time.time()
    result = subprocess.run(
        ["python3", "-m", "pytest", "tests/", "-v", "--tb=short"],
        cwd=str(PROJECT_ROOT),
        capture_output=True, text=True,
        timeout=120,
    )
    duration = time.time() - start

    passed = result.returncode == 0
    # Extract summary line
    summary = ""
    for line in reversed(result.stdout.split("\n")):
        if "passed" in line or "failed" in line or "error" in line:
            summary = line.strip()
            break

    verdict = SafetyVerdict.PASS if passed else SafetyVerdict.FAIL
    details = summary or result.stderr[-300:]
    log_safety("pytest", verdict.value, details)

    return SafetyCheckResult(
        check_name="pytest",
        verdict=verdict,
        details=details,
        duration_seconds=duration,
    )


def run_scan_sh() -> SafetyCheckResult:
    """Run watchdog/scan.sh — checks for hardcoded secrets. HARD GATE."""
    start = time.time()
    result = subprocess.run(
        ["bash", "watchdog/scan.sh"],
        cwd=str(PROJECT_ROOT),
        capture_output=True, text=True,
        timeout=30,
    )
    duration = time.time() - start

    passed = result.returncode == 0
    verdict = SafetyVerdict.PASS if passed else SafetyVerdict.FAIL
    details = result.stdout.strip() or result.stderr.strip()
    log_safety("scan_sh", verdict.value, details)

    return SafetyCheckResult(
        check_name="scan_sh",
        verdict=verdict,
        details=details,
        duration_seconds=duration,
    )


def run_health_sh() -> SafetyCheckResult:
    """Run watchdog/health.sh — service health. SOFT GATE (warn only)."""
    start = time.time()
    result = subprocess.run(
        ["bash", "watchdog/health.sh"],
        cwd=str(PROJECT_ROOT),
        capture_output=True, text=True,
        timeout=60,
    )
    duration = time.time() - start

    passed = "ALL HEALTHY" in result.stdout
    verdict = SafetyVerdict.PASS if passed else SafetyVerdict.WARN
    details = result.stdout.strip()[-200:]
    log_safety("health_sh", verdict.value, details)

    return SafetyCheckResult(
        check_name="health_sh",
        verdict=verdict,
        details=details,
        duration_seconds=duration,
    )


def review_git_diff(branch_name: str) -> SafetyCheckResult:
    """Review git diff for protected files and secrets. HARD GATE."""
    start = time.time()

    # Get changed file names
    name_result = subprocess.run(
        ["git", "diff", "--name-only", "main", branch_name],
        cwd=str(PROJECT_ROOT),
        capture_output=True, text=True,
    )
    changed_files = [f for f in name_result.stdout.strip().split("\n") if f]

    # Get full diff
    diff_result = subprocess.run(
        ["git", "diff", "main", branch_name],
        cwd=str(PROJECT_ROOT),
        capture_output=True, text=True,
    )
    diff_text = diff_result.stdout

    issues = []

    # Check protected files
    protected = [
        "watchdog/scan.sh", "watchdog/shutdown.sh",
        "watchdog/health.sh", "CLAUDE.md",
        "watchdog/.claude_md_checksum",
    ]
    for f in changed_files:
        if f in protected:
            issues.append(f"PROTECTED FILE MODIFIED: {f}")

    # Check for secret patterns in diff
    secret_patterns = [
        r'(?i)(api[_-]?key|password|secret)\s*=\s*["\'][^"\']{8,}["\']',
        r'sk-[a-zA-Z0-9]{20,}',
        r'AKIA[A-Z0-9]{16}',
    ]
    for pattern in secret_patterns:
        if re.search(pattern, diff_text):
            issues.append(f"POTENTIAL SECRET in diff matching: {pattern}")

    # Check for test file deletions
    for f in changed_files:
        if f.startswith("tests/") and f.endswith(".py"):
            if f"--- a/{f}" in diff_text and "+++ /dev/null" in diff_text:
                issues.append(f"TEST FILE DELETED: {f}")

    duration = time.time() - start

    if issues:
        verdict = SafetyVerdict.FAIL
        details = "; ".join(issues)
    else:
        verdict = SafetyVerdict.PASS
        details = f"{len(changed_files)} files changed, no safety issues"

    log_safety("diff_review", verdict.value, details)

    return SafetyCheckResult(
        check_name="diff_review",
        verdict=verdict,
        details=details,
        duration_seconds=duration,
    )


def review_diff_with_llm(branch_name: str) -> SafetyCheckResult:
    """Use Anthropic SDK for deeper diff review and scoring.

    Scores H/R/S/C/D/U/X. Degrades to WARN if no API key.
    HARD GATE when API key is available.
    """
    start = time.time()

    diff_result = subprocess.run(
        ["git", "diff", "main", branch_name],
        cwd=str(PROJECT_ROOT),
        capture_output=True, text=True,
    )
    diff_text = diff_result.stdout

    if not diff_text.strip():
        return SafetyCheckResult(
            check_name="llm_review",
            verdict=SafetyVerdict.PASS,
            details="No changes to review",
            duration_seconds=0,
        )

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return SafetyCheckResult(
            check_name="llm_review",
            verdict=SafetyVerdict.WARN,
            details="No ANTHROPIC_API_KEY — skipping LLM review",
            duration_seconds=0,
        )

    # Truncate large diffs
    if len(diff_text) > 15000:
        diff_text = diff_text[:15000] + "\n... [truncated]"

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        review_prompt = (
            "Review this git diff for a Harris Farm Markets retail analytics project. "
            "Score on 7 criteria (1-10 each): H=Honest, R=Reliable, S=Safe, C=Clean, "
            "D=DataCorrect, U=Usable, X=Documented.\n\n"
            "Check for: function names matching behaviour, hardcoded credentials, "
            "file ops outside project, fake tests, untraceable data outputs.\n\n"
            'Respond with ONLY valid JSON: {"verdict":"pass" or "fail", '
            '"scores":{"H":N,"R":N,"S":N,"C":N,"D":N,"U":N,"X":N}, '
            '"issues":["..."], "summary":"one line"}\n\n'
            f"Diff:\n{diff_text}"
        )

        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=500,
            messages=[{"role": "user", "content": review_prompt}],
        )

        response_text = message.content[0].text.strip()
        # Extract JSON from response (may have surrounding text)
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if not json_match:
            raise ValueError("No JSON found in LLM response")

        review_data = json.loads(json_match.group())
        scores = review_data.get("scores", {})
        avg_score = sum(scores.values()) / len(scores) if scores else 0

        verdict_str = review_data.get("verdict", "fail")
        if any(v < 5 for v in scores.values()):
            verdict_str = "fail"
        if avg_score < 7.0:
            verdict_str = "fail"

        verdict = SafetyVerdict.PASS if verdict_str == "pass" else SafetyVerdict.FAIL
        details = f"avg={avg_score:.1f} | {review_data.get('summary', '')} | scores={scores}"

        log_safety("llm_review", verdict.value, details)

        return SafetyCheckResult(
            check_name="llm_review",
            verdict=verdict,
            details=details,
            duration_seconds=time.time() - start,
        )
    except Exception as e:
        log_error("llm_review", str(e))
        return SafetyCheckResult(
            check_name="llm_review",
            verdict=SafetyVerdict.WARN,
            details=f"LLM review failed: {e}",
            duration_seconds=time.time() - start,
        )


# ---------------------------------------------------------------------------
# Aggregated safety pipeline
# ---------------------------------------------------------------------------

def run_safety_pipeline(
    phase_num: int,
    worker_results: List[WorkerResult],
) -> SafetyReport:
    """Run the full safety pipeline between phases.

    Pipeline:
    1. pytest (HARD)
    2. scan.sh (HARD)
    3. health.sh (SOFT — warn only)
    4. Git diff review per branch (HARD)
    5. LLM diff review per branch (HARD if API key present, else WARN)
    """
    checks: List[SafetyCheckResult] = []

    checks.append(run_pytest())
    checks.append(run_scan_sh())
    checks.append(run_health_sh())

    for wr in worker_results:
        if wr.exit_code == 0 and wr.branch_name:
            checks.append(review_git_diff(wr.branch_name))
            checks.append(review_diff_with_llm(wr.branch_name))

    # Overall: FAIL if any hard gate failed (health_sh is soft, llm_review degrades)
    soft_checks = {"health_sh"}
    hard_fails = [
        c for c in checks
        if c.verdict == SafetyVerdict.FAIL and c.check_name not in soft_checks
    ]

    overall = SafetyVerdict.FAIL if hard_fails else SafetyVerdict.PASS

    # Extract scores from LLM review
    scores = {}
    for c in checks:
        if c.check_name == "llm_review" and "scores=" in c.details:
            try:
                scores_str = c.details.split("scores=")[1]
                scores = json.loads(scores_str.replace("'", '"'))
            except Exception:
                pass

    return SafetyReport(
        phase=phase_num,
        checks=checks,
        overall_verdict=overall,
        scores=scores,
    )
