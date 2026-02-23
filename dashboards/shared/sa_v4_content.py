"""
Skills Academy v4 — Module Content
10 modules with theory, examples, and 3-tier exercises (60 total).
Harris Farm Markets specific content.
"""

# ---------------------------------------------------------------------------
# V4_MODULES — 10 modules (L1-L5, D1-D5)
# Each has: code, series, name, level, description, lessons[], exercises[]
# Exercises: 2 standard, 2 stretch, 2 elite per module = 6 each = 60 total
# ---------------------------------------------------------------------------

V4_MODULES = [
    # ==================================================================
    # L1: PROMPT FOUNDATIONS
    # ==================================================================
    {
        "code": "L1",
        "series": "learn",
        "name": "Prompt Foundations",
        "level": 1,
        "description": "Master the building blocks of effective AI prompting — task verbs, specificity, and context.",
        "lessons": [
            {
                "order": 1,
                "title": "What Makes a Good Prompt",
                "content_md": (
                    "## The Anatomy of an Effective Prompt\n\n"
                    "A great prompt has four parts:\n\n"
                    "1. **Task Verb** — What you want done (analyse, compare, summarise, list, recommend)\n"
                    "2. **Subject** — What data or topic to work with\n"
                    "3. **Context** — Business background the AI needs\n"
                    "4. **Constraints** — Boundaries on the output\n\n"
                    "### Bad vs Good — Harris Farm Example\n\n"
                    "**Bad:** *Tell me about banana sales*\n\n"
                    "**Good:** *Analyse banana sales at our Bondi Beach store for the last 4 weeks. "
                    "Compare to the same period last year. Highlight any weeks where wastage exceeded 8% "
                    "and suggest possible causes.*\n\n"
                    "The good prompt has a clear verb (analyse), specific subject (banana sales, Bondi Beach), "
                    "context (4 weeks, YoY comparison), and constraints (wastage threshold, suggest causes).\n\n"
                    "### Key Principle\n\n"
                    "If a human colleague would need to ask you clarifying questions, your prompt isn't specific enough."
                ),
            },
            {
                "order": 2,
                "title": "Task Verbs That Work",
                "content_md": (
                    "## Choosing the Right Task Verb\n\n"
                    "The verb you start with shapes everything. At Harris Farm, the most useful verbs are:\n\n"
                    "| Verb | When to Use | Example |\n"
                    "|------|------------|--------|\n"
                    "| **Analyse** | Explore data patterns | Analyse avocado pricing trends across stores |\n"
                    "| **Compare** | Find differences | Compare Pyrmont vs Bondi fresh produce margins |\n"
                    "| **Summarise** | Condense information | Summarise last week's store performance |\n"
                    "| **Recommend** | Get actionable advice | Recommend which PLUs to delist from dairy |\n"
                    "| **Identify** | Find specific items | Identify the top 10 highest-wastage products |\n"
                    "| **Forecast** | Predict future values | Forecast Christmas week demand for seafood |\n"
                    "| **Draft** | Create a document | Draft talking points for the store managers meeting |\n\n"
                    "### Avoid Weak Verbs\n\n"
                    "- *Tell me about...* — too vague\n"
                    "- *Help with...* — unclear task\n"
                    "- *Do something about...* — no direction\n\n"
                    "Strong verbs make AI outputs 3-4x more useful because they set clear expectations."
                ),
            },
            {
                "order": 3,
                "title": "Adding Specificity and Context",
                "content_md": (
                    "## Why Specificity Matters\n\n"
                    "Every missing detail is a guess the AI has to make. At Harris Farm, always specify:\n\n"
                    "- **Which stores?** — All 43, a specific store, or a state?\n"
                    "- **What time period?** — Last week, last month, YoY?\n"
                    "- **Which department?** — Fresh produce, deli, grocery, bakery?\n"
                    "- **What metric?** — Revenue, margin, wastage, units, basket size?\n\n"
                    "### Context the AI Doesn't Know\n\n"
                    "The AI doesn't know:\n"
                    "- Harris Farm has 43 stores across NSW and QLD\n"
                    "- Our fiscal year runs July to June\n"
                    "- We're a premium fresh food retailer (not a discount supermarket)\n"
                    "- 'Greater Goodness' is our brand strategy\n\n"
                    "Include this context when it's relevant to your question.\n\n"
                    "### The Specificity Test\n\n"
                    "Read your prompt back. Could two different people interpret it differently? "
                    "If yes, add more detail until there's only one reasonable interpretation."
                ),
            },
        ],
        "exercises": [
            {
                "id": "L1_S1",
                "tier": "standard",
                "instruction": "Rewrite this weak prompt into a strong one: 'Tell me about our store sales.'  Make it specific to Harris Farm, include a time period, store scope, and metric.",
                "context_tag": "operations",
                "scoring_criteria": "Score 1-5: (1) Has a clear task verb, (2) Specifies store scope, (3) Includes time period, (4) Names a specific metric, (5) Adds output format or constraints.",
                "max_score": 5,
            },
            {
                "id": "L1_S2",
                "tier": "standard",
                "instruction": "Write a prompt to help the customer service team understand why customer complaints have increased at the Pyrmont store this month. Include all 4 prompt elements: task verb, subject, context, and constraints.",
                "context_tag": "customer",
                "scoring_criteria": "Score 1-5: (1) Clear task verb used, (2) Subject clearly defined (complaints, Pyrmont), (3) Context provided (this month, customer service), (4) Constraints specified, (5) Actionable output requested.",
                "max_score": 5,
            },
            {
                "id": "L1_R1",
                "tier": "stretch",
                "instruction": "Write two versions of a prompt about fresh produce wastage — one for a store manager audience and one for the executive team. Both should analyse the same data but frame the output differently.",
                "context_tag": "supply_chain",
                "scoring_criteria": "Score 1-5: (1) Both prompts have clear task verbs, (2) Store manager version is operational and actionable, (3) Executive version is strategic and summary-focused, (4) Both reference specific data and time periods, (5) Output formats differ appropriately for each audience.",
                "max_score": 5,
            },
            {
                "id": "L1_R2",
                "tier": "stretch",
                "instruction": "A colleague wrote this prompt: 'What are our best products?' Rewrite it three times, each with a different task verb, to show how the verb changes the output. Explain why each version produces a different result.",
                "context_tag": "commercial",
                "scoring_criteria": "Score 1-5: (1) Three distinct rewrites provided, (2) Each uses a different meaningful task verb, (3) Rewrites include HFM-specific detail, (4) Explanations show understanding of how verbs shape output, (5) At least one version includes constraints or output format.",
                "max_score": 5,
            },
            {
                "id": "L1_E1",
                "tier": "elite",
                "instruction": "You need to brief the CEO on why one store is underperforming. Design a prompt chain: first a data extraction prompt, then an analysis prompt that uses the first output, then a summary prompt for the board. Show all three prompts and explain how they connect.",
                "context_tag": "strategy",
                "scoring_criteria": "Score 1-5: (1) Three connected prompts with logical flow, (2) Data extraction is specific with metrics and timeframes, (3) Analysis prompt references output of first, (4) Summary prompt is CEO/board appropriate, (5) Chain demonstrates progressive refinement of information.",
                "max_score": 5,
            },
            {
                "id": "L1_E2",
                "tier": "elite",
                "instruction": "Create a prompt template that any Harris Farm department manager could fill in to generate a weekly performance report. Include placeholders for [department], [store], [week], and [metric]. Then demonstrate using it for both the produce buyer and the transport manager.",
                "context_tag": "reporting",
                "scoring_criteria": "Score 1-5: (1) Template has clear placeholders and structure, (2) Template includes all 4 prompt elements, (3) Produce buyer example is realistic, (4) Transport manager example is realistic, (5) Both examples produce meaningfully different outputs despite same template.",
                "max_score": 5,
            },
        ],
    },

    # ==================================================================
    # L2: DATA-DRIVEN PROMPTING
    # ==================================================================
    {
        "code": "L2",
        "series": "learn",
        "name": "Data-Driven Prompting",
        "level": 2,
        "description": "Add metrics, time periods, and data sources to prompts for precise, evidence-based outputs.",
        "lessons": [
            {
                "order": 1,
                "title": "Referencing Data in Prompts",
                "content_md": (
                    "## Making Prompts Data-Specific\n\n"
                    "At Harris Farm, we have rich data across multiple systems:\n\n"
                    "- **POS data** — Transaction-level sales, item quantities, basket composition\n"
                    "- **Inventory data** — Stock levels, deliveries, wastage by store\n"
                    "- **Customer data** — 17K customer profiles, purchase history, loyalty\n"
                    "- **Market share** — CBAS postcode-level share data (modelled, not actual revenue)\n\n"
                    "### How to Reference Data\n\n"
                    "Always tell the AI:\n"
                    "1. **What data source** — 'Using our POS weekly sales data...'\n"
                    "2. **What fields** — 'Focus on revenue, units sold, and margin %'\n"
                    "3. **What filters** — 'For NSW stores only, fresh produce department'\n"
                    "4. **What aggregation** — 'Summarise by store and week'\n\n"
                    "### Example\n\n"
                    "*Using our weekly POS sales data for the period Jan-Mar 2026, compare revenue "
                    "per square metre across all NSW stores. Filter to fresh produce department only. "
                    "Rank stores from highest to lowest and flag any with >15% YoY decline.*"
                ),
            },
            {
                "order": 2,
                "title": "Time Periods and Comparisons",
                "content_md": (
                    "## Time Period Best Practices\n\n"
                    "### Always Specify\n"
                    "- Exact dates or date ranges (not 'recently' or 'lately')\n"
                    "- Whether you mean fiscal year (Jul-Jun) or calendar year\n"
                    "- The comparison period (YoY, MoM, vs budget)\n\n"
                    "### Common Harris Farm Time Frames\n\n"
                    "| Use Case | Time Frame | Why |\n"
                    "|----------|-----------|-----|\n"
                    "| Weekly review | Last 4 weeks rolling | Smooths daily noise |\n"
                    "| Seasonal trend | Same month YoY | Controls for seasonality |\n"
                    "| Performance tracking | FY to date vs prior FY | Aligns to budget cycle |\n"
                    "| Product analysis | 13-week rolling | Standard retail quarter |\n\n"
                    "### Critical Rule\n\n"
                    "**Never compare sequential months** (e.g. Jan vs Feb). Seasonality makes this "
                    "misleading. Always compare same-period YoY or rolling averages.\n\n"
                    "### Metrics to Pair\n\n"
                    "Don't look at one metric alone:\n"
                    "- Revenue + margin (growing sales at shrinking margin is a problem)\n"
                    "- Sales + wastage (more volume might mean more waste)\n"
                    "- Customer count + basket size (fewer customers spending more, or vice versa?)"
                ),
            },
            {
                "order": 3,
                "title": "Avoiding Data Interpretation Errors",
                "content_md": (
                    "## Common Data Traps at Harris Farm\n\n"
                    "### Trap 1: Mixing Data Layers\n"
                    "- **Layer 1 (POS)**: Actual transactions, real revenue\n"
                    "- **Layer 2 (Market Share)**: CBAS modelled estimates\n"
                    "- **Never cross-reference** Layer 2 dollar values with Layer 1 revenue\n\n"
                    "### Trap 2: New vs Existing Stores\n"
                    "A new store opening distorts averages. Always specify:\n"
                    "- 'Like-for-like stores only' or 'Excluding stores opened < 12 months'\n\n"
                    "### Trap 3: Confusing Correlation with Causation\n"
                    "If sales rose the same week as a promotion, "
                    "the promotion might have caused it — or it might be seasonal.\n"
                    "Prompt the AI to distinguish: 'Identify whether the sales increase "
                    "is consistent with seasonal patterns or represents an incremental lift.'\n\n"
                    "### Trap 4: Sample Size\n"
                    "Market share data for a postcode with 5 customers is unreliable. "
                    "Always ask: 'Flag any data points with fewer than 50 observations.'"
                ),
            },
        ],
        "exercises": [
            {
                "id": "L2_S1",
                "tier": "standard",
                "instruction": "Write a prompt to analyse banana sales performance across all Harris Farm stores for the last 13 weeks. Specify which metrics to include, how to compare (YoY), and what to flag.",
                "context_tag": "data",
                "scoring_criteria": "Score 1-5: (1) Specifies data source and product, (2) 13-week period clearly stated, (3) YoY comparison included, (4) Multiple metrics requested, (5) Flagging criteria defined.",
                "max_score": 5,
            },
            {
                "id": "L2_S2",
                "tier": "standard",
                "instruction": "A colleague says 'Market share in postcode 2037 dropped 2%, we're losing revenue there.' Write a response explaining why this statement is problematic, and then write a correct prompt to investigate the issue.",
                "context_tag": "customer",
                "scoring_criteria": "Score 1-5: (1) Identifies the Layer 1/Layer 2 mixing error, (2) Explains market share is modelled not actual, (3) Corrected prompt uses share % as primary metric, (4) Corrected prompt specifies YoY comparison, (5) Corrected prompt includes appropriate caveats.",
                "max_score": 5,
            },
            {
                "id": "L2_R1",
                "tier": "stretch",
                "instruction": "Design a prompt that asks the AI to create a weekly store scorecard using POS data. The scorecard should include 5 KPIs, trend arrows, and colour-coded thresholds. Specify exactly what 'good', 'warning', and 'critical' looks like for each KPI.",
                "context_tag": "reporting",
                "scoring_criteria": "Score 1-5: (1) Five distinct KPIs defined, (2) Each KPI has quantified thresholds, (3) Time comparison specified (WoW or YoY), (4) Output format described (table with trend arrows), (5) Colour coding rules clearly defined.",
                "max_score": 5,
            },
            {
                "id": "L2_R2",
                "tier": "stretch",
                "instruction": "Write a prompt that cross-references two data sets safely: weekly store sales (Layer 1) and customer traffic counts (external footfall sensors). Show how to request the analysis without mixing incompatible metrics.",
                "context_tag": "operations",
                "scoring_criteria": "Score 1-5: (1) Both data sources clearly identified, (2) Keeps metrics separate (doesn't divide one by other inappropriately), (3) Specifies correlation analysis not causal claims, (4) Time alignment specified, (5) Includes caveats about data source differences.",
                "max_score": 5,
            },
            {
                "id": "L2_E1",
                "tier": "elite",
                "instruction": "The CFO asks: 'Are we making money on avocados?' Design a multi-step prompt sequence that (1) pulls margin data, (2) accounts for wastage cost, (3) calculates true profitability including handling cost, and (4) compares this across stores. Show all prompts and explain the data flow between them.",
                "context_tag": "finance",
                "scoring_criteria": "Score 1-5: (1) Four logical prompt steps, (2) Each references specific data fields, (3) Wastage cost methodology explained, (4) Store comparison uses like-for-like basis, (5) Final output format is CFO-appropriate with clear bottom line.",
                "max_score": 5,
            },
            {
                "id": "L2_E2",
                "tier": "elite",
                "instruction": "Harris Farm is evaluating opening a new store. Write a prompt that analyses market share data, customer demographics, competitor presence, and existing store cannibalisation risk for a proposed location. Include all necessary data caveats (Layer 2 limitations, distance tiers, sample size flags).",
                "context_tag": "strategy",
                "scoring_criteria": "Score 1-5: (1) Multiple data sources referenced appropriately, (2) Layer 2 caveats explicitly stated, (3) Distance tier analysis included, (4) Cannibalisation risk methodology defined, (5) Output structured as investment case with confidence levels.",
                "max_score": 5,
            },
        ],
    },

    # ==================================================================
    # L3: ADVANCED TECHNIQUES
    # ==================================================================
    {
        "code": "L3",
        "series": "learn",
        "name": "Advanced Techniques",
        "level": 3,
        "description": "Chain-of-thought reasoning, few-shot examples, role assignment, and constraint-setting.",
        "lessons": [
            {
                "order": 1,
                "title": "Chain of Thought Prompting",
                "content_md": (
                    "## Think Step-by-Step\n\n"
                    "Chain of thought (CoT) prompting asks the AI to show its reasoning. "
                    "This dramatically improves accuracy for complex analysis.\n\n"
                    "### Without CoT\n"
                    "*Should we delist organic quinoa from Harris Farm stores?*\n\n"
                    "### With CoT\n"
                    "*Analyse whether Harris Farm should delist organic quinoa. Think step by step:*\n"
                    "*1. What are the sales trends over the last 6 months?*\n"
                    "*2. What's the margin contribution vs shelf space used?*\n"
                    "*3. What substitutes exist in the range?*\n"
                    "*4. What's the customer overlap — do quinoa buyers also buy high-margin items?*\n"
                    "*5. Based on all factors, what's your recommendation and why?*\n\n"
                    "### When to Use CoT\n"
                    "- Multi-factor decisions (delist, promote, reprice)\n"
                    "- Root cause analysis (why did X happen?)\n"
                    "- Any question where you want to verify the AI's logic"
                ),
            },
            {
                "order": 2,
                "title": "Few-Shot Examples",
                "content_md": (
                    "## Teaching by Example\n\n"
                    "Give the AI 1-3 examples of what you want, and it mirrors the pattern.\n\n"
                    "### Example: Product Descriptions\n\n"
                    "*Write product descriptions for Harris Farm's website. Follow this format:*\n\n"
                    "*Example 1: Organic Hass Avocados — Sourced from Comboyne on the NSW Mid North Coast. "
                    "Rich, buttery flesh perfect for smashing on toast or adding to your favourite salad. "
                    "Best enjoyed within 3 days of purchase.*\n\n"
                    "*Example 2: Riverina Pink Lady Apples — Crisp and sweet from the Riverina region. "
                    "A perfect lunchbox apple with a beautiful pink blush. Store in the fridge for maximum crunch.*\n\n"
                    "*Now write descriptions for: 1) Queensland Strawberries, 2) Hunter Valley Free-Range Eggs*\n\n"
                    "### When to Use Few-Shot\n"
                    "- Writing in a specific tone or format\n"
                    "- Classifying items into categories\n"
                    "- Generating content that matches existing style"
                ),
            },
            {
                "order": 3,
                "title": "Role Assignment and Constraints",
                "content_md": (
                    "## Giving AI a Role\n\n"
                    "Assigning a role frames the AI's perspective and expertise:\n\n"
                    "- *You are a Harris Farm fresh produce buyer with 15 years of experience...*\n"
                    "- *You are a retail data analyst specialising in Australian grocery...*\n"
                    "- *You are a supply chain optimisation expert for perishable goods...*\n\n"
                    "### Setting Constraints\n\n"
                    "Constraints prevent the AI from going off-track:\n\n"
                    "- **Scope**: 'Focus only on NSW stores'\n"
                    "- **Format**: 'Present as a table with no more than 10 rows'\n"
                    "- **Tone**: 'Write for a store manager, not a data scientist'\n"
                    "- **Exclusions**: 'Do not include stores open less than 6 months'\n"
                    "- **Length**: 'Keep the summary under 200 words'\n"
                    "- **Guardrails**: 'If the data is insufficient, say so rather than guessing'\n\n"
                    "### Combining Role + Constraints\n\n"
                    "*You are a Harris Farm category manager. Analyse the cheese range and recommend "
                    "3 SKUs to delist. Consider margin, velocity, and supplier diversity. "
                    "Present as a table with columns: SKU, Weekly Revenue, Margin %, Recommendation, Reason. "
                    "Do not recommend delisting any SKU that is the sole product from its supplier.*"
                ),
            },
        ],
        "exercises": [
            {
                "id": "L3_S1",
                "tier": "standard",
                "instruction": "Rewrite this prompt using chain-of-thought: 'Why are deli sales declining at Bondi Beach?' Add numbered reasoning steps that the AI should follow.",
                "context_tag": "operations",
                "scoring_criteria": "Score 1-5: (1) Includes 'think step by step' or numbered steps, (2) At least 4 reasoning steps, (3) Steps are logically ordered, (4) Steps reference specific data points, (5) Final step asks for a recommendation.",
                "max_score": 5,
            },
            {
                "id": "L3_S2",
                "tier": "standard",
                "instruction": "Write a prompt with a role assignment to help the transport team optimise delivery routes. Include at least 3 constraints that keep the output practical and actionable.",
                "context_tag": "supply_chain",
                "scoring_criteria": "Score 1-5: (1) Clear role assigned, (2) Role is relevant to transport/logistics, (3) At least 3 explicit constraints, (4) Constraints are practical and specific, (5) Output format defined.",
                "max_score": 5,
            },
            {
                "id": "L3_R1",
                "tier": "stretch",
                "instruction": "Create a few-shot prompt for classifying customer complaints into categories (product quality, staff service, pricing, availability, store cleanliness). Provide 3 example classifications and then ask the AI to classify 5 new complaints.",
                "context_tag": "customer",
                "scoring_criteria": "Score 1-5: (1) Clear category definitions, (2) Three example complaints with correct classifications, (3) Examples cover different categories, (4) Five new complaints to classify are realistic, (5) Includes instruction for handling ambiguous cases.",
                "max_score": 5,
            },
            {
                "id": "L3_R2",
                "tier": "stretch",
                "instruction": "Combine all three techniques (CoT, few-shot, role assignment) into a single prompt that helps a new store manager write their weekly performance summary. The prompt should teach the format through examples and guide thinking through key areas.",
                "context_tag": "reporting",
                "scoring_criteria": "Score 1-5: (1) Role clearly assigned, (2) Chain of thought steps guide analysis, (3) At least 2 few-shot examples provided, (4) Examples match Harris Farm context, (5) Output format is practical for a store manager.",
                "max_score": 5,
            },
            {
                "id": "L3_E1",
                "tier": "elite",
                "instruction": "Design a prompt system for automated supplier negotiation preparation. Use role assignment (procurement specialist), CoT (step-by-step analysis of supplier's position), and constraints (budget limits, quality standards, delivery requirements). The system should produce a negotiation brief.",
                "context_tag": "commercial",
                "scoring_criteria": "Score 1-5: (1) Procurement role well-defined with expertise, (2) CoT covers market analysis, supplier SWOT, and leverage points, (3) Constraints include budget, quality, and compliance, (4) Output is a structured negotiation brief, (5) Includes fallback positions and BATNA analysis.",
                "max_score": 5,
            },
            {
                "id": "L3_E2",
                "tier": "elite",
                "instruction": "Create a prompt that analyses a product range using all three advanced techniques. The AI should act as a category director (role), work through margin/velocity/customer-fit analysis step by step (CoT), and reference example range reviews from other departments (few-shot). Target: the bakery department's sourdough range.",
                "context_tag": "commercial",
                "scoring_criteria": "Score 1-5: (1) Category director role with clear authority level, (2) CoT includes at least 5 analytical steps, (3) Few-shot examples from other departments are realistic, (4) Analysis covers margin, velocity, and customer fit, (5) Final recommendation is strategic with implementation steps.",
                "max_score": 5,
            },
        ],
    },

    # ==================================================================
    # L4: OUTPUT ENGINEERING
    # ==================================================================
    {
        "code": "L4",
        "series": "learn",
        "name": "Output Engineering",
        "level": 4,
        "description": "Control formatting, structure, tables, action plans, and executive summaries.",
        "lessons": [
            {
                "order": 1,
                "title": "Structured Output Formats",
                "content_md": (
                    "## Telling AI How to Present Results\n\n"
                    "The difference between useful and useless AI output is often just the format.\n\n"
                    "### Format Options\n\n"
                    "| Format | When to Use | Example Request |\n"
                    "|--------|-----------|----------------|\n"
                    "| **Table** | Comparing multiple items | 'Present as a table with columns...' |\n"
                    "| **Bullet list** | Quick actions | 'List the top 5 actions as bullet points' |\n"
                    "| **Executive summary** | Leadership audience | 'Write a 3-paragraph executive summary' |\n"
                    "| **Dashboard narrative** | Weekly reports | 'Write the commentary for each metric' |\n"
                    "| **Email draft** | Communication | 'Draft an email to store managers about...' |\n"
                    "| **Decision matrix** | Complex choices | 'Create a weighted decision matrix' |\n\n"
                    "### Be Explicit About Structure\n\n"
                    "Don't just say 'create a report.' Say:\n"
                    "- How many sections\n"
                    "- What each section covers\n"
                    "- Maximum length per section\n"
                    "- Whether to include charts/tables\n"
                    "- What the final recommendation section should contain"
                ),
            },
            {
                "order": 2,
                "title": "Action Plans and Recommendations",
                "content_md": (
                    "## From Analysis to Action\n\n"
                    "The most valuable AI output isn't data — it's what to do next.\n\n"
                    "### Action Plan Structure\n\n"
                    "Ask the AI to provide:\n"
                    "1. **What** — Specific action (not 'improve sales')\n"
                    "2. **Who** — Which role/team owns it\n"
                    "3. **When** — Timeline or deadline\n"
                    "4. **How** — Implementation steps\n"
                    "5. **Measure** — How to know if it worked\n\n"
                    "### Example Prompt\n\n"
                    "*Based on this wastage analysis, create an action plan with 3-5 recommendations. "
                    "For each, specify: the action, the responsible team (store ops, buying, or supply chain), "
                    "the implementation timeline (this week, this month, this quarter), "
                    "the expected impact in dollar terms, and how we'll measure success.*\n\n"
                    "### Prioritisation Frameworks\n\n"
                    "Ask AI to rank actions by:\n"
                    "- Impact vs effort (2x2 matrix)\n"
                    "- Quick wins vs strategic bets\n"
                    "- Cost to implement vs cost of inaction"
                ),
            },
            {
                "order": 3,
                "title": "Writing for Different Audiences",
                "content_md": (
                    "## Audience-Appropriate Output\n\n"
                    "The same data needs different framing for different people:\n\n"
                    "### Store Manager\n"
                    "- Operational, actionable, specific to their store\n"
                    "- 'Your bakery wastage is 12% this week (target: 8%). Top 3 waste items: sourdough "
                    "loaves (23 units), croissants (18), baguettes (15). Action: reduce bake quantities "
                    "by 20% on low-traffic days (Mon, Tue).'\n\n"
                    "### Regional Manager\n"
                    "- Comparative, trend-focused, highlights outliers\n"
                    "- 'Bakery wastage across your 8 stores ranges from 5% to 14%. Three stores above target...'\n\n"
                    "### Executive / Board\n"
                    "- Strategic, financial impact, tied to company goals\n"
                    "- 'Bakery wastage represents $X annualised opportunity. A 3% reduction achieves "
                    "our Greater Goodness sustainability target while improving margin by $Y.'\n\n"
                    "### The Audience Test\n"
                    "Before submitting: 'Would the person reading this know exactly what to do next?'"
                ),
            },
        ],
        "exercises": [
            {
                "id": "L4_S1",
                "tier": "standard",
                "instruction": "Write a prompt that produces a formatted weekly store performance table. Specify columns, sorting, and conditional formatting rules (e.g. red for metrics below target).",
                "context_tag": "reporting",
                "scoring_criteria": "Score 1-5: (1) Table columns defined, (2) At least 5 meaningful columns, (3) Sorting criteria specified, (4) Conditional formatting rules defined, (5) Includes comparison benchmarks.",
                "max_score": 5,
            },
            {
                "id": "L4_S2",
                "tier": "standard",
                "instruction": "Write a prompt that turns raw sales data into an executive summary suitable for the Harris Farm monthly board meeting. Specify the structure, length, and what the recommendation section should contain.",
                "context_tag": "strategy",
                "scoring_criteria": "Score 1-5: (1) Executive summary format specified, (2) Length constraint included, (3) Structure has clear sections, (4) Recommendation section requirements defined, (5) Tied to strategic goals (Greater Goodness, Vision 2030).",
                "max_score": 5,
            },
            {
                "id": "L4_R1",
                "tier": "stretch",
                "instruction": "Create a prompt that generates a complete action plan for reducing fresh produce wastage by 20%. The action plan must follow the What/Who/When/How/Measure framework for at least 4 initiatives. Include a prioritisation matrix.",
                "context_tag": "operations",
                "scoring_criteria": "Score 1-5: (1) At least 4 initiatives defined, (2) Each has all 5 framework elements, (3) Prioritisation matrix included, (4) Timeline is realistic, (5) Success metrics are quantified.",
                "max_score": 5,
            },
            {
                "id": "L4_R2",
                "tier": "stretch",
                "instruction": "Write three versions of the same analysis (customer basket size decline) formatted for: (1) a store manager meeting slide, (2) a CEO email, (3) a data team Slack message. Show how tone, detail, and format change.",
                "context_tag": "customer",
                "scoring_criteria": "Score 1-5: (1) Three distinct formats produced, (2) Store manager version is visual and actionable, (3) CEO email is concise and strategic, (4) Data team Slack is technical and collaborative, (5) All reference the same underlying data accurately.",
                "max_score": 5,
            },
            {
                "id": "L4_E1",
                "tier": "elite",
                "instruction": "Design a prompt that creates a complete quarterly business review (QBR) document from raw data. Include: executive summary, 5 KPI dashboards with commentary, trend analysis, competitive context, risks and opportunities, and strategic recommendations. Specify formatting for each section.",
                "context_tag": "strategy",
                "scoring_criteria": "Score 1-5: (1) All 6 sections specified with format rules, (2) KPI selection is appropriate for Harris Farm, (3) Commentary instructions guide insight over description, (4) Competitive context references market share data correctly, (5) Recommendations link to Vision 2030 strategy.",
                "max_score": 5,
            },
            {
                "id": "L4_E2",
                "tier": "elite",
                "instruction": "Create a prompt system that generates a decision memo for a major investment (e.g. store renovation). The memo should include: problem statement, 3 options with pros/cons, financial analysis format, risk assessment matrix, recommendation with confidence level, and implementation timeline. Define the format for each element.",
                "context_tag": "finance",
                "scoring_criteria": "Score 1-5: (1) All 6 elements defined with formats, (2) Options are genuinely distinct approaches, (3) Financial analysis includes ROI/payback, (4) Risk matrix has likelihood x impact, (5) Confidence levels and assumptions documented.",
                "max_score": 5,
            },
        ],
    },

    # ==================================================================
    # L5: ENTERPRISE PROMPTING
    # ==================================================================
    {
        "code": "L5",
        "series": "learn",
        "name": "Enterprise Prompting",
        "level": 5,
        "description": "Multi-step workflows, system prompts, tool integration, and organisational guardrails.",
        "lessons": [
            {
                "order": 1,
                "title": "System Prompts and Workflow Design",
                "content_md": (
                    "## Building AI-Powered Workflows\n\n"
                    "Enterprise prompting goes beyond single prompts. You're designing systems.\n\n"
                    "### System Prompt vs User Prompt\n"
                    "- **System prompt**: Sets the AI's identity, rules, and boundaries for an entire session\n"
                    "- **User prompt**: The specific question or task within that session\n\n"
                    "### Example: Weekly Report Generator\n\n"
                    "**System prompt:**\n"
                    "*You are the Harris Farm Weekly Performance Analyst. You have access to POS sales data, "
                    "inventory data, and customer metrics. Always compare to same week last year. "
                    "Never mix market share data with POS revenue. Flag any metric >10% off target. "
                    "Output in the standard HFM weekly report template.*\n\n"
                    "**User prompt:**\n"
                    "*Generate the weekly report for Bondi Beach, week ending 21 Feb 2026.*\n\n"
                    "### Multi-Step Workflows\n"
                    "1. **Trigger** — New data arrives\n"
                    "2. **Extract** — Pull relevant metrics\n"
                    "3. **Analyse** — Apply business rules\n"
                    "4. **Format** — Structure for audience\n"
                    "5. **Route** — Send to right person\n"
                    "6. **Monitor** — Track if actions were taken"
                ),
            },
            {
                "order": 2,
                "title": "Guardrails and Safety",
                "content_md": (
                    "## Enterprise AI Guardrails\n\n"
                    "At scale, AI needs boundaries to prevent errors:\n\n"
                    "### Data Guardrails\n"
                    "- Never expose customer PII in reports\n"
                    "- Always validate calculations against source data\n"
                    "- Flag when data is incomplete or potentially stale\n\n"
                    "### Decision Guardrails\n"
                    "- AI recommends, humans decide\n"
                    "- Any recommendation >$50K requires human review\n"
                    "- Strategic recommendations flagged as 'directional only'\n\n"
                    "### Output Guardrails\n"
                    "- All numbers traceable to data source\n"
                    "- Confidence levels on forecasts\n"
                    "- 'I don't have enough data to answer this' is a valid response\n\n"
                    "### Building Guardrails into Prompts\n\n"
                    "*If any metric cannot be verified against the source data, mark it as "
                    "'[UNVERIFIED]' and explain what additional data would be needed. "
                    "Do not present forecasts without a confidence interval. "
                    "If the analysis suggests an action exceeding $50K in impact, "
                    "flag it as requiring management review.*"
                ),
            },
            {
                "order": 3,
                "title": "Tool Integration and Orchestration",
                "content_md": (
                    "## Connecting AI to Business Tools\n\n"
                    "Enterprise prompting often involves multiple tools working together:\n\n"
                    "### Harris Farm Tool Chain\n"
                    "- **Prompt Engine** — Generate and score prompts\n"
                    "- **Analytics Engine** — Query structured data\n"
                    "- **Hub Assistant** — Natural language Q&A over knowledge base\n"
                    "- **Agent Hub** — Multi-step AI agents for complex tasks\n\n"
                    "### Orchestration Patterns\n\n"
                    "**Sequential:** Extract data → Analyse → Format → Review\n\n"
                    "**Parallel:** Run market analysis AND competitor scan AND customer segment in parallel, "
                    "then synthesise\n\n"
                    "**Conditional:** If wastage > threshold → generate detailed report → alert manager; "
                    "else → log and continue\n\n"
                    "### Prompt Design for Orchestration\n"
                    "Each step needs:\n"
                    "- Clear input specification\n"
                    "- Explicit output format (JSON, table, narrative)\n"
                    "- Error handling instructions\n"
                    "- Handoff instructions to next step"
                ),
            },
        ],
        "exercises": [
            {
                "id": "L5_S1",
                "tier": "standard",
                "instruction": "Write a system prompt for a Harris Farm 'Store Health Monitor' that processes daily sales data and generates alerts. Include identity, data access rules, alert thresholds, and output format.",
                "context_tag": "operations",
                "scoring_criteria": "Score 1-5: (1) Clear system identity, (2) Data access rules defined, (3) At least 3 alert thresholds with triggers, (4) Output format specified, (5) Guardrails included.",
                "max_score": 5,
            },
            {
                "id": "L5_S2",
                "tier": "standard",
                "instruction": "Design a 3-step workflow prompt for processing a new supplier application. Step 1: Extract key details from the application. Step 2: Check against existing supplier database. Step 3: Generate a recommendation memo. Write all three prompts with clear handoffs.",
                "context_tag": "commercial",
                "scoring_criteria": "Score 1-5: (1) Three distinct steps with clear purpose, (2) Output of each step feeds into next, (3) Data fields specified at each step, (4) Handoff format defined, (5) Error handling for missing data.",
                "max_score": 5,
            },
            {
                "id": "L5_R1",
                "tier": "stretch",
                "instruction": "Create a complete guardrail specification for an AI system that analyses customer purchase patterns to recommend personalised promotions. Include data privacy rules, recommendation limits, bias detection, and override procedures.",
                "context_tag": "customer",
                "scoring_criteria": "Score 1-5: (1) Data privacy rules cover PII handling, (2) Recommendation limits prevent gaming, (3) Bias detection methodology defined, (4) Human override process documented, (5) Audit trail requirements specified.",
                "max_score": 5,
            },
            {
                "id": "L5_R2",
                "tier": "stretch",
                "instruction": "Design a parallel workflow that simultaneously analyses a product category from 3 perspectives (financial, customer, operational) and then synthesises the results into a single recommendation. Write all prompts including the synthesis step.",
                "context_tag": "strategy",
                "scoring_criteria": "Score 1-5: (1) Three parallel analysis prompts are distinct, (2) Each covers its domain thoroughly, (3) Output formats are compatible for synthesis, (4) Synthesis prompt handles conflicting signals, (5) Final output is actionable and prioritised.",
                "max_score": 5,
            },
            {
                "id": "L5_E1",
                "tier": "elite",
                "instruction": "Design an end-to-end AI-powered 'Morning Briefing' system for Harris Farm executives. It should: pull overnight sales data, compare to targets, identify top 3 issues, generate talking points, and personalise content for each of the 5 executive roles (CEO, COO, CFO, CTO, CPO). Write the system prompt, data pipeline, and personalisation logic.",
                "context_tag": "strategy",
                "scoring_criteria": "Score 1-5: (1) System prompt covers full scope, (2) Data pipeline has clear steps, (3) Issue identification uses business rules, (4) Personalisation logic maps issues to roles, (5) Each role's output has appropriate depth and focus.",
                "max_score": 5,
            },
            {
                "id": "L5_E2",
                "tier": "elite",
                "instruction": "Design an AI agent system that detects anomalies in daily store data, diagnoses probable causes, recommends actions, and routes alerts to the right team. Include: trigger conditions, diagnosis decision tree, escalation rules, and feedback loop for improving accuracy over time.",
                "context_tag": "data",
                "scoring_criteria": "Score 1-5: (1) Anomaly detection thresholds defined, (2) Diagnosis decision tree covers 5+ scenarios, (3) Routing rules map to specific teams, (4) Escalation hierarchy clear, (5) Feedback loop improves future detection.",
                "max_score": 5,
            },
        ],
    },

    # ==================================================================
    # D1: STORE PERFORMANCE
    # ==================================================================
    {
        "code": "D1",
        "series": "do",
        "name": "Store Performance",
        "level": 1,
        "description": "Apply AI to analyse store sales, wastage, staffing, and customer traffic.",
        "lessons": [
            {
                "order": 1,
                "title": "Understanding Store KPIs",
                "content_md": (
                    "## Harris Farm Store Performance Metrics\n\n"
                    "Every Harris Farm store tracks these key metrics:\n\n"
                    "- **Revenue** — Total sales and sales per square metre\n"
                    "- **Basket Size** — Average transaction value\n"
                    "- **Customer Count** — Transactions per day/week\n"
                    "- **Margin** — Gross profit percentage by department\n"
                    "- **Wastage** — Fresh produce shrinkage (target <8%)\n"
                    "- **Labour Cost** — Staff hours as % of revenue\n\n"
                    "### Relationships Between Metrics\n\n"
                    "Metrics don't exist in isolation:\n"
                    "- High customer count + low basket size = browse-heavy, conversion opportunity\n"
                    "- High revenue + high wastage = over-ordering fresh produce\n"
                    "- Low labour cost + poor customer feedback = understaffing\n\n"
                    "### Using AI for Store Analysis\n\n"
                    "Good store analysis prompts should:\n"
                    "1. Specify which KPIs to examine\n"
                    "2. Set comparison benchmarks (target, peer store, prior year)\n"
                    "3. Ask for both what happened AND why\n"
                    "4. Request prioritised actions"
                ),
            },
            {
                "order": 2,
                "title": "Diagnosing Store Issues",
                "content_md": (
                    "## Root Cause Analysis for Stores\n\n"
                    "When a store underperforms, follow this diagnostic framework:\n\n"
                    "### The 5-Layer Diagnostic\n\n"
                    "1. **Traffic** — Are fewer customers coming? (External: competition, construction, demographics)\n"
                    "2. **Conversion** — Are visitors buying less? (Internal: range, pricing, presentation)\n"
                    "3. **Basket** — Are transactions smaller? (Product: mix shift, downtrade, promotion dependency)\n"
                    "4. **Margin** — Are we earning less per sale? (Cost: wastage, markdowns, supplier pricing)\n"
                    "5. **Execution** — Is the store running well? (Ops: staffing, availability, presentation standards)\n\n"
                    "### AI-Powered Diagnosis\n\n"
                    "Ask the AI to work through each layer systematically:\n"
                    "*Diagnose the performance decline at Mosman store using the 5-layer framework. "
                    "For each layer, identify the metric trend, potential causes, and data needed to confirm.*"
                ),
            },
        ],
        "exercises": [
            {
                "id": "D1_S1",
                "tier": "standard",
                "instruction": "Write a prompt to generate a weekly performance summary for the Bondi Beach store, covering revenue, basket size, customer count, and wastage. Compare to target and same week last year.",
                "context_tag": "operations",
                "scoring_criteria": "Score 1-5: (1) All 4 KPIs included, (2) Target comparison specified, (3) YoY comparison specified, (4) Time period clear, (5) Output format defined.",
                "max_score": 5,
            },
            {
                "id": "D1_S2",
                "tier": "standard",
                "instruction": "A store manager reports that revenue is up 5% but profit is flat. Write a prompt to diagnose why margin isn't keeping pace with revenue at a specific Harris Farm store.",
                "context_tag": "finance",
                "scoring_criteria": "Score 1-5: (1) Revenue vs margin gap clearly stated, (2) Asks for department-level breakdown, (3) Checks for wastage/markdown impact, (4) Checks for mix shift, (5) Requests prioritised causes.",
                "max_score": 5,
            },
            {
                "id": "D1_R1",
                "tier": "stretch",
                "instruction": "Design a prompt that uses the 5-layer diagnostic framework to analyse why Pyrmont store's performance has declined for 3 consecutive weeks. The AI should work through each layer and identify the most likely root cause.",
                "context_tag": "operations",
                "scoring_criteria": "Score 1-5: (1) All 5 layers referenced, (2) Each layer has specific data requests, (3) Asks for cause probability ranking, (4) 3-week trend specified, (5) Actionable recommendation required.",
                "max_score": 5,
            },
            {
                "id": "D1_R2",
                "tier": "stretch",
                "instruction": "Write a prompt to compare staffing efficiency across 5 Harris Farm stores. Include: revenue per labour hour, customer wait time proxies, department coverage gaps, and peak/off-peak staffing alignment. Request a staffing optimisation recommendation.",
                "context_tag": "operations",
                "scoring_criteria": "Score 1-5: (1) Multiple staffing metrics defined, (2) Cross-store comparison framework, (3) Peak vs off-peak analysis, (4) Department-level detail, (5) Optimisation recommendation format.",
                "max_score": 5,
            },
            {
                "id": "D1_E1",
                "tier": "elite",
                "instruction": "Design a comprehensive store health assessment that an AI could run monthly for all 43 Harris Farm stores. Include: KPI scorecard, trend analysis, peer benchmarking, anomaly detection, and automatic categorisation into 'thriving', 'stable', 'at risk', and 'intervention needed'. Define all thresholds and rules.",
                "context_tag": "data",
                "scoring_criteria": "Score 1-5: (1) Scorecard covers 5+ KPIs with thresholds, (2) Trend analysis methodology defined, (3) Peer benchmarking logic fair (controls for store size/age), (4) Anomaly detection rules specified, (5) Category definitions with clear threshold rules.",
                "max_score": 5,
            },
            {
                "id": "D1_E2",
                "tier": "elite",
                "instruction": "A new store opened 6 months ago and is underperforming vs the business case. Design a multi-prompt analysis that separates launch curve effects from genuine issues, benchmarks against other store openings, and produces a remediation plan with 30/60/90 day milestones.",
                "context_tag": "strategy",
                "scoring_criteria": "Score 1-5: (1) Launch curve methodology defined, (2) Benchmarks against comparable openings, (3) Distinguishes structural vs temporary issues, (4) 30/60/90 plan is specific, (5) Includes criteria for escalation if targets not met.",
                "max_score": 5,
            },
        ],
    },

    # ==================================================================
    # D2: PRODUCT INTELLIGENCE
    # ==================================================================
    {
        "code": "D2",
        "series": "do",
        "name": "Product Intelligence",
        "level": 2,
        "description": "Category management, PLU analysis, supplier negotiation, and seasonal planning.",
        "lessons": [
            {
                "order": 1,
                "title": "Category and PLU Analysis",
                "content_md": (
                    "## Product Performance at Harris Farm\n\n"
                    "Harris Farm tracks products at PLU (Price Look-Up) level with ~27M rows of data.\n\n"
                    "### Key Product Metrics\n"
                    "- **Rate of Sale (RoS)** — Units sold per store per week\n"
                    "- **Margin %** — Gross profit percentage\n"
                    "- **Range Penetration** — What % of stores carry this PLU\n"
                    "- **Wastage %** — Spoilage rate for perishables\n"
                    "- **Supplier Diversity** — Number of suppliers in a category\n\n"
                    "### The 4-Box Product Matrix\n\n"
                    "| | High Margin | Low Margin |\n"
                    "|---|---|---|\n"
                    "| **High Velocity** | Stars (protect) | Traffic drivers (review pricing) |\n"
                    "| **Low Velocity** | Hidden gems (promote) | Delist candidates (review) |\n\n"
                    "### AI for Category Management\n\n"
                    "Ask the AI to classify all PLUs in a category into the 4-box matrix, "
                    "then recommend actions for each quadrant."
                ),
            },
            {
                "order": 2,
                "title": "Seasonal Planning and Supplier Management",
                "content_md": (
                    "## Planning for Seasonality\n\n"
                    "Harris Farm's product mix shifts dramatically by season:\n\n"
                    "- **Summer**: Stone fruit, berries, watermelon, salads\n"
                    "- **Autumn**: Apples, pears, mushrooms, root vegetables\n"
                    "- **Winter**: Citrus, broccoli, cauliflower, hearty greens\n"
                    "- **Spring**: Asparagus, avocados, mangoes start\n\n"
                    "### AI for Seasonal Planning\n\n"
                    "Use AI to:\n"
                    "1. Analyse prior year demand patterns by PLU and store\n"
                    "2. Identify which stores over/under-ordered specific products\n"
                    "3. Suggest order quantities based on trend + growth rate\n"
                    "4. Flag supplier capacity risks for peak demand periods\n\n"
                    "### Supplier Negotiation Prep\n\n"
                    "AI can prepare negotiation briefs by analysing:\n"
                    "- Our volume as % of supplier's total business\n"
                    "- Price trend vs market index\n"
                    "- Quality metrics (returns, complaints)\n"
                    "- Alternative supplier availability"
                ),
            },
        ],
        "exercises": [
            {
                "id": "D2_S1",
                "tier": "standard",
                "instruction": "Write a prompt to classify all PLUs in the cheese category into the 4-box product matrix (Stars, Traffic Drivers, Hidden Gems, Delist Candidates) using rate of sale and margin % as the axes.",
                "context_tag": "commercial",
                "scoring_criteria": "Score 1-5: (1) 4-box matrix clearly defined, (2) Thresholds for high/low specified, (3) Both metrics (RoS and margin) referenced, (4) Time period specified, (5) Actions per quadrant requested.",
                "max_score": 5,
            },
            {
                "id": "D2_S2",
                "tier": "standard",
                "instruction": "Write a prompt to forecast strawberry demand for all Harris Farm stores for the next 4 weeks. Reference historical same-period data and specify how to handle new stores without history.",
                "context_tag": "supply_chain",
                "scoring_criteria": "Score 1-5: (1) Product and time frame clear, (2) Historical comparison methodology, (3) New store handling specified, (4) Store-level granularity, (5) Output format includes confidence levels.",
                "max_score": 5,
            },
            {
                "id": "D2_R1",
                "tier": "stretch",
                "instruction": "Design a prompt to prepare a supplier negotiation brief for our top avocado supplier. Include: volume analysis, price benchmarking, quality metrics, market conditions, and recommended negotiation positions (target, walk-away, and best alternative).",
                "context_tag": "commercial",
                "scoring_criteria": "Score 1-5: (1) Volume analysis scope defined, (2) Price benchmarking methodology, (3) Quality metrics included, (4) Market context referenced, (5) Three negotiation positions with rationale.",
                "max_score": 5,
            },
            {
                "id": "D2_R2",
                "tier": "stretch",
                "instruction": "Write a prompt to identify the top 20 PLUs that should be ranged differently by store cluster (CBD stores vs suburban vs regional). Include: demographic fit, sales velocity by store type, margin comparison, and recommendation for which PLUs to add/remove per cluster.",
                "context_tag": "data",
                "scoring_criteria": "Score 1-5: (1) Store clustering logic defined, (2) PLU selection criteria clear, (3) Demographic factors specified, (4) Add/remove recommendations per cluster, (5) Impact quantification requested.",
                "max_score": 5,
            },
            {
                "id": "D2_E1",
                "tier": "elite",
                "instruction": "Design an AI-powered seasonal range planning system for fresh produce. It should: (1) analyse 3 years of historical demand by PLU/store/week, (2) identify emerging trends vs declining categories, (3) recommend new product introductions with volume estimates, (4) flag supplier capacity risks, and (5) produce a store-by-store order guide. Write the complete prompt system.",
                "context_tag": "supply_chain",
                "scoring_criteria": "Score 1-5: (1) 3-year historical analysis specified, (2) Trend detection methodology, (3) New product introduction framework, (4) Supplier risk assessment included, (5) Store-level order guide with practical format.",
                "max_score": 5,
            },
            {
                "id": "D2_E2",
                "tier": "elite",
                "instruction": "Design a comprehensive product delisting analysis system. It should evaluate PLUs across: financial performance, customer loyalty impact (do delisted-product buyers churn?), supplier relationship implications, shelf space opportunity cost, and substitution availability. Create the full prompt chain with guardrails to prevent premature delisting.",
                "context_tag": "commercial",
                "scoring_criteria": "Score 1-5: (1) Five evaluation dimensions covered, (2) Customer churn risk methodology, (3) Supplier relationship impact assessed, (4) Shelf space reallocation plan, (5) Guardrails prevent high-risk delisting without review.",
                "max_score": 5,
            },
        ],
    },

    # ==================================================================
    # D3: CUSTOMER ANALYTICS
    # ==================================================================
    {
        "code": "D3",
        "series": "do",
        "name": "Customer Analytics",
        "level": 3,
        "description": "Customer segmentation, loyalty analysis, market share interpretation, and trade areas.",
        "lessons": [
            {
                "order": 1,
                "title": "Customer Segmentation",
                "content_md": (
                    "## Understanding Harris Farm Customers\n\n"
                    "With 17K+ customer profiles and 383M transactions, "
                    "we can build detailed customer segments.\n\n"
                    "### Segmentation Approaches\n\n"
                    "1. **Behavioural** — Based on purchase patterns\n"
                    "   - Frequency (weekly shoppers vs occasional)\n"
                    "   - Basket composition (fresh-heavy vs pantry-heavy)\n"
                    "   - Price sensitivity (premium vs value-seeking)\n\n"
                    "2. **Value-Based** — Based on revenue contribution\n"
                    "   - Top 20% of customers drive ~60% of revenue\n"
                    "   - At-risk high-value customers need retention strategies\n\n"
                    "3. **Geographic** — Based on distance to store\n"
                    "   - Core (0-3km): Most loyal, highest frequency\n"
                    "   - Primary (3-5km): Regular but competitive\n"
                    "   - Extended (5-10km): Destination shoppers\n\n"
                    "### AI for Customer Analysis\n\n"
                    "Prompt the AI to identify segments, profile them, and recommend "
                    "actions for each segment. Always specify which customer attributes to use."
                ),
            },
            {
                "order": 2,
                "title": "Market Share and Trade Areas",
                "content_md": (
                    "## Interpreting Market Share Data\n\n"
                    "Harris Farm's market share data (CBAS) provides postcode-level "
                    "share for HFM vs other major supermarkets.\n\n"
                    "### Critical Rules (from CLAUDE.md)\n\n"
                    "1. **Share % is the primary metric** — Dollar values are modelled estimates\n"
                    "2. **Never mix with POS revenue** (Layer 1 vs Layer 2)\n"
                    "3. **Compare YoY only** — Never sequential months\n"
                    "4. **Low share ≠ opportunity** — Needs penetration + demographic confirmation\n"
                    "5. **Distance tiers matter** — Core (0-3km) is most reliable\n\n"
                    "### Trade Area Analysis\n\n"
                    "For each store, analyse share in concentric rings:\n"
                    "- 0-3km: Core trade area (most actionable)\n"
                    "- 0-5km: Primary trade area\n"
                    "- 0-10km: Secondary (marketing/brand)\n"
                    "- 10-20km: Extended (online strategy)\n"
                    "- 20km+: Exclude from strategic analysis"
                ),
            },
        ],
        "exercises": [
            {
                "id": "D3_S1",
                "tier": "standard",
                "instruction": "Write a prompt to segment Harris Farm customers into 4-5 behavioural groups based on purchase frequency, basket size, and department preferences. Specify the data fields needed and how to profile each segment.",
                "context_tag": "customer",
                "scoring_criteria": "Score 1-5: (1) Segmentation criteria defined, (2) Data fields specified, (3) 4-5 segments requested, (4) Profiling requirements clear, (5) Action per segment requested.",
                "max_score": 5,
            },
            {
                "id": "D3_S2",
                "tier": "standard",
                "instruction": "Write a prompt to analyse Harris Farm's market share trend in the core trade area (0-3km) around the Mosman store. Compare HFM Instore + Online vs competitors, YoY. Flag any postcodes with >2pp share decline.",
                "context_tag": "customer",
                "scoring_criteria": "Score 1-5: (1) Trade area distance specified, (2) Store identified, (3) Both channels included, (4) YoY comparison, (5) Flagging threshold defined.",
                "max_score": 5,
            },
            {
                "id": "D3_R1",
                "tier": "stretch",
                "instruction": "Design a customer churn early-warning prompt. It should identify customers whose visit frequency has declined by >30% over the last 3 months compared to their personal baseline. Segment churning customers by value tier and suggest retention actions for each.",
                "context_tag": "customer",
                "scoring_criteria": "Score 1-5: (1) Churn definition quantified, (2) Personal baseline methodology, (3) Value tier segmentation, (4) Retention actions per tier, (5) Time period and comparison logic clear.",
                "max_score": 5,
            },
            {
                "id": "D3_R2",
                "tier": "stretch",
                "instruction": "A colleague says 'We should open a store in postcode 2050 because our share is only 2% there.' Write a detailed response explaining why this conclusion is premature, referencing market share interpretation rules. Then write the correct analysis prompt.",
                "context_tag": "strategy",
                "scoring_criteria": "Score 1-5: (1) Identifies the 'low share ≠ opportunity' rule, (2) Lists what else needs confirming, (3) References distance tiers, (4) Corrected prompt includes demographic and penetration checks, (5) Flags output as DIRECTIONAL ONLY.",
                "max_score": 5,
            },
            {
                "id": "D3_E1",
                "tier": "elite",
                "instruction": "Design a comprehensive trade area health assessment for all 43 Harris Farm stores. It should: analyse share trends by distance tier, identify market share risk zones, correlate share movements with demographic changes, flag cannibalisation between nearby stores, and produce a prioritised action plan per store. Include all data caveats.",
                "context_tag": "strategy",
                "scoring_criteria": "Score 1-5: (1) Distance tier analysis for all stores, (2) Risk zone identification methodology, (3) Demographic correlation approach, (4) Cannibalisation detection logic, (5) All CBAS data caveats included.",
                "max_score": 5,
            },
            {
                "id": "D3_E2",
                "tier": "elite",
                "instruction": "Design an AI system that monitors customer lifetime value (CLV) changes in real-time and triggers automated interventions. Include: CLV calculation methodology, trigger thresholds, intervention types (personalised offer, manager outreach, loyalty program upgrade), and ROI measurement for each intervention.",
                "context_tag": "customer",
                "scoring_criteria": "Score 1-5: (1) CLV calculation methodology defined, (2) Trigger thresholds with rationale, (3) Three distinct intervention types, (4) Personalisation logic explained, (5) ROI measurement per intervention.",
                "max_score": 5,
            },
        ],
    },

    # ==================================================================
    # D4: OPERATIONS OPTIMISATION
    # ==================================================================
    {
        "code": "D4",
        "series": "do",
        "name": "Operations Optimisation",
        "level": 4,
        "description": "Supply chain, transport, inventory, and demand forecasting with AI.",
        "lessons": [
            {
                "order": 1,
                "title": "Supply Chain and Inventory Optimisation",
                "content_md": (
                    "## AI for Operations at Harris Farm\n\n"
                    "Operations optimisation is where AI delivers the fastest ROI.\n\n"
                    "### Key Operational Challenges\n\n"
                    "1. **Wastage** — Fresh produce has short shelf life. Over-order = waste. Under-order = lost sales.\n"
                    "2. **Transport** — 43 stores across NSW/QLD need efficient delivery routes.\n"
                    "3. **Staffing** — Labour is largest controllable cost. Peak coverage vs quiet hours.\n"
                    "4. **Inventory** — Balance freshness vs availability. Category-specific rules.\n\n"
                    "### AI Applications\n\n"
                    "- **Demand Forecasting**: Predict by store/PLU/day using weather, events, promotions\n"
                    "- **Auto-Ordering**: Suggest order quantities based on forecast + current stock\n"
                    "- **Route Optimisation**: Minimise fuel and time across delivery network\n"
                    "- **Labour Scheduling**: Match staff hours to predicted customer traffic\n\n"
                    "### Writing Operations Prompts\n\n"
                    "Operations prompts need:\n"
                    "- **Constraints** — Budget limits, truck capacity, staff availability\n"
                    "- **Objectives** — Minimise cost? Maximise freshness? Balance both?\n"
                    "- **Trade-offs** — Explicitly ask the AI to quantify trade-offs"
                ),
            },
            {
                "order": 2,
                "title": "Demand Forecasting with AI",
                "content_md": (
                    "## Building Better Forecasts\n\n"
                    "### Forecast Inputs\n\n"
                    "Good demand forecasts combine:\n"
                    "- Historical sales (same day of week, same season YoY)\n"
                    "- Weather data (hot weather → more salads, cold → more soups)\n"
                    "- Events (school holidays, public holidays, local events)\n"
                    "- Promotions (own and competitor)\n"
                    "- Trends (growing categories vs declining)\n\n"
                    "### Prompt Design for Forecasting\n\n"
                    "Specify:\n"
                    "1. Forecast horizon (tomorrow, next week, next month)\n"
                    "2. Granularity (store-level, department, PLU)\n"
                    "3. Variables to consider\n"
                    "4. Accuracy metric (MAPE, bias)\n"
                    "5. Confidence intervals\n\n"
                    "### Example\n\n"
                    "*Forecast daily banana demand for each NSW store for the next 7 days. "
                    "Use same-week-last-year as baseline, adjust for this week's forecast "
                    "temperature (BOM data), account for the school holiday uplift pattern, "
                    "and flag any store where forecast exceeds 2x the 4-week average.*"
                ),
            },
        ],
        "exercises": [
            {
                "id": "D4_S1",
                "tier": "standard",
                "instruction": "Write a prompt to analyse fresh produce wastage across all Harris Farm stores for the last month. Identify the top 10 highest-wastage PLUs by dollar value and suggest order quantity adjustments.",
                "context_tag": "supply_chain",
                "scoring_criteria": "Score 1-5: (1) Wastage metric defined, (2) Time period specified, (3) Top 10 ranking criteria clear, (4) Order adjustment methodology, (5) Store-level granularity.",
                "max_score": 5,
            },
            {
                "id": "D4_S2",
                "tier": "standard",
                "instruction": "Write a prompt to optimise delivery routes for Harris Farm's Sydney distribution network. Include constraints for truck capacity, delivery time windows, and freshness requirements for perishables.",
                "context_tag": "supply_chain",
                "scoring_criteria": "Score 1-5: (1) Route optimisation objective clear, (2) Truck capacity constraint, (3) Time window constraints, (4) Freshness requirements specified, (5) Output format (route plan) defined.",
                "max_score": 5,
            },
            {
                "id": "D4_R1",
                "tier": "stretch",
                "instruction": "Design a demand forecasting prompt for Christmas week seafood across all Harris Farm stores. Account for: prior year patterns, weather forecast, store-specific trends, online vs instore split, and supply constraints. Include confidence intervals and an over-order risk assessment.",
                "context_tag": "operations",
                "scoring_criteria": "Score 1-5: (1) Multiple input variables specified, (2) Store-level granularity, (3) Channel split (online/instore), (4) Confidence intervals requested, (5) Risk assessment for over-ordering included.",
                "max_score": 5,
            },
            {
                "id": "D4_R2",
                "tier": "stretch",
                "instruction": "Write a prompt to create a labour scheduling model for a Harris Farm store. It should predict hourly customer traffic, calculate required staff by department, identify optimal shift start/end times, and balance full-time vs casual staff. Include cost constraints.",
                "context_tag": "operations",
                "scoring_criteria": "Score 1-5: (1) Hourly traffic prediction methodology, (2) Department-level staffing ratios, (3) Shift optimisation criteria, (4) FT vs casual balance logic, (5) Cost constraint and trade-off analysis.",
                "max_score": 5,
            },
            {
                "id": "D4_E1",
                "tier": "elite",
                "instruction": "Design a complete AI-powered inventory management system for Harris Farm's perishable goods. Include: demand forecasting, auto-ordering rules, wastage prediction, markdown timing optimisation, and a feedback loop that improves accuracy over time. Specify all business rules and guardrails.",
                "context_tag": "supply_chain",
                "scoring_criteria": "Score 1-5: (1) Five components clearly designed, (2) Business rules for auto-ordering, (3) Markdown timing logic, (4) Feedback loop methodology, (5) Guardrails prevent over-ordering disasters.",
                "max_score": 5,
            },
            {
                "id": "D4_E2",
                "tier": "elite",
                "instruction": "Harris Farm wants to reduce food waste by 30% in 12 months while maintaining 95% product availability. Design the AI system that would achieve this. Include: prediction models, operational triggers, staff alerts, supplier coordination, markdown automation, and donation routing for near-expiry items. Quantify expected impact at each stage.",
                "context_tag": "strategy",
                "scoring_criteria": "Score 1-5: (1) System architecture covers all components, (2) Prediction models specified with inputs, (3) Operational triggers are quantified, (4) Donation routing logic included, (5) Impact quantification is credible and staged.",
                "max_score": 5,
            },
        ],
    },

    # ==================================================================
    # D5: STRATEGIC DECISION-MAKING
    # ==================================================================
    {
        "code": "D5",
        "series": "do",
        "name": "Strategic Decision-Making",
        "level": 5,
        "description": "Multi-source analysis, board presentations, scenario modelling, and investment cases.",
        "lessons": [
            {
                "order": 1,
                "title": "Multi-Source Strategic Analysis",
                "content_md": (
                    "## Synthesising Multiple Data Sources\n\n"
                    "Strategic decisions at Harris Farm require combining:\n\n"
                    "- Internal data (POS, inventory, labour, customer)\n"
                    "- Market data (CBAS share, competitor intel)\n"
                    "- External data (demographics, economic indicators, weather patterns)\n\n"
                    "### Framework: The Strategic Question Ladder\n\n"
                    "1. **What happened?** — Descriptive analytics\n"
                    "2. **Why did it happen?** — Diagnostic analytics\n"
                    "3. **What will happen?** — Predictive analytics\n"
                    "4. **What should we do?** — Prescriptive analytics\n\n"
                    "### AI for Strategy\n\n"
                    "The best strategic prompts:\n"
                    "- Specify which data sources to synthesise\n"
                    "- Define the decision being made\n"
                    "- Ask for scenarios, not just one answer\n"
                    "- Request assumptions and sensitivities\n"
                    "- Include implementation considerations"
                ),
            },
            {
                "order": 2,
                "title": "Scenario Modelling and Investment Cases",
                "content_md": (
                    "## Building Scenarios with AI\n\n"
                    "### Three-Scenario Model\n"
                    "For any major decision, build:\n"
                    "1. **Base Case** — Most likely outcome given current trends\n"
                    "2. **Upside Case** — Best reasonable outcome if things go well\n"
                    "3. **Downside Case** — Worst reasonable outcome if things go poorly\n\n"
                    "### Investment Case Components\n\n"
                    "- **Strategic Rationale** — Why this investment aligns with Vision 2030\n"
                    "- **Financial Model** — Revenue, costs, ROI, payback period for each scenario\n"
                    "- **Risk Assessment** — What could go wrong and mitigation strategies\n"
                    "- **Implementation Plan** — Phasing, milestones, decision gates\n"
                    "- **Success Metrics** — How we'll know it's working\n\n"
                    "### AI Prompt Design for Scenarios\n\n"
                    "*Model three scenarios for opening a new Harris Farm store in [suburb]. "
                    "Base case assumes we capture [X]% market share in year 1. "
                    "Upside adds [Y]% for online growth. Downside accounts for competitor response. "
                    "For each scenario, project: revenue, EBITDA, customer count, break-even month. "
                    "Present as a comparison table with key sensitivities highlighted.*"
                ),
            },
        ],
        "exercises": [
            {
                "id": "D5_S1",
                "tier": "standard",
                "instruction": "Write a prompt to create a SWOT analysis for Harris Farm Markets using internal performance data and market share data. Specify which data sources to use for each quadrant (Strengths, Weaknesses, Opportunities, Threats).",
                "context_tag": "strategy",
                "scoring_criteria": "Score 1-5: (1) SWOT framework clearly applied, (2) Data sources mapped to each quadrant, (3) Internal (S/W) uses Layer 1 data, (4) External (O/T) uses appropriate sources, (5) Actionable implications requested per quadrant.",
                "max_score": 5,
            },
            {
                "id": "D5_S2",
                "tier": "standard",
                "instruction": "Write a prompt to model three scenarios (base, upside, downside) for launching an online-only dark store for Harris Farm. Define the assumptions for each scenario and specify the financial metrics to project.",
                "context_tag": "finance",
                "scoring_criteria": "Score 1-5: (1) Three scenarios defined, (2) Key assumptions explicit per scenario, (3) Financial metrics listed, (4) Comparison format specified, (5) Sensitivity analysis requested.",
                "max_score": 5,
            },
            {
                "id": "D5_R1",
                "tier": "stretch",
                "instruction": "Design a prompt for a comprehensive investment case to renovate and expand the Leichhardt store. Include: market analysis, cannibalisation assessment, financial projections (3 scenarios), risk matrix, phased implementation plan, and decision criteria for proceed/pause/abort.",
                "context_tag": "finance",
                "scoring_criteria": "Score 1-5: (1) Market analysis uses appropriate data, (2) Cannibalisation risk quantified, (3) Three scenario financials with ROI, (4) Risk matrix with mitigation, (5) Decision gates defined.",
                "max_score": 5,
            },
            {
                "id": "D5_R2",
                "tier": "stretch",
                "instruction": "Write a prompt to create a board presentation on Harris Farm's competitive position. Synthesise: internal financial performance (Layer 1), market share trends (Layer 2), demographic shifts, and competitor actions. Include data source caveats and confidence levels on all claims.",
                "context_tag": "reporting",
                "scoring_criteria": "Score 1-5: (1) Multiple data sources synthesised, (2) Layer 1/Layer 2 properly separated, (3) Competitive context included, (4) Confidence levels on claims, (5) Board-appropriate format and tone.",
                "max_score": 5,
            },
            {
                "id": "D5_E1",
                "tier": "elite",
                "instruction": "Harris Farm is considering entering a new state (Victoria). Design the complete AI-powered analysis to support this decision. Include: market sizing, competitive landscape, site selection criteria, financial modelling (5-year), risk assessment, cannibalisation of online sales, brand awareness challenges, supply chain implications, and a phased rollout recommendation. This should be a complete strategic recommendation framework.",
                "context_tag": "strategy",
                "scoring_criteria": "Score 1-5: (1) Market sizing methodology appropriate, (2) Site selection criteria are Harris Farm-specific, (3) Financial model covers 5 years with sensitivities, (4) Supply chain implications addressed, (5) Phased rollout is practical with decision gates.",
                "max_score": 5,
            },
            {
                "id": "D5_E2",
                "tier": "elite",
                "instruction": "The board asks: 'Should Harris Farm acquire a competitor with 15 stores?' Design the due diligence analysis framework that an AI system would run. Include: financial analysis (revenue, profitability, assets), customer overlap analysis, brand compatibility assessment, operational integration plan, synergy quantification, risk register, and a recommendation structure with go/no-go criteria.",
                "context_tag": "finance",
                "scoring_criteria": "Score 1-5: (1) Due diligence covers all key areas, (2) Customer overlap analysis methodology, (3) Synergy quantification is realistic, (4) Integration plan phased with milestones, (5) Go/no-go criteria are objective and measurable.",
                "max_score": 5,
            },
        ],
    },
]


