"""
Harris Farm Hub -- Skills Academy Content
==========================================
Defines 10 training modules (L1-L5, D1-D5) for the Skills Academy,
Harris Farm Markets' AI skills training platform.

Two series:
  L-Series (Core AI Skills): Prompt craft, role application, advanced techniques
  D-Series (Applied Data + AI): Data querying, analysis, reporting

Each module contains theory, worked examples, exercises, and a scored assessment.

Python 3.9 compatible.
"""

from typing import Optional

# ---------------------------------------------------------------------------
# 5-CRITERIA ASSESSMENT RUBRIC
# ---------------------------------------------------------------------------

ASSESSMENT_RUBRIC = {
    "criteria": [
        {
            "key": "clarity",
            "name": "Request Clarity",
            "max": 5,
            "description": "Is the request unambiguous and specific?",
        },
        {
            "key": "context",
            "name": "Context Provision",
            "max": 5,
            "description": "Does it include relevant HFM business context?",
        },
        {
            "key": "data_spec",
            "name": "Data Specification",
            "max": 5,
            "description": "Does it specify what data to use or reference?",
        },
        {
            "key": "format",
            "name": "Output Format",
            "max": 5,
            "description": "Does it define the desired output structure?",
        },
        {
            "key": "actionability",
            "name": "Actionability",
            "max": 5,
            "description": "Will the output lead to a concrete business action?",
        },
    ],
    "pass_threshold": 18,
    "max_score": 25,
}


# ---------------------------------------------------------------------------
# SCORING SYSTEM PROMPT  (sent to Claude when evaluating assessments)
# ---------------------------------------------------------------------------

SCORING_SYSTEM_PROMPT = """You are an AI skills evaluator for Harris Farm Markets, \
an Australian fresh-food retailer with 21 stores across Sydney and a growing \
online channel. Your job is to score prompts written by Harris Farm staff as \
part of the Skills Academy training programme.

## Evaluation Criteria (each scored 1-5)

1. **Request Clarity** (clarity)
   - 5: Crystal clear, single unambiguous request with specific scope
   - 4: Clear request with minor ambiguity in one dimension
   - 3: Understandable intent but vague on scope or deliverable
   - 2: Multiple possible interpretations; reader must guess
   - 1: Unclear what is being asked

2. **Context Provision** (context)
   - 5: Rich business context — names a store/department/role, explains the \
situation, states why this matters now
   - 4: Good context with one gap (e.g. missing "why now")
   - 3: Some context but missing store, department, or business reason
   - 2: Minimal context — could apply to any company
   - 1: No business context at all

3. **Data Specification** (data_spec)
   - 5: Names exact data source, time range, filters, and comparison basis
   - 4: Specifies most data dimensions with one minor gap
   - 3: Mentions data broadly but missing time range or comparison
   - 2: Implies data is needed but does not specify what
   - 1: No reference to data or evidence

4. **Output Format** (format)
   - 5: Precise format instruction (e.g. "table with columns X, Y, Z" or \
"3 bullet points with a one-line recommendation")
   - 4: Good format direction with minor ambiguity
   - 3: General format hint (e.g. "a summary") without structure
   - 2: Vague ("make it useful")
   - 1: No format guidance

5. **Actionability** (actionability)
   - 5: Output will directly drive a named decision or next step \
(e.g. "to decide whether to reorder", "for the Monday store meeting")
   - 4: Clear business use with minor gap in decision linkage
   - 3: Useful output but unclear how it will be used
   - 2: Informational only — no clear action follows
   - 1: Academic or hypothetical, no business application

## Scoring Rules
- Be strict but fair. Most untrained prompts score 8-14.
- A well-trained employee should reach 18-22 after completing Skills Academy.
- Reserve 24-25 for genuinely exceptional prompts.
- Australian English context: use "analyse" not "analyze", etc.
- Harris Farm specific references (store names, departments, product \
categories) earn higher context scores.

## Response Format
Return ONLY valid JSON with no markdown fencing:
{
    "clarity": <int 1-5>,
    "context": <int 1-5>,
    "data_spec": <int 1-5>,
    "format": <int 1-5>,
    "actionability": <int 1-5>,
    "total": <int 5-25>,
    "feedback": "<2-4 sentences explaining the score and what to improve>",
    "improved_prompt": "<a rewritten version of the prompt that would score 23+>"
}
"""


# ---------------------------------------------------------------------------
# MODULE DEFINITIONS
# ---------------------------------------------------------------------------

