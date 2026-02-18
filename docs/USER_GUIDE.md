# Harris Farm Hub — User Guide

> For the finance team, buyers, and store managers. No technical knowledge required.

---

## What Is The Hub?

The Hub is Harris Farm's AI-powered data platform. It gives you dashboards, natural language queries, and a prompt builder — all in your browser. No Excel exports, no waiting for reports.

---

## Getting Started

### Accessing The Hub

Open your browser and go to:

| Dashboard | URL | Who It's For |
|-----------|-----|--------------|
| Sales Performance | http://localhost:8501 | Everyone |
| Store Profitability | http://localhost:8502 | Finance team |
| Transport Costs | http://localhost:8503 | Operations / logistics |
| Prompt Builder | http://localhost:8504 | Super users / analysts |
| The Rubric | http://localhost:8505 | AI comparison (everyone) |
| Trending & Analytics | http://localhost:8506 | Usage insights (everyone) |
| API (backend) | http://localhost:8000 | Developers only |

### Your Monday Morning Workflow

1. Open **Sales Dashboard** (8501) — check weekend performance
2. Look at the KPI row: revenue, profit, margin, transactions, avg basket
3. Scan the revenue trend chart — any drops?
4. Check **Store Performance** bar chart — who's up, who's down?
5. If a store looks off, switch to **Profitability** (8502) for the P&L drill-down
6. Use the **NL query box** at the bottom to ask specific questions

---

## Sales Dashboard (Port 8501)

### What You See

- **5 KPI cards** at top: Total Revenue, Gross Profit, Margin %, Transactions, Avg Transaction
- **Revenue Trend** chart: daily revenue and profit over time
- **Store Performance** bar chart: revenue by store, coloured by margin
- **Category Mix** pie chart: revenue split by product category
- **Product-Level Analytics**: out-of-stock alerts and wastage opportunities
- **Online Order Issues**: miss-pick rate, substitution rate, order accuracy

### Filters

| Filter | Options | Default |
|--------|---------|---------|
| Time Period | Last 7/30/90 days, YTD, Custom | Last 7 Days |
| Stores | Individual store selection | All Stores |
| Product Category | Fresh Produce, Dairy, Meat, Bakery, Grocery | All Categories |
| Compare To | Previous Period, Last Year, Budget, None | Previous Period |

### Asking Questions

Scroll to the bottom and type a question in plain English:
- "Which store had the highest revenue last week?"
- "What products have the highest wastage at Bondi?"
- "Show me weekend vs weekday sales trends"

Click **Search** and the Hub will generate an answer with the SQL it used.

---

## Store Profitability Dashboard (Port 8502)

### What You See

- **Network KPIs**: total revenue, gross profit, net profit, best/worst performer
- **Waterfall chart**: revenue → COGS → gross profit → costs → net profit
- **Store comparison**: horizontal bar chart of net profit by store
- **Margin vs Revenue scatter**: bubble chart showing store size, margin, and revenue
- **P&L table**: full store-by-store breakdown (revenue, COGS, labour, rent, utilities, net profit)
- **Transport cost impact**: what-if analysis of delivery cost reduction
- **Insights panel**: auto-generated strong performers and action items

### Key Metrics Explained

| Metric | What It Means |
|--------|---------------|
| Gross Profit | Revenue minus cost of goods sold |
| Net Profit | What's left after all costs (COGS + labour + rent + utilities + other) |
| Margin % | Net profit as a percentage of revenue |
| $/sqm | Revenue per square metre — efficiency measure |

---

## Transport Dashboard (Port 8503)

### What You See

- **Cost overview KPIs**: total cost, deliveries, avg cost/delivery, total distance, $/km
- **Cost components**: pie chart of fuel, driver, vehicle, maintenance breakdown
- **Route efficiency**: bar chart and scatter plot comparing routes
- **Cost trends**: daily time series of total, driver, and fuel costs
- **Optimisation opportunities**: route consolidation and fleet analysis
- **Scenario modelling**: slider to project savings at different reduction targets

### Using the Scenario Slider

1. Find the "Target Cost Reduction %" slider
2. Drag to your target (default: 15%)
3. The stacked bar chart updates to show current vs optimised costs
4. Read the projected annual savings below

---

## Prompt Builder (Port 8504)

### What It Does

Lets you design, test, save, and share custom analytical queries — without writing SQL.

### Four Tabs

1. **Design**: Build your question step by step (data sources, filters, output format)
2. **Test**: Preview the generated SQL, run it, see results and AI analysis
3. **Save & Share**: Name it, tag it, schedule it, share with teams
4. **Examples**: Learn from pre-built prompts by other super users

### Pre-Built Templates

| Template | What It Does |
|----------|-------------|
| Out of Stock Alert | Products OOS for 4+ hours, estimated lost sales |
| High Wastage Analysis | Products with >15% wastage, cost impact and trend |
| Online Miss-Pick Report | Miss-picks by picker, product, and customer impact |
| Over-Ordering Detection | Products ordered 10%+ above sales consistently |

---

## The Rubric — AI Comparison Tool (Port 8505)

### What It Does

Sends the same question to multiple AI models (Claude, ChatGPT, Grok) at the same time, shows their answers side-by-side, and lets you pick the best one. This helps the system learn which AI performs best for different types of questions.

### How to Use It

1. Open http://localhost:8505
2. Type your business question
3. Select which AI models to include (at least one)
4. Click "Run The Rubric"
5. Compare the responses side-by-side
6. Pick the winner and (optionally) explain why
7. Click "Record Decision"

### Tips for Good Comparisons

- Ask specific business questions, not generic ones
- Include context about Harris Farm (the "Additional context" box)
- Try different question types: strategy, analysis, recommendations
- Check the Performance History to see which AI wins most often

---

## Trending & Self-Improvement (Port 8506)

### What It Does

Shows how the Hub is being used and how it's getting smarter over time.

### What You See

- **Weekly KPIs**: Total queries, average rating, SQL success rate, template count
- **LLM Performance**: Which AI wins most often in The Rubric comparisons
- **Top Rated Queries**: Questions that got the highest user ratings
- **Popular Templates**: Most-used prompt templates from the library
- **System Health**: Real-time status of all Hub services
- **Feedback Form**: Rate any query result from 1-5 stars

### How You Help The Hub Improve

Every time you rate a query result or pick a Rubric winner, you're teaching the system. The Hub tracks which types of questions work best, which AI gives better answers, and which templates are most useful.

---

## Tips & Best Practices

1. **Start with the KPIs** — they tell you if something needs attention
2. **Use filters to narrow down** — don't try to look at everything at once
3. **Ask the NL query box** — it's faster than building a custom report
4. **Save useful queries** in the Prompt Builder so your team can reuse them
5. **Check the comparison toggle** — "vs Last Year" and "vs Budget" reveal trends

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Dashboard won't load | Check that services are running: `curl http://localhost:8501` |
| "Connection Error" on query | API may be down. Check http://localhost:8000 |
| Data looks wrong | Mock data is deterministic (seeded). Real data requires DB connection. Report discrepancies to Gus |
| Charts not rendering | Try refreshing the page (Ctrl+R / Cmd+R) |
| Need help | Contact hub-support@harrisfarm.com or #harris-farm-hub on Slack |
