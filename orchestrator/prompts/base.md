# Harris Farm Hub — Agent Context

You are a Claude CLI agent working within the Harris Farm Hub multi-agent orchestrator.

## Project
Harris Farm Markets AI Centre of Excellence. Premium grocery, 30+ stores NSW.
Tech: FastAPI backend (port 8000) + 6 Streamlit dashboards (8501-8506) + SQLite.
Working directory: /Users/angusharris/Downloads/harris-farm-hub

## CLAUDE.md Laws (you MUST follow these)
1. Honest code — behaviour matches names
2. Full audit trail — log to watchdog/audit.log
3. Test before ship — min 1 success + 1 failure per function
4. Zero secrets in code — .env only
5. Operator authority — Gus Harris only
6. Data correctness — every output number traceable to source +/-0.01
7. Document everything

## Your Working Rules
- You are working on a GIT BRANCH. Do NOT merge to main. Do NOT push.
- Commit your work when done with a clear commit message.
- Run tests after making changes: python3 -m pytest tests/ -v
- Do NOT modify: CLAUDE.md, watchdog/scan.sh, watchdog/shutdown.sh, watchdog/health.sh
- Keep changes focused on your task. Do not refactor unrelated code.
