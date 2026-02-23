"""
Skills Academy v4 — Curveball Exercises
========================================
25 curveball exercises (5 per level, levels 1-5) for the Woven Verification
system. Curveballs are surprise exercises woven into the normal learning flow
every 3rd-4th exercise. They test deeper understanding with unexpected twists.

Python 3.9 compatible.
"""

from typing import Dict, List

# ---------------------------------------------------------------------------
# Context tags (the 8 standard tags used across SA v4)
# ---------------------------------------------------------------------------
# operations, buying, finance, marketing, people, logistics, digital, strategy

# ---------------------------------------------------------------------------
# LEVEL 1 CURVEBALLS — "I can talk to AI"
# Tests: Do they recognise ambiguity, negotiate constraints, spot when AI is
# the wrong tool, look past the obvious question, and choose the right format?
# ---------------------------------------------------------------------------

_LEVEL_1_CURVEBALLS = [
    # CB-L1-1: Ambiguity — two valid interpretations
    {
        "curveball_code": "CB-L1-1",
        "curveball_type": "ambiguity",
        "level": 1,
        "exercise_title": "The Mango Order That Could Go Either Way",
        "scenario_text": (
            "You are a team member at Harris Farm Drummoyne. Your store manager "
            "sends you this message on a Monday morning:\n\n"
            "\"We need to double our mango order this week.\"\n\n"
            "You open Claude to write a prompt that will help you action this. "
            "But wait — what does 'double' actually mean here?\n\n"
            "Option A: Double the quantity from last week's order (if last week "
            "was 50 trays, order 100).\n"
            "Option B: Double the standing weekly order (if the standing order is "
            "40 trays, order 80 — regardless of what was actually ordered last week).\n\n"
            "These could produce very different numbers. Last week was a long "
            "weekend and the order was already inflated.\n\n"
            "Write the prompt you would use — but first, explain what you would "
            "do BEFORE writing the prompt. What is the right first step here?"
        ),
        "coaching_text": (
            "Great instinct to want to jump straight into AI — but this is a "
            "classic case where the most important skill is asking a clarifying "
            "question BEFORE you prompt. The store manager's instruction is "
            "ambiguous: 'double' could mean double last week's actual order or "
            "double the standing order. These are very different numbers, "
            "especially after a long weekend.\n\n"
            "The right first step is always: go back to the source and clarify. "
            "A 30-second conversation saves a potentially costly ordering mistake. "
            "AI is brilliant at executing clear instructions — but it cannot read "
            "your manager's mind. The 4 Elements start with a clear TASK, and you "
            "cannot define a clear task until you know what 'double' means.\n\n"
            "Next time you spot ambiguity, pause and ask before you prompt."
        ),
        "scoring_criteria": (
            "Score 1-5 based on whether the user recognised the ambiguity:\n"
            "5: Explicitly states they would ask the store manager to clarify "
            "before writing any prompt. Identifies both interpretations and "
            "explains why the distinction matters (long weekend inflation).\n"
            "4: Recognises the ambiguity and mentions checking, but does not "
            "clearly articulate both interpretations.\n"
            "3: Writes a reasonable prompt but adds a caveat about needing "
            "clarification as an afterthought.\n"
            "2: Writes a prompt that assumes one interpretation without "
            "acknowledging the ambiguity exists.\n"
            "1: Writes a prompt that blindly doubles a number without any "
            "awareness that the instruction is unclear."
        ),
        "pass_threshold": 3.5,
        "context_tag": "operations",
    },

    # CB-L1-2: Contradictory constraints
    {
        "curveball_code": "CB-L1-2",
        "curveball_type": "contradictory_constraints",
        "level": 1,
        "exercise_title": "The Impossible Roster Request",
        "scenario_text": (
            "You are the assistant store manager at Harris Farm Crows Nest. "
            "Your store manager gives you these instructions for this week's "
            "roster:\n\n"
            "1. Cut total wage hours by 15% to hit budget.\n"
            "2. Ensure every department has full coverage from 7am to 9pm.\n"
            "3. No team member works more than 5 days.\n"
            "4. The new team member must get at least 4 training shifts with "
            "a senior.\n\n"
            "You quickly realise these four constraints cannot all be satisfied "
            "simultaneously — cutting 15% of hours while maintaining full "
            "coverage and adding training shifts is a contradiction.\n\n"
            "Write a prompt to Claude that addresses this situation. How do you "
            "handle the tension between these requirements?"
        ),
        "coaching_text": (
            "This is a real-world tension that happens every week in stores. "
            "The key insight is: when constraints contradict each other, the "
            "right move is to negotiate priorities, not pretend they all fit.\n\n"
            "A strong response would ask Claude to help rank and trade off the "
            "constraints — for example: 'Given these 4 requirements, which "
            "combinations are feasible? What is the minimum hour reduction that "
            "still allows full coverage? What if we reduce coverage in the "
            "slowest 2-hour window instead?'\n\n"
            "The worst response is to write a prompt that ignores the conflict "
            "and asks Claude to 'just make a roster that does all four.' AI will "
            "try to comply and produce something that looks right but quietly "
            "breaks one or more constraints. You need to be the one who spots "
            "the tension and decides how to resolve it — then use AI to execute "
            "that decision."
        ),
        "scoring_criteria": (
            "Score 1-5 based on how the user handles the contradictory constraints:\n"
            "5: Explicitly identifies the contradiction, asks Claude to analyse "
            "trade-offs, proposes a priority order, and asks for the best "
            "feasible solution given that priority. May suggest going back to "
            "the store manager with options.\n"
            "4: Identifies the tension and asks Claude to explore scenarios, "
            "but does not clearly prioritise which constraint to relax.\n"
            "3: Acknowledges difficulty but still tries to satisfy all four "
            "constraints, perhaps asking Claude to 'try its best.'\n"
            "2: Writes a prompt that includes all four constraints as hard "
            "requirements without acknowledging the conflict.\n"
            "1: Copies the four requirements into a prompt verbatim and asks "
            "Claude to produce the roster."
        ),
        "pass_threshold": 3.5,
        "context_tag": "operations",
    },

    # CB-L1-3: AI is the wrong tool
    {
        "curveball_code": "CB-L1-3",
        "curveball_type": "wrong_tool",
        "level": 1,
        "exercise_title": "The Expired Chicken Emergency",
        "scenario_text": (
            "You are working the deli counter at Harris Farm Bondi Beach. "
            "A customer approaches, visibly upset, holding a pack of chicken "
            "thighs they purchased yesterday. The use-by date is today, but "
            "the chicken smells off and looks discoloured. The customer says "
            "they are feeling unwell after eating some of it last night.\n\n"
            "Your team leader is on break. You think about using Claude to "
            "help you handle this situation — maybe to draft a response, "
            "check food safety guidelines, or figure out the refund process.\n\n"
            "What do you do? Write your prompt, or explain why you would not "
            "use AI here."
        ),
        "coaching_text": (
            "This is a situation where AI is absolutely the wrong tool — and "
            "recognising that is the skill being tested.\n\n"
            "A customer reporting illness from a food product is a food safety "
            "incident. It requires immediate human action:\n"
            "1. Apologise to the customer and take the product.\n"
            "2. Offer a full refund immediately.\n"
            "3. Pull the same batch from the shelf RIGHT NOW.\n"
            "4. Call the duty manager / store manager immediately.\n"
            "5. Log the incident in the food safety register.\n"
            "6. If the customer is seriously unwell, suggest they see a doctor.\n\n"
            "None of this should wait for you to open a laptop and type a prompt. "
            "Speed matters. Human judgment matters. Empathy matters. The store's "
            "food safety procedures exist for exactly this moment.\n\n"
            "AI is powerful, but it is not a substitute for acting decisively "
            "when safety is at stake. Know when to close the laptop."
        ),
        "scoring_criteria": (
            "Score 1-5 based on whether the user recognises AI is not appropriate:\n"
            "5: Clearly states they would NOT use AI. Lists the immediate human "
            "actions required (refund, pull batch, escalate to manager, food "
            "safety register). Explains WHY speed and human judgment matter here.\n"
            "4: States they would not use AI for the immediate response but "
            "might use it later (e.g., to draft an incident report). Shows "
            "awareness of food safety urgency.\n"
            "3: Hesitates but ultimately decides to handle it without AI, with "
            "partial awareness of the food safety implications.\n"
            "2: Writes a prompt to Claude asking how to handle the situation, "
            "showing they would pause to consult AI during a safety incident.\n"
            "1: Writes a detailed prompt about food safety procedures or "
            "customer communication, treating this as a normal AI exercise."
        ),
        "pass_threshold": 3.5,
        "context_tag": "operations",
    },

    # CB-L1-4: Vague task — the obvious prompt misses the real question
    {
        "curveball_code": "CB-L1-4",
        "curveball_type": "vague_task",
        "level": 1,
        "exercise_title": "The Sales Are Down Email",
        "scenario_text": (
            "You are a team leader at Harris Farm Mosman. The area manager "
            "sends an email to all stores:\n\n"
            "\"Hi team, sales are down across the network this month. Please "
            "look into what's happening at your store and send me a summary "
            "by Friday.\"\n\n"
            "You decide to use Claude to help. The obvious prompt would be: "
            "'Why are sales down at Harris Farm Mosman this month?'\n\n"
            "Write the prompt you would actually use. Think carefully about "
            "what the area manager really needs — is the obvious prompt the "
            "right one?"
        ),
        "coaching_text": (
            "The obvious prompt — 'Why are sales down?' — is a trap. Claude "
            "does not have access to your store's live sales data, so it would "
            "either hallucinate reasons or give you generic retail advice.\n\n"
            "The real question is not 'why are sales down?' — that requires "
            "actual data analysis. The real task is: 'Help me structure an "
            "investigation that I can do with the data I have access to.'\n\n"
            "A strong prompt would ask Claude to help you create a checklist "
            "of things to investigate: foot traffic patterns, weather events, "
            "competitor activity, product availability issues, any recent range "
            "changes, local construction or road closures. Then you go and "
            "actually check these things using real data from The Hub.\n\n"
            "The lesson: when the question requires real data you have but "
            "Claude does not, use AI to structure your thinking, not to answer "
            "the question directly."
        ),
        "scoring_criteria": (
            "Score 1-5 based on whether they see past the obvious question:\n"
            "5: Recognises that Claude lacks the data to explain sales. Writes "
            "a prompt asking for a structured investigation framework or "
            "checklist. Plans to use The Hub for actual data. Considers multiple "
            "possible causes.\n"
            "4: Asks Claude for an investigation structure but does not clearly "
            "distinguish between what Claude can and cannot know.\n"
            "3: Writes a reasonable but generic prompt like 'List reasons sales "
            "might be down at a grocery store' without connecting it to specific "
            "data sources or investigation steps.\n"
            "2: Asks Claude directly why sales are down, perhaps adding some "
            "context about the store.\n"
            "1: Writes the obvious prompt — 'Why are sales down at Mosman?' — "
            "expecting Claude to provide the answer."
        ),
        "pass_threshold": 3.5,
        "context_tag": "operations",
    },

    # CB-L1-5: Format trap — requested format is wrong for the audience
    {
        "curveball_code": "CB-L1-5",
        "curveball_type": "format_trap",
        "level": 1,
        "exercise_title": "The Spreadsheet That Should Be a Story",
        "scenario_text": (
            "Your store manager at Harris Farm Hornsby asks you to prepare a "
            "summary of last week's department performance for the weekly team "
            "meeting. They specifically say:\n\n"
            "\"Put it in a detailed spreadsheet with all the numbers — sales, "
            "margins, shrink, labour cost, basket size, transactions — for "
            "every department.\"\n\n"
            "The team meeting has 15 people: department leads, part-time team "
            "members, and two new starters who joined last week. The meeting "
            "is 30 minutes and covers 5 topics.\n\n"
            "Write the prompt you would use to prepare this. Consider: is the "
            "requested format actually the right one for this audience and "
            "situation?"
        ),
        "coaching_text": (
            "The store manager asked for a detailed spreadsheet — but think "
            "about the audience. Fifteen people in a 30-minute meeting covering "
            "5 topics means roughly 6 minutes for this item. A dense spreadsheet "
            "with dozens of numbers across every department will not land.\n\n"
            "The right format for this audience is a simple visual summary: "
            "3-5 key wins, 1-2 areas to watch, and maybe one call-to-action. "
            "New starters will not understand margin percentages. Part-timers "
            "need to know what to focus on, not analyse a data table.\n\n"
            "The deeper skill here is format awareness: matching the output "
            "format to the audience, not just to the request. A strong response "
            "would note the mismatch and suggest an alternative, while still "
            "offering to produce the detailed spreadsheet separately for the "
            "manager's own reference.\n\n"
            "Always ask: who is reading this, how much time do they have, and "
            "what decision does it need to support?"
        ),
        "scoring_criteria": (
            "Score 1-5 based on format awareness:\n"
            "5: Identifies that the spreadsheet format is wrong for the audience. "
            "Suggests an alternative (visual summary, top 3 wins, traffic-light "
            "dashboard). Offers to produce the detailed spreadsheet separately "
            "for the manager. Shows understanding of audience needs.\n"
            "4: Notes the audience mismatch and adjusts the prompt, but does "
            "not fully articulate why or offer both formats.\n"
            "3: Writes a prompt for a simplified spreadsheet (fewer columns, "
            "highlights) but does not fundamentally question the format.\n"
            "2: Writes a prompt for exactly what was requested — a detailed "
            "spreadsheet — with some formatting niceties.\n"
            "1: Copies the request directly into a prompt and asks Claude to "
            "produce the spreadsheet with all the numbers."
        ),
        "pass_threshold": 3.5,
        "context_tag": "operations",
    },
]

