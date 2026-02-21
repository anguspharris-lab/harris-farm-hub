"""
Harris Farm Hub — Growing Legends Academy Content
All static constants for the Academy page. Mirrors the pattern used by
learning_content.py and training_content.py.
"""

# ---------------------------------------------------------------------------
# 6-LEVEL MATURITY MODEL
# Seed → Sprout → Grower → Harvester → Cultivator → Legend
# ---------------------------------------------------------------------------

MATURITY_LEVELS = [
    {
        "name": "Seed",
        "icon": "\U0001f331",
        "tagline": "Just planted",
        "color": "#dcfce7",
        "text_color": "#166534",
        "description": (
            "You know AI exists and you're curious. You haven't used it at work yet, "
            "but you're ready to learn."
        ),
        "skills": [
            "Can log in to Claude or ChatGPT",
            "Understands what a prompt is",
            "Knows AI can help with everyday tasks",
        ],
        "exercises": [
            "Complete L1: AI Basics in the Learning Centre",
            "Ask Claude one question about your department",
            "Read the Company Knowledge module K1",
        ],
        "rubric_threshold": "0-8 / 25",
        "learning_centre_modules": ["L1", "K1"],
        "recommended_path": "AI Foundations",
    },
    {
        "name": "Sprout",
        "icon": "\U0001f33f",
        "tagline": "First shoots",
        "color": "#bbf7d0",
        "text_color": "#166534",
        "description": (
            "You use AI for simple tasks — drafting emails, looking up info, "
            "basic questions. You know it's not always right."
        ),
        "skills": [
            "Can write a basic prompt with a clear question",
            "Understands AI can be wrong (hallucinations)",
            "Uses AI at least once a week",
            "Can identify a good vs bad AI answer",
        ],
        "exercises": [
            "Complete L2: Prompt Basics in the Learning Centre",
            "Write 3 prompts using the Prompt Builder",
            "Score an AI response using the 5 building blocks",
        ],
        "rubric_threshold": "9-13 / 25",
        "learning_centre_modules": ["L2", "K2"],
        "recommended_path": "Prompt Craft",
    },
    {
        "name": "Grower",
        "icon": "\U0001f33b",
        "tagline": "Growing strong",
        "color": "#86efac",
        "text_color": "#14532d",
        "description": (
            "You use AI daily with structure. You apply the Role-Context-Task "
            "pattern and iterate on outputs to get better results."
        ),
        "skills": [
            "Uses Role / Context / Task / Format / Constraints pattern",
            "Can iterate on AI outputs to improve quality",
            "Understands when to use AI vs when not to",
            "Scores 14+ on the prompt quality rubric",
        ],
        "exercises": [
            "Complete L3: Advanced Prompting",
            "Complete 3 Intermediate challenges in The Rubric",
            "Start D1: Data Basics",
        ],
        "rubric_threshold": "14-17 / 25",
        "learning_centre_modules": ["L3", "D1", "K3"],
        "recommended_path": "Prompt Engineering",
    },
    {
        "name": "Harvester",
        "icon": "\U0001f9fa",
        "tagline": "Reaping results",
        "color": "#4ade80",
        "text_color": "#14532d",
        "description": (
            "You build workflows using AI and teach others. Chain of thought, "
            "few-shot examples, and structured outputs are your tools."
        ),
        "skills": [
            "Uses chain of thought prompting",
            "Applies few-shot examples effectively",
            "Creates structured output formats (tables, JSON)",
            "Writes data analysis prompts with SQL awareness",
            "Teaches colleagues how to use AI",
        ],
        "exercises": [
            "Complete all Advanced challenges in The Rubric",
            "Complete D2 and D3 data modules",
            "Submit a prompt to the Arena",
            "Help a Seed or Sprout colleague level up",
        ],
        "rubric_threshold": "18-20 / 25",
        "learning_centre_modules": ["L4", "D2", "D3", "K4"],
        "recommended_path": "Data Intelligence",
    },
    {
        "name": "Cultivator",
        "icon": "\U0001f333",
        "tagline": "Shaping the farm",
        "color": "#22c55e",
        "text_color": "#f0fdf4",
        "description": (
            "You design AI solutions for the business. Multi-step workflows, "
            "API integration, evaluation rubrics — you build tools that others use."
        ),
        "skills": [
            "Designs multi-step AI workflows end to end",
            "Understands API integration and data pipelines",
            "Creates and uses evaluation rubrics",
            "Builds reusable prompt templates",
            "Participates actively in the Arena",
        ],
        "exercises": [
            "Complete D4: Building with Claude Code",
            "Master all 7 prompt patterns",
            "Win or place in an Arena challenge",
            "Contribute to the Hub Showcase",
        ],
        "rubric_threshold": "21-23 / 25",
        "learning_centre_modules": ["D4"],
        "recommended_path": "Building with Claude Code",
    },
    {
        "name": "Legend",
        "icon": "\U0001f3c6",
        "tagline": "A growing legend",
        "color": "#166534",
        "text_color": "#f0fdf4",
        "description": (
            "You drive AI strategy across the business. You mentor others, "
            "design rubrics, evaluate AI initiatives at a strategic level, "
            "and lead the transformation."
        ),
        "skills": [
            "Evaluates AI initiatives using the 5-tier strategic rubric",
            "Designs rubrics for new use cases",
            "Mentors team members across all levels",
            "Leads AI adoption in their area",
            "Champions WATCHDOG governance principles",
        ],
        "exercises": [
            "All Learning Centre modules complete",
            "Arena champion (3+ entries, 1+ win)",
            "Showcase contributor (1+ published implementation)",
            "Run a training session for the team",
        ],
        "rubric_threshold": "24-25 / 25",
        "learning_centre_modules": ["All"],
        "recommended_path": "AI Leadership",
    },
]


