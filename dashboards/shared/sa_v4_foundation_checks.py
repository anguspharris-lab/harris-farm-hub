"""
Skills Academy v4 -- Foundation Check Exercises
=================================================
Defines 12 foundation check exercises (3 per level, levels 1-4) for the
Woven Verification system. Foundation checks are warm-up exercises injected
for provisionally-placed users to verify they have foundations from lower
levels before proceeding.

Check types:
  L1 (Prompt Basics)       -- Rewrite a vague prompt using all 4 elements
  L2 (Output Verification) -- Spot the hallucinated number in 3 AI outputs
  L3 (Multi-Step Thinking) -- Convert a single-step prompt into a chain
  L4 (Rubric Scoring)      -- Score an AI output on the Advanced Output Rubric

Python 3.9 compatible.
"""

from typing import List, Dict, Any, Optional

# ---------------------------------------------------------------------------
# LEVEL 1 FOUNDATION CHECKS
# Rewrite a vague request using all 4 elements: Task, Context, Format, Constraints
# Score >= 14/20 on Foundational Rubric to pass
# ---------------------------------------------------------------------------

_L1_CHECKS = [
    {
        "check_code": "FC-L1-1",
        "level": 1,
        "check_title": "Rewrite: Vague Sales Request",
        "instructions": (
            "The prompt below is vague and poorly structured. Rewrite it as a "
            "high-quality prompt that includes all 4 foundational elements:\n\n"
            "1. **Task** -- What exactly do you want the AI to do?\n"
            "2. **Context** -- What business situation or background is relevant?\n"
            "3. **Format** -- What should the output look like?\n"
            "4. **Constraints** -- What limits, exclusions, or guardrails apply?\n\n"
            "Your rewritten prompt should be specific to Harris Farm Markets and "
            "ready to send to an AI assistant."
        ),
        "scenario_text": (
            "**Original vague prompt:**\n\n"
            "\"Tell me about our sales.\""
        ),
        "pass_criteria": (
            "The rewritten prompt must contain all 4 elements:\n"
            "- TASK: A specific analytical request (e.g. compare week-on-week "
            "sales, identify top/bottom performers, calculate growth rates)\n"
            "- CONTEXT: Names a store, region, category, or time period relevant "
            "to Harris Farm Markets\n"
            "- FORMAT: Specifies the output structure (e.g. table, bullet points, "
            "executive summary with sections)\n"
            "- CONSTRAINTS: Includes at least one guardrail (e.g. time range, "
            "exclude online, focus on fresh produce only, keep under 200 words)\n"
            "Score each element 1-5, total /20. Pass threshold: 14."
        ),
        "pass_threshold": 14.0,
        "coaching_on_fail": (
            "No worries -- writing clear prompts is a skill that improves with "
            "practice. The key is remembering the 4 elements: Task, Context, "
            "Format, and Constraints. Try thinking of it like a brief you would "
            "give a new team member on their first day -- the more specific you "
            "are, the better the result. Have another go!"
        ),
        "context_tag": "foundation_l1",
    },
    {
        "check_code": "FC-L1-2",
        "level": 1,
        "check_title": "Rewrite: Vague Customer Analysis",
        "instructions": (
            "The prompt below is vague and poorly structured. Rewrite it as a "
            "high-quality prompt that includes all 4 foundational elements:\n\n"
            "1. **Task** -- What exactly do you want the AI to do?\n"
            "2. **Context** -- What business situation or background is relevant?\n"
            "3. **Format** -- What should the output look like?\n"
            "4. **Constraints** -- What limits, exclusions, or guardrails apply?\n\n"
            "Your rewritten prompt should be specific to Harris Farm Markets and "
            "ready to send to an AI assistant."
        ),
        "scenario_text": (
            "**Original vague prompt:**\n\n"
            "\"What are our customers like?\""
        ),
        "pass_criteria": (
            "The rewritten prompt must contain all 4 elements:\n"
            "- TASK: A specific customer analysis request (e.g. segment customers "
            "by purchase frequency, identify lapsed shoppers, profile top-spend "
            "cohorts)\n"
            "- CONTEXT: References Harris Farm customer data, a specific store or "
            "region, loyalty programme, or time period\n"
            "- FORMAT: Specifies output structure (e.g. customer persona cards, "
            "segmentation table with columns, comparison chart description)\n"
            "- CONSTRAINTS: Includes at least one limit (e.g. last 12 months "
            "only, instore transactions, exclude staff purchases, top 5 segments)\n"
            "Score each element 1-5, total /20. Pass threshold: 14."
        ),
        "pass_threshold": 14.0,
        "coaching_on_fail": (
            "Good effort! The trick with customer analysis prompts is to be "
            "precise about which customers and what timeframe. Instead of 'our "
            "customers', try specifying something like 'customers who have "
            "shopped at our Bondi Beach store in the last 6 months'. That "
            "specificity is what turns a vague question into an actionable one. "
            "Give it another crack!"
        ),
        "context_tag": "foundation_l1",
    },
    {
        "check_code": "FC-L1-3",
        "level": 1,
        "check_title": "Rewrite: Vague Product Request",
        "instructions": (
            "The prompt below is vague and poorly structured. Rewrite it as a "
            "high-quality prompt that includes all 4 foundational elements:\n\n"
            "1. **Task** -- What exactly do you want the AI to do?\n"
            "2. **Context** -- What business situation or background is relevant?\n"
            "3. **Format** -- What should the output look like?\n"
            "4. **Constraints** -- What limits, exclusions, or guardrails apply?\n\n"
            "Your rewritten prompt should be specific to Harris Farm Markets and "
            "ready to send to an AI assistant."
        ),
        "scenario_text": (
            "**Original vague prompt:**\n\n"
            "\"Help me with our fruit stuff.\""
        ),
        "pass_criteria": (
            "The rewritten prompt must contain all 4 elements:\n"
            "- TASK: A specific product-related request (e.g. analyse seasonal "
            "fruit sales trends, compare supplier pricing, identify slow-moving "
            "stone fruit lines, draft a range review brief)\n"
            "- CONTEXT: References Harris Farm's fresh produce category, names a "
            "fruit subcategory, season, supplier, or buying situation\n"
            "- FORMAT: Specifies output structure (e.g. ranked table of SKUs, "
            "week-by-week trend chart description, buying brief with sections)\n"
            "- CONSTRAINTS: Includes at least one guardrail (e.g. summer season "
            "only, exclude imported lines, Australian-grown only, last 8 weeks)\n"
            "Score each element 1-5, total /20. Pass threshold: 14."
        ),
        "pass_threshold": 14.0,
        "coaching_on_fail": (
            "Almost there! When it comes to product prompts, specificity is "
            "everything. 'Fruit stuff' could mean a hundred different things. "
            "Try narrowing down to a specific subcategory (like stone fruit or "
            "citrus), a time period, and what decision you are trying to make. "
            "Are you reviewing the range? Checking margins? Planning a seasonal "
            "promotion? That clarity makes all the difference."
        ),
        "context_tag": "foundation_l1",
    },
]