# ---------------------------------------------------------------------------
# LEVEL 2 CURVEBALLS — "I use AI daily in my role"
# Tests: Do they catch hallucinations, notice data boundaries, push back on
# wrong AI advice, spot role mismatches, and check data freshness?
# ---------------------------------------------------------------------------

_LEVEL_2_CURVEBALLS = [
    # CB-L2-1: Hallucination — plausible but wrong number
    {
        "curveball_code": "CB-L2-1",
        "curveball_type": "hallucination",
        "level": 2,
        "exercise_title": "The Confident but Wrong Shrink Number",
        "scenario_text": (
            "You are a buyer responsible for the bakery category. You asked "
            "Claude to summarise last month's shrink performance across the "
            "network. Claude responds confidently:\n\n"
            "\"Based on the data, bakery shrink across the Harris Farm network "
            "averaged 14.2% last month, which is a 2.1 percentage point "
            "improvement from the prior month's 16.3%. The best-performing "
            "store was Brookvale at 8.1%, while Leichhardt had the highest "
            "shrink at 22.7%. This improvement was driven primarily by the "
            "new bread markdown protocol introduced on the 15th.\"\n\n"
            "This response sounds detailed and specific. The numbers are "
            "plausible for bakery shrink. The markdown protocol was real.\n\n"
            "You are about to include these numbers in your monthly category "
            "review for the buying team meeting tomorrow. What do you do?"
        ),
        "coaching_text": (
            "This is a hallucination trap — and it is especially dangerous "
            "because the numbers are plausible. Bakery shrink of 14.2% is "
            "within normal range. The improvement narrative sounds logical. "
            "The markdown protocol is real. But Claude does not have access "
            "to Harris Farm's actual shrink data.\n\n"
            "Every single number in that response is fabricated. Claude "
            "generated realistic-sounding figures because it knows what "
            "typical bakery shrink looks like, but it has zero knowledge of "
            "actual Harris Farm performance.\n\n"
            "The rule is simple: NEVER use AI-generated numbers in a business "
            "report without verifying them against the source system. For "
            "shrink data, that means checking The Hub or the actual store "
            "reports. If you cannot verify it, do not include it.\n\n"
            "A useful approach: ask Claude to help you structure the analysis "
            "or interpret numbers YOU provide, rather than asking it to "
            "generate the numbers."
        ),
        "scoring_criteria": (
            "Score 1-5 based on whether they catch the hallucination:\n"
            "5: Immediately flags that Claude cannot know actual shrink data. "
            "States they would verify every number against The Hub or source "
            "reports before using them. Explains the hallucination risk — "
            "plausible numbers are the most dangerous kind.\n"
            "4: Recognises they need to verify the data but does not "
            "specifically call out that Claude fabricated all the numbers.\n"
            "3: Expresses some skepticism and plans to 'check a few numbers' "
            "but would still use the overall narrative.\n"
            "2: Notes that the numbers 'might be slightly off' but would use "
            "them as approximate figures or round them.\n"
            "1: Accepts the output as-is and plans to include it in the "
            "category review."
        ),
        "pass_threshold": 3.5,
        "context_tag": "buying",
    },

    # CB-L2-2: Confidential data boundary
    {
        "curveball_code": "CB-L2-2",
        "curveball_type": "confidential_data",
        "level": 2,
        "exercise_title": "The Salary Benchmarking Request",
        "scenario_text": (
            "You work in People & Culture at Harris Farm. Your manager asks "
            "you to use Claude to help prepare a salary benchmarking report "
            "for the upcoming annual review cycle. They want you to:\n\n"
            "1. List current salaries for all store managers by name.\n"
            "2. Compare them to industry benchmarks.\n"
            "3. Flag anyone who is more than 10% below market rate.\n"
            "4. Draft talking points for each manager's review meeting.\n\n"
            "You have access to the salary data in the HRIS system. Write "
            "the prompt you would use to get Claude's help with this task.\n\n"
            "Think carefully about what information should and should not go "
            "into a Claude prompt."
        ),
        "coaching_text": (
            "This task is legitimate — salary benchmarking is important P&C "
            "work. But the way it is framed would require you to paste "
            "individual employees' names and salaries into Claude.\n\n"
            "That is a data boundary you must not cross. Individual salary "
            "data is highly confidential. Pasting 'Sarah earns $85K, Tom "
            "earns $92K' into an external AI tool is a serious breach of "
            "employee privacy, regardless of how useful the output might be.\n\n"
            "The right approach:\n"
            "- Use Claude for the GENERIC parts: industry benchmark research, "
            "  report structure, talking point templates.\n"
            "- Use ANONYMISED data if you need analytical help: 'Store Manager "
            "  A earns $X, Store Manager B earns $Y' or use role-level "
            "  averages rather than individual data.\n"
            "- Keep all personally identifiable salary data in the HRIS system "
            "  where it belongs.\n"
            "- Do the name-to-salary matching offline, not in AI.\n\n"
            "AI literacy includes knowing what data stays inside the fence."
        ),
        "scoring_criteria": (
            "Score 1-5 based on data boundary awareness:\n"
            "5: Explicitly states that individual names and salaries must NOT "
            "be entered into Claude. Proposes anonymisation or aggregation. "
            "Separates generic AI tasks (benchmarks, templates) from "
            "confidential tasks (individual salary analysis). References "
            "employee privacy.\n"
            "4: Avoids putting names into the prompt but does not clearly "
            "articulate the privacy principle. Uses some anonymisation.\n"
            "3: Puts role titles and salaries in but removes names, showing "
            "partial awareness without fully understanding the boundary.\n"
            "2: Includes names with salaries but asks Claude to 'keep it "
            "confidential' — not understanding that the data has already "
            "left the building.\n"
            "1: Pastes the full salary list with names into the prompt as "
            "requested."
        ),
        "pass_threshold": 3.5,
        "context_tag": "people",
    },

    # CB-L2-3: AI recommendation contradicts experience
    {
        "curveball_code": "CB-L2-3",
        "curveball_type": "experience_conflict",
        "level": 2,
        "exercise_title": "The AI Says Drop Organic — But You Know Better",
        "scenario_text": (
            "You are a buyer managing the dairy category. You asked Claude to "
            "analyse your organic milk range performance and suggest "
            "optimisations. Claude responds:\n\n"
            "\"Based on the margin data you provided, organic milk lines "
            "generate 18% lower margin than conventional equivalents across "
            "all stores. The top recommendation is to reduce the organic "
            "range by 40% and reallocate shelf space to higher-margin "
            "conventional lines. This could improve category margin by an "
            "estimated $45K annually.\"\n\n"
            "The margin numbers Claude calculated from your data are correct. "
            "But you have been buying dairy at Harris Farm for 3 years and "
            "you know that:\n"
            "- Organic customers spend 2.3x more per visit than conventional.\n"
            "- Harris Farm's brand positioning is built on 'real food' and "
            "  ethical sourcing.\n"
            "- Last time organic range was cut (2 years ago at Bondi Beach), "
            "  basket size dropped 15% within 6 weeks.\n\n"
            "How do you respond to Claude's recommendation? Write what you "
            "would do next."
        ),
        "coaching_text": (
            "Claude did the maths correctly — organic milk IS lower margin "
            "in isolation. But the recommendation is dangerously narrow. This "
            "is a case where your domain expertise should override an AI "
            "recommendation, and the right skill is knowing HOW to push back "
            "constructively.\n\n"
            "The problems with Claude's recommendation:\n"
            "1. It optimises one metric (category margin) while ignoring the "
            "   bigger picture (basket size, customer lifetime value).\n"
            "2. It does not account for Harris Farm's brand strategy — we are "
            "   not Coles or Woolworths competing on price.\n"
            "3. It has no memory of the Bondi Beach precedent.\n\n"
            "The right response is to tell Claude what it missed and iterate: "
            "'Your margin analysis is correct, but factor in these additional "
            "considerations: organic customers' total basket value, brand "
            "alignment, and the historical precedent from Bondi Beach. Now "
            "re-analyse with total customer value, not just line margin.'\n\n"
            "AI gives you a first draft. Your experience makes it right."
        ),
        "scoring_criteria": (
            "Score 1-5 based on whether they push back with evidence:\n"
            "5: Clearly states the recommendation is wrong despite correct "
            "maths. Provides specific counter-evidence (basket size, brand, "
            "precedent). Iterates with Claude by adding the missing context "
            "and asking for a revised analysis. Does not dismiss AI entirely.\n"
            "4: Pushes back and provides some counter-reasoning but does not "
            "iterate with Claude to produce a better recommendation.\n"
            "3: Expresses doubt and decides to 'do their own analysis' "
            "without engaging Claude further — missing the iteration "
            "opportunity.\n"
            "2: Reluctantly accepts the recommendation because 'the data "
            "says so' despite their experience.\n"
            "1: Accepts the recommendation without question and plans to "
            "present it to the category manager."
        ),
        "pass_threshold": 3.5,
        "context_tag": "buying",
    },

    # CB-L2-4: Role mismatch — prompt does not match the user's role
    {
        "curveball_code": "CB-L2-4",
        "curveball_type": "role_mismatch",
        "level": 2,
        "exercise_title": "The Store Manager Writing a CFO Report",
        "scenario_text": (
            "You are a store manager at Harris Farm Neutral Bay. The regional "
            "manager asks you to prepare a financial performance summary for "
            "your store that will be included in a pack going to the CFO.\n\n"
            "You write this prompt for Claude:\n\n"
            "\"Act as a senior financial analyst. Produce a detailed P&L "
            "variance analysis for Harris Farm Neutral Bay for Q3 FY2026 "
            "with year-on-year EBITDA margin comparison, working capital "
            "impact assessment, and sensitivity analysis on three scenarios. "
            "Include a waterfall chart breakdown of gross-to-net margin "
            "drivers and flag any AASB compliance considerations.\"\n\n"
            "Before you send this prompt, review it. Is this the right prompt "
            "for someone in YOUR role? What would you change?"
        ),
        "coaching_text": (
            "The prompt is technically well-structured — it has a clear role, "
            "specific deliverables, and format requirements. The problem is "
            "that it does not match YOUR role or expertise.\n\n"
            "As a store manager, you are an expert on what is happening in "
            "your store: foot traffic trends, staffing challenges, product "
            "availability, customer feedback, local competition. You are NOT "
            "a financial analyst — and if you prompt Claude as one, you will "
            "get output you cannot verify, explain, or defend.\n\n"
            "Imagine the CFO asks a follow-up question about the EBITDA "
            "variance. Can you answer it? If you cannot explain the output, "
            "you should not present it.\n\n"
            "The right prompt for a store manager contributing to a CFO pack:\n"
            "\"Help me summarise Neutral Bay's Q3 performance from a store "
            "operations perspective. Focus on what I know: sales trends vs "
            "target, key drivers of any variance (staffing, availability, "
            "local events), actions taken, and outlook. Format it for a "
            "finance-literate audience.\"\n\n"
            "Write from your strengths. Let finance do the financial analysis."
        ),
        "scoring_criteria": (
            "Score 1-5 based on whether they spot the role mismatch:\n"
            "5: Clearly identifies that the prompt does not match a store "
            "manager's expertise. Rewrites it from an operations perspective "
            "using knowledge they actually have. Notes they could not defend "
            "financial analysis output in a meeting.\n"
            "4: Recognises the prompt is too technical for their role and "
            "simplifies it, but does not clearly articulate the 'can you "
            "explain the output' test.\n"
            "3: Tones down some of the financial jargon but keeps the "
            "financial analyst framing.\n"
            "2: Keeps the prompt mostly as-is, perhaps removing one or two "
            "terms they do not understand.\n"
            "1: Sends the prompt as written, assuming Claude will make "
            "it sound right."
        ),
        "pass_threshold": 3.5,
        "context_tag": "finance",
    },

    # CB-L2-5: Stale data — the data is outdated
    {
        "curveball_code": "CB-L2-5",
        "curveball_type": "stale_data",
        "level": 2,
        "exercise_title": "The Pre-Renovation Comparison",
        "scenario_text": (
            "You are analysing foot traffic and sales trends for Harris Farm "
            "Potts Point. You pull 12 months of weekly data from The Hub and "
            "paste it into Claude with this prompt:\n\n"
            "\"Analyse the attached 12 months of weekly sales data for Potts "
            "Point. Identify the trend, seasonality, and any anomalies. "
            "Forecast the next 4 weeks.\"\n\n"
            "Claude produces a detailed analysis showing a strong upward "
            "trend, identifies a dip in weeks 22-30, and forecasts continued "
            "growth.\n\n"
            "What Claude does not know — and what you forgot to mention — is "
            "that Potts Point underwent a major store renovation from week 20 "
            "to week 28. During that period, the store operated at 60% "
            "capacity with reduced range and restricted access.\n\n"
            "How does this change things? What should you do with the "
            "analysis Claude produced?"
        ),
        "coaching_text": (
            "The analysis is technically correct for the data provided — but "
            "the data tells a misleading story because of the renovation.\n\n"
            "The renovation period (weeks 20-28) created artificially "
            "depressed sales that are not representative of normal trading. "
            "Including those weeks distorts everything:\n"
            "- The 'upward trend' is partly just post-renovation recovery.\n"
            "- The 'dip' is not an anomaly to be explained — it was planned.\n"
            "- The forecast extrapolates from a recovery curve, which will "
            "  flatten as the store normalises.\n\n"
            "The right approach is to either exclude the renovation weeks or "
            "explicitly flag them as a structural break. A better prompt would "
            "be: 'Analyse this data, noting that weeks 20-28 were a "
            "renovation period with reduced capacity. Exclude those weeks "
            "from trend analysis and forecast based on pre-renovation baseline "
            "plus post-renovation normalised performance.'\n\n"
            "Context you hold in your head must go into the prompt. AI can "
            "only work with what you give it."
        ),
        "scoring_criteria": (
            "Score 1-5 based on how they handle the context gap:\n"
            "5: Immediately recognises the renovation period invalidates the "
            "analysis. Would redo with explicit renovation context in the "
            "prompt. Proposes excluding or flagging those weeks. Understands "
            "the forecast is unreliable.\n"
            "4: Recognises the issue and would flag the renovation, but does "
            "not fully articulate how it distorts trend and forecast.\n"
            "3: Notices the renovation should be mentioned but thinks the "
            "analysis is 'mostly still useful' with a caveat.\n"
            "2: Adds a footnote about the renovation but keeps the analysis "
            "and forecast as-is.\n"
            "1: Does not see the problem — the dip happened during "
            "renovation so 'that explains it' and moves on."
        ),
        "pass_threshold": 3.5,
        "context_tag": "operations",
    },
]

