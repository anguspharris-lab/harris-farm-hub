"""Harris Farm Hub -- Training Content for The Rubric
Challenge scenarios, building block definitions, prompt examples,
rubric criteria, and prompt quality heuristic.
"""

# ---------------------------------------------------------------------------
# 5 BUILDING BLOCKS OF A GOOD PROMPT
# ---------------------------------------------------------------------------

BUILDING_BLOCKS = [
    {
        "name": "Role",
        "icon": "1",
        "short": "Tell the AI who to be",
        "explanation": (
            "Start your prompt by telling the AI what role to play. "
            "This helps it give answers from the right perspective."
        ),
        "example": "You are a Harris Farm fresh produce department manager with 10 years of experience...",
        "tip": "Start with: 'You are a...' or 'Act as a...'",
        "keywords": ["you are", "act as", "as a", "your role", "imagine you", "pretend you"],
    },
    {
        "name": "Context",
        "icon": "2",
        "short": "Give background information",
        "explanation": (
            "Share relevant details about Harris Farm so the AI understands "
            "our business. Mention stores, products, or situations."
        ),
        "example": "Harris Farm Markets operates 30+ stores across NSW, specialising in premium fresh produce...",
        "tip": "Mention Harris Farm, specific stores, products, or departments",
        "keywords": ["harris farm", "store", "nsw", "produce", "retail", "department", "customer"],
    },
    {
        "name": "Task",
        "icon": "3",
        "short": "Be clear about what you want",
        "explanation": (
            "Tell the AI exactly what you need it to do. Use action words "
            "like analyse, compare, list, explain, or recommend."
        ),
        "example": "Analyse the top 5 causes of fresh fruit wastage and suggest how to reduce each one...",
        "tip": "Use action words: Analyse, Compare, List, Explain, Recommend",
        "keywords": ["analyse", "analyze", "compare", "list", "explain", "show",
                     "find", "identify", "recommend", "suggest", "describe", "summarise",
                     "summarize", "calculate", "review", "evaluate"],
    },
    {
        "name": "Format",
        "icon": "4",
        "short": "Say how you want the answer",
        "explanation": (
            "Tell the AI how to structure its response. Do you want a list, "
            "a table, step-by-step instructions, or a summary?"
        ),
        "example": "Present your answer as a numbered list with the cause, impact in dollars, and a specific action...",
        "tip": "Ask for: a numbered list, a table, bullet points, step-by-step",
        "keywords": ["list", "table", "bullet", "step by step", "numbered",
                     "format", "structure", "summary", "paragraph", "heading"],
    },
    {
        "name": "Constraints",
        "icon": "5",
        "short": "Set limits and boundaries",
        "explanation": (
            "Narrow down what you want by setting limits: time period, "
            "number of results, what to include or leave out."
        ),
        "example": "Focus on the last 30 days only. Limit to the top 5 items. Exclude seasonal products...",
        "tip": "Add: time period, number of results, what to include/exclude",
        "keywords": ["last", "past", "recent", "top", "bottom", "only", "exclude",
                     "maximum", "minimum", "limit", "days", "weeks", "months",
                     "most", "least", "between", "within", "no more than"],
    },
]


# ---------------------------------------------------------------------------
# GOOD vs BAD PROMPT EXAMPLES (Harris Farm context)
# ---------------------------------------------------------------------------

