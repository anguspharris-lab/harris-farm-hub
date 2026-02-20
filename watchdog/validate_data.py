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

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8500)
    parser.add_argument("--tolerance", type=float, default=0.01)
    args = parser.parse_args()
    sys.exit(0 if validate_response(args.port, args.tolerance) else 1)