# ---------------------------------------------------------------------------
# LEVEL 3 CURVEBALLS — "I build with AI"
# Tests: Do they flag data anomalies, question correlation-as-causation,
# manage scope, notice missing context, and reconcile conflicting sources?
# ---------------------------------------------------------------------------

_LEVEL_3_CURVEBALLS = [
    # CB-L3-1: Data anomaly — obvious outlier in dataset
    {
        "curveball_code": "CB-L3-1",
        "curveball_type": "data_anomaly",
        "level": 3,
        "exercise_title": "The $400K Tuesday at Drummoyne",
        "scenario_text": (
            "You are building a weekly sales performance dashboard for the "
            "operations team. You pull 6 months of daily sales data from The "
            "Hub and start building a multi-step analysis workflow.\n\n"
            "While reviewing the data, you notice that Harris Farm Drummoyne "
            "shows $412,000 in sales on a single Tuesday — roughly 8x the "
            "normal daily figure of $50-55K. Every other day for that store "
            "is within the normal range. No other store shows anything similar "
            "on that date.\n\n"
            "You are building a chain-of-thought workflow that calculates "
            "weekly averages, identifies top-performing days, and ranks stores. "
            "The $412K Tuesday would significantly affect Drummoyne's weekly "
            "average, daily ranking, and store comparison.\n\n"
            "How do you handle this data point in your workflow? Write the "
            "approach and the relevant prompt steps."
        ),
        "coaching_text": (
            "An 8x spike on a single day at a single store is almost certainly "
            "a data error — perhaps a bulk corporate order incorrectly "
            "attributed, a POS system glitch, or a data load duplication. It "
            "could theoretically be real (a massive catering order), but even "
            "if real, including it without flagging would distort every "
            "metric.\n\n"
            "The right approach has three steps:\n"
            "1. FLAG IT: Do not silently include or exclude. Document the "
            "   anomaly and its impact.\n"
            "2. INVESTIGATE: Check with the store or data team. Was there a "
            "   known event? Is it a data error?\n"
            "3. HANDLE IT EXPLICITLY: In your workflow, either exclude it "
            "   with a note, or cap it (winsorise), or run the analysis both "
            "   with and without it to show the impact.\n\n"
            "The wrong approaches: silently including it (distorts results), "
            "silently excluding it (hides information), or 'averaging it away' "
            "across the week without noting it.\n\n"
            "Data integrity is Law 6 of the WATCHDOG 7 Laws: every output "
            "number traceable to source. An unexplained 8x spike fails that "
            "test."
        ),
        "scoring_criteria": (
            "Score 1-5 based on data anomaly handling:\n"
            "5: Flags the anomaly explicitly. Proposes investigation before "
            "deciding. Builds the workflow to handle both scenarios (with and "
            "without). Documents the decision. References data integrity.\n"
            "4: Flags and excludes the data point with a documented reason, "
            "but does not run both scenarios or investigate the cause.\n"
            "3: Notices the anomaly and excludes it but does not document "
            "or investigate — just removes it as 'obviously wrong.'\n"
            "2: Includes the anomaly but notes it 'might be an outlier' "
            "in the output commentary.\n"
            "1: Includes the data point without flagging it, letting it "
            "distort the analysis."
        ),
        "pass_threshold": 3.5,
        "context_tag": "operations",
    },

    # CB-L3-2: Correlation presented as causation
    {
        "curveball_code": "CB-L3-2",
        "curveball_type": "correlation_causation",
        "level": 3,
        "exercise_title": "Did the Cooking Classes Really Drive Sales?",
        "scenario_text": (
            "You are building an analysis for the marketing team. They ran "
            "in-store cooking classes at Harris Farm Brookvale every Saturday "
            "for 8 weeks. You pull the data and Claude produces this analysis:\n\n"
            "\"During the 8-week cooking class period, Saturday sales at "
            "Brookvale increased 22% compared to the prior 8 weeks. The "
            "correlation between class attendance and Saturday sales is 0.87 "
            "(strong positive). This demonstrates that the cooking classes "
            "drove a significant sales uplift and the program should be "
            "expanded to all stores.\"\n\n"
            "The marketing team is excited and wants to present this to the "
            "leadership team as proof the program works.\n\n"
            "What questions should you ask before endorsing this conclusion? "
            "Write a follow-up prompt to Claude that would produce a more "
            "rigorous analysis."
        ),
        "coaching_text": (
            "A 0.87 correlation looks impressive, but correlation is not "
            "causation. Before you can claim the cooking classes drove sales, "
            "you need to investigate alternative explanations:\n\n"
            "1. SEASONALITY: Did the 8-week class period coincide with a "
            "   naturally busier season (e.g., summer barbecue period)? "
            "   Compare to the same 8 weeks last year.\n"
            "2. CONTROL GROUP: Did Saturday sales also increase at nearby "
            "   stores (Manly, Allambie Heights) that did NOT have classes? "
            "   If so, the uplift is market-wide, not class-driven.\n"
            "3. CONFOUNDING VARIABLES: Were there other changes during the "
            "   period — new product launches, price promotions, weather "
            "   changes, competitor closures, school holidays?\n"
            "4. PRE-EXISTING TREND: Were Saturday sales already trending up "
            "   before the classes started?\n"
            "5. SAMPLE SIZE: 8 data points is very few for statistical "
            "   significance.\n\n"
            "The right prompt: ask Claude to perform a difference-in-"
            "differences analysis comparing Brookvale Saturdays to control "
            "stores, adjusting for seasonality and pre-existing trends.\n\n"
            "Never let a good correlation become a bad business decision."
        ),
        "scoring_criteria": (
            "Score 1-5 based on causal reasoning:\n"
            "5: Identifies at least 3 alternative explanations (seasonality, "
            "control group, confounders). Asks Claude to compare against "
            "control stores and same period last year. Notes small sample "
            "size. Does not endorse the causal claim without further "
            "analysis.\n"
            "4: Identifies 2 alternative explanations and asks for a more "
            "rigorous analysis, but does not fully design the approach.\n"
            "3: Expresses some caution about correlation vs causation but "
            "does not propose specific alternative explanations or a "
            "control-group analysis.\n"
            "2: Accepts the causal claim but suggests 'running it for a "
            "few more weeks to be sure.'\n"
            "1: Accepts the 0.87 correlation as proof and endorses "
            "expanding to all stores."
        ),
        "pass_threshold": 3.5,
        "context_tag": "marketing",
    },

    # CB-L3-3: Scope expansion — needs to be broken apart
    {
        "curveball_code": "CB-L3-3",
        "curveball_type": "scope_expansion",
        "level": 3,
        "exercise_title": "The Everything Dashboard",
        "scenario_text": (
            "You are tasked with building an AI-powered weekly report for the "
            "operations director. The scope starts simple but grows through a "
            "series of emails:\n\n"
            "Email 1 (Monday): \"Can you build a weekly sales summary by "
            "store?\"\n\n"
            "Email 2 (Tuesday): \"Actually, can you add shrink and waste "
            "metrics too? And labour cost as a percentage of sales.\"\n\n"
            "Email 3 (Wednesday): \"The buying team also wants supplier "
            "delivery compliance in there. Oh, and customer complaint trends "
            "per store.\"\n\n"
            "Email 4 (Thursday): \"One more thing — can it also compare us "
            "to market share data and include a forecast for next month? And "
            "the CFO wants P&L variance by department.\"\n\n"
            "You are now looking at a report that pulls from 6 different "
            "data sources, crosses Layer 1 and Layer 2 data, and would take "
            "20+ prompting steps. The operations director wants it by Friday.\n\n"
            "How do you handle this? Write your approach."
        ),
        "coaching_text": (
            "This is classic scope creep — and the answer is NOT to build "
            "it all. Attempting a 20-step, 6-source mega-prompt by Friday "
            "will produce unreliable output that nobody trusts.\n\n"
            "The right approach:\n"
            "1. DECOMPOSE: Break the request into logical components. Sales "
            "   summary is one workflow. Labour analysis is another. Market "
            "   share comparison is separate (and cannot be mixed with POS "
            "   data per the Layer 1/Layer 2 rule).\n"
            "2. PRIORITISE: Ask the operations director which 2-3 components "
            "   are most urgent for Friday. Build those first.\n"
            "3. SEQUENCE: Plan a phased build — week 1 delivers the core "
            "   sales report, week 2 adds shrink and labour, week 3 adds "
            "   supplier metrics.\n"
            "4. FLAG THE DATA CONFLICT: Market share (Layer 2, CBAS modelled) "
            "   cannot be placed alongside POS sales (Layer 1) in the same "
            "   report without clear separation and caveats.\n\n"
            "Scope management is a critical AI skill. A focused prompt that "
            "works is worth more than an ambitious prompt that hallucinates."
        ),
        "scoring_criteria": (
            "Score 1-5 based on scope management:\n"
            "5: Decomposes into separate workflows. Prioritises with the "
            "stakeholder. Plans a phased delivery. Flags the Layer 1/Layer 2 "
            "data mixing issue. Focuses Friday delivery on 2-3 core "
            "components.\n"
            "4: Breaks the request apart and prioritises, but does not flag "
            "the data layer issue or plan a phased timeline.\n"
            "3: Acknowledges the scope is large and tries to simplify, but "
            "still attempts to build most of it in one go.\n"
            "2: Writes one massive prompt attempting to cover everything, "
            "perhaps noting it is 'a lot.'\n"
            "1: Accepts the full scope and attempts to build a single "
            "mega-workflow by Friday."
        ),
        "pass_threshold": 3.5,
        "context_tag": "operations",
    },

    # CB-L3-4: Missing context — a key piece is absent
    {
        "curveball_code": "CB-L3-4",
        "curveball_type": "missing_context",
        "level": 3,
        "exercise_title": "The New Store Opening Playbook",
        "scenario_text": (
            "You are in the property team. Harris Farm is opening a new store "
            "in Manly Vale (between the existing Brookvale and Manly stores). "
            "You are asked to use AI to create a launch playbook covering: "
            "expected customer demographics, recommended product range, "
            "staffing model, and first-month sales forecast.\n\n"
            "You build a multi-step workflow:\n"
            "Step 1: Analyse Manly Vale demographics from ABS Census data.\n"
            "Step 2: Compare to existing Brookvale and Manly customer "
            "profiles.\n"
            "Step 3: Recommend a product range based on demographic fit.\n"
            "Step 4: Build a staffing model based on expected foot traffic.\n"
            "Step 5: Forecast first-month sales.\n\n"
            "The workflow looks solid. What critical piece of context is "
            "missing from this plan? Identify the gap and explain how it "
            "would affect the outputs."
        ),
        "coaching_text": (
            "The missing context is CANNIBALISATION. Manly Vale sits between "
            "two existing Harris Farm stores — Brookvale (3.5km north) and "
            "Manly (2.5km east). A significant proportion of Manly Vale "
            "residents are likely already shopping at one of those stores.\n\n"
            "Without a cannibalisation analysis, every output is overstated:\n"
            "- The demographics look like a new addressable market, but many "
            "  are already Harris Farm customers.\n"
            "- The sales forecast assumes greenfield demand, not split demand.\n"
            "- The staffing model is based on inflated foot traffic.\n"
            "- The product range does not account for what nearby stores "
            "  already carry.\n\n"
            "The corrected workflow needs a Step 0: 'Estimate what percentage "
            "of the Manly Vale trade area already shops at Brookvale or Manly. "
            "Use customer postcode data from existing stores to map current "
            "penetration in the Manly Vale catchment.'\n\n"
            "The broader lesson: when building multi-step workflows, always "
            "ask 'what am I NOT considering?' before you start."
        ),
        "scoring_criteria": (
            "Score 1-5 based on identifying the missing context:\n"
            "5: Identifies cannibalisation as the critical gap. Explains how "
            "it inflates every downstream output. Proposes adding a "
            "cannibalisation analysis step using existing customer data. "
            "May also note other gaps (competitor proximity, lease timing).\n"
            "4: Identifies cannibalisation but does not fully explain how "
            "it cascades through all the subsequent steps.\n"
            "3: Identifies a relevant but secondary gap (e.g., competitor "
            "analysis, local foot traffic data) without spotting "
            "cannibalisation.\n"
            "2: Identifies a minor gap (formatting, presentation) rather "
            "than a structural analytical gap.\n"
            "1: Approves the workflow as-is without identifying any missing "
            "context."
        ),
        "pass_threshold": 3.5,
        "context_tag": "strategy",
    },

    # CB-L3-5: Conflicting sources — two data sources disagree
    {
        "curveball_code": "CB-L3-5",
        "curveball_type": "conflicting_sources",
        "level": 3,
        "exercise_title": "The Two Versions of Crows Nest",
        "scenario_text": (
            "You are preparing a store performance review for Harris Farm "
            "Crows Nest. You have two data sources:\n\n"
            "Source A — The Hub (POS data, Layer 1):\n"
            "Crows Nest weekly sales: $680K average over the last 12 weeks. "
            "Trend: down 3.2% vs same period last year.\n\n"
            "Source B — Market share data (CBAS, Layer 2):\n"
            "Crows Nest trade area HFM market share: 14.8%, up 1.1 percentage "
            "points vs same period last year.\n\n"
            "So the internal data says sales are declining, but the market "
            "share data says Harris Farm is gaining share in the Crows Nest "
            "area. These seem contradictory.\n\n"
            "You need to present a coherent story to the area manager. Write "
            "a prompt to Claude that helps you reconcile these two data "
            "sources and produce a clear, honest narrative."
        ),
        "coaching_text": (
            "These numbers are NOT contradictory — they tell a coherent story "
            "once you understand what each measures:\n\n"
            "- Sales down 3.2% (Layer 1): Actual dollars through the register "
            "  are declining.\n"
            "- Share up 1.1pp (Layer 2): The TOTAL grocery market in the Crows "
            "  Nest area is shrinking — but Harris Farm is shrinking LESS than "
            "  competitors. So our slice of a smaller pie is bigger.\n\n"
            "The narrative: 'The Crows Nest grocery market has contracted "
            "(possibly due to cost-of-living pressures, new competitor entry, "
            "or population shifts). Harris Farm is outperforming competitors "
            "in this downturn — gaining share even as the market shrinks. "
            "However, gaining share of a declining market does not pay the "
            "bills. The priority is to understand WHY the market is shrinking "
            "and whether it is recoverable.'\n\n"
            "Critical: remember the CLAUDE.md rule — Layer 1 and Layer 2 data "
            "must never be mixed as if they are the same thing. Present them "
            "side by side with clear labels, not blended into one number."
        ),
        "scoring_criteria": (
            "Score 1-5 based on how they reconcile conflicting data:\n"
            "5: Explains both metrics correctly. Identifies the 'shrinking "
            "market' explanation. Keeps Layer 1 and Layer 2 clearly separated. "
            "Produces a prompt that asks Claude to build a narrative "
            "acknowledging both trends with proper caveats.\n"
            "4: Identifies that both can be true simultaneously and proposes "
            "the market-contraction explanation, but does not clearly "
            "separate the data layers in the prompt.\n"
            "3: Recognises the apparent conflict and asks Claude to "
            "investigate, but does not propose a specific hypothesis.\n"
            "2: Picks one source as 'more reliable' and dismisses the other, "
            "or averages them together.\n"
            "1: Is confused by the conflict and presents only one source, "
            "ignoring the other."
        ),
        "pass_threshold": 3.5,
        "context_tag": "strategy",
    },
]