# ---------------------------------------------------------------------------
# 7 PROMPT PATTERNS — Advanced Techniques
# ---------------------------------------------------------------------------

PROMPT_PATTERNS = [
    {
        "name": "Chain of Thought",
        "icon": "\U0001f9e0",
        "level": "Grower",
        "why": (
            "Asking the AI to think step-by-step forces it to show its reasoning, "
            "reducing errors and making the logic auditable."
        ),
        "description": "Ask the AI to reason through a problem step by step before giving an answer.",
        "hfm_example": (
            "You are a Harris Farm produce buyer. A supplier has offered 500kg of "
            "organic strawberries at $4.50/kg when we normally pay $5.20/kg. "
            "Think through this step by step: What's the total saving? What's the "
            "risk (shelf life, quality)? What's our current strawberry wastage rate? "
            "Should we take the deal? Show your reasoning before your recommendation."
        ),
        "scored_6_prompt": "Should we buy cheap strawberries from the new supplier?",
        "scored_9_prompt": (
            "You are a Harris Farm buying analyst. A supplier offers 500kg organic "
            "strawberries at $4.50/kg vs our usual $5.20/kg. Think step by step: "
            "1) Calculate the saving, 2) Assess shelf-life risk given our 4-day "
            "average sell-through, 3) Check if current wastage rate justifies extra "
            "volume, 4) Recommend accept/reject with conditions."
        ),
        "scored_6_explanation": "No role, no data, no structure. AI has to guess everything.",
        "scored_9_explanation": (
            "Clear role, specific numbers, step-by-step structure, "
            "and a decision framework. AI can give a traceable answer."
        ),
    },
    {
        "name": "Role Prompting",
        "icon": "\U0001f3ad",
        "level": "Sprout",
        "why": (
            "Giving the AI a specific persona activates relevant knowledge "
            "and adjusts tone, depth, and perspective to match the role."
        ),
        "description": "Tell the AI who to be — their role, expertise, and perspective.",
        "hfm_example": (
            "You are a Harris Farm store manager at the Bondi store with 12 years "
            "of experience in fresh produce. You're known for keeping wastage below "
            "2% and mentoring new team members. A new starter asks you: 'What are "
            "the 5 most important things I need to know in my first week?'"
        ),
        "scored_6_prompt": "What should a new person at Harris Farm know?",
        "scored_9_prompt": (
            "You are a Harris Farm Bondi store manager with 12 years of experience "
            "and a reputation for low wastage. Give a new team member the 5 most "
            "important things to learn in their first week, as a numbered list "
            "with one sentence explanation each."
        ),
        "scored_6_explanation": "No role, no store, no specifics. Generic advice incoming.",
        "scored_9_explanation": (
            "Specific role with credibility markers, named store, "
            "clear format (numbered list), and practical scope (first week)."
        ),
    },
    {
        "name": "Few-Shot Examples",
        "icon": "\U0001f4cb",
        "level": "Harvester",
        "why": (
            "Showing the AI 2-3 examples of what you want teaches it the exact "
            "format, tone, and level of detail — far more effective than describing it."
        ),
        "description": "Give the AI examples of the input/output format you want before asking your question.",
        "hfm_example": (
            "You are a Harris Farm category analyst. I need product descriptions "
            "in this exact format:\n\n"
            "Example 1:\n"
            "Product: Organic Fuji Apples 1kg\n"
            "Hook: Crisp, sweet, and grown without synthetic pesticides\n"
            "Details: Sourced from Orange region NSW. Perfect for lunchboxes.\n\n"
            "Example 2:\n"
            "Product: Free Range Eggs 12pk\n"
            "Hook: From happy hens with room to roam\n"
            "Details: RSPCA approved. Bright orange yolks. Farm to shelf in 48hrs.\n\n"
            "Now write descriptions for: Hass Avocados (3pk), Sourdough Loaf, "
            "Barramundi Fillet 200g"
        ),
        "scored_6_prompt": "Write product descriptions for avocados, bread, and fish.",
        "scored_9_prompt": (
            "You are a Harris Farm copywriter. Here are two examples of our style:\n"
            "[Example 1: Organic Fuji Apples — Hook + Details format]\n"
            "[Example 2: Free Range Eggs — Hook + Details format]\n"
            "Now write 3 more in the same format for: Hass Avocados (3pk), "
            "Sourdough Loaf, Barramundi Fillet 200g."
        ),
        "scored_6_explanation": "No examples, no format, no brand voice. AI guesses the style.",
        "scored_9_explanation": (
            "Two concrete examples teach the format perfectly. "
            "AI replicates the Hook + Details pattern with HFM voice."
        ),
    },
    {
        "name": "Structured Output",
        "icon": "\U0001f4ca",
        "level": "Grower",
        "why": (
            "Requesting a specific output format (table, JSON, numbered list) "
            "makes the response immediately usable without reformatting."
        ),
        "description": "Tell the AI exactly how to format the response — table, JSON, bullet points, etc.",
        "hfm_example": (
            "You are a Harris Farm operations analyst. Compare wastage rates "
            "across 5 departments for last month. Present as a markdown table with "
            "columns: Department | Wastage % | Dollar Value | vs Target | Action "
            "Required. Sort by highest wastage first."
        ),
        "scored_6_prompt": "Tell me about wastage across departments.",
        "scored_9_prompt": (
            "Compare wastage across 5 departments as a markdown table: "
            "Department | Wastage % | $ Value | vs Target | Action. "
            "Sort by highest wastage. Flag any department above 3% target in bold."
        ),
        "scored_6_explanation": "No format specified. AI returns a wall of text.",
        "scored_9_explanation": (
            "Exact table columns, sort order, and conditional formatting. "
            "Output is immediately usable in a report."
        ),
    },
    {
        "name": "Constraint Setting",
        "icon": "\U0001f3af",
        "level": "Grower",
        "why": (
            "Constraints prevent the AI from going too broad or too deep. "
            "They keep answers focused, relevant, and the right length."
        ),
        "description": "Set limits: time period, number of items, what to include/exclude, word count.",
        "hfm_example": (
            "You are a Harris Farm finance analyst. Identify the top 3 stores "
            "with the highest shrinkage rate in the last 4 weeks. Exclude seasonal "
            "lines. Keep each analysis to 2 sentences maximum. Include the dollar "
            "impact and one specific action per store."
        ),
        "scored_6_prompt": "Which stores have high shrinkage?",
        "scored_9_prompt": (
            "Top 3 stores by shrinkage in last 4 weeks. Exclude seasonal lines. "
            "For each: 2 sentences max, dollar impact, and 1 specific action. "
            "Present as a numbered list."
        ),
        "scored_6_explanation": "No time period, no limit, no exclusions. AI dumps everything.",
        "scored_9_explanation": (
            "Time-boxed (4 weeks), limited (top 3), exclusions set, "
            "length capped, actionable output requested."
        ),
    },
    {
        "name": "Iterative Refinement",
        "icon": "\U0001f504",
        "level": "Harvester",
        "why": (
            "AI rarely gets it perfect first try. Iterative refinement — asking "
            "for improvements on the output — is how experts get great results."
        ),
        "description": "Start broad, then refine: ask for improvements, more detail, or a different angle.",
        "hfm_example": (
            "Step 1: 'List the main causes of avocado wastage at Harris Farm.'\n"
            "Step 2: 'Good. Now rank those by estimated dollar impact for the "
            "Bondi store specifically.'\n"
            "Step 3: 'For the top cause, give me a detailed 2-week action plan "
            "that the store manager can implement starting Monday.'"
        ),
        "scored_6_prompt": "Fix our avocado wastage problem.",
        "scored_9_prompt": (
            "[Multi-turn conversation]\n"
            "Turn 1: List main causes of avocado wastage at Harris Farm\n"
            "Turn 2: Rank by dollar impact for Bondi store\n"
            "Turn 3: Detail a 2-week action plan for the top cause"
        ),
        "scored_6_explanation": "One vague question expecting a complete answer.",
        "scored_9_explanation": (
            "Progressive refinement: broad → specific → actionable. "
            "Each turn builds on the previous output."
        ),
    },
    {
        "name": "Context Loading",
        "icon": "\U0001f4da",
        "level": "Cultivator",
        "why": (
            "Giving the AI relevant data, documents, or context before asking "
            "a question dramatically improves accuracy and specificity."
        ),
        "description": "Provide the AI with relevant data, rules, or documents before asking your question.",
        "hfm_example": (
            "Here is our 5-4-4 fiscal calendar for FY25:\n"
            "[paste fiscal calendar]\n\n"
            "And here are our Golden Rules for produce ordering:\n"
            "[paste golden rules]\n\n"
            "Based on these rules and the current fiscal period, "
            "recommend the optimal ordering schedule for stone fruit "
            "at the Pennant Hills store for the next 2 weeks."
        ),
        "scored_6_prompt": "When should we order stone fruit?",
        "scored_9_prompt": (
            "Given our 5-4-4 fiscal calendar [attached] and Golden Rules "
            "for produce ordering [attached], recommend the optimal stone fruit "
            "ordering schedule for Pennant Hills store for the next 2 weeks. "
            "Account for the current fiscal period and weekend uplift patterns."
        ),
        "scored_6_explanation": "No context, no data, no rules. AI invents everything.",
        "scored_9_explanation": (
            "Real documents loaded as context. AI answers within "
            "the boundaries of actual Harris Farm rules and data."
        ),
    },
]