# ---------------------------------------------------------------------------
# Seeding helper
# ---------------------------------------------------------------------------

def get_all_exercises_for_seeding():
    """Flatten all exercises from all modules into a list of dicts
    suitable for sa_v4_schema.seed_v4_exercises().

    Maps content fields to DB schema:
    - instruction -> exercise_title + scenario_text
    - scoring_criteria -> expected_approach
    """
    exercises = []
    for mod in V4_MODULES:
        level = mod.get("level", 1)
        rubric = (
            "foundational" if level <= 2
            else ("advanced_output" if level <= 4 else "multi_tier_panel")
        )
        for ex in mod.get("exercises", []):
            exercises.append({
                "module_code": mod["code"],
                "tier": ex["tier"],
                "context_tag": ex.get("context_tag", "general"),
                "is_curveball": False,
                "curveball_type": None,
                "exercise_title": ex["id"],
                "scenario_text": ex["instruction"],
                "expected_approach": ex.get("scoring_criteria", ""),
                "rubric_code": rubric,
                "pass_score": 3.0,
                "xp_reward": 15 if ex["tier"] == "standard" else (20 if ex["tier"] == "stretch" else 25),
            })
    return exercises


def get_all_lessons_for_seeding():
    """Flatten all lessons from all modules for DB seeding."""
    lessons = []
    for mod in V4_MODULES:
        for lesson in mod.get("lessons", []):
            lessons.append({
                "module_code": mod["code"],
                "order": lesson["order"],
                "title": lesson["title"],
                "content_md": lesson["content_md"],
            })
    return lessons


def get_modules_for_seeding():
    """Return module metadata for DB seeding."""
    modules = []
    for mod in V4_MODULES:
        modules.append({
            "module_code": mod["code"],
            "series": mod["series"],
            "module_name": mod["name"],
            "level": mod["level"],
            "description": mod["description"],
        })
    return modules