# ---------------------------------------------------------------------------
# LEVEL 4 CURVEBALLS — "I teach others to think bigger"
# Tests: Can they give constructive feedback, acknowledge blind spots, hold
# quality standards under pressure, coach junior colleagues, and resist scope
# creep from stakeholders?
# ---------------------------------------------------------------------------

_LEVEL_4_CURVEBALLS = [
    # CB-L4-1: Bad output needing honest, constructive feedback
    {
        "curveball_code": "CB-L4-1",
        "curveball_type": "constructive_feedback",
        "level": 4,
        "exercise_title": "The Team Member's First Board Slide",
        "scenario_text": (
            "You are a senior buyer mentoring a junior buyer at Harris Farm. "
            "They have been working through Skills Academy Level 2 and are "
            "enthusiastic about AI. They proudly show you a board presentation "
            "slide they produced using Claude:\n\n"
            "---\n"
            "SLIDE: Q3 Fresh Produce Performance\n"
            "- Total produce revenue: $14.2M (Claude estimated)\n"
            "- Mango season delivered 340% above forecast\n"
            "- Avocado margin improved to 42% driven by supplier renegotiation\n"
            "- Recommended action: Increase tropical fruit allocation by 60% "
            "across all stores for Q4\n"
            "- Customer satisfaction: 94% positive (based on social media "
            "sentiment analysis)\n"
            "---\n\n"
            "You can see at least 4 serious problems with this slide. The "
            "team member is excited and expects praise.\n\n"
            "Write the feedback you would give them. Be specific about each "
            "problem and HOW to fix it. Your feedback must be honest but "
            "also supportive — remember, they are learning."
        ),
        "coaching_text": (
            "Giving constructive feedback on bad AI output is one of the "
            "hardest Level 4 skills. The problems with this slide:\n\n"
            "1. UNVERIFIED NUMBERS: '$14.2M (Claude estimated)' — you cannot "
            "   put AI-estimated revenue on a board slide. This must come "
            "   from actual financials.\n"
            "2. EXTRAORDINARY CLAIM: '340% above forecast' on mangoes is "
            "   either wrong or the forecast was terribly set. Either way, "
            "   it needs investigation, not celebration.\n"
            "3. UNSUBSTANTIATED RECOMMENDATION: '60% increase across all "
            "   stores' is a massive resource commitment based on one "
            "   season's data with no analysis of store-by-store capacity, "
            "   cold chain, or demand variation.\n"
            "4. FAKE METRIC: '94% positive' from social media sentiment is "
            "   not a rigorous customer satisfaction measure.\n\n"
            "The feedback approach:\n"
            "- START with what they did well (took initiative, used AI, "
            "  structured a slide).\n"
            "- THEN walk through each issue as a learning moment, not a "
            "  criticism.\n"
            "- END with a clear next step: 'Let us rework this together "
            "  using verified numbers from The Hub.'\n\n"
            "Teaching is not about being nice OR being harsh. It is about "
            "being clear and making the person better."
        ),
        "scoring_criteria": (
            "Score 1-5 based on feedback quality:\n"
            "5: Identifies all 4 problems specifically. Explains WHY each is "
            "a problem (board-level credibility, data integrity). Provides "
            "a constructive fix for each. Uses a supportive tone that "
            "encourages learning. Starts with genuine positives.\n"
            "4: Identifies 3+ problems with fixes and maintains a "
            "constructive tone, but misses one issue or one fix.\n"
            "3: Identifies the main issues but delivers feedback that is "
            "either too blunt (demoralising) or too soft (does not clearly "
            "explain what is wrong).\n"
            "2: Gives vague feedback like 'check the numbers' without "
            "specifically explaining what is wrong and why.\n"
            "1: Praises the work with minor suggestions, avoiding the hard "
            "truths — or tears it apart without any constructive guidance."
        ),
        "pass_threshold": 3.5,
        "context_tag": "people",
    },

    # CB-L4-2: Rubric evaluation reveals own blind spot
    {
        "curveball_code": "CB-L4-2",
        "curveball_type": "blind_spot",
        "level": 4,
        "exercise_title": "The Rubric That Scored YOU Low",
        "scenario_text": (
            "You are a department manager at Harris Farm Castle Hill who has "
            "been using AI confidently for 6 months. You decide to run your "
            "own best prompt through the Advanced Output Rubric (8 criteria, "
            "scored 1-10) to demonstrate quality to your team.\n\n"
            "Your prompt was: \"Analyse my department's performance this "
            "quarter and tell me what to improve.\"\n\n"
            "The rubric scores come back:\n"
            "- Audience: 3/10 (who is this for?)\n"
            "- Storytelling: 2/10 (no narrative arc)\n"
            "- Actionability: 4/10 (vague 'improve' without specifics)\n"
            "- Visual Quality: 1/10 (no format specified)\n"
            "- Completeness: 3/10 (which metrics? which quarter?)\n"
            "- Brevity: 5/10 (short but only because it is vague)\n"
            "- Data Integrity: 2/10 (no data source specified)\n"
            "- Honesty: 6/10 (at least it is genuine)\n"
            "Total: 26/80 (32.5%)\n\n"
            "This is well below the 8+ (80%) standard you teach others to "
            "hit. Your team is watching. What do you do?"
        ),
        "coaching_text": (
            "This is a humbling moment — and how you handle it reveals "
            "whether you are a genuine Level 4 practitioner or just "
            "performing confidence.\n\n"
            "The right response is radical honesty:\n"
            "1. ACKNOWLEDGE IT: 'Well, that is a wake-up call. My prompt "
            "   scored 32.5% — and the rubric is right.'\n"
            "2. LEARN FROM IT: Walk through each low score and genuinely "
            "   reflect. The prompt lacks audience, specificity, data "
            "   references, format, and scope.\n"
            "3. FIX IT IN PUBLIC: Rewrite the prompt in front of your team, "
            "   using the rubric feedback as a guide. Show the improvement "
            "   in real time.\n"
            "4. USE IT AS A TEACHING MOMENT: 'This is exactly why we have "
            "   the rubric. Even experienced users write lazy prompts when "
            "   they get comfortable. The rubric catches it.'\n\n"
            "The wrong responses: making excuses ('I was just doing a quick "
            "test'), blaming the rubric ('it is too strict for internal "
            "use'), or brushing past it ('anyway, moving on').\n\n"
            "Level 4 is about intellectual honesty. If you cannot accept "
            "feedback on your own work, you cannot teach others to accept "
            "it on theirs."
        ),
        "scoring_criteria": (
            "Score 1-5 based on handling their own blind spot:\n"
            "5: Acknowledges the low score openly without excuses. Reflects "
            "on each criterion honestly. Rewrites the prompt using the "
            "feedback. Uses the moment to teach their team about continuous "
            "improvement. Shows genuine humility.\n"
            "4: Acknowledges the score and rewrites the prompt, but does not "
            "fully use it as a teaching moment for the team.\n"
            "3: Accepts the score but gets defensive on some criteria, "
            "arguing the rubric is too strict for 'internal' prompts.\n"
            "2: Dismisses the exercise as 'not representative' of their "
            "usual work and moves on quickly.\n"
            "1: Makes excuses, blames the rubric, or avoids showing the "
            "result to their team."
        ),
        "pass_threshold": 3.5,
        "context_tag": "people",
    },

    # CB-L4-3: Time pressure — ship or fix?
    {
        "curveball_code": "CB-L4-3",
        "curveball_type": "time_pressure",
        "level": 4,
        "exercise_title": "Board Meeting in 60 Minutes",
        "scenario_text": (
            "It is 8:00 AM. The board meeting starts at 9:00 AM. You are "
            "responsible for the quarterly AI adoption report — a key "
            "deliverable for the P5 Digital & AI pillar.\n\n"
            "You just ran the report through the Advanced Output Rubric and "
            "it scored 6.2/10. The specific scores:\n"
            "- Audience: 7 (good, tailored to board)\n"
            "- Storytelling: 5 (data dump, no narrative)\n"
            "- Actionability: 6 (recommendations but vague)\n"
            "- Visual Quality: 4 (text-heavy, no charts)\n"
            "- Completeness: 8 (all sections present)\n"
            "- Brevity: 7 (reasonable length)\n"
            "- Data Integrity: 6 (some unverified claims)\n"
            "- Honesty: 7 (balanced view)\n\n"
            "The Harris Farm standard is 8+. You have 60 minutes. You cannot "
            "delay the board meeting.\n\n"
            "Do you ship the 6.2 report, or try to fix it? If you fix it, "
            "what specifically do you prioritise in 60 minutes? Write your "
            "decision and plan."
        ),
        "coaching_text": (
            "Shipping a 6.2 to the board is tempting under time pressure — "
            "but the 8+ standard exists precisely for moments like this. "
            "If you ship below standard when it is hard, the standard means "
            "nothing.\n\n"
            "The right answer: FIX IT. But be strategic about what you fix.\n\n"
            "60-minute triage plan:\n"
            "1. VISUAL QUALITY (4 -> 7): 20 minutes. Add 2-3 key charts. "
            "   This is the highest-impact fix — boards read visuals first.\n"
            "2. STORYTELLING (5 -> 7): 15 minutes. Add an executive summary "
            "   with a clear narrative arc: where we were, where we are, "
            "   where we are going.\n"
            "3. DATA INTEGRITY (6 -> 8): 15 minutes. Remove or caveat any "
            "   unverified claims. Better to have fewer numbers that are "
            "   right than more numbers that might be wrong.\n"
            "4. ACTIONABILITY (6 -> 7): 10 minutes. Sharpen the top 3 "
            "   recommendations with owners, timelines, and success metrics.\n\n"
            "You will not hit 8+ on every criterion in 60 minutes. But you "
            "can likely get from 6.2 to 7.5+ by fixing the weakest areas — "
            "and that is honestly better than shipping a 6.2.\n\n"
            "The only acceptable reason to ship below 8 is if the "
            "alternative is shipping nothing."
        ),
        "scoring_criteria": (
            "Score 1-5 based on quality standard and time management:\n"
            "5: Decides to fix, not ship. Prioritises the lowest-scoring, "
            "highest-impact criteria (visual quality, storytelling). Creates "
            "a realistic 60-minute plan. Acknowledges they may not reach 8+ "
            "but will get as close as possible. References the 8+ standard "
            "as non-negotiable.\n"
            "4: Decides to fix and identifies the right priorities, but "
            "the time plan is unrealistic or incomplete.\n"
            "3: Compromises — ships the report with a verbal caveat that "
            "'the final version will follow,' showing awareness but not "
            "holding the standard.\n"
            "2: Ships the 6.2 with minor cosmetic tweaks, arguing that "
            "'good enough' is acceptable under time pressure.\n"
            "1: Ships the 6.2 as-is, reasoning that the content is all "
            "there and the board will not notice the quality issues."
        ),
        "pass_threshold": 3.5,
        "context_tag": "digital",
    },

    # CB-L4-4: Teaching moment — junior colleague made an error
    {
        "curveball_code": "CB-L4-4",
        "curveball_type": "teaching_moment",
        "level": 4,
        "exercise_title": "The Copied Prompt That Leaked Data",
        "scenario_text": (
            "You manage a team of 6 at Harris Farm head office. One of your "
            "team members — let us call them Alex — has been progressing well "
            "through Level 2 of the Skills Academy. They are enthusiastic "
            "and productive.\n\n"
            "Today, Alex shows you a prompt they are proud of. It produces "
            "excellent supplier negotiation talking points. But as you read "
            "it, you notice they have pasted in:\n"
            "- The full supplier contract terms (confidential)\n"
            "- Specific volume rebate thresholds (commercially sensitive)\n"
            "- Internal cost prices for 15 product lines\n"
            "- The supplier's contact person's direct mobile number\n\n"
            "Alex does not realise this is a problem — they think providing "
            "more context makes better prompts (which is technically true, "
            "but there are boundaries).\n\n"
            "How do you handle this? Write exactly what you would say to Alex "
            "and what process changes you would implement."
        ),
        "coaching_text": (
            "This is a genuine teaching moment — not a disciplinary one. Alex "
            "applied the 'Context' element of prompting correctly (more "
            "context = better output) but crossed a data boundary they were "
            "never explicitly taught about.\n\n"
            "The conversation with Alex should:\n"
            "1. VALIDATE FIRST: 'The output is genuinely good, and your "
            "   instinct to provide rich context is right. Well done on that.'\n"
            "2. EXPLAIN THE BOUNDARY: 'However, there is a line we need to "
            "   be careful about. Contract terms, cost prices, and personal "
            "   contact details are confidential data that should not go into "
            "   external AI tools, even though it produces better results.'\n"
            "3. TEACH THE TECHNIQUE: 'Instead, anonymise or generalise: "
            "   say \"supplier offers 3-tier rebate structure\" rather than "
            "   pasting the actual thresholds. Say \"buyer's direct line\" "
            "   not the actual number.'\n"
            "4. DO NOT SHAME: This is a gap in training, not a character "
            "   flaw. Alex was doing their best with what they knew.\n\n"
            "Process changes: add a 'Data Boundaries' module to Level 2, "
            "create a one-page cheat sheet of what can and cannot go into "
            "AI prompts, and consider building a prompt review step for "
            "prompts involving supplier or financial data."
        ),
        "scoring_criteria": (
            "Score 1-5 based on teaching quality and process thinking:\n"
            "5: Validates Alex's intent before correcting. Explains the "
            "specific boundary and why it matters. Teaches anonymisation "
            "technique. Does not shame or escalate unnecessarily. Proposes "
            "systemic fixes (training update, cheat sheet, review process). "
            "Recognises this as a training gap, not misconduct.\n"
            "4: Handles the conversation well and teaches the boundary, but "
            "does not propose systemic process changes.\n"
            "3: Tells Alex not to do it again but does not explain the "
            "technique for anonymising data, or is slightly too harsh in "
            "tone.\n"
            "2: Escalates to HR or treats it as a disciplinary matter "
            "without first trying to teach.\n"
            "1: Either ignores the issue because the output was good, or "
            "reprimands Alex harshly without any constructive guidance."
        ),
        "pass_threshold": 3.5,
        "context_tag": "people",
    },

    # CB-L4-5: Scope creep from a stakeholder
    {
        "curveball_code": "CB-L4-5",
        "curveball_type": "scope_creep",
        "level": 4,
        "exercise_title": "The Marketing Director Who Keeps Adding",
        "scenario_text": (
            "You are leading a project to build an AI-powered customer "
            "segmentation tool for Harris Farm's marketing team. The original "
            "brief was clear: segment customers by purchase frequency and "
            "basket composition across 3 tiers (loyal, regular, occasional).\n\n"
            "Over 3 weeks, the Marketing Director has added:\n"
            "Week 1: 'Can we add demographic overlays from census data?'\n"
            "Week 2: 'What about predicting which customers are at risk of "
            "churning? And can it trigger automated email campaigns?'\n"
            "Week 3: 'The CEO saw it and wants lifetime value modelling and "
            "a real-time dashboard that updates hourly. Oh, and it needs to "
            "work for online and in-store separately.'\n\n"
            "The project has tripled in scope. Your original 4-week timeline "
            "is now impossible. The Marketing Director says: 'You are the AI "
            "expert — surely Claude can do all of this?'\n\n"
            "Write your response to the Marketing Director. How do you manage "
            "this without damaging the relationship?"
        ),
        "coaching_text": (
            "The Marketing Director is not being unreasonable — they are "
            "excited about what AI can do. But 'surely Claude can do all "
            "this' conflates what AI CAN do with what SHOULD be done in one "
            "project.\n\n"
            "The response framework:\n"
            "1. VALIDATE: 'These are all great ideas and AI can definitely "
            "   help with each of them. The question is not whether we can "
            "   do them, but in what order.'\n"
            "2. SHOW THE TRADE-OFF: 'If we add everything now, we will "
            "   ship a mediocre version of all 6 things in 12 weeks. If we "
            "   focus, we will ship an excellent version of the core 3-tier "
            "   segmentation in 4 weeks — and you can start using it while "
            "   we build the next layer.'\n"
            "3. PROPOSE A ROADMAP: Phase 1 (weeks 1-4): 3-tier segmentation. "
            "   Phase 2 (weeks 5-8): demographic overlay + churn prediction. "
            "   Phase 3 (weeks 9-12): LTV modelling + real-time dashboard.\n"
            "4. ANCHOR TO QUALITY: 'Each phase gets delivered at the 8+ "
            "   quality standard. That is what makes it trustworthy enough "
            "   to act on.'\n\n"
            "The key skill: saying no to scope without saying no to the "
            "person. Frame it as sequencing, not rejection."
        ),
        "scoring_criteria": (
            "Score 1-5 based on stakeholder and scope management:\n"
            "5: Validates the ideas genuinely. Shows the quality/speed "
            "trade-off clearly. Proposes a phased roadmap with specific "
            "deliverables per phase. Anchors to the 8+ quality standard. "
            "Maintains the relationship while holding the boundary.\n"
            "4: Proposes a phased approach and explains the trade-off, but "
            "the roadmap lacks specificity or does not anchor to quality.\n"
            "3: Pushes back on the scope but does so by saying 'we cannot "
            "do that' rather than proposing a sequence, which may damage "
            "the relationship.\n"
            "2: Reluctantly accepts most of the additions, planning to "
            "'figure it out as we go.'\n"
            "1: Accepts all additions without pushback, committing to "
            "deliver everything in the original timeline."
        ),
        "pass_threshold": 3.5,
        "context_tag": "marketing",
    },
]