PROMPT_EXAMPLES = [
    {
        "department": "Fresh Produce",
        "bad": "Tell me about fruit wastage",
        "good": (
            "You are a Harris Farm fresh produce specialist. "
            "Analyse the top 3 causes of stone fruit wastage at our Bondi store "
            "over the last 4 weeks. Present as a numbered list with estimated "
            "cost impact and one specific action for each."
        ),
        "why": "The good prompt has a role, specific store, time period, format, and asks for actions.",
    },
    {
        "department": "Online Orders",
        "bad": "How do we reduce miss-picks?",
        "good": (
            "Act as an e-commerce operations analyst for Harris Farm. "
            "Compare miss-pick rates between our top 3 and bottom 3 stores "
            "for the past month. Identify the most commonly confused product pairs "
            "and recommend 3 practical training actions. Use a table format."
        ),
        "why": "The good prompt defines the analyst role, compares specific stores, and requests actionable output in a table.",
    },
    {
        "department": "Buying",
        "bad": "What should we order more of?",
        "good": (
            "You are a buying manager for Harris Farm Markets. "
            "Review the last 13 weeks of sales data and identify 5 products "
            "where actual sales consistently exceeded orders by more than 15%. "
            "For each product, show the average weekly shortfall and estimated "
            "lost revenue. Exclude seasonal items."
        ),
        "why": "The good prompt specifies the time window (13 weeks), a clear threshold (15%), and excludes seasonal noise.",
    },
    {
        "department": "Store Operations",
        "bad": "How should I manage my department?",
        "good": (
            "As a Harris Farm store manager responsible for the dairy section, "
            "list the 5 most important daily checks I should do before 9am "
            "to ensure freshness and minimise waste. Keep each point to "
            "one sentence with a specific action."
        ),
        "why": "The good prompt narrows to a department, time of day, and asks for concise, actionable steps.",
    },
    {
        "department": "Finance",
        "bad": "Show me the numbers for shrinkage",
        "good": (
            "You are a Harris Farm finance analyst. Compare shrinkage as a "
            "percentage of sales across all departments for the last quarter. "
            "Highlight the 3 departments with the highest shrinkage rate and "
            "suggest one cost-reduction initiative for each. "
            "Present as a summary table followed by recommendations."
        ),
        "why": "The good prompt specifies the metric (% of sales), time period (last quarter), and a clear output format.",
    },
]


# ---------------------------------------------------------------------------
# PRACTICE CHALLENGES (3 per difficulty)
# ---------------------------------------------------------------------------

