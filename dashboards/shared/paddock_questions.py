"""
Harris Farm Hub -- The Paddock Assessment Questions & Reference Data
Ported from the-paddock/server/data/*.js

All 41 questions across 5 modules, scoring functions, store/department/tier
constants, maturity level definitions, and learning path recommendations.
"""
import json
from typing import Optional

# ============================================================================
# STORES & DEPARTMENTS
# ============================================================================

PADDOCK_STORES = [
    # NSW Retail
    {"name": "Pennant Hills", "state": "NSW", "type": "retail"},
    {"name": "St Ives", "state": "NSW", "type": "retail"},
    {"name": "Mosman", "state": "NSW", "type": "retail"},
    {"name": "Willoughby", "state": "NSW", "type": "retail"},
    {"name": "Broadway", "state": "NSW", "type": "retail"},
    {"name": "Erina", "state": "NSW", "type": "retail"},
    {"name": "Orange", "state": "NSW", "type": "retail"},
    {"name": "Manly", "state": "NSW", "type": "retail"},
    {"name": "Mona Vale", "state": "NSW", "type": "retail"},
    {"name": "Baulkham Hills", "state": "NSW", "type": "retail"},
    {"name": "Bowral", "state": "NSW", "type": "retail"},
    {"name": "Cammeray", "state": "NSW", "type": "retail"},
    {"name": "Potts Point", "state": "NSW", "type": "retail"},
    {"name": "Boronia Park", "state": "NSW", "type": "retail"},
    {"name": "Bondi Beach", "state": "NSW", "type": "retail"},
    {"name": "Drummoyne", "state": "NSW", "type": "retail"},
    {"name": "Randwick", "state": "NSW", "type": "retail"},
    {"name": "Leichhardt", "state": "NSW", "type": "retail"},
    {"name": "Bondi Westfield", "state": "NSW", "type": "retail"},
    {"name": "Newcastle", "state": "NSW", "type": "retail"},
    {"name": "Lindfield", "state": "NSW", "type": "retail"},
    {"name": "Albury", "state": "NSW", "type": "retail"},
    {"name": "Rose Bay", "state": "NSW", "type": "retail"},
    {"name": "Lane Cove", "state": "NSW", "type": "retail"},
    {"name": "Dural", "state": "NSW", "type": "retail"},
    {"name": "Redfern", "state": "NSW", "type": "retail"},
    {"name": "Marrickville", "state": "NSW", "type": "retail"},
    {"name": "Miranda", "state": "NSW", "type": "retail"},
    {"name": "Maroubra", "state": "NSW", "type": "retail"},
    # QLD Retail
    {"name": "West End", "state": "QLD", "type": "retail"},
    {"name": "Isle of Capri", "state": "QLD", "type": "retail"},
    {"name": "Clayfield", "state": "QLD", "type": "retail"},
    # ACT
    {"name": "Majura Park", "state": "ACT", "type": "retail"},
    # Operations & Corporate
    {"name": "Greystanes DC", "state": "NSW", "type": "distribution"},
    {"name": "Support Office", "state": "NSW", "type": "corporate"},
    {"name": "Board", "state": "NSW", "type": "governance"},
]

STORE_NAMES = [s["name"] for s in PADDOCK_STORES]

STORE_DEPARTMENTS = [
    "Fruit & Vegetables", "Grocery", "Deli & Cheese", "Butcher",
    "Seafood", "Bakery", "Flowers", "Liquor", "Front End",
    "Store Management", "Warehouse / Receiving",
]

DC_DEPARTMENTS = [
    "Warehouse", "Transport", "Receiving", "Quality Assurance", "DC Management",
]

CORPORATE_DEPARTMENTS = [
    "Finance", "People & Culture", "Marketing", "Supply Chain",
    "IT", "Property", "Buying", "E-Commerce", "Executive",
]

BOARD_DEPARTMENTS = ["Board of Directors"]


def get_departments(store_name):
    # type: (str) -> list
    if store_name == "Greystanes DC":
        return DC_DEPARTMENTS
    if store_name == "Support Office":
        return CORPORATE_DEPARTMENTS
    if store_name == "Board":
        return BOARD_DEPARTMENTS
    return STORE_DEPARTMENTS


def suggest_role_tier(department):
    # type: (str) -> int
    tier1 = ["Warehouse", "Warehouse / Receiving", "Receiving", "Transport", "Front End"]
    tier2 = ["Fruit & Vegetables", "Grocery", "Deli & Cheese", "Butcher",
             "Seafood", "Bakery", "Flowers", "Liquor", "Quality Assurance"]
    tier3 = ["Store Management", "DC Management"]
    tier4 = ["Finance", "People & Culture", "Marketing", "Supply Chain",
             "IT", "Property", "Buying", "E-Commerce"]
    tier5 = ["Executive"]
    tier6 = ["Board of Directors"]
    if department in tier1:
        return 1
    if department in tier2:
        return 2
    if department in tier3:
        return 3
    if department in tier4:
        return 4
    if department in tier5:
        return 5
    if department in tier6:
        return 6
    return 3


ROLE_TIER_LABELS = {
    1: "Floor & Warehouse",
    2: "Shop Floor Specialist",
    3: "Department / Store Manager",
    4: "Support Functions",
    5: "Senior Leadership",
    6: "C-Suite & Board",
}

TECH_COMFORT_OPTIONS = [
    {"value": 1, "label": "Yikes", "emoji": "\U0001f630"},
    {"value": 2, "label": "Nervous", "emoji": "\U0001f62c"},
    {"value": 3, "label": "OK-ish", "emoji": "\U0001f610"},
    {"value": 4, "label": "Comfortable", "emoji": "\U0001f60a"},
    {"value": 5, "label": "Bring it on", "emoji": "\U0001f60e"},
]

AI_EXPERIENCE_OPTIONS = [
    {"value": "regular", "label": "Yes -- I use AI regularly"},
    {"value": "few_times", "label": "Yes -- a few times"},
    {"value": "no_curious", "label": "No, but curious"},
    {"value": "no_unsure", "label": "No, and a bit unsure"},
    {"value": "what_is_ai", "label": "What's AI?"},
]

# ============================================================================
# MATURITY LEVELS & SCORING WEIGHTS
# ============================================================================