# ---------------------------------------------------------------------------
# LEVEL 2 FOUNDATION CHECKS
# Spot the hallucinated number among 3 AI outputs
# Must identify the fabricated statistic correctly + explain reasoning
# ---------------------------------------------------------------------------

_L2_CHECKS = [
    {
        "check_code": "FC-L2-1",
        "level": 2,
        "check_title": "Spot the Hallucination: Store Margins",
        "instructions": (
            "Below are 3 AI-generated summaries about Harris Farm store "
            "performance. **One of these outputs contains a hallucinated "
            "(fabricated) number.** Your job is to:\n\n"
            "1. Identify which output (A, B, or C) contains the hallucination\n"
            "2. Explain which specific number is fabricated and why it seems wrong\n"
            "3. Describe what you would do to verify the real figure\n\n"
            "Think about what you know about typical grocery retail metrics "
            "and Harris Farm's business."
        ),
        "scenario_text": (
            "**Output A:**\n"
            "\"Bondi Beach store achieved a gross margin of 28.3% on fresh produce "
            "in Q3 FY25, slightly above the network average of 27.1%. The store's "
            "top-performing subcategory was organic vegetables at 31.2% margin, "
            "driven by strong demand from the local health-conscious demographic.\"\n\n"
            "**Output B:**\n"
            "\"The Drummoyne store reported a dairy category gross margin of 47.6% "
            "in Q3 FY25, making it the highest-margin category in the store. Fresh "
            "milk lines contributed $82,000 in weekly revenue, with cheese and "
            "yoghurt lines adding a further $41,000 per week.\"\n\n"
            "**Output C:**\n"
            "\"Miranda store's fresh produce shrinkage rate was 4.8% in Q3 FY25, "
            "which is within the industry benchmark of 3-6% for specialty fresh "
            "food retailers. The store's waste reduction program brought this down "
            "from 5.9% in the prior quarter through improved ordering cadence.\""
        ),
        "pass_criteria": (
            "Correct answer: Output B contains the hallucination.\n"
            "The fabricated figure is the 47.6% dairy gross margin. In grocery "
            "retail, dairy margins typically range from 20-32%. A 47.6% gross "
            "margin on dairy is unrealistically high -- dairy is a known "
            "low-margin traffic driver. The user must:\n"
            "1. Correctly identify Output B as the hallucinated one (required)\n"
            "2. Identify the 47.6% margin as the suspicious figure (required)\n"
            "3. Provide reasonable explanation for why it is wrong, referencing "
            "typical dairy margins or grocery economics (required)\n"
            "4. Suggest a verification step (e.g. check POS margin reports, "
            "compare to category benchmarks) (bonus)"
        ),
        "pass_threshold": 1.0,
        "coaching_on_fail": (
            "Catching hallucinations is one of the most important AI skills. "
            "The trick is knowing your domain. In grocery, dairy is a classic "
            "low-margin category -- margins of 20-32% are typical. When an AI "
            "claims 47.6%, that should immediately raise a red flag. A good "
            "rule of thumb: if a number seems surprisingly good (or bad), check "
            "it against what you know from experience. Always verify standout "
            "figures against your internal reports."
        ),
        "context_tag": "foundation_l2",
    },
    {
        "check_code": "FC-L2-2",
        "level": 2,
        "check_title": "Spot the Hallucination: Market Share Trends",
        "instructions": (
            "Below are 3 AI-generated summaries about Harris Farm's market share "
            "performance. **One of these outputs contains a hallucinated "
            "(fabricated) number.** Your job is to:\n\n"
            "1. Identify which output (A, B, or C) contains the hallucination\n"
            "2. Explain which specific number is fabricated and why it seems wrong\n"
            "3. Describe what you would do to verify the real figure\n\n"
            "Remember: Harris Farm is a specialty fresh food retailer competing "
            "against major supermarket chains like Coles and Woolworths."
        ),
        "scenario_text": (
            "**Output A:**\n"
            "\"In the core trade area (0-3km) around the Crows Nest store, Harris "
            "Farm's instore market share grew from 6.2% to 7.1% year-on-year in "
            "July 2025. This 0.9 percentage point gain came primarily from the "
            "organic and specialty cheese subcategories.\"\n\n"
            "**Output B:**\n"
            "\"Harris Farm's combined online and instore market share across all "
            "NSW postcodes reached 31.4% in July 2025, overtaking Aldi to become "
            "the third-largest grocery retailer in the state. This represents a "
            "2.3 percentage point gain on the prior year.\"\n\n"
            "**Output C:**\n"
            "\"The Double Bay store's primary trade area (3-5km) saw Harris Farm's "
            "market share decline from 8.8% to 7.5% between July 2024 and July "
            "2025. The 1.3pp decline coincides with a new Woolworths Metro opening "
            "within the catchment in March 2025.\""
        ),
        "pass_criteria": (
            "Correct answer: Output B contains the hallucination.\n"
            "The fabricated figure is the 31.4% statewide market share. Harris "
            "Farm is a specialty retailer with ~21 stores in Sydney. Achieving "
            "31.4% of total NSW grocery market share would make them larger than "
            "Aldi, which has 100+ stores across NSW. Realistic HFM market share "
            "across all NSW postcodes would be in the low single digits (1-4%). "
            "The user must:\n"
            "1. Correctly identify Output B (required)\n"
            "2. Identify 31.4% statewide share as the fabricated number (required)\n"
            "3. Explain why -- HFM is a niche player with limited store count, "
            "nowhere near Aldi or majors at a state level (required)\n"
            "4. Suggest verification (e.g. check CBAS market share data, compare "
            "to known store-level shares) (bonus)"
        ),
        "pass_threshold": 1.0,
        "coaching_on_fail": (
            "This one tests your understanding of Harris Farm's position in the "
            "market. We are a specialty retailer with around 21 stores, all in "
            "Sydney. Claiming 31.4% of all NSW grocery spend would put us ahead "
            "of Aldi, which has over 100 stores statewide. That should be an "
            "immediate red flag. Our statewide share is realistically in the "
            "low single digits. The lesson: always sense-check AI numbers against "
            "what you know about the business's scale and competitive position."
        ),
        "context_tag": "foundation_l2",
    },
    {
        "check_code": "FC-L2-3",
        "level": 2,
        "check_title": "Spot the Hallucination: People & Rostering",
        "instructions": (
            "Below are 3 AI-generated summaries about Harris Farm's people and "
            "rostering metrics. **One of these outputs contains a hallucinated "
            "(fabricated) number.** Your job is to:\n\n"
            "1. Identify which output (A, B, or C) contains the hallucination\n"
            "2. Explain which specific number is fabricated and why it seems wrong\n"
            "3. Describe what you would do to verify the real figure\n\n"
            "Think about typical staffing levels and labour metrics for a "
            "fresh food retailer with ~21 stores."
        ),
        "scenario_text": (
            "**Output A:**\n"
            "\"Harris Farm's average staff turnover rate across the network was "
            "38% in FY25, which is broadly in line with the Australian retail "
            "industry benchmark of 35-45%. The Parramatta store had the highest "
            "turnover at 52%, likely driven by competition from nearby Westfield "
            "retailers for casual staff.\"\n\n"
            "**Output B:**\n"
            "\"The Leichhardt store operates with an average of 42 team members "
            "across all shifts, including 12 full-time, 18 part-time, and 12 "
            "casual staff. Saturday is the peak roster day with 28 staff rostered "
            "on, compared to a Tuesday low of 16.\"\n\n"
            "**Output C:**\n"
            "\"Harris Farm's total labour cost as a percentage of revenue was "
            "8.3% in FY25, significantly below the grocery retail industry "
            "average of 12-16%. This made Harris Farm one of the most labour-"
            "efficient grocers in Australia, ahead of both Coles and Woolworths.\""
        ),
        "pass_criteria": (
            "Correct answer: Output C contains the hallucination.\n"
            "The fabricated figure is the 8.3% labour-to-revenue ratio. For a "
            "specialty fresh food retailer like Harris Farm, which relies heavily "
            "on in-store staff for produce presentation, customer service, and "
            "the deli/butcher/bakery departments, labour costs typically range "
            "from 14-20% of revenue. An 8.3% figure would be impossibly low -- "
            "that is below even the most automated warehouse operations. The user "
            "must:\n"
            "1. Correctly identify Output C (required)\n"
            "2. Identify 8.3% labour cost ratio as fabricated (required)\n"
            "3. Explain why -- fresh food retailers are labour-intensive, and "
            "8.3% is unrealistically low for any bricks-and-mortar grocer "
            "(required)\n"
            "4. Suggest verification (e.g. check payroll vs revenue in finance "
            "reports) (bonus)"
        ),
        "pass_threshold": 1.0,
        "coaching_on_fail": (
            "This one is about knowing what realistic labour metrics look like. "
            "Harris Farm is a fresh food retailer with butchers, bakers, deli "
            "staff, produce teams, and customer service -- it is a labour-"
            "intensive operation. An 8.3% labour-to-revenue ratio would be "
            "impossibly lean. Most grocery retailers run between 12-20%, and "
            "specialty fresh food stores are typically at the higher end. If an "
            "AI gives you a number that seems too good to be true for your "
            "business model, it probably is. Always cross-check with finance."
        ),
        "context_tag": "foundation_l2",
    },
]