# ---------------------------------------------------------------------------
# 5-TIER EVALUATION RUBRIC BREAKDOWN (augmented from agent_teams.py)
# ---------------------------------------------------------------------------

RUBRIC_TIER_BREAKDOWN = [
    {
        "id": "cto",
        "name": "CTO Panel",
        "max_points": 25,
        "panelists": "CTO Amazon, CTO Uber, CTO Anthropic, CTO OpenAI, CTO Canva",
        "criteria_count": 5,
        "what_8_looks_like": (
            "Technically sound, uses existing data sources, integrates cleanly "
            "with the Hub's Streamlit/FastAPI stack, scales to all 34 stores, "
            "and follows WATCHDOG governance."
        ),
        "what_5_looks_like": (
            "Technically possible but requires new infrastructure, has data gaps, "
            "integration is unclear, or governance is an afterthought."
        ),
    },
    {
        "id": "clo",
        "name": "CLO Panel",
        "max_points": 25,
        "panelists": "CLO McKinsey, CLO Bain, CLO Kearney, CLO Google, CLO Amazon",
        "criteria_count": 5,
        "what_8_looks_like": (
            "Genuinely upskills the team, easy to adopt without heavy training, "
            "knowledge transfers naturally, serves existing roles, "
            "and builds lasting capability."
        ),
        "what_5_looks_like": (
            "Some learning value but adoption requires extensive training, "
            "knowledge stays with one person, or it creates work rather "
            "than reducing it."
        ),
    },
    {
        "id": "strategic",
        "name": "Strategic Alignment",
        "max_points": 30,
        "panelists": "Harris Farm Board",
        "criteria_count": 6,
        "what_8_looks_like": (
            "Clear revenue or cost impact, improves the customer experience, "
            "differentiates from Coles/Woolworths, aligns with premium fresh "
            "positioning, and considers sustainability."
        ),
        "what_5_looks_like": (
            "Nice to have but no clear financial impact, could apply to any "
            "retailer (not HFM-specific), or sustainability isn't considered."
        ),
    },
    {
        "id": "implementation",
        "name": "Implementation Readiness",
        "max_points": 25,
        "panelists": "Implementation Committee",
        "criteria_count": 5,
        "what_8_looks_like": (
            "Lean resource plan, realistic timeline with milestones, "
            "risks identified with mitigations, dependencies mapped, "
            "and clear KPIs defined."
        ),
        "what_5_looks_like": (
            "Ambitious timeline, understaffed plan, risks hand-waved, "
            "dependencies unclear, or success criteria are vague."
        ),
    },
    {
        "id": "presentation",
        "name": "Presentation Rubric",
        "max_points": 25,
        "panelists": "Communication Board",
        "criteria_count": 5,
        "what_8_looks_like": (
            "Crystal clear proposal, claims backed by data, compelling "
            "narrative with logical flow, specific action items with owners, "
            "and clean visual communication."
        ),
        "what_5_looks_like": (
            "Understandable but dense, some unsupported claims, "
            "rambling structure, vague next steps, or walls of text "
            "without visuals."
        ),
    },
]