SKILLS_MODULES = [

    # ===================================================================
    # L-SERIES: CORE AI SKILLS
    # ===================================================================

    # ---------------------------------------------------------------
    # L1 — The 4 Elements of Effective Prompts (FULLY FLESHED)
    # ---------------------------------------------------------------
    {
        "code": "L1",
        "series": "L",
        "name": "The 4 Elements of Effective Prompts",
        "description": (
            "Master the four building blocks every great AI prompt needs: "
            "Task, Context, Format, and Constraints. This is the foundation "
            "for everything else in the Skills Academy."
        ),
        "prerequisites": [],
        "difficulty": "beginner",
        "duration_minutes": 30,
        "sort_order": 1,
        "theory": [
            {
                "title": "Element 1 -- Task",
                "body": (
                    "The **Task** is what you want the AI to do. It should be a "
                    "clear, specific verb phrase: *analyse*, *summarise*, *compare*, "
                    "*draft*, *list*, *recommend*. The more precise the verb, the "
                    "better the result.\n\n"
                    "A common mistake is being vague: \"Tell me about sales\" is not "
                    "a task -- it is a topic. \"Analyse Crows Nest store's weekly "
                    "revenue trend for the last 8 weeks\" is a task. Notice the "
                    "difference: one gives the AI permission to ramble; the other "
                    "focuses it on a deliverable.\n\n"
                    "**Harris Farm example:**\n"
                    "> *Compare the Fruit & Veg gross margin at Bondi Beach vs "
                    "Drummoyne for the four weeks ending 16 Feb 2026.*\n\n"
                    "The task verb is *compare*, the subject is *F&V gross margin*, "
                    "and the scope is two named stores over a defined period. That "
                    "single sentence removes 90% of ambiguity."
                ),
            },
            {
                "title": "Element 2 -- Context",
                "body": (
                    "**Context** is the background information the AI needs to give "
                    "you a useful answer. Think: *Who am I? What situation am I in? "
                    "Why does this matter right now?*\n\n"
                    "AI models do not know that you are a Deli Buyer preparing for "
                    "a range review, or that Harris Farm runs a Monday morning store "
                    "meeting where managers review the prior week's numbers. If you "
                    "do not provide that context, the AI will guess -- and it will "
                    "guess generically.\n\n"
                    "Good context includes your **role** (Store Manager, Fresh Buyer, "
                    "Operations Lead), the **business situation** (weekly review, "
                    "supplier negotiation, new product launch), and the **audience** "
                    "who will consume the output (your team, senior leadership, "
                    "a supplier).\n\n"
                    "**Harris Farm example:**\n"
                    "> *I am the Store Manager at Leichhardt. We have just finished "
                    "a strong Christmas trading period but foot traffic has dropped "
                    "15% in January. I need to present a recovery plan at the "
                    "Tuesday leadership call.*"
                ),
            },
            {
                "title": "Element 3 -- Format",
                "body": (
                    "**Format** tells the AI how to structure its response. Without "
                    "format guidance, you get a wall of text. With it, you get "
                    "output you can paste directly into a meeting deck, an email, "
                    "or a spreadsheet.\n\n"
                    "Useful format instructions include:\n"
                    "- \"Return a table with columns: Store, Revenue, WoW Change %\"\n"
                    "- \"Give me 5 numbered bullet points, each one sentence\"\n"
                    "- \"Write a 3-paragraph email suitable for a supplier\"\n"
                    "- \"Produce a SWOT grid in markdown\"\n\n"
                    "**Harris Farm example:**\n"
                    "> *Format the output as a table I can paste into Google Sheets "
                    "with columns: Product Name, Units Sold This Week, Units Sold "
                    "Last Week, % Change. Sort by largest decline first. Add a "
                    "one-line summary sentence below the table.*"
                ),
            },
            {
                "title": "Element 4 -- Constraints",
                "body": (
                    "**Constraints** are the boundaries and exclusions. They tell "
                    "the AI what *not* to do, or set limits on scope, length, tone, "
                    "or data sources.\n\n"
                    "Constraints prevent runaway responses. Without them, a request "
                    "for \"a report on store performance\" might produce 2,000 words "
                    "covering every metric. With a constraint like \"focus only on "
                    "Fruit & Veg and limit to 300 words\", you get exactly what you "
                    "need.\n\n"
                    "Common constraints at Harris Farm:\n"
                    "- **Scope:** \"Only NSW stores\", \"Exclude online orders\"\n"
                    "- **Length:** \"Maximum 200 words\", \"No more than 10 rows\"\n"
                    "- **Tone:** \"Write for a non-technical audience\", \"Keep it "
                    "conversational\"\n"
                    "- **Exclusions:** \"Do not include Richmond -- it was closed "
                    "for refurbishment\", \"Ignore weeks with public holidays\"\n\n"
                    "**Harris Farm example:**\n"
                    "> *Exclude the Bondi Junction store (it moved to a new site "
                    "mid-period so the data is not comparable). Keep the analysis "
                    "under 400 words. Use plain English -- this will be shared with "
                    "the in-store team, not analysts.*"
                ),
            },
            {
                "title": "Putting It All Together",
                "body": (
                    "A great prompt combines all four elements into a single, "
                    "coherent request. Here is the formula:\n\n"
                    "**Task** + **Context** + **Format** + **Constraints** = "
                    "Effective Prompt\n\n"
                    "You do not need to label each element explicitly -- just make "
                    "sure all four are present. With practice, writing 4-element "
                    "prompts becomes second nature.\n\n"
                    "**Complete Harris Farm example:**\n"
                    "> *Analyse Crows Nest store's F&V sales for the last 4 weeks "
                    "compared to the same period last year. I am the Fresh Buyer "
                    "preparing for the weekly buying meeting. Show week-by-week "
                    "revenue, the top 5 growing items and top 5 declining items, "
                    "formatted as a table I can paste into a Monday morning store "
                    "meeting slide. Exclude organic lines -- they are reported "
                    "separately.*\n\n"
                    "Notice how every element is covered: the task (analyse F&V "
                    "sales with YoY comparison), the context (Fresh Buyer, weekly "
                    "buying meeting), the format (table for a slide, top/bottom 5), "
                    "and the constraints (exclude organic lines)."
                ),
            },
        ],
        "examples": [
            {
                "weak": "Tell me about our sales.",
                "strong": (
                    "Analyse Crows Nest store's F&V sales for the last 4 weeks "
                    "compared to the same period last year. Show week-by-week "
                    "revenue, top 5 growing items and top 5 declining items, "
                    "formatted as a table I can paste into a Monday morning "
                    "store meeting."
                ),
                "explanation": (
                    "The weak prompt has no task verb, no store, no time period, "
                    "no format, and no purpose. The strong prompt specifies "
                    "exactly what to analyse (F&V at Crows Nest), the comparison "
                    "basis (YoY), the deliverable (top/bottom 5 table), and "
                    "the use case (Monday meeting)."
                ),
            },
            {
                "weak": "Write an email about deli specials.",
                "strong": (
                    "Draft a 150-word customer email promoting this week's Deli "
                    "specials at Harris Farm: truffle brie ($12.99), prosciutto "
                    "di Parma ($8.99/100g), and marinated artichokes ($6.49). "
                    "Tone should be warm and enthusiastic, matching Harris Farm's "
                    "'For The Greater Goodness' brand voice. Include a clear "
                    "call-to-action directing customers to their nearest store. "
                    "Do not mention competitor pricing."
                ),
                "explanation": (
                    "The weak prompt gives no products, no price points, no word "
                    "count, no tone guidance, and no call-to-action instruction. "
                    "The strong version provides all four elements: the task "
                    "(draft email), context (specific products and prices), "
                    "format (150 words, warm tone, CTA), and constraints (no "
                    "competitor pricing)."
                ),
            },
            {
                "weak": "How are our stores doing?",
                "strong": (
                    "Compare weekly revenue across all North Shore stores (Crows "
                    "Nest, Neutral Bay, North Sydney, Willoughby) for the last "
                    "6 weeks. I am the Regional Manager preparing for a quarterly "
                    "business review. Format as a table with columns: Store, "
                    "Week, Revenue, WoW % Change. Highlight any store that "
                    "declined more than 5% in consecutive weeks. Limit commentary "
                    "to 3 bullet points of key takeaways."
                ),
                "explanation": (
                    "\"How are our stores doing?\" could mean anything -- sales, "
                    "staffing, customer satisfaction, cleanliness. The strong "
                    "version narrows to revenue, names 4 specific stores, sets "
                    "a time window, explains who will use it, defines the table "
                    "structure, and adds a threshold-based highlight rule."
                ),
            },
            {
                "weak": "Help me with rostering.",
                "strong": (
                    "I am the Store Manager at Miranda. Create a suggested "
                    "weekly roster for my Bakery team (6 staff) for next week, "
                    "covering 6am-8pm daily. Our busiest days are Saturday and "
                    "Sunday. Each staff member works a maximum of 38 hours per "
                    "week. Format as a grid with days across the top and staff "
                    "names down the side, showing shift start/end times. "
                    "Do not schedule anyone for more than 5 consecutive days."
                ),
                "explanation": (
                    "The weak prompt gives no store, no department, no team size, "
                    "no constraints. The strong version provides the full picture: "
                    "which store, which department, how many people, operating "
                    "hours, peak days, hour limits, output format, and a rest-day "
                    "constraint."
                ),
            },
            {
                "weak": "What should we order?",
                "strong": (
                    "Based on Drummoyne store's Fruit & Veg sales for the last "
                    "3 weeks, suggest the top 10 items where we should increase "
                    "our order quantity and the top 5 where we should reduce. "
                    "I am the Fresh Buyer and I place orders every Tuesday. "
                    "Show each item with: current weekly average units sold, "
                    "current order quantity, suggested new order quantity, and "
                    "reason for change. Exclude seasonal lines that are ending "
                    "this month (stone fruit, cherries)."
                ),
                "explanation": (
                    "\"What should we order?\" has no store, no department, no "
                    "data basis, no format. The strong version specifies the "
                    "store, the category, the lookback period, the number of "
                    "recommendations, the table columns, and seasonal exclusions."
                ),
            },
        ],
        "exercise": {
            "instructions": (
                "Rewrite each of the following weak prompts using all 4 elements "
                "(Task, Context, Format, Constraints). Imagine you are a Harris "
                "Farm team member in the role described. Each rewrite should be "
                "3-6 sentences."
            ),
            "prompts": [
                "Summarise our customer feedback.",
                "Make a report about wastage.",
                "Help me plan a promotion.",
                "What products are trending?",
                "Analyse staff performance.",
            ],
        },
        "assessment": {
            "instructions": (
                "Write 3 original prompts for your actual role at Harris Farm. "
                "Each prompt must clearly use all 4 elements (Task, Context, "
                "Format, Constraints). At least one prompt should involve "
                "data analysis. Your prompts will be scored on the 5-criteria "
                "rubric -- aim for 18/25 or higher."
            ),
            "rubric_criteria": [
                "clarity", "context", "data_spec", "format", "actionability",
            ],
        },
    },

    # ---------------------------------------------------------------
    # L2 -- Role-Specific AI Applications (SCAFFOLD)
    # ---------------------------------------------------------------
    {
        "code": "L2",
        "series": "L",
        "name": "Role-Specific AI Applications",
        "description": (
            "Learn how different roles at Harris Farm use AI differently. "
            "Build prompts tailored to Fresh Buyers, Store Managers, Finance, "
            "Marketing, and Operations teams."
        ),
        "prerequisites": ["L1"],
        "difficulty": "beginner",
        "duration_minutes": 35,
        "sort_order": 2,
        "theory": [
            {
                "title": "Why Role Matters",
                "body": (
                    "The same AI tool will give you completely different value "
                    "depending on how you frame your role. A Store Manager at "
                    "Bondi Beach asking about \"sales performance\" needs a "
                    "daily operational snapshot. A Fresh Buyer asking the same "
                    "question needs category-level trends across all stores to "
                    "inform purchasing decisions.\n\n"
                    "When you tell the AI your role, you are setting the lens "
                    "through which it filters information. Think of it as "
                    "telling a new colleague: \"I am the person who makes "
                    "buying decisions for Deli across all stores\" versus "
                    "\"I run the Gladesville store day-to-day\". The advice "
                    "each person needs is fundamentally different."
                ),
            },
            {
                "title": "Fresh Buyers",
                "body": (
                    "Fresh Buyers at Harris Farm manage product range, supplier "
                    "relationships, and order quantities across multiple stores. "
                    "AI is most useful for:\n\n"
                    "- **Demand forecasting:** \"Based on last year's sales "
                    "pattern, how many kilos of strawberries should I order for "
                    "Crows Nest next week?\"\n"
                    "- **Range review preparation:** \"Summarise the top 20 and "
                    "bottom 20 SKUs in the Deli category by gross margin across "
                    "all stores for the last quarter.\"\n"
                    "- **Supplier communication:** \"Draft an email to our "
                    "prosciutto supplier requesting a 5% volume discount, "
                    "referencing our 12-month order history.\"\n\n"
                    "The key context for Buyer prompts: always name the "
                    "category, specify the store scope (single store vs network), "
                    "and state the decision you are making."
                ),
            },
            {
                "title": "Store Managers",
                "body": (
                    "Store Managers need AI for day-to-day operational decisions: "
                    "rostering, daily sales review, customer issue resolution, "
                    "and team communication.\n\n"
                    "- **Daily review:** \"Give me a morning briefing for "
                    "Neutral Bay store: yesterday's revenue vs target, top 3 "
                    "selling departments, any departments more than 10% below "
                    "target.\"\n"
                    "- **Customer response:** \"Draft a professional response "
                    "to a customer complaint about out-of-stock items in our "
                    "organic range. Tone: empathetic, solution-focused.\"\n\n"
                    "Store Manager prompts should always name the store and "
                    "specify the time frame (today, this week, this month)."
                ),
            },
            {
                "title": "Finance and Marketing",
                "body": (
                    "**Finance** teams use AI for variance analysis, budget "
                    "commentary, and report preparation:\n"
                    "- \"Explain the $42K revenue shortfall at Hornsby for "
                    "January 2026 vs budget. Break down by department and "
                    "identify the top 3 contributing factors.\"\n\n"
                    "**Marketing** teams use AI for campaign planning, customer "
                    "segmentation, and content creation:\n"
                    "- \"Write 3 Instagram captions for our Easter hamper range. "
                    "Each should be under 150 characters, use Harris Farm's "
                    "warm/friendly tone, and include a call-to-action.\"\n\n"
                    "Finance prompts benefit from exact dollar figures and "
                    "comparison periods. Marketing prompts need brand voice "
                    "guidance, channel specifications, and content constraints."
                ),
            },
            {
                "title": "Operations",
                "body": (
                    "Operations teams manage logistics, transport, store "
                    "maintenance, and supply chain efficiency:\n"
                    "- \"Analyse delivery route efficiency for our Northern "
                    "Beaches stores (Allambie Heights, Brookvale, Manly). "
                    "Compare current delivery windows to sales volume by "
                    "hour. Are we delivering at the right times?\"\n\n"
                    "Operations prompts should reference specific locations, "
                    "time windows, and operational metrics (fill rates, delivery "
                    "times, wastage percentages)."
                ),
            },
        ],
        "examples": [
            {
                "weak": "I need to know about our cheese sales.",
                "strong": (
                    "I am the Deli Buyer responsible for cheese across all "
                    "Harris Farm stores. Analyse cheese sub-category sales "
                    "(hard, soft, blue, fresh) for the last 4 weeks across "
                    "the top 5 stores by cheese revenue. I need this for "
                    "my quarterly range review meeting with the Head of "
                    "Fresh. Show a table with: sub-category, store, revenue, "
                    "margin %, and units sold. Highlight any sub-category "
                    "where margin dropped below 35%."
                ),
                "explanation": (
                    "The weak prompt has no role, no store scope, no time "
                    "period, no purpose, and no format. The strong prompt "
                    "establishes the Buyer role, scopes to top 5 stores, "
                    "sets a 4-week window, names the audience (Head of Fresh), "
                    "defines the table structure, and adds a margin threshold."
                ),
            },
            {
                "weak": "How do I improve my store's performance?",
                "strong": (
                    "I am the Store Manager at Castle Hill. Our store has "
                    "been 8% below revenue target for 3 consecutive weeks. "
                    "Foot traffic is stable, so the issue is likely basket "
                    "size or conversion. Suggest 5 specific, actionable "
                    "tactics I can implement this week to increase average "
                    "basket value, drawing on best practices from high-"
                    "performing Harris Farm stores. Format as numbered "
                    "actions with expected impact. Do not suggest tactics "
                    "requiring capital expenditure."
                ),
                "explanation": (
                    "The strong version names the store, quantifies the "
                    "problem, narrows the likely cause, asks for a specific "
                    "number of actions, sets a time frame (this week), and "
                    "excludes capex solutions."
                ),
            },
            {
                "weak": "Write me a marketing email.",
                "strong": (
                    "I am the Marketing Coordinator at Harris Farm. Draft a "
                    "customer email (200 words max) announcing our new weekly "
                    "organic veg box available for home delivery across Sydney. "
                    "Price: $49. Includes seasonal organic vegetables for a "
                    "family of four. Tone: warm, community-focused, aligned "
                    "with our 'For The Greater Goodness' values. Include one "
                    "customer testimonial placeholder. CTA: 'Order by Wednesday "
                    "for Friday delivery.' Do not mention competitors."
                ),
                "explanation": (
                    "Role, product details, price, audience, tone, brand "
                    "alignment, word count, testimonial structure, CTA text, "
                    "and exclusions are all specified."
                ),
            },
        ],
        "exercise": {
            "instructions": (
                "Choose YOUR specific role at Harris Farm (or the role closest "
                "to yours). Write 3 prompts that you would genuinely use in "
                "your day-to-day work. Each prompt must: (a) state your role "
                "explicitly, (b) reference a real scenario you face, (c) use "
                "all 4 elements from L1."
            ),
            "prompts": [
                "Write a prompt for a task you do every week.",
                "Write a prompt for a task you find difficult or time-consuming.",
                "Write a prompt for a task you have never tried with AI before.",
            ],
        },
        "assessment": {
            "instructions": (
                "Submit 3 role-tailored prompts. Each must name your role, "
                "include a realistic Harris Farm business scenario, specify "
                "the output format, and lead to a concrete action or decision. "
                "Aim for 18/25 or higher on the rubric."
            ),
            "rubric_criteria": [
                "clarity", "context", "data_spec", "format", "actionability",
            ],
        },
    },

    # ---------------------------------------------------------------
    # L3 -- Advanced Prompting Techniques (SCAFFOLD)
    # ---------------------------------------------------------------
    {
        "code": "L3",
        "series": "L",
        "name": "Advanced Prompting Techniques",
        "description": (
            "Go beyond the basics with chain-of-thought reasoning, few-shot "
            "examples, multi-turn conversations, document analysis, and "
            "structured output techniques."
        ),
        "prerequisites": ["L1", "L2"],
        "difficulty": "intermediate",
        "duration_minutes": 45,
        "sort_order": 3,
        "theory": [
            {
                "title": "Chain-of-Thought Prompting",
                "body": (
                    "Chain-of-thought (CoT) prompting asks the AI to show its "
                    "working before giving a final answer. This dramatically "
                    "improves accuracy on multi-step problems.\n\n"
                    "Instead of asking \"Which store should I allocate extra "
                    "avocado stock to?\", add: \"Think through this step by "
                    "step: first look at each store's avocado sales trend, "
                    "then check current stock levels, then consider day of "
                    "week demand patterns, and finally make a recommendation "
                    "with reasoning.\"\n\n"
                    "CoT is especially useful at Harris Farm for:\n"
                    "- Analysing why a store is underperforming (multiple "
                    "factors to weigh)\n"
                    "- Deciding between supplier offers (price vs quality vs "
                    "reliability)\n"
                    "- Planning promotions (customer segment, timing, product "
                    "selection, margin impact)"
                ),
            },
            {
                "title": "Few-Shot Prompting",
                "body": (
                    "Few-shot prompting means giving the AI 1-3 examples of "
                    "the input/output pattern you want before asking it to "
                    "generate a new one. This is powerful when you need "
                    "consistent formatting or a specific style.\n\n"
                    "**Example:** If you want the AI to write product "
                    "descriptions in Harris Farm's brand voice, give it two "
                    "existing descriptions first:\n\n"
                    "> *Here are two examples of how we describe products:*\n"
                    "> *Example 1: \"Our Barossa Valley free-range chicken is "
                    "raised on open pastures with no added hormones. Juicy, "
                    "flavourful, and perfect for a Sunday roast.\"*\n"
                    "> *Example 2: \"Hand-picked from the Hawkesbury, these "
                    "heirloom tomatoes burst with the flavour that mass-"
                    "produced varieties just cannot match.\"*\n"
                    "> *Now write a description for our new high-welfare "
                    "Wagyu beef mince in the same style.*\n\n"
                    "The AI learns the tone, length, and structure from your "
                    "examples and replicates it."
                ),
            },
            {
                "title": "Multi-Turn Conversations",
                "body": (
                    "Not every task fits in a single prompt. Multi-turn "
                    "conversations break a complex request into steps, where "
                    "each message builds on the AI's previous response.\n\n"
                    "**Step 1:** \"Summarise Bondi Beach store's sales by "
                    "department for last week.\"\n"
                    "**Step 2:** \"Now focus on the Deli. What were the top "
                    "5 and bottom 5 products by revenue?\"\n"
                    "**Step 3:** \"For the bottom 5, suggest whether to "
                    "discontinue, re-merchandise, or mark down. Give a "
                    "one-line rationale for each.\"\n\n"
                    "This drill-down approach is how experienced users get "
                    "the most value from AI -- starting broad and refining."
                ),
            },
        ],
        "examples": [
            {
                "weak": "Why is Hornsby store underperforming?",
                "strong": (
                    "I am the Regional Manager for the Upper North Shore. "
                    "Hornsby store has been 12% below revenue target for the "
                    "last 4 weeks. Think through this step by step:\n"
                    "1. First, compare Hornsby's department-level sales to the "
                    "same period last year to identify which departments are "
                    "driving the shortfall.\n"
                    "2. Then check if foot traffic has changed or if basket "
                    "size is the issue.\n"
                    "3. Consider external factors (roadworks, competitor "
                    "openings, weather).\n"
                    "4. Finally, recommend 3 specific recovery actions ranked "
                    "by likely impact.\n"
                    "Format as a structured analysis with clear headings for "
                    "each step."
                ),
                "explanation": (
                    "The strong version uses chain-of-thought prompting, "
                    "breaking the analysis into logical steps. It provides "
                    "role context, quantifies the problem, and specifies "
                    "the output structure."
                ),
            },
            {
                "weak": "Write product descriptions for new items.",
                "strong": (
                    "Here are two examples of Harris Farm product descriptions "
                    "in our brand voice:\n\n"
                    "Example 1: \"Our Barossa Valley free-range chicken is "
                    "raised on open pastures with no added hormones. Juicy, "
                    "flavourful, and perfect for a Sunday roast.\"\n\n"
                    "Example 2: \"Hand-picked from the Hawkesbury, these "
                    "heirloom tomatoes burst with the flavour that mass-"
                    "produced varieties just cannot match.\"\n\n"
                    "Now write descriptions in the same style for these 3 "
                    "new products:\n"
                    "1. Meredith Dairy marinated goat cheese\n"
                    "2. Bangalow pork sausages (gluten-free)\n"
                    "3. Yarra Valley smoked trout\n\n"
                    "Each description: 2 sentences, under 40 words, mention "
                    "the producer region and one key quality attribute."
                ),
                "explanation": (
                    "This uses few-shot prompting -- two examples set the "
                    "style, tone, and length. The constraints (2 sentences, "
                    "40 words, region + quality attribute) ensure consistency "
                    "across all three outputs."
                ),
            },
        ],
        "exercise": {
            "instructions": (
                "Apply each of the three advanced techniques to a real Harris "
                "Farm scenario. Write one prompt using chain-of-thought, one "
                "using few-shot examples, and one designed as the first message "
                "in a multi-turn conversation."
            ),
            "prompts": [
                (
                    "Use chain-of-thought to analyse why a department is "
                    "underperforming at a specific store."
                ),
                (
                    "Use few-shot examples to get the AI to write in a "
                    "consistent format (e.g., product descriptions, meeting "
                    "summaries, customer responses)."
                ),
                (
                    "Design a 3-step multi-turn conversation that drills "
                    "down from a broad overview to a specific action plan."
                ),
            ],
        },
        "assessment": {
            "instructions": (
                "Complete a multi-step analysis task: Write a chain-of-thought "
                "prompt that analyses a real problem at Harris Farm (e.g., "
                "declining performance in a category, a staffing challenge, "
                "a marketing opportunity). The prompt must guide the AI through "
                "at least 3 logical steps, use your role context, specify "
                "the output format, and lead to actionable recommendations."
            ),
            "rubric_criteria": [
                "clarity", "context", "data_spec", "format", "actionability",
            ],
        },
    },

    # ---------------------------------------------------------------
    # L4 -- Rubric Mastery (SCAFFOLD)
    # ---------------------------------------------------------------
    {
        "code": "L4",
        "series": "L",
        "name": "Rubric Mastery",
        "description": (
            "Understand the 5-criteria Skills Academy rubric inside and out. "
            "Learn to self-evaluate your prompts, spot common weaknesses, "
            "and consistently score 18/25 or higher."
        ),
        "prerequisites": ["L1"],
        "difficulty": "intermediate",
        "duration_minutes": 40,
        "sort_order": 4,
        "theory": [
            {
                "title": "Understanding the 5 Criteria",
                "body": (
                    "Every prompt you submit in the Skills Academy is scored "
                    "on 5 criteria, each worth 1-5 points (total: 25):\n\n"
                    "1. **Request Clarity** -- Is the ask unambiguous? Could "
                    "two different people read it and produce the same output?\n"
                    "2. **Context Provision** -- Does it include your role, "
                    "the business situation, and why this matters?\n"
                    "3. **Data Specification** -- Does it name the data "
                    "source, time period, filters, and comparison basis?\n"
                    "4. **Output Format** -- Does it define the structure "
                    "of the response (table, bullets, email, etc.)?\n"
                    "5. **Actionability** -- Will the output drive a real "
                    "decision or next step?\n\n"
                    "The pass threshold is **18/25**. Most untrained prompts "
                    "score 8-14. After completing this module, you should "
                    "be able to self-assess within 2 points of the AI score."
                ),
            },
            {
                "title": "Common Pitfalls and How to Fix Them",
                "body": (
                    "**Pitfall 1: Vague task verbs.** \"Look into\", \"help "
                    "with\", \"tell me about\" are not tasks. Replace with "
                    "\"analyse\", \"compare\", \"draft\", \"list\", "
                    "\"recommend\".\n\n"
                    "**Pitfall 2: Missing the 'why'.** Saying what you want "
                    "without saying why you need it. Add the business decision "
                    "the output will inform: \"I need this to decide whether "
                    "to increase our cheese order\" or \"This will be presented "
                    "at Tuesday's leadership meeting.\"\n\n"
                    "**Pitfall 3: No data anchor.** Even if you are not asking "
                    "for data analysis, reference the evidence base. \"Based on "
                    "our last 4 weeks of customer feedback\" is better than "
                    "giving the AI nothing to work with.\n\n"
                    "**Pitfall 4: Format afterthought.** Adding \"make it "
                    "useful\" is not a format instruction. Be specific: "
                    "\"3 bullet points\", \"a table with columns X, Y, Z\", "
                    "\"a 200-word email\".\n\n"
                    "**Pitfall 5: No action link.** If the output does not "
                    "connect to a decision, meeting, or next step, it is just "
                    "trivia. Always link to an action."
                ),
            },
            {
                "title": "Scored Examples: 12/25 vs 23/25",
                "body": (
                    "**Prompt A (scores 12/25):**\n"
                    "> \"What are the best-selling products at our stores?\"\n\n"
                    "- Clarity: 2 (which stores? which products? best by what "
                    "measure?)\n"
                    "- Context: 1 (no role, no situation)\n"
                    "- Data Spec: 2 (implies sales data but no time period or "
                    "scope)\n"
                    "- Format: 2 (no structure requested)\n"
                    "- Actionability: 5 (potential to act, but vague)\n\n"
                    "**Prompt B (scores 23/25):**\n"
                    "> \"I am the Category Manager for Bakery. Rank the top 15 "
                    "Bakery SKUs across all stores by unit volume for the last "
                    "8 weeks, compared to the same 8 weeks last year. I am "
                    "preparing for next month's range review with the Head of "
                    "Fresh. Format as a table: SKU Name, Units (This Year), "
                    "Units (Last Year), YoY % Change, Gross Margin %. "
                    "Highlight any SKU with margin below 30%. Exclude "
                    "seasonal Christmas lines.\"\n\n"
                    "- Clarity: 5 (single, unambiguous request)\n"
                    "- Context: 5 (role, audience, business occasion)\n"
                    "- Data Spec: 5 (metric, time range, comparison, scope)\n"
                    "- Format: 4 (excellent table spec, minor: could specify "
                    "sort order)\n"
                    "- Actionability: 4 (clear link to range review, could "
                    "name the specific decision)"
                ),
            },
        ],
        "examples": [
            {
                "weak": "Give me sales data for last month.",
                "strong": (
                    "I am the Finance Business Partner for NSW stores. Pull "
                    "total revenue by store for February 2026, compared to "
                    "budget and to February 2025. I am preparing the monthly "
                    "variance report for the CFO. Format as a table: Store, "
                    "Actual Revenue, Budget, Var to Budget ($ and %), Prior "
                    "Year, YoY Change %. Sort by largest negative variance "
                    "first. Add a 3-sentence executive summary at the top "
                    "highlighting the key story. Exclude the Richmond store "
                    "as it was closed for refurbishment."
                ),
                "explanation": (
                    "The weak prompt scores roughly 8/25 (clarity 2, context "
                    "1, data 2, format 1, action 2). The strong prompt hits "
                    "all 5 criteria hard: exact role, specific data dimensions, "
                    "detailed table spec, named audience, and an exclusion "
                    "constraint. Likely score: 23-24/25."
                ),
            },
            {
                "weak": "How is our online business going?",
                "strong": (
                    "As the E-Commerce Manager, summarise our online channel "
                    "performance for the last 4 weeks: total orders, revenue, "
                    "average order value, and fulfilment rate. Compare each "
                    "metric to the same 4 weeks last year. I need this for "
                    "the Monday digital standup to decide whether to increase "
                    "our Google Ads spend for March. Format as a 4-row table "
                    "(one row per metric) with columns: Metric, This Period, "
                    "Last Year, Change %. Follow with 2 bullet-point "
                    "recommendations."
                ),
                "explanation": (
                    "The strong version scores approximately 22/25. It names "
                    "the role, specifies 4 exact metrics, sets the time period "
                    "and comparison, names the meeting and decision, and "
                    "defines the table plus recommendations format."
                ),
            },
        ],
        "exercise": {
            "instructions": (
                "Score the following 3 prompts yourself using the 5-criteria "
                "rubric (1-5 per criterion, total out of 25). Write a brief "
                "justification for each score. Then compare your scores to "
                "the AI's scoring."
            ),
            "prompts": [
                (
                    "I need a report on fruit sales at Mosman for the last "
                    "month. Make it detailed."
                ),
                (
                    "As the Deli Buyer, list the 10 slowest-moving cheeses "
                    "across all stores for the last 12 weeks by unit volume. "
                    "I need to decide which to delist at next week's range "
                    "review. Table format: Product, Total Units, Revenue, "
                    "Margin %, Stores Stocking. Exclude any product launched "
                    "in the last 6 weeks."
                ),
                (
                    "Help me understand our customers better so I can make "
                    "better decisions about what to stock."
                ),
            ],
        },
        "assessment": {
            "instructions": (
                "Write a prompt on any Harris Farm topic that scores 20/25 "
                "or higher on the rubric. Before submitting, self-score it "
                "and explain how you ensured each criterion is addressed. "
                "The AI will then score it independently -- your goal is to "
                "match the AI score within 2 points."
            ),
            "rubric_criteria": [
                "clarity", "context", "data_spec", "format", "actionability",
            ],
        },
    },

    # ---------------------------------------------------------------
    # L5 -- AI Workflow Mastery & Mentoring (SCAFFOLD)
    # ---------------------------------------------------------------
    {
        "code": "L5",
        "series": "L",
        "name": "AI Workflow Mastery & Mentoring",
        "description": (
            "Build reusable prompt templates, automate repetitive tasks, "
            "quality-check AI outputs, and teach others. This is the "
            "capstone module for AI skills at Harris Farm."
        ),
        "prerequisites": ["L3", "L4"],
        "difficulty": "advanced",
        "duration_minutes": 50,
        "sort_order": 5,
        "theory": [
            {
                "title": "Building a Personal Prompt Library",
                "body": (
                    "Once you have mastered the fundamentals, the next step "
                    "is to stop writing prompts from scratch every time. A "
                    "prompt library is a collection of your best, highest-"
                    "scoring prompts organised by task type.\n\n"
                    "Structure your library by frequency: **daily** prompts "
                    "(morning briefing, sales check), **weekly** prompts "
                    "(range review prep, roster planning), and **monthly** "
                    "prompts (variance report, category review). Each prompt "
                    "should be a template with placeholders like [STORE], "
                    "[DATE_RANGE], [DEPARTMENT] that you fill in each time.\n\n"
                    "**Harris Farm example template:**\n"
                    "> *Analyse [DEPARTMENT] sales at [STORE] for the week "
                    "ending [DATE], compared to the same week last year. "
                    "Show: total revenue, units sold, margin %, top 5 "
                    "growth SKUs, top 5 decline SKUs. Format as a one-page "
                    "summary for the Monday store meeting.*"
                ),
            },
            {
                "title": "Quality-Checking AI Outputs",
                "body": (
                    "AI outputs are not always correct. As an advanced user, "
                    "you need a systematic approach to verification:\n\n"
                    "1. **Sense-check the numbers.** If the AI says Crows "
                    "Nest sold $2M of avocados last week, that is obviously "
                    "wrong. Develop a feel for realistic ranges.\n"
                    "2. **Check the logic.** If the AI recommends increasing "
                    "orders for a product with declining sales, challenge it.\n"
                    "3. **Verify the sources.** If the AI cites data, check "
                    "that the data actually exists and says what the AI "
                    "claims.\n"
                    "4. **Test with edge cases.** Ask follow-up questions "
                    "that probe the boundaries of the AI's analysis.\n\n"
                    "A useful technique: ask the AI \"What assumptions did "
                    "you make?\" and \"What could be wrong with this "
                    "analysis?\" This forces it to surface its own "
                    "weaknesses."
                ),
            },
            {
                "title": "Teaching Others",
                "body": (
                    "The highest-value AI skill at Harris Farm is the ability "
                    "to help your colleagues get better. When mentoring "
                    "others:\n\n"
                    "- **Start with their real work.** Do not teach abstract "
                    "prompting theory. Ask \"What task takes you the longest "
                    "each week?\" and build a prompt for that task together.\n"
                    "- **Show the before/after.** Run a weak prompt and a "
                    "strong prompt side by side. The difference in output "
                    "quality is the most persuasive lesson.\n"
                    "- **Use the rubric.** Score their prompts together. The "
                    "rubric makes feedback objective, not personal.\n"
                    "- **Celebrate progress.** Moving from a 10/25 to a "
                    "16/25 is a significant improvement worth recognising."
                ),
            },
        ],
        "examples": [
            {
                "weak": "Create a template for weekly reports.",
                "strong": (
                    "I am the Operations Manager and I produce a weekly "
                    "performance summary every Monday for the leadership "
                    "team. Create a reusable prompt template with "
                    "placeholders for [WEEK_ENDING_DATE] and [REGION]. "
                    "The template should request: total revenue vs target, "
                    "top 3 and bottom 3 stores by WoW growth, wastage % "
                    "by department, and 3 key callouts. Output format: "
                    "executive summary (3 sentences), then a performance "
                    "table, then callouts as bullet points. Constrain to "
                    "one page equivalent (approximately 400 words)."
                ),
                "explanation": (
                    "The strong version specifies the role, the recurring "
                    "cadence, the audience, the exact metrics, the "
                    "placeholder variables, and the output structure. "
                    "This template can be reused every Monday by just "
                    "swapping in the date and region."
                ),
            },
            {
                "weak": "Help me check if AI gave me good results.",
                "strong": (
                    "I just received an AI-generated analysis of Gladesville "
                    "store's Butcher department performance. Review the "
                    "following output for: (1) any numbers that seem "
                    "unrealistic for a single Harris Farm store, (2) logical "
                    "inconsistencies between the recommendations and the "
                    "data, (3) missing context that would change the "
                    "conclusions. Flag each issue with a severity rating "
                    "(high/medium/low) and suggest how to correct it. "
                    "Format as a numbered checklist."
                ),
                "explanation": (
                    "This demonstrates an advanced skill: using AI to "
                    "quality-check AI. The prompt gives specific verification "
                    "criteria, a severity framework, and output format."
                ),
            },
        ],
        "exercise": {
            "instructions": (
                "Create a reusable prompt template for a task you perform "
                "at least weekly. The template must include at least 2 "
                "placeholders (e.g., [STORE], [DATE_RANGE]), cover all "
                "4 elements from L1, and be designed so that a colleague "
                "could use it without additional explanation."
            ),
            "prompts": [
                (
                    "Write the prompt template with clear placeholder "
                    "names in square brackets."
                ),
                (
                    "Fill in the template with real values and run it. "
                    "Paste the AI's output."
                ),
                (
                    "Write a 3-point quality check of the AI's output: "
                    "what is correct, what needs verification, and what "
                    "is missing."
                ),
            ],
        },
        "assessment": {
            "instructions": (
                "Create a prompt template for a recurring Harris Farm task "
                "that scores 22/25 or higher. Submit: (a) the template with "
                "placeholders, (b) one filled-in example, and (c) a brief "
                "guide (3-5 bullet points) explaining how a colleague should "
                "use it. The template itself will be scored on the rubric."
            ),
            "rubric_criteria": [
                "clarity", "context", "data_spec", "format", "actionability",
            ],
        },
    },


    # ===================================================================
    # D-SERIES: APPLIED DATA + AI
    # ===================================================================

    # ---------------------------------------------------------------
    # D1 -- Talking to Data with AI (FULLY FLESHED)
    # ---------------------------------------------------------------
    {
        "code": "D1",
        "series": "D",
        "name": "Talking to Data with AI",
        "description": (
            "Learn how to ask AI meaningful questions about data. Understand "
            "what AI can and cannot do with business data, and how to "
            "structure queries that get precise, useful answers."
        ),
        "prerequisites": [],
        "difficulty": "beginner",
        "duration_minutes": 35,
        "sort_order": 6,
        "theory": [
            {
                "title": "What AI Can (and Cannot) Do with Data",
                "body": (
                    "AI tools like Claude and ChatGPT can be remarkably useful "
                    "for data work -- but they are not databases. Understanding "
                    "the boundary is critical.\n\n"
                    "**What AI can do well:**\n"
                    "- Summarise and interpret data you provide\n"
                    "- Suggest the right analysis approach for a question\n"
                    "- Write queries, formulas, and code to analyse data\n"
                    "- Explain trends and patterns in plain English\n"
                    "- Generate charts and visualisations from data\n\n"
                    "**What AI cannot do:**\n"
                    "- Access Harris Farm's live databases directly (unless "
                    "connected via the Hub)\n"
                    "- Guarantee that numbers are accurate without "
                    "verification\n"
                    "- Replace business judgement on what the data *means*\n\n"
                    "The Harris Farm Hub has AI tools connected to our real "
                    "data (Sales dashboard, PLU Intel, Buying Hub). When "
                    "using these, you are talking to AI *about* real data. "
                    "When using standalone Claude or ChatGPT, you need to "
                    "provide the data yourself."
                ),
            },
            {
                "title": "The 5 Dimensions of a Good Data Query",
                "body": (
                    "Every effective data question specifies 5 things:\n\n"
                    "1. **Metric** -- What are you measuring? Revenue, units, "
                    "margin, customer count, basket size, wastage?\n"
                    "2. **Entity** -- What are you measuring it for? A store, "
                    "a department, a product, a customer segment?\n"
                    "3. **Time Period** -- When? Last week, last 4 weeks, "
                    "same period last year, rolling 12 months?\n"
                    "4. **Comparison** -- Against what? Budget, last year, "
                    "another store, the network average?\n"
                    "5. **Threshold** -- What matters? Highlight items above "
                    "or below a certain value, show only the top 10, flag "
                    "changes greater than 5%.\n\n"
                    "**Harris Farm example:**\n"
                    "- Metric: weekly revenue\n"
                    "- Entity: all North Shore stores\n"
                    "- Time period: last 8 weeks\n"
                    "- Comparison: same 8 weeks last year\n"
                    "- Threshold: flag any store down more than 10% YoY"
                ),
            },
            {
                "title": "From Vague to Specific: The Data Query Ladder",
                "body": (
                    "Most people start with vague data questions and need to "
                    "learn to be specific. Here is the progression:\n\n"
                    "**Level 1 (Vague):** \"How are sales?\"\n"
                    "**Level 2 (Slightly better):** \"How are F&V sales this "
                    "month?\"\n"
                    "**Level 3 (Good):** \"What is F&V revenue for Crows Nest "
                    "for the last 4 weeks?\"\n"
                    "**Level 4 (Strong):** \"Compare Crows Nest F&V revenue "
                    "for the last 4 weeks to the same 4 weeks last year, "
                    "broken down by week.\"\n"
                    "**Level 5 (Excellent):** \"Compare Crows Nest F&V revenue "
                    "for the last 4 weeks to the same 4 weeks last year, "
                    "broken down by week. Show the top 5 growing and top 5 "
                    "declining items by revenue change. Flag anything with "
                    "margin below 25%. I need this for the Tuesday buying "
                    "meeting to adjust next week's orders.\"\n\n"
                    "Each level adds one of the 5 data dimensions. Level 5 "
                    "also adds the business action (adjusting orders), which "
                    "helps the AI prioritise what to highlight."
                ),
            },
            {
                "title": "Common Harris Farm Data Questions",
                "body": (
                    "Here are the kinds of questions each team typically asks:\n\n"
                    "**Store Managers:**\n"
                    "- \"How did my store perform yesterday/this week vs target?\"\n"
                    "- \"Which departments are above/below plan?\"\n"
                    "- \"What were my top 10 sellers today?\"\n\n"
                    "**Buyers:**\n"
                    "- \"Which products are selling through fastest?\"\n"
                    "- \"What is the margin profile for my category by store?\"\n"
                    "- \"Which items should I increase/decrease orders for?\"\n\n"
                    "**Finance:**\n"
                    "- \"What is the revenue variance to budget by store?\"\n"
                    "- \"What is driving the margin change this month?\"\n\n"
                    "**Leadership:**\n"
                    "- \"What is the network sales trend over the last 12 weeks?\"\n"
                    "- \"Which stores are consistently outperforming?\"\n\n"
                    "All of these become excellent prompts when you add the 5 "
                    "data dimensions."
                ),
            },
            {
                "title": "Working with Data in the Harris Farm Hub",
                "body": (
                    "The Harris Farm Hub connects AI directly to our data. "
                    "This means you can ask questions in natural language and "
                    "get answers drawn from real sales, customer, and product "
                    "data.\n\n"
                    "**Key Hub tools for data queries:**\n"
                    "- **Hub Assistant:** General questions across all data\n"
                    "- **Sales Dashboard:** Store and department performance\n"
                    "- **PLU Intel:** Product-level analysis across stores\n"
                    "- **Buying Hub:** Category and supplier analysis\n"
                    "- **Customer Dashboard:** Customer segments and behaviour\n\n"
                    "When using these tools, the same rules apply: be specific "
                    "about what metric, what entity, what time period, what "
                    "comparison, and what threshold. The AI is smart, but it "
                    "cannot read your mind."
                ),
            },
        ],
        "examples": [
            {
                "weak": "What are our sales?",
                "strong": (
                    "Show me weekly total revenue for all NSW stores for the "
                    "last 8 weeks, broken down by department, highlighting any "
                    "department that dropped more than 10% week-on-week. "
                    "Format as a table sorted by largest decline."
                ),
                "explanation": (
                    "The weak version has no entity, no time period, no "
                    "comparison, no threshold, and no format. The strong "
                    "version specifies all 5 data dimensions plus format "
                    "and sort order."
                ),
            },
            {
                "weak": "How many customers do we have?",
                "strong": (
                    "What is the active customer count (at least one purchase "
                    "in the last 90 days) for each store, compared to the "
                    "same 90-day window last year? Show: Store, Active "
                    "Customers (Current), Active Customers (Last Year), "
                    "Change %. I need this to assess whether our loyalty "
                    "programme is driving retention. Sort by largest decline."
                ),
                "explanation": (
                    "The strong version defines \"customer\" precisely "
                    "(active = purchase in last 90 days), sets a comparison "
                    "period, specifies the table format, and links to a "
                    "business decision (loyalty programme effectiveness)."
                ),
            },
            {
                "weak": "Which products are doing well?",
                "strong": (
                    "List the top 20 Fruit & Veg SKUs across the Bondi Beach "
                    "and Bondi Junction stores by unit growth (this 4 weeks "
                    "vs same 4 weeks last year). Include: Product Name, "
                    "Units (Current), Units (Prior Year), Growth %, Current "
                    "Margin %. I am the F&V Buyer and I want to ensure we "
                    "are allocating enough stock to fast-moving lines. "
                    "Exclude any product with fewer than 50 units sold."
                ),
                "explanation": (
                    "\"Doing well\" is undefined. The strong version chooses "
                    "a specific metric (unit growth), names the stores, "
                    "sets the period, defines the minimum threshold (50 "
                    "units), and connects to a buying action."
                ),
            },
            {
                "weak": "Tell me about wastage.",
                "strong": (
                    "Show the wastage percentage (waste dollars / total cost "
                    "of goods) for the Bakery department at Drummoyne, "
                    "Leichhardt, and Rozelle for each of the last 6 weeks. "
                    "I am the Regional Manager for Inner West and I am "
                    "investigating whether wastage is improving after we "
                    "introduced new end-of-day markdown procedures last "
                    "month. Format as a line chart with one line per store "
                    "and a table below it."
                ),
                "explanation": (
                    "The strong version defines the wastage metric precisely, "
                    "names 3 specific stores, sets a 6-week window, explains "
                    "the business context (new markdown procedures), and "
                    "asks for both a chart and table."
                ),
            },
            {
                "weak": "Give me revenue numbers.",
                "strong": (
                    "Pull daily revenue for Manly store for the last 14 "
                    "days, broken down by trading hour (7am-8pm). I am the "
                    "Store Manager and I want to identify our peak and "
                    "trough hours so I can adjust staff rostering. Format "
                    "as a heatmap-style table with days as rows and hours "
                    "as columns. Highlight hours where revenue is more than "
                    "20% above or below the daily average."
                ),
                "explanation": (
                    "\"Revenue numbers\" is the vaguest possible data request. "
                    "The strong version specifies daily granularity by hour, "
                    "a single store, a 14-day window, the business action "
                    "(rostering), and an innovative format (heatmap table "
                    "with threshold highlighting)."
                ),
            },
        ],
        "exercise": {
            "instructions": (
                "Transform each of the following vague data questions into "
                "specific, well-structured queries. Each rewrite must include "
                "all 5 data dimensions (Metric, Entity, Time Period, "
                "Comparison, Threshold) and an output format."
            ),
            "prompts": [
                "How is our online business performing?",
                "What products should we stop selling?",
                "Are we making enough margin?",
                "How busy are our stores?",
                "What do our customers buy together?",
            ],
        },
        "assessment": {
            "instructions": (
                "Write 5 AI-powered data queries for real Harris Farm "
                "business questions. Each query must specify the store (or "
                "stores), the time period, the metric, the comparison basis, "
                "and the output format. At least 2 queries should be for "
                "your specific role. Each will be scored on the 5-criteria "
                "rubric -- aim for an average of 18/25 or higher."
            ),
            "rubric_criteria": [
                "clarity", "context", "data_spec", "format", "actionability",
            ],
        },
    },

    # ---------------------------------------------------------------
    # D2 -- AI-Powered Analysis (SCAFFOLD)
    # ---------------------------------------------------------------
    {
        "code": "D2",
        "series": "D",
        "name": "AI-Powered Analysis",
        "description": (
            "Move beyond data retrieval to genuine analysis. Learn to use AI "
            "for variance analysis, trend identification, benchmarking, and "
            "root cause investigation at Harris Farm."
        ),
        "prerequisites": ["D1"],
        "difficulty": "intermediate",
        "duration_minutes": 45,
        "sort_order": 7,
        "theory": [
            {
                "title": "From Data Retrieval to Analysis",
                "body": (
                    "D1 taught you how to ask for data. This module teaches "
                    "you how to ask AI to *analyse* data -- to find patterns, "
                    "explain variances, and generate insights.\n\n"
                    "The difference is in the task verb. Retrieval prompts "
                    "say \"show me\" or \"list\". Analysis prompts say "
                    "\"explain why\", \"identify the drivers of\", \"compare "
                    "and contrast\", or \"assess whether\".\n\n"
                    "**Retrieval:** \"Show me Drummoyne revenue for the last "
                    "4 weeks.\"\n"
                    "**Analysis:** \"Explain why Drummoyne revenue dropped "
                    "8% last week compared to the prior week. Break down the "
                    "decline by department and identify the top 3 contributing "
                    "factors.\"\n\n"
                    "The analysis prompt asks the AI to think, not just "
                    "fetch."
                ),
            },
            {
                "title": "Four Core Analysis Patterns",
                "body": (
                    "Most business analysis at Harris Farm falls into four "
                    "patterns:\n\n"
                    "1. **Variance Analysis:** \"Why is [metric] different "
                    "from [benchmark]?\" Example: \"Why is Neutral Bay 12% "
                    "below budget this month?\"\n\n"
                    "2. **Trend Analysis:** \"What direction is [metric] "
                    "heading and why?\" Example: \"Is our network average "
                    "basket size growing or shrinking over the last 12 "
                    "weeks?\"\n\n"
                    "3. **Benchmarking:** \"How does [entity A] compare to "
                    "[entity B]?\" Example: \"Compare Crows Nest and Double "
                    "Bay Deli performance across revenue, margin, and "
                    "wastage.\"\n\n"
                    "4. **Root Cause:** \"What is causing [problem]?\" "
                    "Example: \"Manly store's customer count has dropped 15% "
                    "in January. Analyse possible causes by looking at "
                    "foot traffic, basket size, and department-level sales.\""
                ),
            },
            {
                "title": "Giving AI Enough to Work With",
                "body": (
                    "AI produces better analysis when you provide reference "
                    "points. Instead of asking \"Is this good?\", tell the "
                    "AI what \"good\" looks like:\n\n"
                    "- \"Our target wastage for Bakery is 8%. Drummoyne is "
                    "at 12%. Analyse why.\"\n"
                    "- \"The network average basket size is $38. Castle Hill "
                    "is at $31. What could explain the gap?\"\n"
                    "- \"Last year's February revenue for Bondi Beach was "
                    "$420K. This year it is $395K. Break down where we lost "
                    "ground.\"\n\n"
                    "The more concrete benchmarks you give, the more "
                    "targeted the analysis will be."
                ),
            },
        ],
        "examples": [
            {
                "weak": "Why are sales down?",
                "strong": (
                    "I am the Store Manager at Edgecliff. Our total store "
                    "revenue was $118K last week, down 9% from $130K the "
                    "prior week and 6% below the same week last year. "
                    "Analyse the decline by department: which departments "
                    "drove most of the drop? Was it fewer customers, lower "
                    "basket size, or both? Cross-reference with any known "
                    "factors (public holidays, weather, local events). "
                    "Format as: (1) a waterfall breakdown of the $12K "
                    "decline by department, (2) 3 bullet-point hypotheses "
                    "for root causes, (3) 2 recommended actions for this "
                    "week."
                ),
                "explanation": (
                    "The strong version provides exact numbers, comparison "
                    "points, a structured analysis framework (department "
                    "waterfall, root causes, actions), and specifies the "
                    "output format precisely."
                ),
            },
            {
                "weak": "Compare our stores.",
                "strong": (
                    "Benchmark the 4 Inner West stores (Drummoyne, "
                    "Leichhardt, Rozelle, Gladesville) across 5 metrics for "
                    "the last 4 weeks: revenue, revenue per sqm, average "
                    "basket size, customer count, and wastage %. Rank each "
                    "store on each metric. Identify which store is the "
                    "strongest overall and which has the most room for "
                    "improvement. I am the Regional Manager preparing for "
                    "my monthly review. Format as a comparison table plus "
                    "a 3-sentence summary."
                ),
                "explanation": (
                    "The strong version names the specific stores, selects "
                    "5 concrete metrics, asks for ranking and synthesis, "
                    "and defines the audience and output format."
                ),
            },
        ],
        "exercise": {
            "instructions": (
                "Write an analysis prompt for each of the four core patterns "
                "(variance, trend, benchmarking, root cause) using a real "
                "Harris Farm scenario. Each prompt should include the "
                "specific numbers or benchmarks the AI needs."
            ),
            "prompts": [
                "Variance analysis: Explain a performance gap at a store.",
                "Trend analysis: Assess whether a metric is improving or worsening.",
                "Benchmarking: Compare two stores or departments head to head.",
                "Root cause: Investigate why a KPI has changed significantly.",
            ],
        },
        "assessment": {
            "instructions": (
                "Write a detailed analysis prompt that combines at least 2 "
                "of the 4 core patterns (e.g., variance + root cause). The "
                "prompt should specify the metric, entity, time period, "
                "benchmark, and output format. It must lead to a concrete "
                "business decision. Score target: 20/25."
            ),
            "rubric_criteria": [
                "clarity", "context", "data_spec", "format", "actionability",
            ],
        },
    },

    # ---------------------------------------------------------------
    # D3 -- Chain-of-Thought Analysis (SCAFFOLD)
    # ---------------------------------------------------------------
    {
        "code": "D3",
        "series": "D",
        "name": "Chain-of-Thought Analysis",
        "description": (
            "Use step-by-step reasoning to tackle complex data problems. "
            "Break multi-variable questions into logical stages that the AI "
            "can solve sequentially."
        ),
        "prerequisites": ["D1", "D2"],
        "difficulty": "intermediate",
        "duration_minutes": 45,
        "sort_order": 8,
        "theory": [
            {
                "title": "Why Step-by-Step Matters for Data",
                "body": (
                    "Complex business questions rarely have single-step "
                    "answers. \"Should we open a new store in the Inner West?\" "
                    "requires analysing current store performance, "
                    "cannibalisation risk, demographic fit, competitive "
                    "landscape, and financial projections -- in sequence.\n\n"
                    "Chain-of-thought prompting forces the AI to work through "
                    "each step explicitly, showing its reasoning so you can "
                    "verify each stage before moving to the next. This is "
                    "far more reliable than asking the AI to give you a "
                    "single answer to a complex question."
                ),
            },
            {
                "title": "Building a Chain for Data Analysis",
                "body": (
                    "A good chain-of-thought data prompt has this structure:\n\n"
                    "**Step 1 -- Gather:** \"First, pull [specific data].\"\n"
                    "**Step 2 -- Calculate:** \"Then, compute [metric or "
                    "comparison].\"\n"
                    "**Step 3 -- Analyse:** \"Next, identify the key patterns "
                    "or anomalies.\"\n"
                    "**Step 4 -- Explain:** \"Then, suggest possible causes "
                    "for the patterns you found.\"\n"
                    "**Step 5 -- Recommend:** \"Finally, recommend specific "
                    "actions based on your analysis.\"\n\n"
                    "**Harris Farm example:**\n"
                    "> \"I am the F&V Buyer. I need to decide whether to "
                    "increase avocado supply to Bondi Beach. Think through "
                    "this step by step:\n"
                    "> 1. First, show Bondi Beach avocado sales (units and "
                    "revenue) for the last 8 weeks.\n"
                    "> 2. Then compare to the same 8 weeks last year.\n"
                    "> 3. Next, check if avocado sales at neighbouring stores "
                    "(Bondi Junction, Double Bay) show a similar trend.\n"
                    "> 4. Assess whether the growth is seasonal or structural.\n"
                    "> 5. Recommend a specific order quantity change with "
                    "reasoning.\""
                ),
            },
            {
                "title": "Multi-Turn Drill-Downs",
                "body": (
                    "Not everything needs to be in one prompt. Sometimes the "
                    "most powerful approach is to use each AI response as "
                    "the starting point for the next question:\n\n"
                    "**Turn 1:** \"Show me the top 10 departments by revenue "
                    "decline across all stores for last week.\"\n"
                    "**Turn 2:** (After seeing results) \"The Deli is down "
                    "the most. Break this down by product sub-category for "
                    "the top 5 stores.\"\n"
                    "**Turn 3:** \"Smallgoods are the biggest driver. What is "
                    "the margin impact and should we adjust pricing?\"\n\n"
                    "Each turn narrows the focus based on what you learned "
                    "in the previous step. This mimics how an experienced "
                    "analyst naturally works."
                ),
            },
        ],
        "examples": [
            {
                "weak": "Should we change our avocado orders?",
                "strong": (
                    "I am the F&V Buyer. Help me decide whether to increase "
                    "avocado supply across the network. Think step by step:\n"
                    "1. Show total network avocado sales (units and revenue) "
                    "for the last 12 weeks, trended week by week.\n"
                    "2. Identify the top 5 stores by avocado unit growth.\n"
                    "3. Check wastage data for avocados at those 5 stores -- "
                    "are we already over-ordering?\n"
                    "4. Compare our avocado price per unit to typical market "
                    "pricing (if available).\n"
                    "5. Recommend: should I increase orders, maintain, or "
                    "redistribute stock between stores? Include specific "
                    "percentage changes.\n"
                    "Format each step with a clear heading and show your "
                    "working."
                ),
                "explanation": (
                    "The strong version uses explicit numbered steps, "
                    "specifies data for each step, and asks the AI to "
                    "show its working at each stage. This makes verification "
                    "easy."
                ),
            },
            {
                "weak": "Why are customers leaving?",
                "strong": (
                    "I am the Customer Insights Analyst. Analyse customer "
                    "retention across the Lindfield store over the last 6 "
                    "months. Work through this in stages:\n"
                    "1. How has the active customer count (purchase in last "
                    "90 days) changed month by month?\n"
                    "2. Of customers who were active 6 months ago, what "
                    "percentage are still active today?\n"
                    "3. For lapsed customers, what was their average basket "
                    "size and visit frequency before they stopped shopping?\n"
                    "4. Were they concentrated in any particular department "
                    "or day of week?\n"
                    "5. Based on this, what are the top 3 hypotheses for "
                    "why they left, and what retention action would you "
                    "recommend for each?\n"
                    "Show each step's findings before moving to the next."
                ),
                "explanation": (
                    "This chain builds logically: first establish the size "
                    "of the problem, then profile the lost customers, then "
                    "hypothesise causes, then recommend actions. Each step "
                    "depends on the previous one."
                ),
            },
        ],
        "exercise": {
            "instructions": (
                "Choose a complex business question relevant to your role "
                "at Harris Farm. Break it into a 4-5 step chain-of-thought "
                "analysis prompt. Each step should build on the previous "
                "one and specify what data is needed."
            ),
            "prompts": [
                (
                    "Write a chain-of-thought prompt that investigates a "
                    "performance issue at a specific store."
                ),
                (
                    "Write a multi-turn drill-down sequence (3 turns) that "
                    "starts broad and narrows to a specific action."
                ),
                (
                    "Combine chain-of-thought with a format constraint: "
                    "ask the AI to produce a summary at each step before "
                    "moving to the next."
                ),
            ],
        },
        "assessment": {
            "instructions": (
                "Write a chain-of-thought analysis prompt with at least "
                "4 logical steps that addresses a real Harris Farm business "
                "question. Each step must specify the data needed and what "
                "the AI should conclude before proceeding. The final step "
                "must produce actionable recommendations. Aim for 20/25."
            ),
            "rubric_criteria": [
                "clarity", "context", "data_spec", "format", "actionability",
            ],
        },
    },

    # ---------------------------------------------------------------
    # D4 -- Building AI-Powered Reports (SCAFFOLD)
    # ---------------------------------------------------------------
    {
        "code": "D4",
        "series": "D",
        "name": "Building AI-Powered Reports",
        "description": (
            "Create recurring, structured reports using AI. Learn to design "
            "report templates, automate commentary, and build dashboards "
            "that combine data retrieval with AI-generated insights."
        ),
        "prerequisites": ["D2", "D3"],
        "difficulty": "advanced",
        "duration_minutes": 50,
        "sort_order": 9,
        "theory": [
            {
                "title": "From Ad-Hoc Queries to Recurring Reports",
                "body": (
                    "By now you know how to ask AI great one-off data "
                    "questions. The next level is building reusable report "
                    "structures that you (or your team) use every week or "
                    "month.\n\n"
                    "A good AI-powered report template has three layers:\n"
                    "1. **Data layer:** The specific metrics and filters "
                    "(what you learned in D1)\n"
                    "2. **Analysis layer:** The comparison, trending, and "
                    "variance logic (what you learned in D2/D3)\n"
                    "3. **Narrative layer:** AI-generated commentary that "
                    "explains the numbers in plain English\n\n"
                    "**Harris Farm example:** A weekly store performance "
                    "report that auto-generates for each Regional Manager, "
                    "combining this week's numbers with AI commentary on "
                    "what changed and why."
                ),
            },
            {
                "title": "Designing Report Prompts with Placeholders",
                "body": (
                    "Reusable report prompts use placeholders that change "
                    "each time you run them. The structure stays constant "
                    "while the data refreshes.\n\n"
                    "**Template structure:**\n"
                    "> \"Generate the weekly [DEPARTMENT] performance report "
                    "for [STORE] for the week ending [DATE].\n"
                    "> Section 1: Revenue summary vs target and vs same week "
                    "last year.\n"
                    "> Section 2: Top 5 and bottom 5 products by revenue "
                    "change.\n"
                    "> Section 3: Wastage analysis vs the 8% target.\n"
                    "> Section 4: 3 key callouts and recommended actions.\n"
                    "> Format: professional report with clear headings, "
                    "tables where appropriate, and a 2-sentence executive "
                    "summary at the top.\"\n\n"
                    "This template works for any store, any department, any "
                    "week -- just swap the placeholders."
                ),
            },
            {
                "title": "AI-Generated Commentary Best Practices",
                "body": (
                    "The most valuable part of AI-powered reports is the "
                    "commentary -- the AI's explanation of what the numbers "
                    "mean. To get good commentary:\n\n"
                    "- **Set the audience:** \"Write for a Store Manager "
                    "who knows their business but is time-poor.\"\n"
                    "- **Be opinionated:** \"Do not just describe the data. "
                    "State what is going well, what is concerning, and what "
                    "to do about it.\"\n"
                    "- **Use comparisons:** \"Always reference the prior "
                    "week, the prior year, and the target.\"\n"
                    "- **Flag outliers:** \"Highlight anything more than "
                    "10% above or below expectation.\"\n"
                    "- **Keep it concise:** \"Limit commentary to 3 bullet "
                    "points per section.\""
                ),
            },
        ],
        "examples": [
            {
                "weak": "Write me a weekly report.",
                "strong": (
                    "I am the Regional Manager for North Shore (Crows Nest, "
                    "Neutral Bay, North Sydney, Willoughby). Generate my "
                    "weekly performance report for the week ending 21 Feb "
                    "2026.\n\n"
                    "Section 1 -- Executive Summary: 3-sentence overview of "
                    "the region's week.\n"
                    "Section 2 -- Revenue Table: Store | Actual | Target | "
                    "Var % | LY | YoY %. Sort by largest variance.\n"
                    "Section 3 -- Department Spotlight: For the store with "
                    "the largest negative variance, break down by department.\n"
                    "Section 4 -- Wins & Risks: 2 positive callouts and 2 "
                    "areas of concern with specific numbers.\n"
                    "Section 5 -- Actions: 3 recommended actions for next "
                    "week, each with an owner and deadline.\n\n"
                    "Tone: direct, data-driven, action-oriented. Maximum "
                    "500 words total."
                ),
                "explanation": (
                    "The strong version is a complete report specification "
                    "with 5 named sections, exact table columns, audience "
                    "context, tone guidance, and a word limit. This could "
                    "be reused every week by changing the date."
                ),
            },
            {
                "weak": "Summarise this month's performance.",
                "strong": (
                    "As the Finance Business Partner, generate the February "
                    "2026 monthly performance pack for the CFO. Structure:\n"
                    "1. One-paragraph executive summary (largest positive "
                    "and negative variance to budget).\n"
                    "2. Network P&L summary: Revenue, COGS, Gross Margin, "
                    "Operating Costs, EBITDA -- each with Actual, Budget, "
                    "Variance, and Prior Year.\n"
                    "3. Store-by-store revenue vs budget table (all 21 stores).\n"
                    "4. Commentary on the 3 stores with largest budget miss "
                    "-- identify drivers.\n"
                    "5. Outlook statement for March based on current trends.\n\n"
                    "Use professional financial report language. All numbers "
                    "in $000s. Flag any item with variance greater than 5%."
                ),
                "explanation": (
                    "This is a complete monthly report spec with financial "
                    "rigour: named metrics, comparison bases, formatting "
                    "rules ($000s), and a forward-looking section."
                ),
            },
        ],
        "exercise": {
            "instructions": (
                "Design a recurring report template for a report you (or "
                "your team) produce regularly. Include: 3-5 named sections, "
                "table specifications, commentary guidelines, and at least "
                "2 placeholders."
            ),
            "prompts": [
                (
                    "Write the full report template with placeholders for "
                    "a weekly operational report."
                ),
                (
                    "Fill in the template for a specific week and store. "
                    "Run it and review the output."
                ),
                (
                    "Iterate: identify one section where the AI output "
                    "was weak and rewrite that section's instructions "
                    "to improve it."
                ),
            ],
        },
        "assessment": {
            "instructions": (
                "Submit a complete, reusable report template with at least "
                "4 sections, 2 placeholders, table specifications, and "
                "commentary guidelines. Include one filled-in example "
                "showing the template in action. Aim for 22/25."
            ),
            "rubric_criteria": [
                "clarity", "context", "data_spec", "format", "actionability",
            ],
        },
    },

    # ---------------------------------------------------------------
    # D5 -- Advanced AI + Data Techniques (SCAFFOLD)
    # ---------------------------------------------------------------
    {
        "code": "D5",
        "series": "D",
        "name": "Advanced AI + Data Techniques",
        "description": (
            "Master the most powerful AI + data techniques: multi-source "
            "analysis, scenario modelling, anomaly detection, and building "
            "AI workflows that combine multiple data views."
        ),
        "prerequisites": ["D3", "D4"],
        "difficulty": "advanced",
        "duration_minutes": 55,
        "sort_order": 10,
        "theory": [
            {
                "title": "Multi-Source Analysis",
                "body": (
                    "The most impactful analyses combine data from multiple "
                    "sources. At Harris Farm, this might mean combining:\n"
                    "- Sales data (what sold) with customer data (who bought "
                    "it)\n"
                    "- Store performance data with external factors (weather, "
                    "local events, competitor activity)\n"
                    "- Product data with supplier data (cost changes, lead "
                    "times, quality scores)\n\n"
                    "When prompting for multi-source analysis, be explicit "
                    "about which datasets to use and how they should be "
                    "joined. For example: \"Combine Crows Nest's weekly "
                    "sales data with customer loyalty data. For each "
                    "department, show revenue alongside the number of unique "
                    "loyalty card customers and the ratio of new vs returning "
                    "customers.\"\n\n"
                    "The key skill is knowing which data sources exist and "
                    "how they connect -- something you have built through "
                    "D1 to D4."
                ),
            },
            {
                "title": "Scenario Modelling with AI",
                "body": (
                    "AI can help you model \"what if\" scenarios by applying "
                    "assumptions to data:\n\n"
                    "- \"If we increase avocado prices by 10%, and price "
                    "elasticity is -1.2, what would happen to revenue and "
                    "margin at Bondi Beach?\"\n"
                    "- \"If foot traffic at Hornsby returns to last year's "
                    "levels, but basket size stays flat, what revenue would "
                    "we expect?\"\n"
                    "- \"Model 3 scenarios for next month's Bakery revenue "
                    "at Manly: optimistic (10% growth), base case (flat), "
                    "and pessimistic (10% decline). For each, show revenue, "
                    "margin, and wastage.\"\n\n"
                    "Always state your assumptions explicitly so the AI can "
                    "show how different assumptions change the outcome."
                ),
            },
            {
                "title": "Anomaly Detection and Early Warning",
                "body": (
                    "One of AI's strongest data capabilities is spotting "
                    "patterns that humans might miss. Use AI to build early "
                    "warning prompts:\n\n"
                    "- \"Scan all stores' daily revenue for the last 7 days. "
                    "Flag any store where revenue was more than 2 standard "
                    "deviations below its rolling 4-week average on any "
                    "day.\"\n"
                    "- \"Check all departments at Parramatta for unusual "
                    "wastage patterns: any department where this week's "
                    "wastage is more than double the 4-week average.\"\n\n"
                    "These prompts are powerful because they catch problems "
                    "early, before they compound into larger issues. They "
                    "work best as recurring checks (daily or weekly)."
                ),
            },
        ],
        "examples": [
            {
                "weak": "What if we changed our pricing?",
                "strong": (
                    "I am the Head of Fresh. Model the impact of a 5% price "
                    "increase on our top 20 F&V lines across the network. "
                    "Assumptions: price elasticity of -0.8 (a 5% price "
                    "increase leads to a 4% unit volume decline). For each "
                    "product show: Current Price, New Price, Current Weekly "
                    "Units, Projected Weekly Units, Current Weekly Revenue, "
                    "Projected Weekly Revenue, Current Margin %, Projected "
                    "Margin %. Show the net revenue and margin impact "
                    "across all 20 products. Format as a table with a "
                    "summary row. Add a 3-sentence recommendation on "
                    "whether to proceed."
                ),
                "explanation": (
                    "The strong version states the role, specifies the "
                    "scope (top 20 F&V lines), declares the elasticity "
                    "assumption, defines every column in the output table, "
                    "asks for a net impact summary, and requests a "
                    "recommendation."
                ),
            },
            {
                "weak": "Are there any problems I should know about?",
                "strong": (
                    "Run a daily anomaly scan across all 21 Harris Farm "
                    "stores for yesterday. Flag any of the following:\n"
                    "1. Store revenue more than 15% below the same day last "
                    "week (after adjusting for day-of-week patterns).\n"
                    "2. Any department with wastage above 12% of COGS.\n"
                    "3. Any product category with zero sales (potential "
                    "stock-out).\n"
                    "4. Any store where customer count dropped more than "
                    "20% vs the 4-week daily average.\n\n"
                    "For each flag, show: Store, Issue Type, Metric Value, "
                    "Expected Value, Severity (high/medium/low). Sort by "
                    "severity. I am the Operations Director and I review "
                    "this at 7am each morning."
                ),
                "explanation": (
                    "This is an automated anomaly detection template. It "
                    "defines 4 specific alert conditions with thresholds, "
                    "asks for a structured output with severity ratings, "
                    "and names the audience and use case."
                ),
            },
        ],
        "exercise": {
            "instructions": (
                "Write one prompt for each of the three advanced techniques: "
                "multi-source analysis, scenario modelling, and anomaly "
                "detection. Each must be grounded in a real Harris Farm "
                "business context with specific metrics and thresholds."
            ),
            "prompts": [
                (
                    "Multi-source: Combine two data sources (e.g., sales + "
                    "customer, or performance + weather) to answer a "
                    "question that neither source could answer alone."
                ),
                (
                    "Scenario modelling: Model 3 scenarios (optimistic, "
                    "base, pessimistic) for a specific decision at a "
                    "specific store."
                ),
                (
                    "Anomaly detection: Design a daily or weekly automated "
                    "check that flags issues before they become problems."
                ),
            ],
        },
        "assessment": {
            "instructions": (
                "Design an advanced AI + data workflow that combines at "
                "least 2 of the 3 techniques from this module. The workflow "
                "should address a real, recurring Harris Farm business need. "
                "Submit the complete prompt (or multi-prompt sequence) with "
                "all data specifications, assumptions, and output formats. "
                "Aim for 22/25."
            ),
            "rubric_criteria": [
                "clarity", "context", "data_spec", "format", "actionability",
            ],
        },
    },
]