CHALLENGES = {
    "Beginner": [
        {
            "id": "b1",
            "title": "Golden Rules Lookup",
            "scenario": (
                "A new team member in the Fruit & Veg department asks you: "
                "'What are the golden rules I need to follow?' "
                "Write a prompt to get a clear, helpful answer from AI."
            ),
            "hints": [
                "Think about who the AI should pretend to be",
                "Mention which department you're asking about",
                "Ask for the answer in a specific format (like a numbered list)",
            ],
            "criteria": ["Mentions Fruit & Veg department", "Asks for a list or structured answer",
                         "Specifies it's for a new team member"],
        },
        {
            "id": "b2",
            "title": "Online Order Picking",
            "scenario": (
                "You've been asked to train someone on how to pick online orders. "
                "Write a prompt to get step-by-step picking instructions from AI."
            ),
            "hints": [
                "Tell the AI to act as a trainer",
                "Ask for step-by-step instructions",
                "Mention it's for Harris Farm online orders",
            ],
            "criteria": ["Mentions online order picking", "Asks for steps or instructions",
                         "References Harris Farm"],
        },
        {
            "id": "b3",
            "title": "Customer Complaint",
            "scenario": (
                "A customer has complained that the avocados they bought "
                "were not ripe enough. Write a prompt to get advice on how "
                "to handle this complaint and prevent it happening again."
            ),
            "hints": [
                "Give the AI some context about the situation",
                "Ask for both an immediate response and a longer-term fix",
                "Think about what a customer service expert would say",
            ],
            "criteria": ["Mentions the specific complaint (avocados/ripeness)",
                         "Asks for both immediate and preventive actions",
                         "References customer service"],
        },
        {
            "id": "b4",
            "title": "Customer Loyalty Spotlight",
            "scenario": (
                "Your store manager wants to know who the most loyal customers "
                "are at your store and what they typically buy. "
                "Write a prompt to get a useful summary from AI."
            ),
            "hints": [
                "Mention that you have customer loyalty data",
                "Name a specific store",
                "Ask for specific metrics like visit frequency or average spend",
            ],
            "criteria": ["Mentions customer loyalty or membership data",
                         "Names a specific store",
                         "Asks for measurable customer metrics"],
        },
    ],
    "Intermediate": [
        {
            "id": "i1",
            "title": "Weekend Wastage Analysis",
            "scenario": (
                "Your area manager wants to know why weekend fresh produce "
                "wastage is higher than weekdays. Write a prompt to "
                "investigate the root causes."
            ),
            "hints": [
                "Compare weekdays vs weekends specifically",
                "Ask for data-driven causes, not just guesses",
                "Include a time period (e.g. last 30 days)",
                "Request actionable recommendations",
            ],
            "criteria": ["Compares weekend vs weekday", "Sets a time period",
                         "Asks for root causes with data", "Requests recommendations"],
        },
        {
            "id": "i2",
            "title": "Over-Ordering Detection",
            "scenario": (
                "The finance team has flagged that some products are being "
                "over-ordered, tying up cash. Write a prompt to identify "
                "which products and stores are the worst offenders."
            ),
            "hints": [
                "Define what 'over-ordering' means (e.g. orders exceeding sales by X%)",
                "Specify a time window",
                "Ask for the financial impact (cost of excess inventory)",
                "Request a ranked list",
            ],
            "criteria": ["Defines over-ordering threshold", "Specifies time period",
                         "Asks for financial impact", "Requests ranked output"],
        },
        {
            "id": "i3",
            "title": "Store Performance Comparison",
            "scenario": (
                "You need to understand why Bondi consistently outperforms "
                "Manly on fresh berries. Write a prompt to analyse the "
                "difference and find actionable insights."
            ),
            "hints": [
                "Name the specific stores and product category",
                "Ask the AI to compare specific metrics (sales, wastage, ordering)",
                "Request factors that explain the difference",
                "Ask for actions the underperforming store can take",
            ],
            "criteria": ["Names both stores and product", "Requests specific metrics comparison",
                         "Asks for explanatory factors", "Requests improvement actions"],
        },
        {
            "id": "i4",
            "title": "Margin Erosion Investigation",
            "scenario": (
                "The buying team has noticed that gross profit margins on "
                "some fresh produce lines have been declining. Write a prompt "
                "to identify which products and stores have the worst margin "
                "erosion compared to their department average."
            ),
            "hints": [
                "Define what margin erosion means (GP% below department average)",
                "Specify a time period to compare",
                "Ask for both product and store level findings",
                "Request actionable recommendations for buyers",
            ],
            "criteria": ["Defines margin erosion or GP% threshold",
                         "Specifies time period",
                         "Requests product and store breakdown",
                         "Asks for buyer-actionable recommendations"],
        },
        {
            "id": "i5",
            "title": "Store League Table",
            "scenario": (
                "The operations director wants a weekly store performance "
                "league table that ranks all stores across key metrics. "
                "Write a prompt to generate a comprehensive store comparison."
            ),
            "hints": [
                "List specific KPIs to compare (revenue, basket value, etc.)",
                "Ask for ranking or percentile format",
                "Request outlier highlighting",
                "Mention who the audience is (area managers, exec team)",
            ],
            "criteria": ["Names specific KPIs to compare",
                         "Requests ranking or percentile output",
                         "Asks for outlier identification",
                         "Specifies the target audience"],
        },
    ],
    "Advanced": [
        {
            "id": "a1",
            "title": "Supplier Reliability Rubric",
            "scenario": (
                "Create a prompt that asks AI to build a scoring rubric "
                "for evaluating supplier delivery reliability. The rubric "
                "should be usable by the buying team."
            ),
            "hints": [
                "Define what 'reliability' means (on-time, quality, quantity accuracy)",
                "Ask for scoring criteria with clear scales (e.g. 1-5)",
                "Request that it's practical for the buying team to use weekly",
                "Include constraints on how many criteria to use",
            ],
            "criteria": ["Defines reliability dimensions", "Requests a scoring scale",
                         "Specifies the audience (buying team)", "Sets practical constraints"],
        },
        {
            "id": "a2",
            "title": "Weekly Buying Recommendation",
            "scenario": (
                "Design a prompt that generates a weekly buying recommendation "
                "combining sales trends, wastage data, and weather forecasts "
                "for the fresh produce department."
            ),
            "hints": [
                "Combine multiple data sources in your request",
                "Ask for a format the buying team can act on immediately",
                "Include specific product categories",
                "Set the time horizon (next week's buying)",
            ],
            "criteria": ["Combines 3+ data sources", "Specifies actionable output format",
                         "Names product categories", "Sets time horizon"],
        },
        {
            "id": "a3",
            "title": "Staffing Optimisation",
            "scenario": (
                "Write a prompt that uses customer traffic patterns and "
                "sales data to recommend optimal staffing levels for each "
                "day of the week at a specific store."
            ),
            "hints": [
                "Name a specific store",
                "Ask for day-by-day breakdown",
                "Include the trade-off between cost and service",
                "Request a comparison with current staffing",
            ],
            "criteria": ["Names a specific store", "Requests day-by-day output",
                         "Considers cost vs service trade-off", "Compares to current state"],
        },
        {
            "id": "a4",
            "title": "At-Risk Customer Recovery Plan",
            "scenario": (
                "Marketing wants to launch a targeted retention campaign for "
                "customers who used to shop frequently but have not visited "
                "recently. Write a prompt that identifies at-risk customers "
                "and recommends specific re-engagement strategies."
            ),
            "hints": [
                "Define what 'at-risk' means (e.g. no visit in 90+ days, "
                "previously visited 6+ times)",
                "Ask for the financial value of the at-risk segment",
                "Request personalised recommendations based on purchase history",
                "Specify the output format for the marketing team to action",
            ],
            "criteria": ["Defines at-risk customer criteria quantitatively",
                         "Requests financial impact of the segment",
                         "Asks for personalised re-engagement strategies",
                         "Specifies actionable output format for marketing"],
        },
    ],
}