MATURITY_LEVELS = [
    {"level": 1, "name": "Seedling", "icon": "\U0001f331", "min": 0, "max": 25,
     "message": "You're just getting started -- and that's great! Every expert was once a beginner."},
    {"level": 2, "name": "Sprout", "icon": "\U0001f33f", "min": 26, "max": 45,
     "message": "You're growing! You've got the basics and you're ready to experiment."},
    {"level": 3, "name": "Grower", "icon": "\U0001fab4", "min": 46, "max": 65,
     "message": "You're building real skills. Keep practising and you'll be a Harvester in no time."},
    {"level": 4, "name": "Harvester", "icon": "\U0001f33e", "min": 66, "max": 85,
     "message": "Impressive! You're confidently using AI and making it work for you."},
    {"level": 5, "name": "Cultivator", "icon": "\U0001f333", "min": 86, "max": 100,
     "message": "You're an AI champion! You could teach others and help shape our AI future."},
]

WEIGHTS = {
    "awareness": 0.15,
    "usage": 0.25,
    "critical": 0.25,
    "applied": 0.25,
    "confidence": 0.10,
}

MODULE_IDS = ["awareness", "usage", "critical", "applied", "confidence"]

MODULE_META = {
    "awareness": {"title": "What's the Buzz?", "subtitle": "How much do you know about AI?", "icon": "\U0001f41d"},
    "usage": {"title": "Getting Your Hands Dirty", "subtitle": "Can you use AI tools effectively?", "icon": "\U0001f331"},
    "critical": {"title": "Reading the Soil", "subtitle": "Can you think critically about AI outputs?", "icon": "\U0001f50d"},
    "applied": {"title": "Growing Season", "subtitle": "Using AI in YOUR role", "icon": "\U0001f33e"},
    "confidence": {"title": "The Harvest", "subtitle": "Let's wrap up -- how are you feeling?", "icon": "\U0001f33b"},
}


def get_maturity(overall_score):
    # type: (int) -> dict
    for m in MATURITY_LEVELS:
        if m["min"] <= overall_score <= m["max"]:
            return m
    return MATURITY_LEVELS[-1]


def calculate_overall(module_scores):
    # type: (dict) -> int
    total = sum(module_scores.get(m, 0) * WEIGHTS[m] for m in MODULE_IDS)
    return round(total)


# ============================================================================
# MODULE 1: "What's the Buzz?" -- AI Awareness (8 questions)
# ============================================================================

MODULE_1_QUESTIONS = [
    {
        "id": "a1",
        "text": "Which of these have you heard of? Select all that apply.",
        "type": "multiple_select",
        "options": [
            {"value": "chatgpt", "label": "ChatGPT"},
            {"value": "claude", "label": "Claude"},
            {"value": "copilot", "label": "Microsoft Copilot"},
            {"value": "siri", "label": "Siri / Google Assistant"},
            {"value": "midjourney", "label": "Midjourney / DALL-E (image AI)"},
            {"value": "none", "label": "None of these ring a bell"},
        ],
    },
    {
        "id": "a2",
        "text": "Which of these tasks could AI realistically help with at Harris Farm?",
        "type": "multiple_select",
        "options": [
            {"value": "forecast", "label": "Predicting how much fruit to order for a long weekend", "correct": True},
            {"value": "roster", "label": "Helping draft a staff roster", "correct": True},
            {"value": "email", "label": "Writing a customer apology email", "correct": True},
            {"value": "taste", "label": "Tasting whether the mangoes are ripe"},
            {"value": "negotiate", "label": "Negotiating with a new produce supplier face-to-face"},
            {"value": "pricing", "label": "Suggesting pricing based on competitor data", "correct": True},
        ],
    },
    {
        "id": "a3",
        "text": "What's the difference between AI making a SUGGESTION and AI making a DECISION?",
        "type": "multiple_choice",
        "options": [
            {"value": "same", "label": "They're basically the same thing"},
            {"value": "suggest_human", "label": "AI suggests options, but a human makes the final call", "correct": True},
            {"value": "ai_better", "label": "AI decisions are always better than human ones"},
            {"value": "unsure", "label": "I'm not sure"},
        ],
    },
    {
        "id": "a4",
        "text": 'A customer asks: "Do you have organic kale in stock?" How could AI help here?',
        "type": "multiple_choice",
        "options": [
            {"value": "check_stock", "label": "Check real-time stock levels and tell you instantly", "correct": True},
            {"value": "grow_kale", "label": "Grow the kale faster in the back room"},
            {"value": "no_help", "label": "It can't help -- you need to walk to the shelf and check"},
            {"value": "replace_staff", "label": "Replace the staff member entirely"},
        ],
    },
    {
        "id": "a5",
        "text": "AI is best described as...",
        "type": "multiple_choice",
        "options": [
            {"value": "robot", "label": "A robot that thinks like a human"},
            {"value": "tool", "label": "A powerful tool that finds patterns in data and helps with tasks", "correct": True},
            {"value": "magic", "label": "Magic software that always gets things right"},
            {"value": "threat", "label": "Something that will replace all jobs"},
        ],
    },
    {
        "id": "a6",
        "text": "Which industry is MOST similar to grocery retail in how it uses AI?",
        "type": "multiple_choice",
        "options": [
            {"value": "space", "label": "Space exploration"},
            {"value": "logistics", "label": "Logistics and supply chain (like Amazon warehouses)", "correct": True},
            {"value": "music", "label": "Music production"},
            {"value": "mining", "label": "Deep sea mining"},
        ],
    },
    {
        "id": "a7",
        "text": "Have you ever seen AI being used at Harris Farm (or heard about it)?",
        "type": "multiple_choice",
        "options": [
            {"value": "yes_use", "label": "Yes -- I've used AI tools at work"},
            {"value": "yes_heard", "label": "Yes -- I've heard about the AI Hub"},
            {"value": "maybe", "label": 'Maybe, but I\'m not sure what counts as "AI"'},
            {"value": "no", "label": "No, this is all new to me"},
        ],
    },
    {
        "id": "a8",
        "text": 'When you hear "Artificial Intelligence", what\'s your first feeling?',
        "type": "multiple_choice",
        "options": [
            {"value": "excited", "label": "Excited -- the future is here!"},
            {"value": "curious", "label": "Curious -- I want to learn more"},
            {"value": "nervous", "label": "A bit nervous -- will it affect my job?"},
            {"value": "confused", "label": "Confused -- I don't really get it yet"},
            {"value": "indifferent", "label": "Meh -- it's just another tech thing"},
        ],
    },
]