# ---------------------------------------------------------------------------
# "SCORE THIS" EXERCISES — Interactive Learning
# ---------------------------------------------------------------------------

SCORE_THIS_EXERCISES = [
    {
        "label": "The Vague One",
        "prompt": "Tell me about our customers.",
        "expected_score": "~6 / 25",
        "explanation": (
            "No role, no context, no specifics, no format, no constraints. "
            "The AI has to guess everything. This is a Seed-level prompt — "
            "it works but gives generic, unhelpful output."
        ),
    },
    {
        "label": "The Decent One",
        "prompt": (
            "You are a Harris Farm customer analyst. What are the top 5 reasons "
            "customers shop at our Bondi store? Present as a numbered list."
        ),
        "expected_score": "~16 / 25",
        "explanation": (
            "Has a role and format, mentions a specific store, and asks a clear "
            "question. Missing: time period, data source, constraints, and what "
            "to do with the findings. Solid Grower-level prompt."
        ),
    },
    {
        "label": "The Excellent One",
        "prompt": (
            "You are a Harris Farm customer insights analyst with access to our "
            "loyalty data. Analyse the top 5 reasons customers choose our Bondi "
            "store over nearby competitors, based on the last 12 months of "
            "transaction and survey data. Present as a table with columns: "
            "Reason | Evidence (data point) | Strength (1-5) | Action to "
            "Reinforce. Exclude price — focus on non-price differentiators. "
            "Keep each reason to one sentence."
        ),
        "expected_score": "~23 / 25",
        "explanation": (
            "All 5 building blocks present: Role (analyst), Context (loyalty data, "
            "Bondi, competitors), Task (analyse reasons), Format (table with "
            "specific columns), Constraints (12 months, exclude price, one sentence). "
            "This is Harvester/Cultivator level — the output is immediately actionable."
        ),
    },
]