# ---------------------------------------------------------------------------
# RUBRIC SCORING CRITERIA (for Tab 4: Scorecard)
# ---------------------------------------------------------------------------

RUBRIC_CRITERIA = [
    {
        "name": "Accuracy",
        "description": "Is the information correct and relevant to Harris Farm?",
        "guide": {
            1: "Mostly wrong or completely generic",
            2: "Some correct points but major errors",
            3: "Generally correct with minor gaps",
            4: "Accurate with good Harris Farm relevance",
            5: "Spot-on, factually correct, highly relevant",
        },
    },
    {
        "name": "Practicality",
        "description": "Could a store manager actually act on this advice?",
        "guide": {
            1: "Completely theoretical, no actionable steps",
            2: "Some ideas but hard to implement",
            3: "A few actionable points mixed with theory",
            4: "Mostly practical with clear next steps",
            5: "Every point is something you could do tomorrow",
        },
    },
    {
        "name": "Completeness",
        "description": "Does it cover all parts of the question?",
        "guide": {
            1: "Misses most of what was asked",
            2: "Covers some parts, ignores others",
            3: "Addresses the main question but misses details",
            4: "Covers all parts with minor gaps",
            5: "Thorough, complete, nothing missed",
        },
    },
    {
        "name": "Clarity",
        "description": "Is it easy to read and understand? No jargon?",
        "guide": {
            1: "Confusing, hard to follow",
            2: "Some clear parts but mostly unclear",
            3: "Understandable but could be simpler",
            4: "Clear and well-organised",
            5: "Crystal clear, anyone on the team could follow it",
        },
    },
    {
        "name": "Specificity",
        "description": "Does it mention specific stores, products, or numbers?",
        "guide": {
            1: "Completely generic, no specifics at all",
            2: "Very few specific details",
            3: "Some specific references",
            4: "Good use of specific examples and data",
            5: "Rich in specifics: names, numbers, stores, products",
        },
    },
]