# ---------------------------------------------------------------------------
# HELPER: Build a lookup dict keyed by module code
# ---------------------------------------------------------------------------

SKILLS_MODULE_MAP = {m["code"]: m for m in SKILLS_MODULES}


# ---------------------------------------------------------------------------
# PREREQUISITE GRAPH (convenience for UI rendering)
# ---------------------------------------------------------------------------

PREREQUISITE_GRAPH = {
    m["code"]: m["prerequisites"] for m in SKILLS_MODULES
}


# ---------------------------------------------------------------------------
# SERIES METADATA
# ---------------------------------------------------------------------------

SERIES_INFO = {
    "L": {
        "name": "Core AI Skills",
        "description": (
            "Master the fundamentals of prompting, role-specific applications, "
            "advanced techniques, and rubric-based self-evaluation."
        ),
        "colour": "#2ECC71",
    },
    "D": {
        "name": "Applied Data + AI",
        "description": (
            "Learn to query, analyse, and report on Harris Farm data using "
            "AI tools -- from basic data questions to automated reports."
        ),
        "colour": "#1a73e8",
    },
}


# ---------------------------------------------------------------------------
# V3: ADAPTIVE EXERCISE VARIANTS  (Standard / Stretch / Elite)
# ---------------------------------------------------------------------------
# For each of the 10 modules, three difficulty tiers with HFM-relevant
# scenarios.  "standard" covers the module basics, "stretch" adds complexity,
# "elite" demands multi-dimensional, executive-level thinking.
# ---------------------------------------------------------------------------