# ---------------------------------------------------------------------------
# 6 LEARNING PATHS — Mapped to Maturity Levels
# ---------------------------------------------------------------------------

LEARNING_PATHS = [
    {
        "name": "AI Foundations",
        "audience": "Everyone",
        "levels": "Seed \u2192 Sprout",
        "hours": "~2 hrs",
        "tagline": "Your first steps with AI",
        "color": "#dcfce7",
        "text_color": "#166534",
        "goal_tags": ["G3"],
        "description": (
            "Start here if you've never used AI at work. Learn what AI can do, "
            "how to ask it questions, and why it sometimes gets things wrong."
        ),
        "modules": [
            {"id": "L1", "name": "AI Basics", "type": "AI Prompting"},
            {"id": "K1", "name": "Company Knowledge", "type": "Knowledge"},
            {"id": "L2", "name": "Prompt Basics", "type": "AI Prompting"},
        ],
    },
    {
        "name": "Prompt Craft",
        "audience": "All Staff",
        "levels": "Sprout \u2192 Grower",
        "hours": "~3 hrs",
        "tagline": "Write prompts that actually work",
        "color": "#bbf7d0",
        "text_color": "#166534",
        "goal_tags": ["G3"],
        "description": (
            "Master the 5 building blocks of a great prompt. Learn Role, Context, "
            "Task, Format, and Constraints through Harris Farm examples."
        ),
        "modules": [
            {"id": "L2", "name": "Prompt Basics", "type": "AI Prompting"},
            {"id": "L3", "name": "Advanced Prompting", "type": "AI Prompting"},
            {"id": "K2", "name": "Store Operations", "type": "Knowledge"},
            {"id": "K3", "name": "Product Knowledge", "type": "Knowledge"},
        ],
    },
    {
        "name": "Data Intelligence",
        "audience": "Analysts",
        "levels": "Grower \u2192 Harvester",
        "hours": "~3 hrs",
        "tagline": "Turn data into decisions",
        "color": "#86efac",
        "text_color": "#14532d",
        "goal_tags": ["G2", "G3"],
        "description": (
            "Learn to prompt AI for data analysis. Query transaction data, "
            "interpret sales trends, and build data-backed recommendations."
        ),
        "modules": [
            {"id": "D1", "name": "Data Basics", "type": "Data Prompting"},
            {"id": "D2", "name": "Transaction Analysis", "type": "Data Prompting"},
            {"id": "D3", "name": "Advanced Queries", "type": "Data Prompting"},
            {"id": "D4", "name": "Building with Claude Code", "type": "Data Prompting"},
        ],
    },
    {
        "name": "Prompt Engineering",
        "audience": "Power Users",
        "levels": "Grower \u2192 Harvester",
        "hours": "~4 hrs",
        "tagline": "Master advanced techniques",
        "color": "#4ade80",
        "text_color": "#14532d",
        "goal_tags": ["G3"],
        "description": (
            "Go beyond the basics. Learn chain of thought, few-shot examples, "
            "structured outputs, and the 7 prompt patterns that experts use."
        ),
        "modules": [
            {"id": "L3", "name": "Advanced Prompting", "type": "AI Prompting"},
            {"id": "L4", "name": "Expert Techniques", "type": "AI Prompting"},
            {"id": "Patterns", "name": "All 7 Prompt Patterns", "type": "Academy"},
        ],
    },
    {
        "name": "Building with Claude Code",
        "audience": "IT Team",
        "levels": "Harvester \u2192 Cultivator",
        "hours": "~5 hrs",
        "tagline": "Build AI-powered tools",
        "color": "#22c55e",
        "text_color": "#f0fdf4",
        "goal_tags": ["G3", "G5"],
        "description": (
            "Build real tools using Claude Code. API integration, multi-step "
            "workflows, evaluation rubrics, and contributing to the Hub."
        ),
        "modules": [
            {"id": "L4", "name": "Expert Techniques", "type": "AI Prompting"},
            {"id": "D2", "name": "Transaction Analysis", "type": "Data Prompting"},
            {"id": "D4", "name": "Building with Claude Code", "type": "Data Prompting"},
            {"id": "Arena", "name": "Arena Participation", "type": "Academy"},
        ],
    },
    {
        "name": "AI Leadership",
        "audience": "Managers",
        "levels": "Cultivator \u2192 Legend",
        "hours": "~3 hrs",
        "tagline": "Lead AI transformation",
        "color": "#166534",
        "text_color": "#f0fdf4",
        "goal_tags": ["G1", "G3"],
        "description": (
            "Evaluate AI initiatives using the 5-tier strategic rubric. "
            "Design rubrics for your team, mentor others, and drive adoption."
        ),
        "modules": [
            {"id": "Rubric", "name": "5-Tier Evaluation Mastery", "type": "Academy"},
            {"id": "Arena", "name": "Arena Challenges", "type": "Academy"},
            {"id": "Showcase", "name": "Showcase Contributions", "type": "Academy"},
            {"id": "Mentoring", "name": "Teaching & Mentoring", "type": "Academy"},
        ],
    },
]


