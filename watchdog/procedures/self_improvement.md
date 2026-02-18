# Self-Improvement v7 | MAX 3 ATTEMPTS per criterion per cycle

1. Read last 10 audit entries, calc avg H/R/S/C/D/U/X
2. Identify lowest criterion
3. Check improvement_attempts.log — ≥3 fails → ESCALATE to operator
4. Propose improvement, test on recent low-scoring task
5. If improves: update procedure + docs, log learning, reset counter
6. If not: log "[IMPROVE] FAILED | criterion | attempt N/3 | before→after", increment counter
7. NEVER modify Laws, shutdown, or data correctness reqs
8. After any data-touching improvement: validate_data.py
9. After any UI improvement: score against design_usability rubric