# ---------------------------------------------------------------------------
# LEVEL 3 FOUNDATION CHECKS
# Convert a single-step prompt into a multi-step chain (>= 3 connected steps)
# ---------------------------------------------------------------------------

_L3_CHECKS = [
    {
        "check_code": "FC-L3-1",
        "level": 3,
        "check_title": "Multi-Step Chain: Supplier Negotiation Prep",
        "instructions": (
            "The prompt below answers the question in a single step but misses "
            "the bigger picture. Rewrite it as a **multi-step prompt chain** "
            "with at least 3 connected steps that build on each other.\n\n"
            "Each step should:\n"
            "- Have a clear purpose that feeds into the next step\n"
            "- Specify what data or output from the previous step it uses\n"
            "- End with a defined output that the next step consumes\n\n"
            "Think about the full workflow a Harris Farm buyer would actually "
            "need to prepare for a supplier meeting."
        ),
        "scenario_text": (
            "**Original single-step prompt:**\n\n"
            "\"What are our top 10 suppliers by spend in the fresh produce "
            "category for the last quarter?\""
        ),
        "pass_criteria": (
            "The multi-step chain must have >= 3 connected steps with clear "
            "logic flow. A strong answer would include steps like:\n\n"
            "Step 1: Pull top 10 suppliers by spend (the original question)\n"
            "Step 2: For each supplier, pull quality metrics (reject rates, "
            "shrinkage, delivery reliability, margin performance)\n"
            "Step 3: Compare each supplier's pricing to market benchmarks or "
            "alternative suppliers\n"
            "Step 4: Generate a negotiation brief per supplier with leverage "
            "points, risks, and recommended ask\n"
            "Step 5: Draft an agenda and talking points for the quarterly "
            "supplier review meeting\n\n"
            "Minimum requirements:\n"
            "- At least 3 distinct steps (required)\n"
            "- Each step references output from the previous step (required)\n"
            "- Steps build toward a clear business action (required)\n"
            "- Harris Farm-specific context in at least 2 steps (required)"
        ),
        "pass_threshold": 14.0,
        "coaching_on_fail": (
            "Good start! The key to multi-step prompting is thinking about the "
            "full workflow, not just the first question. Asking for top suppliers "
            "by spend is step one, but what do you actually do with that list? "
            "You would probably want to check their quality and reliability, "
            "compare their pricing, and then build a negotiation brief. Each "
            "step feeds the next -- that is the chain. Try thinking about what "
            "a buyer would do after getting the initial answer."
        ),
        "context_tag": "foundation_l3",
    },
    {
        "check_code": "FC-L3-2",
        "level": 3,
        "check_title": "Multi-Step Chain: New Store Opening Analysis",
        "instructions": (
            "The prompt below answers the question in a single step but misses "
            "the bigger picture. Rewrite it as a **multi-step prompt chain** "
            "with at least 3 connected steps that build on each other.\n\n"
            "Each step should:\n"
            "- Have a clear purpose that feeds into the next step\n"
            "- Specify what data or output from the previous step it uses\n"
            "- End with a defined output that the next step consumes\n\n"
            "Think about the full analysis a Harris Farm executive would need "
            "before committing to a new location."
        ),
        "scenario_text": (
            "**Original single-step prompt:**\n\n"
            "\"Which suburbs in Sydney have the highest grocery market share "
            "opportunity for Harris Farm?\""
        ),
        "pass_criteria": (
            "The multi-step chain must have >= 3 connected steps with clear "
            "logic flow. A strong answer would include steps like:\n\n"
            "Step 1: Profile existing successful stores -- identify what "
            "demographics and trade area characteristics correlate with high "
            "HFM market share\n"
            "Step 2: Screen candidate suburbs against the success profile "
            "(professional/managerial workforce %, household income, population "
            "density, competitor proximity)\n"
            "Step 3: For shortlisted suburbs, model potential revenue and "
            "cannibalisation risk against existing stores\n"
            "Step 4: Assess real estate availability, lease costs, and fit-out "
            "requirements for top 3 candidates\n"
            "Step 5: Produce a board-ready recommendation with financial "
            "projections, risk assessment, and go/no-go recommendation\n\n"
            "Minimum requirements:\n"
            "- At least 3 distinct steps (required)\n"
            "- Each step references output from the previous step (required)\n"
            "- Steps build toward a clear business decision (required)\n"
            "- Addresses cannibalisation or competition risk (strong signal)"
        ),
        "pass_threshold": 14.0,
        "coaching_on_fail": (
            "Opening a new store is one of the biggest decisions we make, so "
            "the analysis needs to be thorough. Asking for market share "
            "opportunity is a fine starting point, but it skips the critical "
            "step of defining what makes a location right for Harris Farm. You "
            "need to profile your winners first, then screen candidates, then "
            "model the financials. Each step builds the evidence base for the "
            "final recommendation. Try working backwards from the board "
            "decision: what would they need to see to say yes?"
        ),
        "context_tag": "foundation_l3",
    },
    {
        "check_code": "FC-L3-3",
        "level": 3,
        "check_title": "Multi-Step Chain: Weekly Trade Review",
        "instructions": (
            "The prompt below answers the question in a single step but misses "
            "the bigger picture. Rewrite it as a **multi-step prompt chain** "
            "with at least 3 connected steps that build on each other.\n\n"
            "Each step should:\n"
            "- Have a clear purpose that feeds into the next step\n"
            "- Specify what data or output from the previous step it uses\n"
            "- End with a defined output that the next step consumes\n\n"
            "Think about the full preparation an Area Manager would need "
            "for their weekly trade review meeting with store managers."
        ),
        "scenario_text": (
            "**Original single-step prompt:**\n\n"
            "\"Give me a summary of this week's sales by store.\""
        ),
        "pass_criteria": (
            "The multi-step chain must have >= 3 connected steps with clear "
            "logic flow. A strong answer would include steps like:\n\n"
            "Step 1: Pull this week's sales by store vs last week and vs same "
            "week last year, flagging stores with >5% decline\n"
            "Step 2: For underperforming stores, break down by department "
            "(produce, deli, bakery, dairy, grocery, meat) to identify which "
            "categories are driving the shortfall\n"
            "Step 3: Cross-reference category declines with shrinkage, out-of-"
            "stocks, staffing gaps, and local events or weather that week\n"
            "Step 4: For each underperforming store, draft 2-3 specific action "
            "items with owners and deadlines for the store manager\n"
            "Step 5: Compile into a one-page trade review brief with a "
            "performance heatmap and talking points per store\n\n"
            "Minimum requirements:\n"
            "- At least 3 distinct steps (required)\n"
            "- Each step references output from the previous step (required)\n"
            "- Steps move from data to diagnosis to action (required)\n"
            "- Considers multiple possible causes for performance (strong signal)"
        ),
        "pass_threshold": 14.0,
        "coaching_on_fail": (
            "A weekly trade review is about more than just the numbers. The "
            "sales summary is the starting point, not the destination. A great "
            "Area Manager would ask: which stores are off target? Why? Is it a "
            "category issue, a staffing issue, or an external factor? And most "
            "importantly: what are we going to do about it this week? Try "
            "building a chain that goes from raw data to root cause to action "
            "plan. That is the workflow that drives real results."
        ),
        "context_tag": "foundation_l3",
    },
]