# ---------------------------------------------------------------------------
# ARENA CHALLENGES
# ---------------------------------------------------------------------------

ARENA_CHALLENGES = [
    {
        "week": "Current",
        "title": "Wastage Reduction Prompt",
        "description": (
            "Write a prompt that analyses fresh produce wastage across all stores "
            "and recommends the single highest-impact action for each department. "
            "Must be specific enough for a store manager to act on Monday morning."
        ),
        "difficulty": "Intermediate",
        "status": "active",
        "goal_tags": ["G4", "G2"],
    },
    {
        "week": "Week 3",
        "title": "Customer Segmentation Brief",
        "description": (
            "Design a prompt that segments Harris Farm customers into 4-6 groups "
            "based on purchase behaviour, then recommends targeted marketing "
            "actions for each segment."
        ),
        "difficulty": "Advanced",
        "status": "past",
        "goal_tags": ["G1", "G2"],
    },
    {
        "week": "Week 2",
        "title": "Supplier Scorecard",
        "description": (
            "Create a prompt that builds a supplier reliability scorecard "
            "with 5 criteria scored 1-5, usable by the buying team weekly."
        ),
        "difficulty": "Advanced",
        "status": "past",
        "goal_tags": ["G4"],
    },
    {
        "week": "Week 1",
        "title": "New Starter Onboarding Guide",
        "description": (
            "Write a prompt that generates a department-specific first-week "
            "guide for new team members. Should cover golden rules, key people, "
            "and common mistakes to avoid."
        ),
        "difficulty": "Beginner",
        "status": "past",
        "goal_tags": ["G3"],
    },
    {
        "week": "Launch Week",
        "title": "My Department in 30 Seconds",
        "description": (
            "Write a prompt that generates a 30-second elevator pitch for your "
            "department — what you do, why it matters, and one thing you're "
            "proud of this month."
        ),
        "difficulty": "Beginner",
        "status": "past",
        "goal_tags": ["G3"],
    },
]


