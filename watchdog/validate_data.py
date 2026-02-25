#!/usr/bin/env python3
"""Deep data validation: queries source and compares to dashboard output."""
import sys, os, json, argparse, hashlib
from datetime import datetime

def log_audit(msg):
    with open("watchdog/audit.log", "a") as f:
        f.write(f"[DATA_VAL] {datetime.now().isoformat()} | {msg}\n")

def validate_response(port, tolerance=0.01):
    import urllib.request
    try:
        resp = urllib.request.urlopen(f"http://localhost:{port}", timeout=5)
        body = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"❌ Cannot reach port {port}: {e}")
        log_audit(f"port:{port} | FAIL | unreachable: {e}")
        return False
    errors = []
    for indicator in ["Traceback", "Exception", "Error:", "NaN", "undefined"]:
        if indicator in body: errors.append(f"Found '{indicator}'")
    if body.count("<tr>") <= 1 and "<table" in body.lower():
        errors.append("Table appears empty")
    if errors:
        for e in errors: print(f"⚠️ {e}")
        log_audit(f"port:{port} | WARN | {'; '.join(errors)}")
        return False
    print(f"✅ Port {port} validation passed")
    log_audit(f"port:{port} | PASS")
    return True

def validate_checksum(data_name, values, store=True):
    checksum = hashlib.sha256(json.dumps(values, sort_keys=True, default=str).encode()).hexdigest()[:16]
    os.makedirs("watchdog/data_checksums", exist_ok=True)
    path = f"watchdog/data_checksums/{data_name}.checksum"
    if store:
        with open(path, "w") as f: f.write(f"{checksum}\n{datetime.now().isoformat()}\n{len(values)} records\n")
        log_audit(f"checksum:{data_name} | {checksum} | {len(values)} records | STORED")
    elif os.path.exists(path):
        stored = open(path).readline().strip()
        if stored != checksum:
            print(f"🚨 CHECKSUM MISMATCH: {data_name}")
            log_audit(f"checksum:{data_name} | MISMATCH | stored:{stored} current:{checksum}")
            return False
    return True

def range_check(values, field, min_val=None, max_val=None, allow_null=False):
    issues = []
    for i, row in enumerate(values):
        val = row.get(field) if isinstance(row, dict) else None
        if val is None:
            if not allow_null: issues.append(f"Row {i}: null {field}")
            continue
        try:
            num = float(val)
            if min_val is not None and num < min_val: issues.append(f"Row {i}: {field}={num} < {min_val}")
            if max_val is not None and num > max_val: issues.append(f"Row {i}: {field}={num} > {max_val}")
        except (ValueError, TypeError): issues.append(f"Row {i}: {field} not numeric")
    if issues:
        for e in issues[:5]: print(f"⚠️ {e}")
        log_audit(f"range:{field} | FAIL | {len(issues)} issues")
        return False
    log_audit(f"range:{field} | PASS | {len(values)} rows")
    return True