ADAPTIVE_EXERCISES = {

    # ---------------------------------------------------------------
    # L1 — The 4 Elements of Effective Prompts
    # ---------------------------------------------------------------
    "L1": {
        "standard": {
            "instruction": (
                "Write a prompt asking AI to summarise last week's sales for "
                "Crows Nest store. Include all 4 elements (task, context, "
                "format, constraints)."
            ),
            "scenario": (
                "You are a store manager preparing for the Monday team meeting."
            ),
            "success_criteria": (
                "Must include clear task, store context, output format, and "
                "at least one constraint."
            ),
        },
        "stretch": {
            "instruction": (
                "Write a prompt asking AI to compare Crows Nest and Mosman "
                "store performance over the last 4 weeks. Include all 4 "
                "elements plus a comparison framework."
            ),
            "scenario": (
                "You are an area manager responsible for both stores. The "
                "regional meeting is Thursday."
            ),
            "added_constraint": (
                "The output must be structured for a 5-minute verbal update, "
                "not a written report."
            ),
            "success_criteria": (
                "All 4 elements + comparison structure + verbal format "
                "adaptation."
            ),
        },
        "elite": {
            "instruction": (
                "Write a prompt asking AI to produce a multi-store performance "
                "analysis that identifies the top 3 improvement opportunities, "
                "with specific actions and owners, formatted as a one-page "
                "executive brief."
            ),
            "scenario": (
                "You are presenting to the Co-CEOs at the monthly leadership "
                "meeting. You manage 5 stores in the Northern Beaches area."
            ),
            "added_constraint": (
                "Each recommendation must include: evidence (data), action "
                "(what), owner (who), and timeline (when). The tone must "
                "balance urgency with optimism."
            ),
            "success_criteria": (
                "All 4 elements + executive audience adaptation + structured "
                "recommendations + tone management."
            ),
            "rubric": "advanced",
        },
    },

    # ---------------------------------------------------------------
    # L2 — Role-Based Prompting
    # ---------------------------------------------------------------
    "L2": {
        "standard": {
            "instruction": (
                "Write a prompt for a STORE MANAGER asking AI to help plan "
                "next week's staffing based on expected foot traffic patterns."
            ),
            "scenario": (
                "Dee Why store. Summer holidays are ending, back-to-school "
                "week. Staff of 25."
            ),
            "success_criteria": (
                "Role-appropriate language, relevant store context, practical "
                "output format."
            ),
        },
        "stretch": {
            "instruction": (
                "Write TWO prompts for different roles (a BUYER and a STORE "
                "MANAGER) about the same product issue: organic avocados are "
                "consistently selling out before Thursday."
            ),
            "scenario": (
                "Both roles need to solve the same problem but need different "
                "information and actions."
            ),
            "added_constraint": (
                "Each prompt must use role-appropriate language and request "
                "role-specific outputs."
            ),
            "success_criteria": (
                "Clear role differentiation, appropriate data requests per "
                "role, actionable for each."
            ),
        },
        "elite": {
            "instruction": (
                "Design a 3-prompt sequence where each prompt is written from "
                "a different role's perspective (Marketing, Buying, Store Ops) "
                "to collaboratively solve a customer retention problem."
            ),
            "scenario": (
                "Harris Farm Bondi has seen a 12% drop in repeat customers "
                "over 3 months. Each department needs to investigate their "
                "angle and propose coordinated actions."
            ),
            "added_constraint": (
                "The outputs from each prompt must explicitly feed into the "
                "next role's analysis. Include handoff instructions."
            ),
            "success_criteria": (
                "Three distinct role perspectives, clear data handoffs, "
                "coordinated action plan."
            ),
            "rubric": "advanced",
        },
    },

    # ---------------------------------------------------------------
    # L3 — Advanced Prompt Techniques
    # ---------------------------------------------------------------
    "L3": {
        "standard": {
            "instruction": (
                "Rewrite the following vague prompt using chain-of-thought: "
                "'Which products should I promote this week?' Add step-by-step "
                "reasoning instructions so the AI walks through the logic."
            ),
            "scenario": (
                "You are the Category Manager for Dairy at Harris Farm. "
                "You have access to weekly sales data and current stock levels."
            ),
            "success_criteria": (
                "Prompt explicitly asks AI to reason step-by-step, includes "
                "at least 3 logical steps, and ties to a promotion decision."
            ),
        },
        "stretch": {
            "instruction": (
                "Write a few-shot prompt that teaches AI how to classify "
                "customer complaints into the categories Harris Farm uses: "
                "Product Quality, Stock Availability, Price, Service, and "
                "Store Condition. Provide 3 labelled examples, then ask it "
                "to classify 5 new unlabelled complaints."
            ),
            "scenario": (
                "The People & Culture team receives 50+ customer comments per "
                "week via in-store feedback cards. Manual classification takes "
                "2 hours."
            ),
            "added_constraint": (
                "Each example must be realistic and drawn from a different "
                "store. The AI must also assign a severity rating (low, "
                "medium, high) alongside the category."
            ),
            "success_criteria": (
                "Well-structured few-shot examples, clear classification "
                "schema, severity dimension, realistic HFM complaints."
            ),
        },
        "elite": {
            "instruction": (
                "Design a multi-turn conversation plan (3+ turns) that uses "
                "chain-of-thought in turn 1, few-shot examples in turn 2, "
                "and a refinement loop in turn 3 to produce a supplier "
                "negotiation brief."
            ),
            "scenario": (
                "You are the Head Buyer for Fruit & Veg. You are preparing "
                "for a quarterly review with your top avocado supplier. You "
                "need to negotiate a 5% price reduction while maintaining "
                "quality commitments."
            ),
            "added_constraint": (
                "Each turn must explicitly reference the output of the "
                "previous turn. The final output must be a one-page brief "
                "with talking points, BATNA, and concession thresholds."
            ),
            "success_criteria": (
                "Three distinct techniques combined, clear inter-turn "
                "references, actionable negotiation brief with BATNA."
            ),
            "rubric": "advanced",
        },
    },

    # ---------------------------------------------------------------
    # L4 — Rubric Mastery & Self-Evaluation
    # ---------------------------------------------------------------
    "L4": {
        "standard": {
            "instruction": (
                "Score the following prompt using the 5-criteria rubric "
                "(clarity, context, data spec, format, actionability) and "
                "explain your reasoning: 'Show me the top selling fruit "
                "this month.'"
            ),
            "scenario": (
                "You are practising self-evaluation before submitting your "
                "prompts to the Prompt Engine for formal scoring."
            ),
            "success_criteria": (
                "Accurate score for each criterion with 1-2 sentence "
                "justification. Total should be in the 7-10 range for "
                "this weak prompt."
            ),
        },
        "stretch": {
            "instruction": (
                "Write a prompt, self-score it, identify the weakest "
                "criterion, rewrite to fix only that weakness, then re-score. "
                "Show the before/after prompts and both scorecards."
            ),
            "scenario": (
                "You are the Bakery Department Manager at Pymble store. You "
                "want AI to help you reduce end-of-day waste by 20%."
            ),
            "added_constraint": (
                "Your fix must improve the weakest criterion by at least 2 "
                "points without reducing any other criterion score."
            ),
            "success_criteria": (
                "Honest self-scoring, targeted improvement of weakest area, "
                "clear before/after comparison, no criterion regression."
            ),
        },
        "elite": {
            "instruction": (
                "Take a complex business question and produce THREE prompt "
                "versions: one that scores 10/25, one that scores 18/25, and "
                "one that scores 23+/25. For each, provide the full rubric "
                "scorecard and explain exactly what makes each version "
                "stronger than the last."
            ),
            "scenario": (
                "The CFO has asked you to use AI to investigate why the "
                "Drummoyne store's gross margin has dropped 3 percentage "
                "points over the last quarter despite stable revenue."
            ),
            "added_constraint": (
                "The 10/25 version must have realistic beginner mistakes, not "
                "be deliberately awful. The progression must teach a reader "
                "how to improve their own prompts."
            ),
            "success_criteria": (
                "Three realistic quality tiers, accurate self-scoring, "
                "clear progression narrative, teaching value for others."
            ),
            "rubric": "advanced",
        },
    },

    # ---------------------------------------------------------------
    # L5 — Workflow Design & Teaching Others
    # ---------------------------------------------------------------
    "L5": {
        "standard": {
            "instruction": (
                "Design a simple 2-step AI workflow for a task you do "
                "regularly. Step 1 should gather and structure data; Step 2 "
                "should analyse and recommend. Write the prompt for each step."
            ),
            "scenario": (
                "You are a Store Manager who does a weekly performance review "
                "every Monday morning before the team huddle."
            ),
            "success_criteria": (
                "Two clear, connected prompts. Step 2 explicitly references "
                "Step 1 output. Both prompts score 18+ individually."
            ),
        },
        "stretch": {
            "instruction": (
                "Create a 'Prompt Playbook' entry for your department. It "
                "should include: the business trigger (when to use it), the "
                "template prompt with fill-in-the-blank slots, a scoring "
                "checklist, and a worked example."
            ),
            "scenario": (
                "You are the Deli Team Leader at Leichhardt. Your team of "
                "6 people are all new to using AI. You want them to be "
                "able to use AI for weekly stock ordering without needing "
                "your help each time."
            ),
            "added_constraint": (
                "The playbook entry must be understandable by someone who "
                "has only completed L1. No jargon. Include a 'common "
                "mistakes' section."
            ),
            "success_criteria": (
                "Reusable template, clear fill-in slots, beginner-friendly "
                "language, practical worked example, common mistakes listed."
            ),
        },
        "elite": {
            "instruction": (
                "Design a complete AI upskilling program for a team of 10 "
                "people who have never used AI. Include: a 4-week schedule, "
                "the first prompt exercise for each week, success metrics, "
                "and a plan for measuring whether the training actually "
                "improved business outcomes."
            ),
            "scenario": (
                "You are the Regional Manager for the 6 Inner West stores. "
                "The Co-CEOs have asked you to pilot AI adoption with your "
                "store manager team and report back with measurable results "
                "in 30 days."
            ),
            "added_constraint": (
                "The program must account for varying tech comfort levels "
                "(some managers are over 55 and cautious about AI). Include "
                "a 'buddy system' pairing structure and weekly check-in "
                "format."
            ),
            "success_criteria": (
                "Realistic 4-week plan, progressive difficulty, measurable "
                "KPIs, inclusivity for different comfort levels, buddy "
                "system design."
            ),
            "rubric": "advanced",
        },
    },

    # ---------------------------------------------------------------
    # D1 — Asking Data Questions with AI
    # ---------------------------------------------------------------
    "D1": {
        "standard": {
            "instruction": (
                "Write a prompt asking AI to answer this question using "
                "Harris Farm sales data: 'How did Fruit & Veg perform at "
                "Mosman last week compared to the week before?'"
            ),
            "scenario": (
                "You are the produce team leader at Mosman and need a quick "
                "check before your Wednesday stock order."
            ),
            "success_criteria": (
                "Specifies data source, time range (last week vs prior week), "
                "metric (revenue or units), and store filter."
            ),
        },
        "stretch": {
            "instruction": (
                "Write a prompt that asks AI to identify the 3 fastest "
                "declining product categories at your store over the last "
                "8 weeks, then hypothesise why each is declining."
            ),
            "scenario": (
                "You are the Store Manager at Drummoyne. The Area Manager "
                "flagged your store as underperforming this month and wants "
                "reasons by Friday."
            ),
            "added_constraint": (
                "The AI must separate seasonal effects from genuine declines. "
                "Each hypothesis must suggest one data point that would "
                "confirm or deny it."
            ),
            "success_criteria": (
                "Clear data query, seasonal adjustment request, structured "
                "hypotheses with testable predictions."
            ),
        },
        "elite": {
            "instruction": (
                "Design a prompt that asks AI to build a 'store health "
                "scorecard' using 5 data metrics of your choice. The "
                "scorecard must rate each metric as green/amber/red with "
                "thresholds you define, and produce a single overall "
                "health rating."
            ),
            "scenario": (
                "You are the Head of Store Operations. You want a repeatable "
                "scorecard that any area manager can run for any store, any "
                "week, without needing to adjust the prompt."
            ),
            "added_constraint": (
                "The prompt must be fully parameterised (store name and date "
                "range as the only inputs). Thresholds must be based on "
                "Harris Farm benchmarks, not arbitrary. Include a 'watch "
                "list' output for any metric trending from green to amber."
            ),
            "success_criteria": (
                "5 well-chosen metrics, defensible thresholds, parameterised "
                "design, RAG rating system, trend detection."
            ),
            "rubric": "advanced",
        },
    },

    # ---------------------------------------------------------------
    # D2 — Combining Data Sources & Finding Trends
    # ---------------------------------------------------------------
    "D2": {
        "standard": {
            "instruction": (
                "Write a prompt asking AI to combine weekly sales data with "
                "weather data to see if rain affects foot traffic at your "
                "store."
            ),
            "scenario": (
                "You are the Dee Why store manager. You suspect rainy days "
                "hurt your trade more than other stores because customers "
                "drive to a covered shopping centre instead."
            ),
            "success_criteria": (
                "Names both data sources, specifies the join logic (date), "
                "requests a correlation or comparison output."
            ),
        },
        "stretch": {
            "instruction": (
                "Write a prompt that combines Harris Farm sales data, market "
                "share data, and local demographic data to explain why two "
                "similar-sized stores have very different performance."
            ),
            "scenario": (
                "Bondi Beach and Crows Nest are similar in square footage and "
                "staff count, but Crows Nest outperforms on gross margin by "
                "4 points. The Head of Operations wants to understand why."
            ),
            "added_constraint": (
                "The analysis must explicitly keep sales data (Layer 1) and "
                "market share data (Layer 2) separate. Do not mix dollar "
                "values across layers."
            ),
            "success_criteria": (
                "Correct multi-source combination, Layer 1/2 separation "
                "respected, structured comparison framework."
            ),
        },
        "elite": {
            "instruction": (
                "Design a prompt that creates a 'Customer Catchment Profile' "
                "by combining transaction data, market share data, postcode "
                "demographics, and store distance calculations for a single "
                "store. The output should identify: where customers come "
                "from, what share HFM has in each zone, and where the "
                "biggest untapped opportunity lies."
            ),
            "scenario": (
                "Harris Farm is considering a major refurbishment at Neutral "
                "Bay. Before investing $2M, the Co-CEOs want a detailed "
                "catchment analysis to validate the customer base will "
                "support a larger format."
            ),
            "added_constraint": (
                "The analysis must use the standard trade area tiers (0-3km, "
                "0-5km, 0-10km). Opportunity claims must be flagged as "
                "DIRECTIONAL ONLY per data governance rules. Include "
                "cannibalisation risk from nearby HFM stores."
            ),
            "success_criteria": (
                "4+ data sources combined correctly, trade area tiers used, "
                "directional-only flagging, cannibalisation analysis, "
                "investment-grade output."
            ),
            "rubric": "advanced",
        },
    },

    # ---------------------------------------------------------------
    # D3 — Chain-of-Thought Data Analysis
    # ---------------------------------------------------------------
    "D3": {
        "standard": {
            "instruction": (
                "Write a prompt that asks AI to analyse why Bakery sales "
                "dropped 8% last week at Bondi. Explicitly instruct the AI "
                "to reason step-by-step through possible causes before "
                "reaching a conclusion."
            ),
            "scenario": (
                "You are the Bakery Team Leader. Your manager asked you to "
                "investigate before the Thursday review."
            ),
            "success_criteria": (
                "Chain-of-thought instruction present, at least 3 candidate "
                "causes to investigate, data references for each."
            ),
        },
        "stretch": {
            "instruction": (
                "Write a prompt that asks AI to perform a root cause analysis "
                "on declining basket size at 3 stores. The AI must: list "
                "hypotheses, rank them by likelihood, identify the data "
                "needed to test each, and recommend the top 2 to investigate "
                "first."
            ),
            "scenario": (
                "Leichhardt, Drummoyne, and Balmain stores all saw average "
                "basket size decline by $4-6 over the last month. They share "
                "a geographic cluster but different customer profiles."
            ),
            "added_constraint": (
                "The AI must consider both internal factors (range changes, "
                "pricing, staffing) and external factors (new competitor, "
                "seasonal shift, economic conditions). It must show its "
                "reasoning for the ranking."
            ),
            "success_criteria": (
                "Structured hypothesis generation, explicit ranking logic, "
                "data requirements per hypothesis, cross-store pattern "
                "recognition."
            ),
        },
        "elite": {
            "instruction": (
                "Design a multi-step analytical prompt that performs a "
                "complete 'margin erosion diagnosis' for a store. The AI "
                "must: (1) decompose margin into components (revenue mix, "
                "cost changes, waste, markdown), (2) identify which "
                "component drove the change, (3) drill into the top driver "
                "by category, and (4) propose 3 corrective actions with "
                "expected margin impact."
            ),
            "scenario": (
                "Pymble store's gross margin dropped from 34.2% to 31.8% "
                "over 6 weeks while revenue held steady. The CFO wants a "
                "diagnosis and fix plan by Monday."
            ),
            "added_constraint": (
                "Each analytical step must specify exactly which data tables "
                "and fields to query. The corrective actions must include "
                "estimated financial impact (even if approximate) and "
                "implementation timeline. The analysis must rule out data "
                "quality issues before drawing conclusions."
            ),
            "success_criteria": (
                "4-step analytical decomposition, specific data references, "
                "data quality check included, quantified corrective actions, "
                "executive-ready output."
            ),
            "rubric": "advanced",
        },
    },

    # ---------------------------------------------------------------
    # D4 — Building AI-Powered Reports
    # ---------------------------------------------------------------
    "D4": {
        "standard": {
            "instruction": (
                "Write a prompt asking AI to generate a weekly store "
                "performance report for Neutral Bay. Specify at least 4 "
                "sections the report must include and the format for each."
            ),
            "scenario": (
                "You are the Neutral Bay store manager. You send this report "
                "to your area manager every Monday by 10am."
            ),
            "success_criteria": (
                "4+ report sections defined, format specified per section "
                "(table, chart description, bullets, etc.), clear data "
                "sources named."
            ),
        },
        "stretch": {
            "instruction": (
                "Write a prompt that generates a comparative performance "
                "report covering 5 stores in the Inner West cluster. The "
                "report must include: a ranking table, a 'spotlight' on the "
                "most improved store, a 'concern' flag on the weakest, and "
                "3 cluster-wide trends."
            ),
            "scenario": (
                "You are the Inner West Area Manager. This report goes to "
                "the Head of Retail every fortnight. It must be concise "
                "enough to read in 3 minutes."
            ),
            "added_constraint": (
                "The report must follow a consistent template so it can be "
                "generated weekly with only the date range changing. Include "
                "a 'so what?' sentence after every data point. No section "
                "may exceed 100 words."
            ),
            "success_criteria": (
                "5-store comparison, template structure, spotlight/concern "
                "sections, cluster trends, 3-minute readability, insight "
                "after every data point."
            ),
        },
        "elite": {
            "instruction": (
                "Design a prompt (or prompt chain) that produces a monthly "
                "Board Report for Harris Farm's AI program. The report must "
                "combine: AI usage metrics (from the Hub), business impact "
                "data (from sales/ops), and qualitative feedback (from staff "
                "surveys). Include an executive summary, detailed findings, "
                "and forward-looking recommendations."
            ),
            "scenario": (
                "You are the CTO presenting to the Harris Farm board. The "
                "board includes external directors who are sceptical about "
                "AI investment. You need data-driven proof of value."
            ),
            "added_constraint": (
                "Every claim must link to a specific metric or data source. "
                "Include a 'confidence level' (high/medium/low) for each "
                "finding. Separate proven ROI from projected ROI. The tone "
                "must be professional and measured, not evangelical."
            ),
            "success_criteria": (
                "Multi-source report, executive summary quality, confidence "
                "ratings, proven vs projected ROI separation, sceptic-proof "
                "tone."
            ),
            "rubric": "advanced",
        },
    },

    # ---------------------------------------------------------------
    # D5 — Automated Workflows & Scaling
    # ---------------------------------------------------------------
    "D5": {
        "standard": {
            "instruction": (
                "Write a prompt that automates the generation of daily "
                "markdown stock alerts for the Fruit & Veg department. The "
                "alert should flag items with less than 1 day of stock "
                "remaining."
            ),
            "scenario": (
                "You are the Fruit & Veg buyer. Every morning you manually "
                "check 200+ lines to see what needs urgent reordering. You "
                "want AI to do the filtering and produce a prioritised list."
            ),
            "success_criteria": (
                "Automation-ready prompt (repeatable without editing), clear "
                "threshold logic, prioritised output format."
            ),
        },
        "stretch": {
            "instruction": (
                "Design a 3-prompt workflow that runs sequentially: (1) pull "
                "the latest waste data by department, (2) compare to the "
                "previous 4-week average and flag anomalies, (3) generate "
                "an email to each department manager with their specific "
                "waste issues and suggested actions."
            ),
            "scenario": (
                "You are the Head of Sustainability. Harris Farm has a target "
                "to reduce food waste by 15% this financial year. You need "
                "weekly accountability without manually reviewing every "
                "department."
            ),
            "added_constraint": (
                "Each email must be personalised with the department name, "
                "manager name, and their specific data. The anomaly "
                "threshold must be configurable (default: >20% above "
                "4-week average). Include a 'positive shout-out' for "
                "departments that improved."
            ),
            "success_criteria": (
                "3-step sequential workflow, parameterised thresholds, "
                "personalised outputs, positive reinforcement included, "
                "configurable design."
            ),
        },
        "elite": {
            "instruction": (
                "Design an end-to-end automated reporting system that: "
                "(1) runs nightly to collect data from sales, waste, "
                "staffing, and customer feedback systems, (2) produces a "
                "store-level daily brief for each of the 21 stores, (3) "
                "escalates critical issues to area managers automatically, "
                "and (4) compiles a weekly executive dashboard. Write the "
                "complete prompt chain with data specifications."
            ),
            "scenario": (
                "You are the CTO designing Harris Farm's 'Morning "
                "Intelligence' system. The Co-CEOs want every store "
                "manager to start their day with an AI-generated brief "
                "that tells them exactly what to focus on."
            ),
            "added_constraint": (
                "The system must handle missing data gracefully (some stores "
                "may have incomplete feeds). Escalation rules must be "
                "explicit (what triggers an alert to the area manager vs "
                "the store manager only). The weekly executive view must "
                "be a single page with drill-down links. Include error "
                "handling and a 'system health' check prompt."
            ),
            "success_criteria": (
                "4-stage pipeline design, graceful error handling, "
                "escalation rules defined, 21-store personalisation, "
                "executive rollup, system health monitoring."
            ),
            "rubric": "advanced",
        },
    },
}