# ---------------------------------------------------------------------------
# BADGES (for Tab 5: My Progress)
# ---------------------------------------------------------------------------

BADGES = [
    {"id": "first_prompt", "name": "First Prompt",
     "description": "Completed your first practice challenge", "icon": "🌱"},
    {"id": "sharp_eye", "name": "Sharp Eye",
     "description": "Scored an AI response using the rubric", "icon": "👁️"},
    {"id": "prompt_pro", "name": "Prompt Pro",
     "description": "Scored 4+ on all 5 building blocks in a challenge", "icon": "🏅"},
    {"id": "rubric_master", "name": "Rubric Master",
     "description": "Evaluated 3 or more AI responses", "icon": "⚖️"},
    {"id": "multi_model", "name": "Multi-Model",
     "description": "Compared 3 different AI providers in one session", "icon": "🤖"},
    {"id": "advanced_learner", "name": "Advanced Learner",
     "description": "Completed an Advanced difficulty challenge", "icon": "🎓"},
]


# ---------------------------------------------------------------------------
# COACH SYSTEM PROMPT (used by Practice tab via /api/chat)
# ---------------------------------------------------------------------------

COACH_SYSTEM_PROMPT = """You are a friendly prompt writing coach for Harris Farm Markets staff. \
Your job is to help retail workers learn to write better AI prompts.

A staff member has written a prompt for the following challenge:

CHALLENGE: {scenario}

THEIR PROMPT:
{user_prompt}

Evaluate their prompt against these 5 criteria, scoring each 1-5:
1. ROLE: Did they define who the AI should act as? (e.g. "You are a...")
2. CONTEXT: Did they provide Harris Farm-specific context? (stores, products, etc.)
3. TASK: Is the request clear and specific? (action verbs, clear question)
4. FORMAT: Did they specify how they want the answer structured? (list, table, etc.)
5. CONSTRAINTS: Did they set appropriate limits? (time period, number of results, etc.)

Respond in EXACTLY this format:

SCORES:
- Role: X/5
- Context: X/5
- Task: X/5
- Format: X/5
- Constraints: X/5

FEEDBACK:
(2-3 sentences of specific, encouraging feedback. Be kind but honest. \
Mention what they did well first, then what to improve.)

IMPROVED VERSION:
(Rewrite their prompt incorporating all 5 building blocks. \
Make it a prompt they could actually use at Harris Farm.)

Keep your language simple and encouraging. These are retail workers, not developers."""


# ---------------------------------------------------------------------------
# PROMPT QUALITY HEURISTIC (client-side, no API call)
# ---------------------------------------------------------------------------

def check_prompt_quality(prompt: str) -> dict:
    """Check a prompt against the 5 building blocks using keyword matching.

    Returns dict with:
        checks: dict of {block_name: {"present": bool, "tip": str}}
        score: int (0-5)
        max_score: 5
        level: str ("Needs work" | "Getting there" | "Good" | "Excellent")
    """
    prompt_lower = prompt.lower()

    checks = {}
    for block in BUILDING_BLOCKS:
        present = any(kw in prompt_lower for kw in block["keywords"])
        # Task block also matches if a question mark is present
        if block["name"] == "Task" and "?" in prompt:
            present = True
        checks[block["name"]] = {
            "present": present,
            "tip": block["tip"],
        }

    score = sum(1 for c in checks.values() if c["present"])

    if score >= 4:
        level = "Excellent"
    elif score >= 3:
        level = "Good"
    elif score >= 2:
        level = "Getting there"
    else:
        level = "Needs work"

    return {
        "checks": checks,
        "score": score,
        "max_score": 5,
        "level": level,
    }