# ---------------------------------------------------------------------------
# LEVEL 4 FOUNDATION CHECKS
# Score an AI output on the 8-criteria Advanced Output Rubric
# User's scores must be within 1.5 points average of Claude's scores
# ---------------------------------------------------------------------------

_L4_CHECKS = [
    {
        "check_code": "FC-L4-1",
        "level": 4,
        "check_title": "Rubric Scoring: Category Review Email",
        "instructions": (
            "Below is an AI-generated output written for a Harris Farm audience. "
            "Score it on the **8-criteria Advanced Output Rubric**:\n\n"
            "1. **Audience Fit** (1-10): Tailored to the reader's role and needs?\n"
            "2. **Storytelling** (1-10): Clear narrative arc, logical flow?\n"
            "3. **Actionability** (1-10): Specific next steps with owners?\n"
            "4. **Visual Quality** (1-10): Professional formatting, data presentation?\n"
            "5. **Completeness** (1-10): All necessary information present?\n"
            "6. **Brevity** (1-10): Concise, every sentence earns its place?\n"
            "7. **Data Integrity** (1-10): Claims backed by verified data?\n"
            "8. **Honesty** (1-10): Transparent about limitations and risks?\n\n"
            "For each criterion, provide your score (1-10) and a one-sentence "
            "rationale. Then calculate the average and give a verdict: "
            "SHIP (8.0+), REVISE (5.0-7.9), or REJECT (<5.0)."
        ),
        "scenario_text": (
            "**AI Output to Score:**\n\n"
            "---\n\n"
            "**To:** Head of Buying\n"
            "**Subject:** Stone Fruit Category Review -- Q1 FY26 Recommendation\n\n"
            "Hi team,\n\n"
            "Quick update on stone fruit. Summer has been solid and we should "
            "keep going with current suppliers. Peaches and nectarines are doing "
            "well. Plums are a bit slower.\n\n"
            "Here is what I reckon we should do:\n"
            "- Keep ordering peaches from our main guy\n"
            "- Maybe try some new plum varieties\n"
            "- Look at what Coles is doing with their stone fruit display\n\n"
            "The numbers have been pretty good overall. Margins are healthy and "
            "customers seem happy. We should be able to hit our targets if we "
            "keep the momentum.\n\n"
            "Let me know if you want to chat about this.\n\n"
            "Cheers,\n"
            "AI Assistant\n\n"
            "---"
        ),
        "pass_criteria": (
            "This is a deliberately weak output. Claude's expected scores:\n"
            "- Audience Fit: 4 (informal tone for a Head of Buying category "
            "review; lacks strategic framing)\n"
            "- Storytelling: 3 (no narrative arc, no data-driven story, just "
            "scattered observations)\n"
            "- Actionability: 3 (vague actions -- 'keep ordering from our main "
            "guy' has no name, quantity, or timeline)\n"
            "- Visual Quality: 4 (basic bullet points but no tables, no data, "
            "no structure)\n"
            "- Completeness: 3 (missing: specific sales figures, margin data, "
            "supplier names, competitor pricing, demand forecast)\n"
            "- Brevity: 6 (it is short, but only because it lacks substance, "
            "not because it is efficiently dense)\n"
            "- Data Integrity: 2 (no actual numbers cited anywhere -- 'pretty "
            "good' and 'healthy margins' are meaningless without figures)\n"
            "- Honesty: 5 (does not mislead but omits risks like weather, "
            "supply chain, or seasonal tail-off)\n"
            "Expected average: ~3.8 (REJECT)\n"
            "User's scores must average within 1.5 points of Claude's scores."
        ),
        "pass_threshold": 1.5,
        "coaching_on_fail": (
            "Rubric scoring is about being objective and evidence-based. Look "
            "at each criterion independently. This output reads like a casual "
            "Slack message, not a category review for the Head of Buying. It "
            "has no specific data, no supplier names, no margin figures, and "
            "vague actions. The scores should reflect that. Focus especially on "
            "Data Integrity (are there any actual numbers?) and Actionability "
            "(could someone act on these recommendations without asking "
            "follow-up questions?)."
        ),
        "context_tag": "foundation_l4",
    },
    {
        "check_code": "FC-L4-2",
        "level": 4,
        "check_title": "Rubric Scoring: Shrinkage Reduction Proposal",
        "instructions": (
            "Below is an AI-generated output written for a Harris Farm audience. "
            "Score it on the **8-criteria Advanced Output Rubric**:\n\n"
            "1. **Audience Fit** (1-10): Tailored to the reader's role and needs?\n"
            "2. **Storytelling** (1-10): Clear narrative arc, logical flow?\n"
            "3. **Actionability** (1-10): Specific next steps with owners?\n"
            "4. **Visual Quality** (1-10): Professional formatting, data presentation?\n"
            "5. **Completeness** (1-10): All necessary information present?\n"
            "6. **Brevity** (1-10): Concise, every sentence earns its place?\n"
            "7. **Data Integrity** (1-10): Claims backed by verified data?\n"
            "8. **Honesty** (1-10): Transparent about limitations and risks?\n\n"
            "For each criterion, provide your score (1-10) and a one-sentence "
            "rationale. Then calculate the average and give a verdict: "
            "SHIP (8.0+), REVISE (5.0-7.9), or REJECT (<5.0)."
        ),
        "scenario_text": (
            "**AI Output to Score:**\n\n"
            "---\n\n"
            "**Shrinkage Reduction Plan -- Brookvale Store**\n"
            "**Prepared for:** Store Manager, Brookvale\n"
            "**Date:** January 2026\n\n"
            "**1. Current State**\n"
            "Brookvale's fresh produce shrinkage is currently 6.2% of category "
            "revenue (FY25 H1), compared to the network average of 4.4%. This "
            "equates to approximately $14,300 per month in lost value. The three "
            "worst subcategories are pre-packed salads (11.3%), berries (9.7%), "
            "and herbs (8.1%).\n\n"
            "**2. Root Cause Analysis**\n"
            "Based on the last 13 weeks of data:\n"
            "- Pre-packed salads: Ordering is not aligned with day-of-week demand "
            "patterns. Monday orders are 40% higher than Monday sales.\n"
            "- Berries: Supplier delivery quality has declined -- reject rate up "
            "from 3% to 7% since September.\n"
            "- Herbs: Display rotation is inconsistent. Back-of-house audits show "
            "an average of 2.1 days between FIFO rotations vs the 1-day target.\n\n"
            "**3. Recommended Actions**\n\n"
            "| Action | Owner | Deadline | Expected Impact |\n"
            "|--------|-------|----------|----------------|\n"
            "| Implement day-of-week ordering model for salads | Produce Mgr | Feb 7 | -3pp shrinkage |\n"
            "| Escalate berry quality to supplier (Green Valley Farms) | Buyer (Berries) | Jan 24 | -2pp reject rate |\n"
            "| Daily FIFO audit checklist for herbs section | 2IC | Jan 20 | -2pp shrinkage |\n"
            "| Review cold chain from dock to shelf -- temp logger install | Store Mgr | Feb 14 | Diagnostic |\n\n"
            "**4. Financial Impact**\n"
            "If all actions land, projected shrinkage reduction from 6.2% to "
            "~4.0%, saving approximately $9,800 per month ($117,600 annualised).\n\n"
            "**5. Risks & Caveats**\n"
            "- Supplier escalation may not resolve quickly; backup supplier "
            "(Sunny Ridge) should be identified.\n"
            "- Ordering model assumes historical demand patterns continue; school "
            "holidays and long weekends may create variance.\n"
            "- Shrinkage data is based on inventory counts, not direct waste "
            "measurement -- actual waste may differ.\n\n"
            "---"
        ),
        "pass_criteria": (
            "This is a strong, well-structured output. Claude's expected scores:\n"
            "- Audience Fit: 8 (well-targeted to a store manager -- practical, "
            "specific, action-oriented)\n"
            "- Storytelling: 8 (clear arc from problem to root cause to solution "
            "to financial impact)\n"
            "- Actionability: 9 (specific actions with named owners, deadlines, "
            "and expected impact)\n"
            "- Visual Quality: 8 (good use of sections, table for actions, clear "
            "hierarchy)\n"
            "- Completeness: 8 (covers current state, root cause, actions, "
            "financial impact, and risks)\n"
            "- Brevity: 8 (dense and efficient -- no padding, every paragraph "
            "earns its place)\n"
            "- Data Integrity: 7 (good internal data but some figures like "
            "'$14,300 per month' and projected savings should cite source "
            "calculations)\n"
            "- Honesty: 9 (excellent risk section, acknowledges data limitations "
            "and external variables)\n"
            "Expected average: ~8.1 (SHIP)\n"
            "User's scores must average within 1.5 points of Claude's scores."
        ),
        "pass_threshold": 1.5,
        "coaching_on_fail": (
            "This output is actually quite strong -- it has a clear structure, "
            "specific numbers, named owners, and deadlines. The key areas to "
            "look at carefully are: Actionability (does each action have an "
            "owner and deadline? Yes.), Data Integrity (are the numbers sourced? "
            "Mostly, but some could be better cited), and Honesty (is it upfront "
            "about risks? Very much so). If your scores were too low, you may "
            "be applying a harsher standard than the rubric intends. If too "
            "high, look at where the data sourcing could be tighter."
        ),
        "context_tag": "foundation_l4",
    },
    {
        "check_code": "FC-L4-3",
        "level": 4,
        "check_title": "Rubric Scoring: Customer Loyalty Analysis",
        "instructions": (
            "Below is an AI-generated output written for a Harris Farm audience. "
            "Score it on the **8-criteria Advanced Output Rubric**:\n\n"
            "1. **Audience Fit** (1-10): Tailored to the reader's role and needs?\n"
            "2. **Storytelling** (1-10): Clear narrative arc, logical flow?\n"
            "3. **Actionability** (1-10): Specific next steps with owners?\n"
            "4. **Visual Quality** (1-10): Professional formatting, data presentation?\n"
            "5. **Completeness** (1-10): All necessary information present?\n"
            "6. **Brevity** (1-10): Concise, every sentence earns its place?\n"
            "7. **Data Integrity** (1-10): Claims backed by verified data?\n"
            "8. **Honesty** (1-10): Transparent about limitations and risks?\n\n"
            "For each criterion, provide your score (1-10) and a one-sentence "
            "rationale. Then calculate the average and give a verdict: "
            "SHIP (8.0+), REVISE (5.0-7.9), or REJECT (<5.0)."
        ),
        "scenario_text": (
            "**AI Output to Score:**\n\n"
            "---\n\n"
            "**Customer Loyalty Deep Dive -- Eastern Suburbs Cluster**\n"
            "**Prepared for:** Head of Marketing\n"
            "**Period:** FY25 H1 (July-December 2024)\n\n"
            "**Executive Summary**\n"
            "The Eastern Suburbs cluster (Bondi Beach, Bondi Junction, Double Bay, "
            "Edgecliff) accounts for 28% of network revenue but is showing early "
            "signs of loyalty erosion. Repeat purchase frequency has declined 6% "
            "YoY while average basket size has held steady.\n\n"
            "**Key Findings**\n\n"
            "**1. Frequency Decline is Concentrated in Mid-Tier Shoppers**\n"
            "The top 20% of customers (by annual spend) have maintained frequency. "
            "The decline is driven by the middle 40% -- shoppers spending $80-200 "
            "per week -- who have reduced visits from 2.3 to 2.0 per week.\n\n"
            "**2. Online Channel is Not Compensating**\n"
            "Despite a 12% increase in online orders from the cluster, the average "
            "online basket ($62) is significantly lower than instore ($94). Net "
            "revenue effect of the channel shift is negative.\n\n"
            "**3. Competitor Activity**\n"
            "A new Woolworths Metro opened in Bondi Junction (September 2024) and "
            "a new IGA in Rose Bay (November 2024). Post-opening, the Bondi "
            "Junction store saw a 4.2% decline in weekday lunch-hour transactions.\n\n"
            "**Recommendations**\n"
            "1. Launch a mid-tier loyalty reactivation campaign targeting the "
            "$80-200/week cohort with personalised produce boxes (Owner: CRM "
            "Manager, Target: March 2026)\n"
            "2. Review online pricing and minimum order thresholds to close the "
            "basket gap (Owner: Head of Digital, Target: February 2026)\n"
            "3. Strengthen weekday lunch offer at Bondi Junction with grab-and-go "
            "expansion (Owner: Store Manager BJ, Target: February 2026)\n\n"
            "**Limitations**\n"
            "- Customer identification relies on payment card matching, which "
            "captures approximately 70% of transactions. Cash and unlinked "
            "card transactions are excluded.\n"
            "- Competitor impact is inferred from timing correlation, not direct "
            "customer surveys. Causation is not confirmed.\n"
            "- Online basket comparison does not account for delivery fees, which "
            "may suppress order frequency rather than basket size.\n\n"
            "---"
        ),
        "pass_criteria": (
            "This is a solid mid-to-high quality output. Claude's expected scores:\n"
            "- Audience Fit: 8 (well-targeted to Head of Marketing -- strategic "
            "lens, customer segments, competitive context)\n"
            "- Storytelling: 7 (good structure but the narrative could connect "
            "the three findings more explicitly into a single story)\n"
            "- Actionability: 7 (good actions with owners and dates, but missing "
            "specific budget or success metrics for each)\n"
            "- Visual Quality: 7 (clean sections and hierarchy, but no charts, "
            "tables, or visual data -- all text-based)\n"
            "- Completeness: 7 (covers key areas but missing: what did top 20% "
            "customers do differently? What is the retention risk forecast?)\n"
            "- Brevity: 8 (efficiently written, no padding, good density)\n"
            "- Data Integrity: 7 (specific numbers cited throughout, but source "
            "systems not named -- where did the 6% YoY decline come from?)\n"
            "- Honesty: 9 (excellent limitations section, acknowledges inference "
            "vs causation, data coverage gaps)\n"
            "Expected average: ~7.5 (REVISE)\n"
            "User's scores must average within 1.5 points of Claude's scores."
        ),
        "pass_threshold": 1.5,
        "coaching_on_fail": (
            "This output is a good example of the REVISE zone -- it is solid "
            "work but has clear room for improvement. The strengths are the "
            "limitations section (very honest) and the specificity of the data. "
            "The gaps are in visual presentation (no charts or tables), "
            "actionability (actions need success metrics and budgets), and "
            "storytelling (the three findings are presented in parallel but do "
            "not build on each other into a single narrative). If your scores "
            "were far from the expected range, focus on evaluating each "
            "criterion strictly against the rubric definitions."
        ),
        "context_tag": "foundation_l4",
    },
]