# ============================================================================
# MODULE 2: "Getting Your Hands Dirty" -- Basic Usage (8 questions)
# ============================================================================

MODULE_2_QUESTIONS = [
    {
        "id": "u1",
        "text": "Have you ever typed a question or request into an AI chatbot (like ChatGPT or Claude)?",
        "type": "multiple_choice",
        "options": [
            {"value": "daily", "label": "Yes -- I use it regularly"},
            {"value": "few_times", "label": "Yes -- I've tried it a few times"},
            {"value": "once", "label": "Once or twice"},
            {"value": "never", "label": "Never"},
        ],
    },
    {
        "id": "u2",
        "text": "Which prompt would get a BETTER result from AI?",
        "type": "prompt_comparison",
        "options": [
            {"value": "A", "label": "Prompt A", "prompt": "Write an email."},
            {"value": "B", "label": "Prompt B", "prompt": "Write a friendly email to the Bondi Beach store team about Saturday's mango sale. Mention we expect 2x normal foot traffic and need extra stock on the floor by 7am.", "correct": True},
        ],
    },
    {
        "id": "u3",
        "text": "You want AI to help write a product description for our new sourdough bread. Which prompt is best?",
        "type": "multiple_choice",
        "options": [
            {"value": "basic", "label": '"Write about bread"'},
            {"value": "good", "label": '"Write a 50-word product description for Harris Farm\'s new artisan sourdough, highlighting that it\'s baked fresh daily in-store using a 3-day fermentation process"', "correct": True},
            {"value": "long", "label": '"Write a very very long and detailed description about every possible thing about bread and sourdough and how it\'s made and where wheat comes from"'},
            {"value": "rude", "label": '"GIVE ME BREAD WORDS NOW"'},
        ],
    },
    {
        "id": "u4",
        "text": "You need to create a roster for next week. What information should you give AI to help?",
        "type": "multiple_select",
        "options": [
            {"value": "staff", "label": "Staff names and availability", "correct": True},
            {"value": "hours", "label": "Trading hours for the store", "correct": True},
            {"value": "events", "label": "Any special events (e.g., long weekend)", "correct": True},
            {"value": "budget", "label": "Labour budget or hours cap", "correct": True},
            {"value": "fav_colour", "label": "Each staff member's favourite colour"},
            {"value": "history", "label": "Previous week's roster as a starting point", "correct": True},
        ],
    },
    {
        "id": "u5",
        "text": "AI gives you an answer that doesn't quite make sense. What's the BEST thing to do?",
        "type": "multiple_choice",
        "options": [
            {"value": "accept", "label": "Accept it -- AI knows best"},
            {"value": "rephrase", "label": "Rephrase your question and try again", "correct": True},
            {"value": "give_up", "label": "Give up -- AI clearly doesn't work"},
            {"value": "complain", "label": 'Type "WRONG" in caps and hope it fixes itself'},
        ],
    },
    {
        "id": "u6",
        "text": 'What does "context" mean when talking to AI?',
        "type": "multiple_choice",
        "options": [
            {"value": "background", "label": "The background information you give AI so it understands your situation", "correct": True},
            {"value": "password", "label": "A special password to unlock better answers"},
            {"value": "nothing", "label": "It doesn't matter what you type -- AI figures it out"},
            {"value": "unsure", "label": "I'm not sure"},
        ],
    },
    {
        "id": "u7",
        "text": "You're writing a complaint response to a customer. Which approach is safest?",
        "type": "multiple_choice",
        "options": [
            {"value": "send_direct", "label": "Get AI to write it and send it straight to the customer"},
            {"value": "draft_review", "label": "Get AI to draft it, then review and personalise before sending", "correct": True},
            {"value": "no_ai", "label": "Never use AI for customer communication"},
            {"value": "template", "label": "Just use the same template for every complaint"},
        ],
    },
    {
        "id": "u8",
        "text": "If you could use AI for ONE thing at work right now, what would it be?",
        "type": "free_text",
        "placeholder": "Tell us in a sentence or two...",
    },
]

# ============================================================================
# MODULE 3: "Reading the Soil" -- Critical Thinking (8 questions)
# ============================================================================