# ---------------------------------------------------------------------------
# TOP SHOWCASE IMPLEMENTATIONS
# ---------------------------------------------------------------------------

TOP_SHOWCASE = [
    {
        "name": "Transaction Query Engine",
        "stat": "383M rows queryable via natural language",
        "description": "Ask questions about 3 years of transaction data in plain English.",
        "goal_tags": ["G2"],
    },
    {
        "name": "Product Hierarchy Navigator",
        "stat": "72,911 products mapped",
        "description": "Navigate the full product tree from department to PLU.",
        "goal_tags": ["G2", "G4"],
    },
    {
        "name": "5-4-4 Fiscal Calendar",
        "stat": "Zero manual date calculations",
        "description": "Automated fiscal period mapping across all dashboards.",
        "goal_tags": ["G2"],
    },
    {
        "name": "Multi-LLM Evaluation Arena",
        "stat": "5 AI teams compete on real prompts",
        "description": "Compare Claude, GPT, Gemini and more side-by-side.",
        "goal_tags": ["G3", "G5"],
    },
    {
        "name": "WATCHDOG Governance",
        "stat": "7 Laws, zero violations",
        "description": "Automated safety scanning, audit trails, and compliance checks.",
        "goal_tags": ["G5"],
    },
]


# ---------------------------------------------------------------------------
# SITE QUALITY RUBRICS — Continuous Improvement Tools
# ---------------------------------------------------------------------------