# ---------------------------------------------------------------------------
# V3: L6 ENTERPRISE CHALLENGES
# ---------------------------------------------------------------------------
# Advanced challenges for users who have mastered L1-L5 and D1-D5.
# Scored by a panel rubric (peer + AI + manager review).
# ---------------------------------------------------------------------------

L6_ENTERPRISE_CHALLENGES = [
    {
        "code": "L6-1",
        "name": "Quality at Scale",
        "icon": "🏗️",
        "description": (
            "Design a quality assurance framework for AI outputs across "
            "all 21 Harris Farm stores."
        ),
        "brief": (
            "The Co-CEOs want to ensure that as AI usage scales from 5 "
            "pilot users to 200+ staff, output quality remains consistently "
            "high. Design a framework that includes: quality metrics, "
            "automated checks, human review triggers, feedback loops, and "
            "escalation paths. Your framework should work for prompts "
            "ranging from simple stock queries to complex competitor "
            "analyses."
        ),
        "rubric": "panel",
        "xp_reward": 100,
    },
    {
        "code": "L6-2",
        "name": "Hallucination Prevention",
        "icon": "🛡️",
        "description": (
            "Build a hallucination detection and prevention protocol for "
            "business-critical AI outputs."
        ),
        "brief": (
            "Harris Farm is increasingly using AI to generate reports that "
            "inform buying decisions worth $100K+. Design a protocol that: "
            "identifies hallucination risks by output type, establishes "
            "verification steps, creates a confidence rating system, and "
            "defines what to do when confidence is low. Include specific "
            "examples from HFM's buying, finance, and operations contexts."
        ),
        "rubric": "panel",
        "xp_reward": 100,
    },
    {
        "code": "L6-3",
        "name": "Data Governance Framework",
        "icon": "📊",
        "description": (
            "Create an AI data governance policy that balances innovation "
            "speed with data safety."
        ),
        "brief": (
            "As AI tools access more Harris Farm data (sales, customer, "
            "supplier, HR), design a governance framework that defines: "
            "who can access what data via AI, what data should never be "
            "fed to external AI, how to audit AI data access, and how to "
            "handle data breaches involving AI. Consider the needs of "
            "store managers, buyers, executives, and IT."
        ),
        "rubric": "panel",
        "xp_reward": 100,
    },
    {
        "code": "L6-4",
        "name": "Cross-Department AI Strategy",
        "icon": "🌐",
        "description": (
            "Design an AI adoption strategy that creates synergies across "
            "Harris Farm departments."
        ),
        "brief": (
            "Each department (Buying, Store Ops, Marketing, Finance, "
            "People & Culture) is using AI independently. Design a strategy "
            "that: identifies cross-department AI synergies, proposes shared "
            "prompt libraries and workflows, creates an internal AI "
            "marketplace, and measures collective impact. The strategy "
            "should show how insights from one department's AI usage can "
            "benefit others."
        ),
        "rubric": "panel",
        "xp_reward": 100,
    },
    {
        "code": "L6-5",
        "name": "ROI Measurement System",
        "icon": "💰",
        "description": (
            "Build a comprehensive ROI measurement system for Harris "
            "Farm's AI investment."
        ),
        "brief": (
            "The board wants to know: Is our AI investment paying off? "
            "Design a measurement system that captures: time saved, "
            "quality improvements, revenue impact, risk reduction, and "
            "employee capability growth. Include specific KPIs for each "
            "department, a dashboard mockup description, and a quarterly "
            "reporting template. Address both hard ROI (dollars) and soft "
            "ROI (capability, speed, quality)."
        ),
        "rubric": "panel",
        "xp_reward": 100,
    },
    {
        "code": "L6-6",
        "name": "AI Ethics & Policy Design",
        "icon": "⚖️",
        "description": (
            "Draft Harris Farm's AI ethics policy and responsible use "
            "guidelines."
        ),
        "brief": (
            "Harris Farm needs an AI ethics policy before scaling to 200+ "
            "users. Design a policy that covers: acceptable use cases, "
            "prohibited uses, transparency requirements (when to disclose "
            "AI use), bias monitoring, environmental impact, and staff "
            "rights regarding AI in the workplace. The policy should be "
            "practical enough for a store manager to follow, yet "
            "comprehensive enough for board governance."
        ),
        "rubric": "panel",
        "xp_reward": 100,
    },
]