MODULE_3_QUESTIONS = [
    {
        "id": "c1",
        "text": "AI suggests ordering 500kg of strawberries for Bowral store in July. What's the problem?",
        "type": "multiple_choice",
        "options": [
            {"value": "nothing", "label": "Nothing -- sounds right"},
            {"value": "season", "label": "Strawberries are out of season in July (winter) -- demand will be much lower", "correct": True},
            {"value": "too_much", "label": "500kg is always too much for any store"},
            {"value": "bowral", "label": "Bowral doesn't sell fruit"},
        ],
    },
    {
        "id": "c2",
        "text": 'You ask AI: "What were Harris Farm\'s total sales last quarter?" It confidently says "$47.3 million." Should you trust this?',
        "type": "multiple_choice",
        "options": [
            {"value": "trust", "label": "Yes -- it sounds specific and confident"},
            {"value": "check", "label": "No -- AI doesn't have access to our internal sales data, so it's making this up", "correct": True},
            {"value": "close_enough", "label": "Probably close enough to use in a presentation"},
            {"value": "unsure", "label": "I'm not sure how to tell"},
        ],
    },
    {
        "id": "c3",
        "text": "Here's an AI-generated product description: \"Harris Farm's organic bananas are grown on our own farm in North Queensland and are certified by the USDA Organic program.\" Find the problems.",
        "type": "multiple_select",
        "options": [
            {"value": "own_farm", "label": "Harris Farm doesn't grow its own bananas -- we're a retailer", "correct": True},
            {"value": "usda", "label": "USDA is American -- Australia uses Australian Certified Organic", "correct": True},
            {"value": "organic", "label": "The word 'organic' is wrong"},
            {"value": "queensland", "label": "Bananas don't grow in Queensland"},
            {"value": "no_problem", "label": "I don't see any problems"},
        ],
    },
    {
        "id": "c4",
        "text": 'What is "hallucination" in the context of AI?',
        "type": "multiple_choice",
        "options": [
            {"value": "correct", "label": "When AI confidently generates information that sounds real but is completely made up", "correct": True},
            {"value": "vision", "label": "When AI can see things through a camera"},
            {"value": "dream", "label": "When AI has dreams while it's switched off"},
            {"value": "unsure", "label": "I've never heard this term"},
        ],
    },
    {
        "id": "c5",
        "text": "Which of these should you NEVER rely on AI alone to do? Select all that apply.",
        "type": "multiple_select",
        "options": [
            {"value": "food_safety", "label": "Make food safety decisions", "correct": True},
            {"value": "hr_decision", "label": "Make hiring or firing decisions", "correct": True},
            {"value": "draft_email", "label": "Draft an internal email"},
            {"value": "legal", "label": "Give legal or medical advice to customers", "correct": True},
            {"value": "summarise", "label": "Summarise a long document"},
            {"value": "price_change", "label": "Change product prices without human review", "correct": True},
        ],
    },
    {
        "id": "c6",
        "text": "AI analyses our sales data and says \"Leichhardt store should stop selling flowers -- they only make up 2% of revenue.\" What's missing from this analysis?",
        "type": "multiple_choice",
        "options": [
            {"value": "nothing", "label": "Nothing -- if it's only 2%, cut it"},
            {"value": "context", "label": "Flowers might drive foot traffic, create atmosphere, and attract customers who then buy groceries -- revenue % alone doesn't tell the full story", "correct": True},
            {"value": "more_data", "label": "We need 10 more years of data before deciding"},
            {"value": "wrong", "label": "AI can't analyse sales data"},
        ],
    },
    {
        "id": "c7",
        "text": "You notice AI keeps recommending we stock more \"Vegemite\" even though we barely sell it. Why might this happen?",
        "type": "multiple_choice",
        "options": [
            {"value": "popular", "label": "Because Vegemite is Australia's favourite food"},
            {"value": "bias", "label": "AI was trained on general Australian grocery data where Vegemite is popular -- it doesn't know Harris Farm's specialty fresh food focus", "correct": True},
            {"value": "correct", "label": "AI is right -- we should stock more Vegemite"},
            {"value": "broken", "label": "The AI is broken and needs to be turned off"},
        ],
    },
    {
        "id": "c8",
        "text": "On a scale of 1-10, how confident are you that you could spot when AI gets something wrong?",
        "type": "slider",
        "min": 1,
        "max": 10,
        "labels": {1: "Not confident at all", 5: "Somewhat confident", 10: "Very confident"},
    },
]

# ============================================================================
# MODULE 4: "Growing Season" -- Applied Skills (ROLE-ADAPTIVE)
# ============================================================================

# Tier 1-2: Floor & Warehouse / Shop Floor Specialists
APPLIED_TIER_1_2 = [
    {
        "id": "ap_12_1",
        "text": "A customer asks about the difference between types of apples. How could AI help YOU right now?",
        "type": "multiple_choice",
        "options": [
            {"value": "phone", "label": "Pull up a quick answer on my phone to share with the customer", "correct": True},
            {"value": "robot", "label": "Send a robot to talk to the customer"},
            {"value": "no_help", "label": "It can't -- I know my products"},
            {"value": "unsure", "label": "I'm not sure how AI could help on the shop floor"},
        ],
    },
    {
        "id": "ap_12_2",
        "text": "You notice the avocados are going brown faster than usual. How could AI-powered tools help?",
        "type": "multiple_select",
        "options": [
            {"value": "discount", "label": "Suggest automatic markdowns before they go to waste", "correct": True},
            {"value": "alert", "label": "Alert the buyer that this batch quality is low", "correct": True},
            {"value": "recipe", "label": 'Generate recipe cards: "Perfect for guacamole today!"', "correct": True},
            {"value": "fix", "label": "Fix the avocados so they're green again"},
            {"value": "pattern", "label": "Track patterns -- is this supplier always delivering overripe?", "correct": True},
        ],
    },
    {
        "id": "ap_12_3",
        "text": "Imagine you could talk to your phone and it would fill in a wastage report for you. Would that be useful?",
        "type": "multiple_choice",
        "options": [
            {"value": "very", "label": "Very useful -- I hate paperwork"},
            {"value": "somewhat", "label": "Somewhat -- but I'd want to check it"},
            {"value": "not_really", "label": "Not really -- it's quick to fill in by hand"},
            {"value": "worried", "label": "I'd worry about it getting things wrong"},
        ],
    },
    {
        "id": "ap_12_4",
        "text": "An AI stock system suggests you need 50 watermelons for tomorrow. You know there's a heatwave coming and you usually sell 100 on hot days. What do you do?",
        "type": "multiple_choice",
        "options": [
            {"value": "ai", "label": "Trust the AI -- it probably knows something I don't"},
            {"value": "override", "label": "Override to 100 -- I know my store and the weather forecast", "correct": True},
            {"value": "split", "label": "Order 75 as a compromise"},
            {"value": "ignore", "label": "Ignore the AI system entirely from now on"},
        ],
    },
    {
        "id": "ap_12_5",
        "text": "What scares you most about AI in your workplace?",
        "type": "multiple_choice",
        "options": [
            {"value": "job", "label": "It might replace my job"},
            {"value": "learn", "label": "I'll have to learn new technology"},
            {"value": "mistakes", "label": "It'll make mistakes that I get blamed for"},
            {"value": "nothing", "label": "Nothing -- I'm keen to try it"},
            {"value": "unsure", "label": "I don't know enough to say"},
        ],
    },
]