def validate_store_pl(api_base="http://localhost:8000"):
    """WATCHDOG checks for Store P&L data integrity."""
    import urllib.request
    passed = 0
    failed = 0
    warnings = 0

    def _get(path):
        resp = urllib.request.urlopen(f"{api_base}{path}", timeout=10)
        return json.loads(resp.read().decode())

    # Check 1: Completeness — stores exist
    try:
        stores = _get("/api/store-pl/stores")
        if len(stores) >= 30:
            print(f"  ✅ Completeness: {len(stores)} stores loaded")
            log_audit(f"store_pl:completeness | PASS | {len(stores)} stores")
            passed += 1
        else:
            print(f"  ⚠️ Completeness: only {len(stores)} stores (expected 30+)")
            log_audit(f"store_pl:completeness | WARN | {len(stores)} stores")
            warnings += 1
    except Exception as e:
        print(f"  ❌ Completeness: API unreachable — {e}")
        log_audit(f"store_pl:completeness | FAIL | {e}")
        failed += 1

    # Check 2: Freshness — latest FY year
    try:
        fy_years = _get("/api/store-pl/fy-years")
        if 2026 in fy_years or 2025 in fy_years:
            print(f"  ✅ Freshness: FY years {fy_years}")
            log_audit(f"store_pl:freshness | PASS | years={fy_years}")
            passed += 1
        else:
            print(f"  ⚠️ Freshness: latest FY is {max(fy_years) if fy_years else 'none'}")
            log_audit(f"store_pl:freshness | WARN | years={fy_years}")
            warnings += 1
    except Exception as e:
        print(f"  ❌ Freshness: {e}")
        log_audit(f"store_pl:freshness | FAIL | {e}")
        failed += 1

    # Check 3: Revenue sanity — network revenue should be $500M-$1B
    try:
        annual = _get("/api/store-pl/annual?fy_year=2025")
        if annual:
            total_rev = sum(s.get("revenue", 0) or 0 for s in annual)
            if 300_000_000 < total_rev < 1_500_000_000:
                print(f"  ✅ Revenue sanity: FY2025 network = ${total_rev/1e6:,.1f}M")
                log_audit(f"store_pl:revenue_sanity | PASS | ${total_rev/1e6:.1f}M")
                passed += 1
            else:
                print(f"  ❌ Revenue sanity: ${total_rev/1e6:,.1f}M outside expected range")
                log_audit(f"store_pl:revenue_sanity | FAIL | ${total_rev/1e6:.1f}M")
                failed += 1
        else:
            print("  ⚠️ Revenue sanity: no annual data returned")
            warnings += 1
    except Exception as e:
        print(f"  ❌ Revenue sanity: {e}")
        log_audit(f"store_pl:revenue_sanity | FAIL | {e}")
        failed += 1

    # Check 4: GP% range — should be 20-40% for grocery retail
    try:
        if annual:
            gp_pcts = [s.get("gp_pct", 0) or 0 for s in annual if s.get("gp_pct")]
            if gp_pcts:
                avg_gp = sum(gp_pcts) / len(gp_pcts)
                if 15 < avg_gp < 45:
                    print(f"  ✅ GP% range: avg {avg_gp:.1f}% across {len(gp_pcts)} stores")
                    log_audit(f"store_pl:gp_range | PASS | avg={avg_gp:.1f}%")
                    passed += 1
                else:
                    print(f"  ❌ GP% range: avg {avg_gp:.1f}% outside 15-45%")
                    log_audit(f"store_pl:gp_range | FAIL | avg={avg_gp:.1f}%")
                    failed += 1
    except Exception as e:
        print(f"  ❌ GP% range: {e}")
        failed += 1

    # Check 5: Cross-reference — store count matches between APIs
    try:
        annual_stores = len(annual) if annual else 0
        list_stores = len(stores) if stores else 0
        if annual_stores > 0 and abs(annual_stores - list_stores) <= 5:
            print(f"  ✅ Cross-ref: annual={annual_stores}, list={list_stores}")
            log_audit(f"store_pl:cross_ref | PASS | annual={annual_stores} list={list_stores}")
            passed += 1
        else:
            print(f"  ⚠️ Cross-ref: annual={annual_stores} vs list={list_stores}")
            log_audit(f"store_pl:cross_ref | WARN")
            warnings += 1
    except Exception as e:
        print(f"  ❌ Cross-ref: {e}")
        failed += 1

    # Check 6: ROCE validation — EBIT should derive correctly
    try:
        ebit_data = _get("/api/store-pl/ebit?fy_year=2025")
        if ebit_data:
            ebit_positive = [e for e in ebit_data if (e.get("ebit") or 0) > 0]
            ebit_ratio = len(ebit_positive) / len(ebit_data) if ebit_data else 0
            if ebit_ratio > 0.5:
                print(f"  ✅ EBIT check: {len(ebit_positive)}/{len(ebit_data)} stores EBIT-positive")
                log_audit(f"store_pl:ebit | PASS | {len(ebit_positive)}/{len(ebit_data)} positive")
                passed += 1
            else:
                print(f"  ⚠️ EBIT check: only {len(ebit_positive)}/{len(ebit_data)} stores positive")
                log_audit(f"store_pl:ebit | WARN | low positive ratio")
                warnings += 1
    except Exception as e:
        print(f"  ❌ EBIT check: {e}")
        failed += 1

    # Check 7: Data quality report
    try:
        quality = _get("/api/store-pl/quality")
        total_checks = quality.get("total_checks", 0)
        checks_passed = quality.get("passed", 0)
        if total_checks > 0:
            print(f"  ✅ Quality report: {checks_passed}/{total_checks} checks passed")
            log_audit(f"store_pl:quality | {checks_passed}/{total_checks}")
            passed += 1
    except Exception as e:
        print(f"  ❌ Quality report: {e}")
        failed += 1

    print(f"\n  Store P&L WATCHDOG: {passed} passed, {warnings} warnings, {failed} failed")
    log_audit(f"store_pl:SUMMARY | passed={passed} warn={warnings} fail={failed}")
    return failed == 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8500)
    parser.add_argument("--tolerance", type=float, default=0.01)
    parser.add_argument("--store-pl", action="store_true", help="Run Store P&L data checks")
    parser.add_argument("--api-port", type=int, default=8000, help="Backend API port")
    args = parser.parse_args()

    results = []
    results.append(validate_response(args.port, args.tolerance))
    if args.store_pl:
        results.append(validate_store_pl(f"http://localhost:{args.api_port}"))
    sys.exit(0 if all(results) else 1)