# ---------------------------------------------------------------------------
# COMBINED FOUNDATION CHECKS DICTIONARY
# Keyed by level number (1-4)
# ---------------------------------------------------------------------------

FOUNDATION_CHECKS = {
    1: _L1_CHECKS,
    2: _L2_CHECKS,
    3: _L3_CHECKS,
    4: _L4_CHECKS,
}  # type: Dict[int, List[Dict[str, Any]]]


# ---------------------------------------------------------------------------
# HELPER: Flatten for seeding into sa_exercises table
# ---------------------------------------------------------------------------

def get_foundation_checks_for_seeding():
    # type: () -> List[Dict[str, Any]]
    """Flatten all foundation checks into exercise dicts for seeding.

    Returns a list of dicts matching the sa_exercises insert format, with
    foundation checks marked as non-curveball standard-tier exercises
    under the appropriate module code.
    """
    exercises = []  # type: List[Dict[str, Any]]
    for level, checks in FOUNDATION_CHECKS.items():
        module_code = "L{}".format(level) if level <= 5 else "L5"
        for fc in checks:
            exercises.append({
                "module_code": module_code,
                "tier": "standard",
                "context_tag": fc["context_tag"],
                "is_curveball": False,
                "curveball_type": None,
                "exercise_title": "[Foundation Check] " + fc["check_title"],
                "scenario_text": (
                    fc["instructions"] + "\n\n" + fc["scenario_text"]
                ),
                "expected_approach": fc["pass_criteria"],
                "rubric_code": (
                    "foundational" if level <= 2 else "advanced_output"
                ),
                "pass_score": fc["pass_threshold"],
                "xp_reward": 10,
            })
    return exercises