# Tier 3-4: Managers / Support Functions
APPLIED_TIER_3_4 = [
    {
        "id": "ap_34_1",
        "text": "You need to write a weekly performance summary for your store. How would you use AI?",
        "type": "multiple_choice",
        "options": [
            {"value": "all", "label": "Give AI the data and let it write the whole thing"},
            {"value": "draft", "label": "Use AI to draft a structure, then fill in the specific numbers and add my commentary", "correct": True},
            {"value": "no", "label": "Write it myself -- AI can't understand store performance"},
            {"value": "numbers", "label": "Only use AI to format the numbers into a table"},
        ],
    },
    {
        "id": "ap_34_2",
        "text": "Your department's wastage has increased 15% month-on-month. What AI analysis would you request?",
        "type": "multiple_select",
        "options": [
            {"value": "products", "label": "Which specific products are driving the increase?", "correct": True},
            {"value": "time", "label": "What time of day is waste being recorded?", "correct": True},
            {"value": "weather", "label": "Was there a weather event affecting supply quality?", "correct": True},
            {"value": "compare", "label": "How do other stores compare for the same period?", "correct": True},
            {"value": "fire", "label": "Which staff member should be blamed?"},
        ],
    },
    {
        "id": "ap_34_3",
        "text": "You're preparing a business case for a new initiative. How could AI help most?",
        "type": "multiple_choice",
        "options": [
            {"value": "whole_case", "label": "Write the entire business case"},
            {"value": "research", "label": "Research industry benchmarks and structure the argument, then I add our specific data and strategy", "correct": True},
            {"value": "slides", "label": "Just make it look pretty with formatting"},
            {"value": "no_use", "label": "Business cases are too important for AI"},
        ],
    },
    {
        "id": "ap_34_4",
        "text": "What's the most important thing when sharing AI-generated analysis with your team?",
        "type": "multiple_choice",
        "options": [
            {"value": "present_as_ai", "label": "Present it as 'the AI said...' to deflect responsibility"},
            {"value": "verify_own", "label": "Verify the numbers, add your insight, and present it as your informed recommendation", "correct": True},
            {"value": "dont_mention", "label": "Don't mention AI was involved -- people won't trust it"},
            {"value": "raw", "label": "Share the raw AI output so people can judge for themselves"},
        ],
    },
    {
        "id": "ap_34_5",
        "text": "How would you integrate AI tools into your current workflow? Be specific.",
        "type": "free_text",
        "placeholder": "Describe one concrete way you'd use AI in your daily work...",
    },
]

# Tier 5-6: Senior Leadership / C-Suite & Board
APPLIED_TIER_5_6 = [
    {
        "id": "ap_56_1",
        "text": "A competitor announces they're using AI to personalise customer offers. What's your first strategic response?",
        "type": "multiple_choice",
        "options": [
            {"value": "copy", "label": "Rush to copy exactly what they're doing"},
            {"value": "assess", "label": "Assess our own customer data capabilities and identify where AI could enhance our unique strengths", "correct": True},
            {"value": "ignore", "label": "Ignore it -- our brand is strong enough"},
            {"value": "ban", "label": "Ban AI to avoid risk"},
        ],
    },
    {
        "id": "ap_56_2",
        "text": 'The board asks: "What\'s our AI strategy?" Which response shows the strongest understanding?',
        "type": "multiple_choice",
        "options": [
            {"value": "tools", "label": '"We\'ve bought some AI tools for the IT team"'},
            {"value": "strategy", "label": '"We\'re building AI literacy across all roles, starting with assessment, then targeted training -- measuring readiness by store and function"', "correct": True},
            {"value": "wait", "label": '"We\'re waiting to see what the industry does first"'},
            {"value": "everything", "label": '"We\'re going to use AI for everything"'},
        ],
    },
    {
        "id": "ap_56_3",
        "text": "What governance framework should Harris Farm have for AI use?",
        "type": "multiple_select",
        "options": [
            {"value": "policy", "label": "Clear policy on what data can/cannot be shared with AI", "correct": True},
            {"value": "review", "label": "Human review requirement for customer-facing AI outputs", "correct": True},
            {"value": "training", "label": "Mandatory basic AI training for all staff", "correct": True},
            {"value": "ban", "label": "Complete ban on AI until regulations are finalised"},
            {"value": "audit", "label": "Regular audit of AI tool usage and outcomes", "correct": True},
            {"value": "champion", "label": "AI champions in each store/department", "correct": True},
        ],
    },
    {
        "id": "ap_56_4",
        "text": "How would you measure ROI on the company's AI investment?",
        "type": "multiple_select",
        "options": [
            {"value": "waste", "label": "Reduction in wastage/shrinkage", "correct": True},
            {"value": "time", "label": "Time saved on routine tasks", "correct": True},
            {"value": "satisfaction", "label": "Employee satisfaction and confidence scores", "correct": True},
            {"value": "speed", "label": "Speed of decision-making", "correct": True},
            {"value": "fancy", "label": "How fancy the AI dashboards look"},
            {"value": "revenue", "label": "Revenue uplift in AI-assisted areas", "correct": True},
        ],
    },
    {
        "id": "ap_56_5",
        "text": "What's your vision for how AI should transform Harris Farm over the next 3 years?",
        "type": "free_text",
        "placeholder": "Share your strategic vision...",
    },
]

# ============================================================================
# MODULE 5: "The Harvest" -- Confidence & Appetite (5 questions)
# ============================================================================

MODULE_5_QUESTIONS = [
    {
        "id": "h1",
        "text": "After going through this assessment, how confident do you feel about using AI?",
        "type": "slider",
        "min": 1,
        "max": 10,
        "labels": {1: "Not confident", 5: "Getting there", 10: "Bring it on!"},
    },
    {
        "id": "h2",
        "text": "What excites you MOST about AI at Harris Farm? Pick up to 3.",
        "type": "multiple_select",
        "max_select": 3,
        "options": [
            {"value": "less_waste", "label": "Less food waste"},
            {"value": "save_time", "label": "Saving time on boring tasks"},
            {"value": "better_service", "label": "Better customer service"},
            {"value": "learn_new", "label": "Learning new skills"},
            {"value": "smarter_buying", "label": "Smarter buying decisions"},
            {"value": "competitive", "label": "Staying ahead of competitors"},
            {"value": "fun", "label": "It's just cool!"},
            {"value": "nothing", "label": "Nothing excites me about it"},
        ],
    },
    {
        "id": "h3",
        "text": "What worries you MOST about AI? Pick up to 3.",
        "type": "multiple_select",
        "max_select": 3,
        "options": [
            {"value": "job_loss", "label": "Job losses"},
            {"value": "mistakes", "label": "AI making mistakes"},
            {"value": "privacy", "label": "Privacy and data concerns"},
            {"value": "hard_learn", "label": "It'll be hard to learn"},
            {"value": "impersonal", "label": "Losing the personal touch"},
            {"value": "cost", "label": "Cost of implementation"},
            {"value": "nothing", "label": "Nothing worries me"},
        ],
    },
    {
        "id": "h4",
        "text": '"I would use AI tools daily at work if..."',
        "type": "free_text",
        "placeholder": "Complete the sentence...",
    },
    {
        "id": "h5",
        "text": '"The one thing that would help me learn AI is..."',
        "type": "free_text",
        "placeholder": "Tell us what would help most...",
    },
]