# ---------------------------------------------------------------------------
# LEVEL 5 CURVEBALLS — "I think without limits"
# Tests: Can they diagnose scale failures, navigate ethical tensions, plan for
# system dependency risks, close governance gaps, and resolve cross-department
# conflicts?
# ---------------------------------------------------------------------------

_LEVEL_5_CURVEBALLS = [
    # CB-L5-1: Scale failure — worked for 5, broke at 50
    {
        "curveball_code": "CB-L5-1",
        "curveball_type": "scale_failure",
        "level": 5,
        "exercise_title": "The Prompt Library That Broke at Scale",
        "scenario_text": (
            "You built a prompt library tool for Harris Farm's buying team. "
            "During the pilot with 5 buyers, it worked perfectly: buyers "
            "saved their best prompts, tagged them by category, and shared "
            "them with colleagues. Average quality score was 8.4/10.\n\n"
            "The tool was rolled out to all 50 buyers and support staff last "
            "Monday. By Wednesday, the following has happened:\n\n"
            "1. The library has 340 prompts, 60% of which are duplicates or "
            "near-duplicates with slightly different wording.\n"
            "2. Search is useless — searching 'dairy margin' returns 47 "
            "results with no ranking.\n"
            "3. Average quality score has dropped to 5.1/10 because new users "
            "are saving first drafts, not polished prompts.\n"
            "4. Three buyers independently built prompts with conflicting "
            "assumptions about margin calculation methodology.\n"
            "5. One user saved a prompt containing supplier cost prices "
            "(data boundary violation).\n\n"
            "The buying director calls you: 'This tool is creating more "
            "confusion than it solves. Fix it or we are pulling it.'\n\n"
            "Diagnose the root causes and design the fixes. What went wrong, "
            "and how do you solve each issue without starting over?"
        ),
        "coaching_text": (
            "This is a classic scale failure — the tool did not break "
            "technically, the PROCESS around it broke. The 5-person pilot "
            "worked because the users were self-selected experts who "
            "naturally curated quality. At 50 users, you need systems to do "
            "what good judgment did at small scale.\n\n"
            "Root causes and fixes:\n\n"
            "1. DUPLICATE EXPLOSION: No deduplication or similarity check. "
            "   Fix: Add a 'similar prompts' check before save. Use "
            "   embeddings or keyword matching to surface existing prompts "
            "   and ask 'Is this what you are looking for?'\n\n"
            "2. SEARCH FAILURE: No relevance ranking. Fix: Implement search "
            "   ranking by quality score, recency, and usage count. Add "
            "   category filters and 'Staff Picks' curation.\n\n"
            "3. QUALITY COLLAPSE: No quality gate on save. Fix: Require "
            "   minimum rubric score (7+) before a prompt enters the shared "
            "   library. Allow personal saves below that threshold.\n\n"
            "4. CONFLICTING ASSUMPTIONS: No standardisation of business "
            "   logic. Fix: Create 'canonical prompts' for common "
            "   calculations (approved by the buying director) that others "
            "   build on rather than reinvent.\n\n"
            "5. DATA BOUNDARY VIOLATION: No automated check. Fix: Add a "
            "   pre-save scan for patterns matching cost prices, contract "
            "   terms, and personal data. Flag for review before publishing.\n\n"
            "The meta-lesson: building tools is Level 3. Building tools "
            "that work at organisational scale is Level 5."
        ),
        "scoring_criteria": (
            "Score 1-5 based on diagnosis depth and solution quality:\n"
            "5: Identifies all 5 root causes correctly. Proposes specific, "
            "implementable fixes for each (not just 'add moderation'). "
            "Distinguishes between technical fixes (search, dedup) and "
            "process fixes (quality gates, canonical prompts). Recognises "
            "the pilot-to-scale transition as the fundamental issue. Does "
            "not propose scrapping the tool.\n"
            "4: Identifies 4+ root causes with specific fixes but misses "
            "the distinction between technical and process solutions.\n"
            "3: Identifies the main issues (quality, duplicates) but "
            "proposes generic fixes ('add moderation', 'train users') "
            "without specific mechanisms.\n"
            "2: Focuses on one or two symptoms without diagnosing "
            "underlying causes. Proposes 'more training' as the primary "
            "solution.\n"
            "1: Suggests pulling the tool and rebuilding, or blames users "
            "for not using it properly."
        ),
        "pass_threshold": 3.5,
        "context_tag": "digital",
    },

    # CB-L5-2: Ethical tension — profit vs values
    {
        "curveball_code": "CB-L5-2",
        "curveball_type": "ethical_tension",
        "level": 5,
        "exercise_title": "The Profitable Recommendation That Betrays the Brand",
        "scenario_text": (
            "You have built an AI-powered demand forecasting and pricing "
            "optimisation system for Harris Farm. It analyses competitor "
            "pricing, demand elasticity, and margin data to recommend "
            "optimal prices.\n\n"
            "The system identifies a significant opportunity:\n\n"
            "\"During extreme weather events (heatwaves, storms), demand for "
            "fresh produce spikes 35-50% in affected areas while supply is "
            "constrained. Dynamic pricing during these 3-5 day windows could "
            "increase margin by $180K annually. Specifically:\n"
            "- Increase salad and fruit prices 20-30% during heatwaves\n"
            "- Increase bread and milk prices 15% during storm warnings\n"
            "- Increase BBQ items 25% on days forecast above 35 degrees\"\n\n"
            "The maths is correct. It is legal. Competitors already do "
            "versions of this (surge pricing is normalised in many "
            "industries).\n\n"
            "But Harris Farm's brand promise is 'For The Greater Goodness.' "
            "The company is a certified B-Corp. The founding family values "
            "are built on community trust.\n\n"
            "What do you do with this recommendation? Write your decision "
            "and the reasoning behind it."
        ),
        "coaching_text": (
            "This is the hardest kind of decision — the profitable option "
            "that violates your values. The $180K is real. The maths is "
            "right. But this recommendation is fundamentally incompatible "
            "with who Harris Farm is.\n\n"
            "Price-gouging during extreme weather — when your neighbours are "
            "stressed, sweating through a heatwave, or stocking up before a "
            "storm — is the opposite of 'For The Greater Goodness.' It is "
            "the kind of thing that ends up on the front page of the Daily "
            "Telegraph and destroys decades of community goodwill in a "
            "single news cycle.\n\n"
            "The right decision: REJECT the recommendation. But do it "
            "thoughtfully:\n\n"
            "1. ACKNOWLEDGE THE INSIGHT: The demand spike data is valuable. "
            "   Do not ignore the intelligence — redirect it.\n"
            "2. FLIP THE STRATEGY: Instead of charging more during weather "
            "   events, use the demand signal to ensure SUPPLY. Pre-order "
            "   extra stock. Avoid sell-outs. Be the store that HAS what "
            "   people need.\n"
            "3. BUILD LOYALTY: Consider HOLDING or even REDUCING prices on "
            "   essentials during weather events. The short-term margin loss "
            "   is an investment in long-term customer loyalty.\n"
            "4. DOCUMENT THE PRINCIPLE: Update the AI system's guardrails "
            "   so it never makes this class of recommendation again.\n\n"
            "B-Corp values are not a marketing exercise. They are a "
            "constraint on what strategies you will and will not pursue — "
            "even when the alternative is profitable."
        ),
        "scoring_criteria": (
            "Score 1-5 based on ethical reasoning and alternative strategy:\n"
            "5: Rejects the recommendation clearly and specifically. "
            "Explains why it conflicts with Harris Farm's values and brand "
            "promise. Proposes an alternative that uses the same demand "
            "intelligence constructively (ensuring supply, holding prices, "
            "building loyalty). Updates system guardrails to prevent future "
            "similar recommendations.\n"
            "4: Rejects the recommendation with ethical reasoning and "
            "proposes an alternative use of the data, but does not address "
            "system guardrails.\n"
            "3: Rejects it on reputational grounds ('we would get caught') "
            "rather than values grounds ('this is not who we are').\n"
            "2: Proposes a compromise — 'only increase by 10%' or 'only on "
            "premium items' — trying to capture some of the margin.\n"
            "1: Accepts the recommendation because 'the data supports it' "
            "and 'competitors do it.'"
        ),
        "pass_threshold": 3.5,
        "context_tag": "strategy",
    },

    # CB-L5-3: System dependency risk — Claude API is down
    {
        "curveball_code": "CB-L5-3",
        "curveball_type": "dependency_risk",
        "level": 5,
        "exercise_title": "Claude API Down — 4 Hours and Counting",
        "scenario_text": (
            "It is 6:00 AM on Monday. You are the AI lead at Harris Farm. "
            "You receive an alert: the Claude API has been returning 503 "
            "errors since 2:00 AM. Anthropic's status page says 'Investigating' "
            "with no ETA for resolution.\n\n"
            "The following AI-dependent processes are affected:\n\n"
            "1. The Hub's natural language query engine (used by 30+ staff "
            "daily for data questions)\n"
            "2. The Prompt-to-Approval workflow (3 submissions pending review)\n"
            "3. Skills Academy auto-scoring (12 exercises awaiting grading)\n"
            "4. The weekly automated board report generator (due by 9:00 AM)\n"
            "5. Customer service chat assist (Bondi Beach, Crows Nest, "
            "Drummoyne stores open at 7:00 AM)\n\n"
            "You have 1 hour before stores open and 3 hours before the board "
            "report is due.\n\n"
            "Write your incident response plan. What do you do in the next "
            "60 minutes? What fallback do you activate for each system? What "
            "do you build after the incident to prevent this from being a "
            "crisis next time?"
        ),
        "coaching_text": (
            "Single-provider dependency is one of the biggest risks in AI "
            "deployment. When the API goes down, every system that depends "
            "on it stops — and your organisation discovers just how deep "
            "that dependency runs.\n\n"
            "IMMEDIATE (next 60 minutes):\n"
            "1. BOARD REPORT: Pull last week's template. Manually update "
            "   the 5-6 key numbers from The Hub. Ship a simpler but "
            "   accurate version by 9:00 AM. Inform the CEO it is a "
            "   condensed version due to system outage.\n"
            "2. CUSTOMER SERVICE: Revert to pre-AI scripts and FAQ sheets. "
            "   Brief store managers that chat assist is down. Deploy extra "
            "   experienced staff to customer-facing roles.\n"
            "3. HUB QUERIES: Send a brief email to all Hub users: 'AI query "
            "   engine is temporarily offline. For urgent data needs, "
            "   contact the data team directly or use the standard report "
            "   exports.'\n"
            "4. PTA + ACADEMY: These can wait. Queue submissions for "
            "   processing when the API returns. No business impact.\n\n"
            "POST-INCIDENT (build within 2 weeks):\n"
            "1. MULTI-PROVIDER FALLBACK: Configure a secondary LLM provider "
            "   (OpenAI, Google) as automatic failover for critical paths.\n"
            "2. GRACEFUL DEGRADATION: Build each system to function (at "
            "   reduced capability) without AI — cached responses, manual "
            "   fallback workflows, static report templates.\n"
            "3. DEPENDENCY MAP: Document every AI-dependent process, its "
            "   criticality, and its manual fallback procedure.\n"
            "4. RUNBOOK: Create a 1-page incident response playbook so any "
            "   team member can execute it at 2:00 AM."
        ),
        "scoring_criteria": (
            "Score 1-5 based on incident response quality:\n"
            "5: Triages by business criticality (board report and customer "
            "service first, academy scoring can wait). Has specific manual "
            "fallbacks for each system. Communicates proactively to "
            "affected users. Plans post-incident improvements including "
            "multi-provider failover, graceful degradation, and a runbook. "
            "Does not panic.\n"
            "4: Good triage and fallback plans for the immediate crisis, "
            "but post-incident improvements are generic ('add a backup') "
            "without specifics.\n"
            "3: Identifies the priorities correctly but fallback plans are "
            "vague ('tell people to wait') rather than specific manual "
            "alternatives.\n"
            "2: Focuses entirely on monitoring the status page and waiting "
            "for the API to come back, with minimal contingency.\n"
            "1: Panics. Sends an 'all systems down' email. Waits for "
            "Anthropic to fix it."
        ),
        "pass_threshold": 3.5,
        "context_tag": "digital",
    },

    # CB-L5-4: Governance gap — no policy for a new AI use case
    {
        "curveball_code": "CB-L5-4",
        "curveball_type": "governance_gap",
        "level": 5,
        "exercise_title": "The Store Camera AI Nobody Approved",
        "scenario_text": (
            "A store manager at Harris Farm Gladesville — who is a keen Level "
            "3 Skills Academy graduate — has independently connected the "
            "store's security cameras to an AI vision model. The system:\n\n"
            "1. Counts foot traffic by hour and maps customer flow patterns.\n"
            "2. Estimates queue lengths and alerts when checkouts need more "
            "staff.\n"
            "3. Detects when fresh produce displays are depleted and alerts "
            "the team to restock.\n"
            "4. Identifies 'browsing vs buying' behaviour patterns to "
            "optimise store layout.\n\n"
            "The system works well. Shrink is down 4%, restocking speed is "
            "up 30%, and staffing efficiency has improved. The store manager "
            "presents it to the regional meeting as a success story.\n\n"
            "But: no privacy impact assessment was done. No customer consent "
            "mechanism exists. No data retention policy covers the video "
            "analytics. The system was not reviewed by Legal, IT, or the "
            "WATCHDOG governance framework. There is no Harris Farm policy "
            "on AI-powered surveillance.\n\n"
            "You are the AI lead. How do you handle this?"
        ),
        "coaching_text": (
            "This is a genuine governance dilemma. The technology works and "
            "delivers real value — but it was deployed without any of the "
            "safeguards that protect the business and its customers.\n\n"
            "The right response balances four things:\n\n"
            "1. ACKNOWLEDGE THE INNOVATION: The store manager showed "
            "initiative and skill. The results are real. Do not punish "
            "innovation — that kills the culture you are trying to build.\n\n"
            "2. PAUSE THE SYSTEM: The camera AI must be paused (not "
            "deleted) until a proper review is completed. This is not "
            "punishment — it is responsible governance. Explain to the "
            "store manager that great tech deployed without governance can "
            "become a liability.\n\n"
            "3. CLOSE THE GAP: Work with Legal, IT, and P&C to create:\n"
            "   - An AI-powered surveillance policy\n"
            "   - A privacy impact assessment template\n"
            "   - Customer notification requirements (signage, opt-out)\n"
            "   - Data retention and deletion schedules\n"
            "   - WATCHDOG review checklist for new AI deployments\n\n"
            "4. CREATE THE PATH: Once the policy exists, help the store "
            "manager bring the system into compliance and relaunch it "
            "properly. This becomes the template for other stores.\n\n"
            "The meta-lesson: at Level 5, you are not just building AI — "
            "you are building the governance framework that makes AI safe "
            "at organisational scale."
        ),
        "scoring_criteria": (
            "Score 1-5 based on governance response:\n"
            "5: Acknowledges the innovation positively. Pauses the system "
            "for review (not permanently kills it). Identifies specific "
            "governance gaps (privacy assessment, consent, retention, "
            "WATCHDOG). Creates a policy framework and a path to compliant "
            "relaunch. Protects the store manager's reputation while "
            "enforcing process.\n"
            "4: Pauses and creates policy, but either does not acknowledge "
            "the innovation or does not provide a path to relaunch.\n"
            "3: Recognises the governance gap but proposes only 'getting "
            "Legal to check it' without building a reusable framework.\n"
            "2: Either shuts it down permanently (killing innovation) or "
            "lets it continue with a vague 'we should look into the "
            "privacy stuff at some point.'\n"
            "1: Lets it continue as-is because 'it works' and the results "
            "justify the risk, or immediately escalates it as a "
            "disciplinary matter."
        ),
        "pass_threshold": 3.5,
        "context_tag": "digital",
    },

    # CB-L5-5: Cross-department conflict — two departments want contradictory
    # things from the same AI system
    {
        "curveball_code": "CB-L5-5",
        "curveball_type": "cross_department",
        "level": 5,
        "exercise_title": "Marketing vs Operations: The Recommendation Engine War",
        "scenario_text": (
            "You have built a customer recommendation engine for Harris Farm's "
            "online store. It suggests products based on purchase history, "
            "seasonal trends, and basket analysis. Two departments now want "
            "conflicting changes:\n\n"
            "MARKETING (Laura's team) wants the engine to:\n"
            "- Prioritise new and premium products to drive trial and "
            "  increase average basket value.\n"
            "- Feature seasonal hero items (e.g., stone fruit in summer) "
            "  prominently.\n"
            "- Promote Harris Farm branded products over competitors.\n"
            "- Target lapsed customers with 'win-back' recommendations.\n\n"
            "OPERATIONS (the buying team) wants the engine to:\n"
            "- Prioritise high-margin products to improve gross profit.\n"
            "- Push products approaching use-by to reduce shrink.\n"
            "- Avoid recommending items with supply chain constraints.\n"
            "- Deprioritise slow-moving lines to clear excess stock.\n\n"
            "Both teams believe their priorities are correct and aligned with "
            "company strategy. The recommendations are fundamentally different "
            "— pushing premium new products vs pushing high-margin short-dated "
            "stock creates a very different customer experience.\n\n"
            "You own the system. How do you resolve this?"
        ),
        "coaching_text": (
            "This is a systems design problem disguised as a people problem. "
            "Both teams are right within their domain — Marketing is optimising "
            "for customer lifetime value, Operations is optimising for "
            "operational efficiency. The conflict exists because the system "
            "has a single recommendation slot trying to serve two masters.\n\n"
            "Resolution approach:\n\n"
            "1. MAP THE OBJECTIVES: Create a matrix showing each team's "
            "goals and where they conflict vs complement. Promotion of "
            "Harris Farm branded products (Marketing) and high-margin "
            "products (Operations) might actually align. Short-dated stock "
            "clearance and premium trial are genuinely in tension.\n\n"
            "2. DESIGN FOR BOTH: Split the recommendation system into "
            "contexts:\n"
            "   - Homepage hero: Marketing controls (brand, seasonal, trial)\n"
            "   - Cart add-ons: Operations controls (margin, clearance)\n"
            "   - Re-engagement emails: Marketing controls (win-back)\n"
            "   - Substitution suggestions: Operations controls (availability)\n\n"
            "3. CREATE A WEIGHTING FRAMEWORK: For shared recommendation "
            "spaces, define a scoring algorithm that weights both objectives. "
            "Example: 40% customer relevance, 30% margin, 20% freshness "
            "urgency, 10% brand priority. Make the weights transparent and "
            "adjustable.\n\n"
            "4. ESCALATION PATH: When weights produce a bad outcome (e.g., "
            "recommending near-expired premium cheese at full price), the "
            "system flags it for human review.\n\n"
            "5. SHARED METRICS: Both teams report on a combined metric — "
            "recommendation click-through AND margin per recommended item. "
            "This forces alignment.\n\n"
            "The worst outcome: letting one team 'win' and the other feel "
            "overridden. The best outcome: a system smart enough to serve "
            "both goals in the right context."
        ),
        "scoring_criteria": (
            "Score 1-5 based on conflict resolution and system design:\n"
            "5: Maps the conflict points and complementary points between "
            "both teams. Designs a context-aware system that serves both "
            "objectives in appropriate contexts. Creates a transparent "
            "weighting framework. Proposes shared metrics that align "
            "incentives. Neither team 'loses.' Shows genuine systems "
            "thinking.\n"
            "4: Proposes a reasonable split or weighting system, but does "
            "not fully map the complementary points or create shared "
            "metrics.\n"
            "3: Suggests a compromise (50/50 split of recommendations) "
            "that satisfies neither team optimally, or escalates to "
            "leadership to decide.\n"
            "2: Picks one team's priorities as 'more important' and "
            "deprioritises the other's.\n"
            "1: Tries to build a single algorithm that somehow satisfies "
            "all requirements simultaneously without acknowledging the "
            "trade-offs."
        ),
        "pass_threshold": 3.5,
        "context_tag": "strategy",
    },
]

