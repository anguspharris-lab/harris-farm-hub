# Data Correctness v7

## Before displaying any number:
1. Log source query + row count
2. Checksum key column → watchdog/data_checksums/
3. Cross-validate against control total
4. Range check (no negative revenue, no future dates, qty <100k)
5. Null check (flag, never silently drop)
6. Type check + float tolerance ±0.01

## Mock→real switchover:
Side-by-side → log differences → operator confirms

## Validation fail: do NOT display. Show reason. Log FAIL. Alert operator.