# ============================================================================
# QUESTION RETRIEVAL
# ============================================================================

def get_module_questions(module_id, role_tier=3):
    # type: (str, int) -> list
    if module_id == "applied":
        if role_tier <= 2:
            return APPLIED_TIER_1_2
        elif role_tier <= 4:
            return APPLIED_TIER_3_4
        else:
            return APPLIED_TIER_5_6
    return {
        "awareness": MODULE_1_QUESTIONS,
        "usage": MODULE_2_QUESTIONS,
        "critical": MODULE_3_QUESTIONS,
        "confidence": MODULE_5_QUESTIONS,
    }.get(module_id, [])


# ============================================================================
# SCORING ENGINE
# ============================================================================

def _score_a1(answer):
    if not answer or "none" in answer:
        return 0
    return min(len(answer) * 20, 100)


def _score_a2(answer):
    if not answer:
        return 0
    correct = {"forecast", "roster", "email", "pricing"}
    incorrect = {"taste", "negotiate"}
    score = 0
    for a in answer:
        if a in correct:
            score += 20
        if a in incorrect:
            score -= 15
    return max(0, min(score, 100))


def _score_a7(answer):
    scores = {"yes_use": 100, "yes_heard": 70, "maybe": 40, "no": 10}
    return scores.get(answer, 0)


def _score_a8(answer):
    scores = {"excited": 90, "curious": 80, "nervous": 40, "confused": 20, "indifferent": 30}
    return scores.get(answer, 0)


def _score_u1(answer):
    scores = {"daily": 100, "few_times": 70, "once": 40, "never": 0}
    return scores.get(answer, 0)


def _score_u4(answer):
    if not answer:
        return 0
    correct = {"staff", "hours", "events", "budget", "history"}
    score = 0
    for a in answer:
        if a in correct:
            score += 20
        if a == "fav_colour":
            score -= 10
    return max(0, min(score, 100))


def _score_u8(answer):
    if not answer or len(str(answer).strip()) < 5:
        return 20
    if len(str(answer).strip()) > 20:
        return 80
    return 50


def _score_c3(answer):
    if not answer:
        return 0
    correct = {"own_farm", "usda"}
    wrong = {"organic", "queensland", "no_problem"}
    score = 0
    for a in answer:
        if a in correct:
            score += 40
        if a in wrong:
            score -= 20
    return max(0, min(score, 100))


def _score_c5(answer):
    if not answer:
        return 0
    correct = {"food_safety", "hr_decision", "legal", "price_change"}
    fine = {"draft_email", "summarise"}
    score = 0
    for a in answer:
        if a in correct:
            score += 25
        if a in fine:
            score -= 10
    return max(0, min(score, 100))


def _score_slider(answer):
    try:
        return round(int(answer or 1) * 10)
    except (ValueError, TypeError):
        return 10


def _score_ap_12_2(answer):
    if not answer:
        return 0
    correct = {"discount", "alert", "recipe", "pattern"}
    score = 0
    for a in answer:
        if a in correct:
            score += 25
        if a == "fix":
            score -= 15
    return max(0, min(score, 100))


def _score_ap_12_3(answer):
    scores = {"very": 90, "somewhat": 70, "not_really": 40, "worried": 50}
    return scores.get(answer, 0)


def _score_ap_12_5(answer):
    scores = {"nothing": 90, "learn": 60, "mistakes": 50, "job": 30, "unsure": 40}
    return scores.get(answer, 0)


def _score_ap_34_2(answer):
    if not answer:
        return 0
    correct = {"products", "time", "weather", "compare"}
    score = 0
    for a in answer:
        if a in correct:
            score += 25
        if a == "fire":
            score -= 20
    return max(0, min(score, 100))


def _score_ap_34_5(answer):
    if not answer or len(str(answer).strip()) < 10:
        return 20
    keywords = ["data", "report", "analysis", "email", "roster", "meeting",
                "summary", "forecast", "review", "draft", "template"]
    found = [k for k in keywords if k in str(answer).lower()]
    return min(40 + len(found) * 15, 100)


def _score_ap_56_3(answer):
    if not answer:
        return 0
    correct = {"policy", "review", "training", "audit", "champion"}
    score = 0
    for a in answer:
        if a in correct:
            score += 20
        if a == "ban":
            score -= 20
    return max(0, min(score, 100))


def _score_ap_56_4(answer):
    if not answer:
        return 0
    correct = {"waste", "time", "satisfaction", "speed", "revenue"}
    score = 0
    for a in answer:
        if a in correct:
            score += 20
        if a == "fancy":
            score -= 10
    return max(0, min(score, 100))


def _score_ap_56_5(answer):
    if not answer or len(str(answer).strip()) < 10:
        return 20
    strategic = ["customer", "efficiency", "data", "culture", "training",
                 "competitive", "growth", "supply chain", "waste",
                 "experience", "team", "people"]
    found = [k for k in strategic if k in str(answer).lower()]
    return min(30 + len(found) * 12, 100)


def _score_h2(answer):
    if not answer or "nothing" in answer:
        return 20
    return min(len(answer) * 30, 100)


def _score_h3(answer):
    if not answer or "nothing" in answer:
        return 90
    return max(90 - len(answer) * 15, 30)


def _score_free_text_short(answer):
    if not answer or len(str(answer).strip()) < 5:
        return 30
    return 80


# Scoring dispatch table
_CUSTOM_SCORERS = {
    "a1": _score_a1,
    "a2": _score_a2,
    "a7": _score_a7,
    "a8": _score_a8,
    "u1": _score_u1,
    "u4": _score_u4,
    "u8": _score_u8,
    "c3": _score_c3,
    "c5": _score_c5,
    "c8": _score_slider,
    "ap_12_2": _score_ap_12_2,
    "ap_12_3": _score_ap_12_3,
    "ap_12_5": _score_ap_12_5,
    "ap_34_2": _score_ap_34_2,
    "ap_34_5": _score_ap_34_5,
    "ap_56_3": _score_ap_56_3,
    "ap_56_4": _score_ap_56_4,
    "ap_56_5": _score_ap_56_5,
    "h1": _score_slider,
    "h2": _score_h2,
    "h3": _score_h3,
    "h4": _score_free_text_short,
    "h5": _score_free_text_short,
}