def get_checks_for_level(level):
    # type: (int) -> List[Dict[str, Any]]
    """Return the 3 foundation checks for a given level.

    Args:
        level: The level whose foundations are being checked (1-4).

    Returns:
        List of 3 foundation check dicts, or empty list if level invalid.
    """
    return FOUNDATION_CHECKS.get(level, [])


def get_check_by_code(check_code):
    # type: (str) -> Optional[Dict[str, Any]]
    """Look up a single foundation check by its check_code (e.g. 'FC-L2-1').

    Args:
        check_code: The unique check code string.

    Returns:
        The foundation check dict, or None if not found.
    """
    for checks in FOUNDATION_CHECKS.values():
        for fc in checks:
            if fc["check_code"] == check_code:
                return fc
    return None


def get_required_checks_for_placement(placed_level):
    # type: (int) -> Dict[int, List[Dict[str, Any]]]
    """Given a user's placement level, return all foundation checks they
    must pass before that level is confirmed.

    A user placed at level N must pass foundation checks for all levels
    below N (i.e. levels 1 through N-1).

    Args:
        placed_level: The level the user was provisionally placed at (2-5).

    Returns:
        Dict mapping level number to list of foundation check dicts.
        Empty dict if placed_level <= 1 (no foundations to check).
    """
    if placed_level <= 1:
        return {}

    required = {}  # type: Dict[int, List[Dict[str, Any]]]
    for level in range(1, min(placed_level, 5)):
        checks = FOUNDATION_CHECKS.get(level)
        if checks:
            required[level] = checks
    return required


def total_check_count_for_placement(placed_level):
    # type: (int) -> int
    """Return the total number of foundation checks a user must pass
    for a given placement level.

    Args:
        placed_level: The level the user was provisionally placed at.

    Returns:
        Integer count of required foundation checks.
    """
    required = get_required_checks_for_placement(placed_level)
    return sum(len(checks) for checks in required.values())