# ---------------------------------------------------------------------------
# V3: DAILY MICRO-CHALLENGE SEED POOL
# ---------------------------------------------------------------------------
# 30 quick-fire questions for the daily challenge system. Each is answerable
# in under 90 seconds. Topics: fundamentals (10), role-specific (5),
# data + AI (5), rubric knowledge (5), ethics & best practices (5).
# ---------------------------------------------------------------------------

DAILY_MICRO_POOL = [
    # ------------------------------------------------------------------
    # FUNDAMENTALS (10)
    # ------------------------------------------------------------------
    {
        "question": (
            "Which element is MISSING from this prompt: "
            "'Tell me about our sales'?"
        ),
        "options": [
            "Task clarity",
            "All four elements are missing",
            "Just the format",
            "Just the context",
        ],
        "correct_answer": "All four elements are missing",
        "topic": "fundamentals",
        "time_limit": 90,
    },
    {
        "question": (
            "What is the TASK verb in this prompt: 'Compare Crows Nest "
            "and Mosman Fruit & Veg revenue for the last 4 weeks'?"
        ),
        "options": [
            "Crows Nest",
            "Compare",
            "Revenue",
            "4 weeks",
        ],
        "correct_answer": "Compare",
        "topic": "fundamentals",
        "time_limit": 90,
    },
    {
        "question": (
            "Which of these is a CONSTRAINT, not a format instruction? "
            "'Exclude online orders from the analysis.'"
        ),
        "options": [
            "It is a format instruction",
            "It is a constraint",
            "It is context",
            "It is a task",
        ],
        "correct_answer": "It is a constraint",
        "topic": "fundamentals",
        "time_limit": 90,
    },
    {
        "question": (
            "A store manager writes: 'Summarise last week for my store.' "
            "What is the BIGGEST problem with this prompt?"
        ),
        "options": [
            "No task verb",
            "No format specified",
            "No store name or metric specified",
            "Too short",
        ],
        "correct_answer": "No store name or metric specified",
        "topic": "fundamentals",
        "time_limit": 90,
    },
    {
        "question": (
            "Which of these is the BEST format instruction?"
        ),
        "options": [
            "'Make it useful'",
            "'A summary'",
            "'Table with columns: Product, Units, Revenue, WoW Change %'",
            "'Something I can use in a meeting'",
        ],
        "correct_answer": (
            "'Table with columns: Product, Units, Revenue, WoW Change %'"
        ),
        "topic": "fundamentals",
        "time_limit": 90,
    },
    {
        "question": (
            "True or False: 'Write a 200-word email' contains both a "
            "task and a constraint."
        ),
        "options": [
            "True -- 'write' is the task, '200 words' is the constraint",
            "False -- it only contains a task",
            "False -- it only contains a constraint",
            "True -- but only if you add context",
        ],
        "correct_answer": (
            "True -- 'write' is the task, '200 words' is the constraint"
        ),
        "topic": "fundamentals",
        "time_limit": 90,
    },
    {
        "question": (
            "You want AI to produce output for a Monday store meeting. "
            "Which element does 'Monday store meeting' belong to?"
        ),
        "options": [
            "Task",
            "Context",
            "Format",
            "Constraint",
        ],
        "correct_answer": "Context",
        "topic": "fundamentals",
        "time_limit": 90,
    },
    {
        "question": (
            "Which prompt is MORE specific? (A) 'Analyse store sales' or "
            "(B) 'Analyse Dee Why store F&V sales for week ending 16 Feb "
            "2026'?"
        ),
        "options": [
            "A -- it covers more ground",
            "B -- it names the store, category, and date",
            "Both are equally specific",
            "Neither is specific enough",
        ],
        "correct_answer": "B -- it names the store, category, and date",
        "topic": "fundamentals",
        "time_limit": 90,
    },
    {
        "question": (
            "What does adding 'I am the Fresh Buyer preparing for the "
            "weekly buying meeting' to a prompt improve?"
        ),
        "options": [
            "Clarity",
            "Context",
            "Format",
            "Constraints",
        ],
        "correct_answer": "Context",
        "topic": "fundamentals",
        "time_limit": 90,
    },
    {
        "question": (
            "'Sort by largest decline first. Maximum 10 rows.' These "
            "instructions improve which TWO elements?"
        ),
        "options": [
            "Task and Context",
            "Format and Constraints",
            "Context and Format",
            "Task and Constraints",
        ],
        "correct_answer": "Format and Constraints",
        "topic": "fundamentals",
        "time_limit": 90,
    },

    # ------------------------------------------------------------------
    # ROLE-SPECIFIC APPLICATIONS (5)
    # ------------------------------------------------------------------
    {
        "question": (
            "A BUYER and a STORE MANAGER both need to address avocado "
            "shortages. What should differ between their prompts?"
        ),
        "options": [
            "Nothing -- the same prompt works for both",
            "The role context, data requested, and action type",
            "Only the store name",
            "Only the format",
        ],
        "correct_answer": "The role context, data requested, and action type",
        "topic": "role_specific",
        "time_limit": 90,
    },
    {
        "question": (
            "Which role would MOST benefit from a prompt that includes "
            "supplier lead times and minimum order quantities?"
        ),
        "options": [
            "Store Manager",
            "Buyer",
            "Marketing Manager",
            "People & Culture Lead",
        ],
        "correct_answer": "Buyer",
        "topic": "role_specific",
        "time_limit": 90,
    },
    {
        "question": (
            "A Marketing Manager writes a prompt about an upcoming "
            "campaign. What context element is MOST important for them "
            "to include?"
        ),
        "options": [
            "Supplier payment terms",
            "Target customer segment and campaign objective",
            "Store opening hours",
            "Waste reduction targets",
        ],
        "correct_answer": "Target customer segment and campaign objective",
        "topic": "role_specific",
        "time_limit": 90,
    },
    {
        "question": (
            "An Operations Lead asks AI to 'optimise delivery routes'. "
            "What critical context is missing?"
        ),
        "options": [
            "The AI model to use",
            "Number of stores, vehicle capacity, and time windows",
            "The brand colours",
            "The CEO's name",
        ],
        "correct_answer": (
            "Number of stores, vehicle capacity, and time windows"
        ),
        "topic": "role_specific",
        "time_limit": 90,
    },
    {
        "question": (
            "The People & Culture team wants AI to draft interview "
            "questions. Which constraint is MOST important to include?"
        ),
        "options": [
            "'Maximum 500 words'",
            "'Use bullet points'",
            "'Questions must comply with Australian employment law'",
            "'Include a table'",
        ],
        "correct_answer": (
            "'Questions must comply with Australian employment law'"
        ),
        "topic": "role_specific",
        "time_limit": 90,
    },

    # ------------------------------------------------------------------
    # DATA + AI (5)
    # ------------------------------------------------------------------
    {
        "question": (
            "You want to compare Harris Farm's market share in Bondi vs "
            "last year. What is the correct comparison approach?"
        ),
        "options": [
            "Compare this month to last month",
            "Compare same month year-on-year",
            "Compare total annual figures",
            "Compare week by week",
        ],
        "correct_answer": "Compare same month year-on-year",
        "topic": "data_ai",
        "time_limit": 90,
    },
    {
        "question": (
            "Market share data shows a postcode has 1.2% HFM share. "
            "Is this definitely an expansion opportunity?"
        ),
        "options": [
            "Yes -- low share means high opportunity",
            "No -- low share could mean distance, demographics, or travel "
            "patterns make it unsuitable",
            "Yes -- if the market size is large",
            "Only if it is within 3km of a store",
        ],
        "correct_answer": (
            "No -- low share could mean distance, demographics, or travel "
            "patterns make it unsuitable"
        ),
        "topic": "data_ai",
        "time_limit": 90,
    },
    {
        "question": (
            "Why should you NEVER cross-reference market share dollar "
            "values with POS revenue data?"
        ),
        "options": [
            "They use different currencies",
            "Market share is Layer 2 (modelled estimates), POS is Layer 1 "
            "(actual transactions) -- they measure different things",
            "POS data is always wrong",
            "Market share data is always higher",
        ],
        "correct_answer": (
            "Market share is Layer 2 (modelled estimates), POS is Layer 1 "
            "(actual transactions) -- they measure different things"
        ),
        "topic": "data_ai",
        "time_limit": 90,
    },
    {
        "question": (
            "You write a prompt asking AI to analyse sales data. What "
            "should you ALWAYS specify about the time range?"
        ),
        "options": [
            "Just say 'recently'",
            "Name the exact start and end dates or week numbers",
            "Say 'last few weeks'",
            "Let the AI decide what time range to use",
        ],
        "correct_answer": (
            "Name the exact start and end dates or week numbers"
        ),
        "topic": "data_ai",
        "time_limit": 90,
    },
    {
        "question": (
            "A prompt asks AI to 'find trends in our data'. What makes "
            "this a WEAK data prompt?"
        ),
        "options": [
            "It is too short",
            "It does not specify which data, which metrics, or what time "
            "period to examine",
            "It uses the word 'trends'",
            "'Find' is not a valid task verb",
        ],
        "correct_answer": (
            "It does not specify which data, which metrics, or what time "
            "period to examine"
        ),
        "topic": "data_ai",
        "time_limit": 90,
    },

    # ------------------------------------------------------------------
    # RUBRIC KNOWLEDGE (5)
    # ------------------------------------------------------------------
    {
        "question": (
            "In the 5-criteria rubric, what does a score of 3/5 for "
            "'Context Provision' mean?"
        ),
        "options": [
            "No context at all",
            "Some context but missing store, department, or business reason",
            "Rich, complete context",
            "Context is perfect but format is missing",
        ],
        "correct_answer": (
            "Some context but missing store, department, or business reason"
        ),
        "topic": "rubric",
        "time_limit": 90,
    },
    {
        "question": (
            "A prompt scores: Clarity 4, Context 5, Data Spec 2, "
            "Format 4, Actionability 4. Total = 19. What should the "
            "author improve FIRST?"
        ),
        "options": [
            "Clarity -- it is not perfect",
            "Data Specification -- it is the weakest criterion",
            "Format -- tables are always better",
            "Nothing -- 19 is a passing score",
        ],
        "correct_answer": (
            "Data Specification -- it is the weakest criterion"
        ),
        "topic": "rubric",
        "time_limit": 90,
    },
    {
        "question": (
            "What is the passing threshold on the Skills Academy rubric?"
        ),
        "options": [
            "15 out of 25",
            "18 out of 25",
            "20 out of 25",
            "22 out of 25",
        ],
        "correct_answer": "18 out of 25",
        "topic": "rubric",
        "time_limit": 90,
    },
    {
        "question": (
            "'Actionability' scores highest when the prompt output will:"
        ),
        "options": [
            "Be interesting to read",
            "Directly drive a named decision or next step",
            "Include lots of data",
            "Be formatted as a table",
        ],
        "correct_answer": "Directly drive a named decision or next step",
        "topic": "rubric",
        "time_limit": 90,
    },
    {
        "question": (
            "A prompt says 'give me some data about sales'. What would "
            "the Data Specification criterion likely score?"
        ),
        "options": [
            "5 -- it mentions data",
            "4 -- close enough",
            "2 -- implies data is needed but does not specify what",
            "1 -- no reference to data at all",
        ],
        "correct_answer": (
            "2 -- implies data is needed but does not specify what"
        ),
        "topic": "rubric",
        "time_limit": 90,
    },

    # ------------------------------------------------------------------
    # ETHICS & BEST PRACTICES (5)
    # ------------------------------------------------------------------
    {
        "question": (
            "A colleague pastes a full customer complaint (with name, "
            "email, phone number) into ChatGPT. What is the MAIN risk?"
        ),
        "options": [
            "The AI will give a bad response",
            "Personal customer data is being sent to an external AI service",
            "The prompt is too long",
            "ChatGPT does not understand complaints",
        ],
        "correct_answer": (
            "Personal customer data is being sent to an external AI service"
        ),
        "topic": "ethics",
        "time_limit": 90,
    },
    {
        "question": (
            "AI generates a report saying 'Harris Farm's revenue was "
            "$850M last year'. You are unsure. What should you do?"
        ),
        "options": [
            "Trust the AI -- it is usually right",
            "Verify against an internal source before sharing the number",
            "Round it to $800M to be safe",
            "Delete the number and leave the rest of the report",
        ],
        "correct_answer": (
            "Verify against an internal source before sharing the number"
        ),
        "topic": "ethics",
        "time_limit": 90,
    },
    {
        "question": (
            "When should you disclose that a document was generated with "
            "AI assistance?"
        ),
        "options": [
            "Never -- it is embarrassing",
            "Only if someone asks",
            "When the output will inform decisions or be shared externally",
            "Only for legal documents",
        ],
        "correct_answer": (
            "When the output will inform decisions or be shared externally"
        ),
        "topic": "ethics",
        "time_limit": 90,
    },
    {
        "question": (
            "Which of these should NEVER be pasted into an external AI "
            "tool like ChatGPT?"
        ),
        "options": [
            "A generic product description",
            "Staff payroll data and personal details",
            "A request to summarise a public news article",
            "A draft marketing headline",
        ],
        "correct_answer": "Staff payroll data and personal details",
        "topic": "ethics",
        "time_limit": 90,
    },
    {
        "question": (
            "AI suggests Harris Farm should stop stocking a product "
            "category entirely. What is the best response?"
        ),
        "options": [
            "Follow the recommendation immediately",
            "Treat it as one input, validate with actual data and domain "
            "expertise before acting",
            "Ignore AI recommendations entirely",
            "Ask the AI again to double-check",
        ],
        "correct_answer": (
            "Treat it as one input, validate with actual data and domain "
            "expertise before acting"
        ),
        "topic": "ethics",
        "time_limit": 90,
    },
]