def score_question(question, answer):
    # type: (dict, object) -> int
    qid = question["id"]
    qtype = question["type"]

    if qid in _CUSTOM_SCORERS:
        return _CUSTOM_SCORERS[qid](answer)

    # Default: correct/incorrect for multiple_choice and prompt_comparison
    if qtype in ("multiple_choice", "prompt_comparison"):
        correct_opt = next((o for o in question.get("options", []) if o.get("correct")), None)
        if correct_opt and answer == correct_opt["value"]:
            return 100
        return 0

    # Default slider
    if qtype == "slider":
        return _score_slider(answer)

    # Default free_text
    if qtype == "free_text":
        return _score_u8(answer)

    return 0


# ============================================================================
# LEARNING PATH RECOMMENDATIONS
# ============================================================================

def _tier_to_category(tier):
    # type: (int) -> str
    if tier <= 1:
        return "floor"
    if tier == 2:
        return "specialist"
    if tier <= 4:
        return "manager"
    return "leadership"


LEARNING_PATHS = {
    "seedling": {
        "floor": [
            {"id": "S_F_1", "title": "AI in 60 Seconds", "type": "video", "duration": "1 min",
             "description": "A quick, friendly intro to what AI actually is -- no jargon."},
            {"id": "S_F_2", "title": "Talk to Claude: Your First Chat", "type": "hands-on", "duration": "5 min",
             "description": "Open Claude, type a question about your job, see what happens."},
            {"id": "S_F_3", "title": "How AI Helps in the Warehouse", "type": "article", "duration": "3 min",
             "description": "Real examples of AI in grocery retail -- stock, waste, deliveries."},
        ],
        "specialist": [
            {"id": "S_S_1", "title": "AI for Fresh Food Teams", "type": "video", "duration": "3 min",
             "description": "How AI helps with ordering, wastage, and quality -- in your department."},
            {"id": "S_S_2", "title": "Try Asking AI About Your Products", "type": "hands-on", "duration": "5 min",
             "description": "Ask Claude about cooking tips, pairings, or seasonal availability."},
            {"id": "S_S_3", "title": "What AI Can and Can't Do", "type": "article", "duration": "3 min",
             "description": "The honest truth about AI's strengths and weaknesses."},
        ],
        "manager": [
            {"id": "S_M_1", "title": "AI for Team Leaders", "type": "video", "duration": "5 min",
             "description": "How managers at top retailers are using AI -- and where to start."},
            {"id": "S_M_2", "title": "Your First AI-Assisted Report", "type": "hands-on", "duration": "10 min",
             "description": "Use Claude to draft a weekly store summary from dot points."},
            {"id": "S_M_3", "title": "When NOT to Use AI", "type": "article", "duration": "5 min",
             "description": "The critical boundaries every manager should know."},
        ],
        "leadership": [
            {"id": "S_L_1", "title": "AI Strategy in 10 Minutes", "type": "video", "duration": "10 min",
             "description": "What boards need to know about AI -- Woolworths, Coles, and what we're doing."},
            {"id": "S_L_2", "title": "The AI Governance Checklist", "type": "article", "duration": "5 min",
             "description": "10 questions every board member should ask about AI."},
            {"id": "S_L_3", "title": "Try It Yourself", "type": "hands-on", "duration": "5 min",
             "description": "Ask Claude to summarise a business document -- see the quality firsthand."},
        ],
    },
    "sprout": {
        "floor": [
            {"id": "SP_F_1", "title": "Voice-to-Text for Reporting", "type": "hands-on", "duration": "5 min",
             "description": "Use your phone to dictate wastage reports -- faster than writing."},
            {"id": "SP_F_2", "title": "AI Stock Alerts: What They Mean", "type": "article", "duration": "4 min",
             "description": "Understanding AI-powered stock suggestions and when to trust them."},
            {"id": "SP_F_3", "title": "Quick Product Lookup with AI", "type": "hands-on", "duration": "5 min",
             "description": "How to ask AI about product info, allergens, and storage."},
        ],
        "specialist": [
            {"id": "SP_S_1", "title": "Writing Better Prompts", "type": "hands-on", "duration": "10 min",
             "description": "The difference between a vague and a great prompt -- with examples."},
            {"id": "SP_S_2", "title": "AI for Customer Questions", "type": "article", "duration": "5 min",
             "description": "How to quickly get AI to help with customer queries about products."},
            {"id": "SP_S_3", "title": "Department-Specific AI Use Cases", "type": "video", "duration": "5 min",
             "description": "Butcher, baker, florist -- specific AI wins for each department."},
        ],
        "manager": [
            {"id": "SP_M_1", "title": "Prompt Engineering for Managers", "type": "hands-on", "duration": "15 min",
             "description": "Learn to write prompts that give you useful business outputs."},
            {"id": "SP_M_2", "title": "AI for Roster Planning", "type": "hands-on", "duration": "10 min",
             "description": "Draft a roster with AI -- give it constraints and let it optimise."},
            {"id": "SP_M_3", "title": "Data-Driven Decisions", "type": "article", "duration": "5 min",
             "description": "How to ask AI the right questions about your store data."},
        ],
        "leadership": [
            {"id": "SP_L_1", "title": "AI ROI Framework", "type": "article", "duration": "8 min",
             "description": "How to measure and communicate AI investment returns."},
            {"id": "SP_L_2", "title": "Competitive AI Landscape: Grocery", "type": "article", "duration": "10 min",
             "description": "What Woolworths, Coles, and Amazon Fresh are doing -- and our edge."},
            {"id": "SP_L_3", "title": "Leading AI Culture Change", "type": "video", "duration": "10 min",
             "description": "How to champion AI adoption without alienating your team."},
        ],
    },
    "grower": {
        "floor": [
            {"id": "G_F_1", "title": "AI-Powered Quality Checks", "type": "hands-on", "duration": "10 min",
             "description": "How image AI can help assess produce quality at receiving."},
            {"id": "G_F_2", "title": "Reporting Issues Faster", "type": "hands-on", "duration": "5 min",
             "description": "Use AI to draft clear, actionable incident reports."},
            {"id": "G_F_3", "title": "Becoming an AI Champion", "type": "article", "duration": "5 min",
             "description": "You're ahead of most -- here's how to help your teammates."},
        ],
        "specialist": [
            {"id": "G_S_1", "title": "Product Knowledge Superpowers", "type": "hands-on", "duration": "10 min",
             "description": "Use AI to become the product expert customers love."},
            {"id": "G_S_2", "title": "Creating Content with AI", "type": "hands-on", "duration": "15 min",
             "description": "Generate POS signage, recipe cards, and product descriptions."},
            {"id": "G_S_3", "title": "Waste Reduction with AI Insights", "type": "article", "duration": "5 min",
             "description": "How AI-spotted patterns can help your department cut waste."},
        ],
        "manager": [
            {"id": "G_M_1", "title": "Advanced Prompt Patterns", "type": "hands-on", "duration": "20 min",
             "description": "Chain-of-thought, role-based, and template prompts for business."},
            {"id": "G_M_2", "title": "Building an AI-Assisted Workflow", "type": "workshop", "duration": "30 min",
             "description": "Map your daily tasks and identify AI integration points."},
            {"id": "G_M_3", "title": "Presenting AI Insights to Your Team", "type": "article", "duration": "5 min",
             "description": "How to share AI-generated analysis without losing credibility."},
        ],
        "leadership": [
            {"id": "G_L_1", "title": "AI Ethics for Leaders", "type": "article", "duration": "10 min",
             "description": "Responsible AI: bias, transparency, and Harris Farm values."},
            {"id": "G_L_2", "title": "Building Your AI Roadmap", "type": "workshop", "duration": "30 min",
             "description": "A structured approach to prioritising AI initiatives."},
            {"id": "G_L_3", "title": "Change Management for AI", "type": "video", "duration": "15 min",
             "description": "Lessons from successful AI rollouts in retail."},
        ],
    },
    "harvester": {
        "floor": [
            {"id": "H_F_1", "title": "Training Others on AI", "type": "workshop", "duration": "20 min",
             "description": "You're ready to be an AI buddy -- here's how to teach your mates."},
            {"id": "H_F_2", "title": "AI for Process Improvement", "type": "hands-on", "duration": "15 min",
             "description": "Identify and propose workflow improvements using AI analysis."},
            {"id": "H_F_3", "title": "The AI Ambassador Program", "type": "article", "duration": "5 min",
             "description": "Ready to be recognised? Join the ambassador program."},
        ],
        "specialist": [
            {"id": "H_S_1", "title": "Creating Department AI Playbooks", "type": "workshop", "duration": "30 min",
             "description": "Document the best AI practices for your specific department."},
            {"id": "H_S_2", "title": "Advanced Analysis Techniques", "type": "hands-on", "duration": "20 min",
             "description": "Use AI for trend analysis, forecasting, and pattern detection."},
            {"id": "H_S_3", "title": "Mentoring Seedlings", "type": "article", "duration": "5 min",
             "description": "How to help your less confident colleagues feel safe with AI."},
        ],
        "manager": [
            {"id": "H_M_1", "title": "AI-Powered Decision Support", "type": "workshop", "duration": "30 min",
             "description": "Build decision frameworks that combine AI insight with human judgment."},
            {"id": "H_M_2", "title": "Automating Reports and Analysis", "type": "hands-on", "duration": "30 min",
             "description": "Set up recurring AI-assisted reporting workflows."},
            {"id": "H_M_3", "title": "Cross-Functional AI Projects", "type": "article", "duration": "10 min",
             "description": "How to champion AI projects that span multiple departments."},
        ],
        "leadership": [
            {"id": "H_L_1", "title": "AI Strategy Deep Dive", "type": "workshop", "duration": "45 min",
             "description": "Advanced strategy: build vs buy, vendor assessment, talent planning."},
            {"id": "H_L_2", "title": "Communicating AI Value to the Board", "type": "article", "duration": "10 min",
             "description": "Frameworks for presenting AI ROI and risk to governance."},
            {"id": "H_L_3", "title": "Industry Benchmarking", "type": "article", "duration": "15 min",
             "description": "Where Harris Farm sits vs industry AI maturity benchmarks."},
        ],
    },
    "cultivator": {
        "floor": [
            {"id": "C_F_1", "title": "Lead an AI Innovation Session", "type": "workshop", "duration": "30 min",
             "description": "You're at the top -- run a brainstorm on AI ideas for your area."},
            {"id": "C_F_2", "title": "Propose an AI Pilot", "type": "hands-on", "duration": "20 min",
             "description": "Write a one-page proposal for an AI pilot in your department."},
        ],
        "specialist": [
            {"id": "C_S_1", "title": "Design Your Department AI Workflow", "type": "workshop", "duration": "45 min",
             "description": "Create the blueprint for AI-enhanced operations in your area."},
            {"id": "C_S_2", "title": "Cross-Training: Teach AI Skills", "type": "workshop", "duration": "30 min",
             "description": "Develop and deliver a 15-minute AI training for your team."},
        ],
        "manager": [
            {"id": "C_M_1", "title": "AI Innovation Lab", "type": "workshop", "duration": "60 min",
             "description": "Design and prototype an AI solution for a real business problem."},
            {"id": "C_M_2", "title": "Building AI into Team Culture", "type": "article", "duration": "10 min",
             "description": "How to make AI a natural part of your team's daily rhythm."},
        ],
        "leadership": [
            {"id": "C_L_1", "title": "Shape the AI Roadmap", "type": "workshop", "duration": "60 min",
             "description": "Work with the Co-CEOs to define the next phase of AI at Harris Farm."},
            {"id": "C_L_2", "title": "External AI Advisory", "type": "article", "duration": "10 min",
             "description": "Connect with industry AI leaders and advisory boards."},
        ],
    },
}

_LEVEL_NAMES = ["seedling", "sprout", "grower", "harvester", "cultivator"]


def get_recommendations(maturity_level, role_tier):
    # type: (int, int) -> list
    level_key = _LEVEL_NAMES[max(0, min(maturity_level - 1, 4))]
    category = _tier_to_category(role_tier)
    paths = LEARNING_PATHS.get(level_key, {})
    return paths.get(category, paths.get("manager", []))
