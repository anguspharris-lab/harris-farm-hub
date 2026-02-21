"""
Harris Farm Hub — WATCHDOG Background Scheduler
Runs periodic health checks, code audits, score backfills, and metrics snapshots.
Logs everything to watchdog/audit.log.
"""

import json
import os
import sqlite3
import threading
import urllib.request
from datetime import datetime, timedelta

PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
AUDIT_LOG = os.path.join(PROJECT_ROOT, "watchdog", "audit.log")
DEFAULT_DB = os.path.join(os.path.dirname(__file__), "hub_data.db")


class WatchdogScheduler:
    """Background scheduler that runs WATCHDOG checks on a timer."""

    def __init__(self, interval_hours=6, db_path=None):
        self.interval = interval_hours * 3600
        self.interval_hours = interval_hours
        self.db_path = db_path or DEFAULT_DB
        self._timer = None
        self.last_run = None
        self.next_run = None
        self.run_count = 0
        self.last_results = {}

    def start(self, delay=120):
        """Start the scheduler. First run after `delay` seconds."""
        self._timer = threading.Timer(delay, self._run_cycle)
        self._timer.daemon = True
        self._timer.start()
        self.next_run = (datetime.now() + timedelta(seconds=delay)).isoformat()

    def stop(self):
        """Cancel the pending timer."""
        if self._timer:
            self._timer.cancel()
            self._timer = None

    def status(self):
        """Return scheduler status dict."""
        return {
            "running": self._timer is not None,
            "interval_hours": self.interval_hours,
            "last_run": self.last_run,
            "next_run": self.next_run,
            "run_count": self.run_count,
            "last_results": self.last_results,
        }

    # ── Core cycle ────────────────────────────────────────────────────────

    def _run_cycle(self):
        """Execute one full WATCHDOG cycle, then re-schedule."""
        start = datetime.now()
        results = {}

        try:
            # 1. Health checks
            results["health"] = self._check_health()

            # 2. Continuous improvement audit
            results["audit"] = self._run_audit()

            # 3. Score backfill
            results["scores"] = self._backfill_scores()

            # 4. Metrics snapshot
            results["metrics"] = self._collect_metrics()

            # Store run in DB
            self._store_run(results)

            elapsed = (datetime.now() - start).total_seconds()
            self._log("CYCLE", "completed in {:.1f}s | health: api:{} hub:{} | "
                      "findings: {} total, {} new | scores backfilled: {}".format(
                          elapsed,
                          results["health"].get("api", "?"),
                          results["health"].get("hub", "?"),
                          results["audit"].get("findings_total", 0),
                          results["audit"].get("findings_new", 0),
                          results["scores"].get("backfilled", 0),
                      ))
        except Exception as e:
            self._log("ERROR", "cycle failed: {}".format(e))
            results["error"] = str(e)

        self.last_run = datetime.now().isoformat()
        self.run_count += 1
        self.last_results = results

        # Re-schedule
        self._timer = threading.Timer(self.interval, self._run_cycle)
        self._timer.daemon = True
        self._timer.start()
        self.next_run = (datetime.now() + timedelta(seconds=self.interval)).isoformat()

    # ── Individual checks ─────────────────────────────────────────────────

    def _check_health(self):
        """HTTP health check on API and Hub."""
        result = {}
        for name, port in [("api", 8000), ("hub", 8500)]:
            status = self._http_check(port)
            if status == "DOWN":
                # Retry once after 2s
                import time
                time.sleep(2)
                status = self._http_check(port)
                if status == "UP":
                    status = "UP (retry)"
            result[name] = status
        self._log("HEALTH", "api:{} hub:{}".format(result["api"], result["hub"]))
        return result

    def _http_check(self, port):
        """GET localhost:port, return UP or DOWN."""
        try:
            req = urllib.request.Request(
                "http://localhost:{}".format(port),
                method="GET",
            )
            resp = urllib.request.urlopen(req, timeout=3)
            code = resp.getcode()
            return "UP" if code in (200, 302) else "DOWN ({})".format(code)
        except Exception:
            return "DOWN"

    def _run_audit(self):
        """Run the continuous improvement audit."""
        try:
            from continuous_improvement import run_full_audit
            result = run_full_audit(db_path=self.db_path)
            summary = {
                "findings_total": result.get("findings_count", 0),
                "findings_new": result.get("new_findings", 0),
                "by_severity": result.get("by_severity", {}),
            }
            self._log("AUDIT", "findings:{} new:{} severity:{}".format(
                summary["findings_total"],
                summary["findings_new"],
                json.dumps(summary["by_severity"]),
            ))
            return summary
        except Exception as e:
            self._log("AUDIT", "failed: {}".format(e))
            return {"error": str(e)}

    def _backfill_scores(self):
        """Backfill WATCHDOG scores from audit log into task_scores."""
        try:
            from self_improvement import backfill_scores_from_audit
            count = backfill_scores_from_audit() or 0
            if count > 0:
                self._log("SCORES", "backfilled:{}".format(count))
            return {"backfilled": count}
        except Exception as e:
            self._log("SCORES", "failed: {}".format(e))
            return {"error": str(e)}

    def _collect_metrics(self):
        """Collect health metrics snapshot."""
        try:
            from continuous_improvement import HealthMetricsCollector
            return HealthMetricsCollector().collect()
        except Exception as e:
            return {"error": str(e)}

    # ── Storage ───────────────────────────────────────────────────────────

    def _store_run(self, results):
        """Write run results to watchdog_runs table."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute(
                "INSERT INTO watchdog_runs "
                "(run_at, health_api, health_hub, findings_total, findings_new, "
                "scores_backfilled, health_metrics_json) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    datetime.now().isoformat(),
                    results.get("health", {}).get("api", "unknown"),
                    results.get("health", {}).get("hub", "unknown"),
                    results.get("audit", {}).get("findings_total", 0),
                    results.get("audit", {}).get("findings_new", 0),
                    results.get("scores", {}).get("backfilled", 0),
                    json.dumps(results.get("metrics", {})),
                ),
            )
            conn.commit()
            conn.close()
        except Exception:
            pass  # Table may not exist yet on first run

    def _log(self, category, message):
        """Append to watchdog/audit.log."""
        try:
            os.makedirs(os.path.dirname(AUDIT_LOG), exist_ok=True)
            with open(AUDIT_LOG, "a") as f:
                f.write("[WATCHDOG] {} | {} | {}\n".format(
                    datetime.now().isoformat(), category, message,
                ))
        except Exception:
            pass