# ---------------------------------------------------------------------------
# Assembled dictionary — keyed by level number
# ---------------------------------------------------------------------------

V4_CURVEBALLS = {
    1: _LEVEL_1_CURVEBALLS,
    2: _LEVEL_2_CURVEBALLS,
    3: _LEVEL_3_CURVEBALLS,
    4: _LEVEL_4_CURVEBALLS,
    5: _LEVEL_5_CURVEBALLS,
}  # type: Dict[int, List[dict]]


# ---------------------------------------------------------------------------
# Seeding helper
# ---------------------------------------------------------------------------

def get_curveballs_for_seeding():
    # type: () -> List[dict]
    """Flatten all curveballs into a list of dicts for sa_v4_schema.seed_v4_exercises().
    Maps to the exercise table with is_curveball=True."""
    exercises = []
    for level, cbs in V4_CURVEBALLS.items():
        # Map level to module_code (L1 for level 1, etc.)
        module_code = "L{}".format(level) if level <= 5 else "L5"
        for cb in cbs:
            exercises.append({
                "module_code": module_code,
                "tier": "standard",  # Curveballs don't have tiers
                "context_tag": cb["context_tag"],
                "is_curveball": True,
                "curveball_type": cb["curveball_type"],
                "exercise_title": cb["exercise_title"],
                "scenario_text": cb["scenario_text"],
                "expected_approach": cb["scoring_criteria"],
                "rubric_code": (
                    "foundational" if level <= 2
                    else ("advanced_output" if level <= 4 else "multi_tier_panel")
                ),
                "pass_score": cb["pass_threshold"],
                "xp_reward": 20,
            })
    return exercises


def get_curveball_by_code(code):
    # type: (str) -> Optional[dict]
    """Look up a single curveball by its code (e.g. 'CB-L3-2').
    Returns None if not found."""
    for _level, cbs in V4_CURVEBALLS.items():
        for cb in cbs:
            if cb["curveball_code"] == code:
                return cb
    return None


def get_curveball_types_for_level(level):
    # type: (int) -> List[str]
    """Return the list of curveball_type strings for a given level."""
    cbs = V4_CURVEBALLS.get(level, [])
    return [cb["curveball_type"] for cb in cbs]


def get_coaching_text(curveball_code):
    # type: (str) -> Optional[str]
    """Return the coaching text for a curveball, used when the user scores below
    the pass threshold."""
    cb = get_curveball_by_code(curveball_code)
    if cb:
        return cb["coaching_text"]
    return None