DASHBOARD_QUALITY_RUBRIC = {
    "name": "Dashboard Quality Rubric",
    "max_points": 35,
    "description": "Use this to evaluate any data dashboard in the Hub.",
    "criteria": [
        {"name": "Data Accuracy", "max": 5,
         "description": "Numbers match source data within +/- 0.01. No silent NaN or Inf values."},
        {"name": "Filter Resilience", "max": 5,
         "description": "Every filter combination degrades gracefully. No red tracebacks visible to users."},
        {"name": "Loading Performance", "max": 5,
         "description": "Page loads in under 3 seconds on Render. Caching used where appropriate."},
        {"name": "Visual Clarity", "max": 5,
         "description": "Clear visual hierarchy, no clutter, brand-consistent colours and fonts."},
        {"name": "Actionable Insights", "max": 5,
         "description": "Tells the user what to DO, not just what IS. Recommendations included."},
        {"name": "Error Communication", "max": 5,
         "description": "Failures show helpful st.warning/st.info messages, never raw tracebacks."},
        {"name": "Mobile Readability", "max": 5,
         "description": "Key metrics visible on tablet. Charts resize. No horizontal scroll."},
    ],
}

PAGE_CONTENT_RUBRIC = {
    "name": "Page Content Rubric",
    "max_points": 25,
    "description": "Use this to evaluate any content page in the Hub.",
    "criteria": [
        {"name": "Completeness", "max": 5,
         "description": "All sections have real content, no placeholders or coming soon."},
        {"name": "Harris Farm Relevance", "max": 5,
         "description": "Uses HFM stores, products, real scenarios. Not generic retail examples."},
        {"name": "Cross-linking", "max": 5,
         "description": "Links to related pages, not a dead end. User can continue their journey."},
        {"name": "Learning Value", "max": 5,
         "description": "Reader leaves knowing something they didn't before. Clear takeaways."},
        {"name": "Inspiration", "max": 5,
         "description": "Makes someone WANT to engage with the content. Motivating, not dry."},
    ],
}


# ---------------------------------------------------------------------------
# ACADEMY SELF-SCORE — Walking the Talk
# ---------------------------------------------------------------------------

ACADEMY_SELF_SCORE = {
    "page": "Growing Legends Academy",
    "dashboard_rubric": "N/A — Content page, not a data dashboard",
    "content_rubric": {
        "Completeness": {
            "score": 4,
            "rationale": (
                "All 8 tabs populated with real content. Some Arena challenges "
                "are placeholders until the program matures."
            ),
        },
        "Harris Farm Relevance": {
            "score": 5,
            "rationale": (
                "Every prompt example uses HFM stores, products, and real scenarios. "
                "Maturity levels reference actual Learning Centre modules."
            ),
        },
        "Cross-linking": {
            "score": 5,
            "rationale": (
                "Links to Learning Centre, The Rubric, Prompt Builder, Hub Portal, "
                "Hub Assistant, and WATCHDOG. Quick Links tab provides full navigation."
            ),
        },
        "Learning Value": {
            "score": 5,
            "rationale": (
                "6-level maturity model, 7 prompt patterns with scored comparisons, "
                "interactive Score This exercises, and 6 structured learning paths."
            ),
        },
        "Inspiration": {
            "score": 4,
            "rationale": (
                "Capability journey is motivating. Arena challenges create "
                "competition. Could add more team success stories over time."
            ),
        },
    },
    "content_total": "23 / 25",
}
