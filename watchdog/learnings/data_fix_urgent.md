# URGENT DATA FIX — from Gus Harris 13 Feb 11:55pm

## Problems:
1. Sales dashboard shows postcode market share — WRONG. Must show transactional sales.
2. Mock data is not realistic — random numbers don't reflect real store patterns
3. datetime.now().normalize() error — replace with datetime.now().replace(hour=0,minute=0,second=0,microsecond=0)

## Requirements:
- Sales logged by STORE (actual HFM store network), not by postcode
- Time periods: daily, weekly, monthly — use proper calendar
- Revenue and margin from aggregated transactions
- Market share by postcode is a SEPARATE strategic dashboard, not the sales view
- Mock data must follow realistic retail patterns: weekday/weekend variation, seasonal trends, store size differences
- All dollar figures must reconcile: daily totals sum to weekly, weekly to monthly

## Fix priority: HIGH — do this before anything else next session

## STATUS: FIXED — 14 Feb 2026
All items addressed in sales_dashboard.py rewrite. See data_context.md for rules.

## ALL DASHBOARDS AFFECTED — not just sales
- Sales (8501): must be by STORE SITE not postcode
- Profitability (8502): P&L by STORE SITE not postcode
- Transport (8503): routes between STORE SITES and distribution centre
- Prompt Builder (8504): queries should reference store names not postcodes

## Harris Farm store network is the primary dimension for ALL operational dashboards
## Postcode/market share is ONLY for the separate strategic analysis view
