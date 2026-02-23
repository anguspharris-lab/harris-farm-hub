"""
Skills Academy v4 — Database Schema
All 25 v4 tables + seed functions.
"""

import json
import sqlite3
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Table DDL
# ---------------------------------------------------------------------------

_TABLES = """
-- ============================================================
-- LEVELS, SERIES, MODULES
-- ============================================================

CREATE TABLE IF NOT EXISTS sa_levels (
    level_id INTEGER PRIMARY KEY AUTOINCREMENT,
    level_number INTEGER NOT NULL UNIQUE,
    level_code TEXT NOT NULL UNIQUE,
    level_name TEXT NOT NULL,
    identity_statement TEXT NOT NULL,
    color_hex TEXT NOT NULL,
    xp_threshold_min INTEGER NOT NULL,
    xp_threshold_max INTEGER NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sa_series (
    series_id INTEGER PRIMARY KEY AUTOINCREMENT,
    series_code TEXT NOT NULL UNIQUE,
    series_name TEXT NOT NULL,
    description TEXT,
    color_hex TEXT NOT NULL,
    icon TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sa_modules (
    module_id INTEGER PRIMARY KEY AUTOINCREMENT,
    series_id INTEGER NOT NULL,
    module_code TEXT NOT NULL UNIQUE,
    module_name TEXT NOT NULL,
    description TEXT,
    difficulty TEXT CHECK(difficulty IN ('beginner', 'intermediate', 'advanced')) DEFAULT 'beginner',
    estimated_minutes INTEGER DEFAULT 30,
    prerequisite_module_id INTEGER NULL,
    level_number INTEGER NOT NULL,
    display_order INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (series_id) REFERENCES sa_series(series_id),
    FOREIGN KEY (prerequisite_module_id) REFERENCES sa_modules(module_id)
);

CREATE TABLE IF NOT EXISTS sa_lessons (
    lesson_id INTEGER PRIMARY KEY AUTOINCREMENT,
    module_id INTEGER NOT NULL,
    lesson_type TEXT CHECK(lesson_type IN ('theory', 'examples', 'exercise', 'assessment')) NOT NULL,
    lesson_title TEXT NOT NULL,
    content_markdown TEXT NOT NULL,
    display_order INTEGER DEFAULT 0,
    xp_reward INTEGER DEFAULT 10,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (module_id) REFERENCES sa_modules(module_id)
);

-- ============================================================
-- EXERCISES (with adaptive difficulty + curveball support)
-- ============================================================

CREATE TABLE IF NOT EXISTS sa_exercises (
    exercise_id INTEGER PRIMARY KEY AUTOINCREMENT,
    module_id INTEGER NOT NULL,
    tier TEXT CHECK(tier IN ('standard', 'stretch', 'elite')) NOT NULL,
    context_tag TEXT NOT NULL,
    is_curveball INTEGER DEFAULT 0,
    curveball_type TEXT,
    exercise_title TEXT NOT NULL,
    scenario_text TEXT NOT NULL,
    expected_approach TEXT,
    rubric_code TEXT NOT NULL,
    pass_score REAL NOT NULL,
    xp_reward INTEGER DEFAULT 15,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (module_id) REFERENCES sa_modules(module_id)
);

CREATE TABLE IF NOT EXISTS sa_exercise_state (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    module_id INTEGER NOT NULL,
    current_tier TEXT CHECK(current_tier IN ('standard', 'stretch', 'elite')) DEFAULT 'standard',
    consecutive_high_scores INTEGER DEFAULT 0,
    exercises_since_curveball INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, module_id)
);

CREATE TABLE IF NOT EXISTS sa_exercise_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    exercise_id INTEGER NOT NULL,
    user_response TEXT NOT NULL,
    scores_json TEXT NOT NULL,
    total_score REAL NOT NULL,
    passed INTEGER NOT NULL,
    ai_feedback TEXT,
    is_curveball_result INTEGER DEFAULT 0,
    curveball_score REAL,
    context_tag TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (exercise_id) REFERENCES sa_exercises(exercise_id)
);

-- ============================================================
-- RUBRICS
-- ============================================================

CREATE TABLE IF NOT EXISTS sa_rubrics (
    rubric_id INTEGER PRIMARY KEY AUTOINCREMENT,
    rubric_code TEXT NOT NULL UNIQUE,
    rubric_name TEXT NOT NULL,
    description TEXT,
    applicable_levels TEXT NOT NULL,
    criteria_json TEXT NOT NULL,
    pass_threshold REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sa_rubric_evaluations (
    evaluation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    rubric_id INTEGER NOT NULL,
    module_id INTEGER,
    exercise_id INTEGER,
    prompt_text TEXT,
    output_text TEXT,
    scores_json TEXT NOT NULL,
    total_score REAL NOT NULL,
    passed INTEGER NOT NULL,
    ai_feedback TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (rubric_id) REFERENCES sa_rubrics(rubric_id)
);

-- ============================================================
-- WOVEN VERIFICATION (Mastery Evidence)
-- ============================================================

CREATE TABLE IF NOT EXISTS sa_mastery_evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    target_level INTEGER NOT NULL,
    dimension TEXT CHECK(dimension IN ('foundation', 'breadth', 'depth', 'application')) NOT NULL,
    evidence_type TEXT NOT NULL,
    context_tag TEXT,
    score REAL,
    passed INTEGER NOT NULL,
    source_exercise_id INTEGER,
    detail_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sa_verification_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    level_number INTEGER NOT NULL,
    level_status TEXT CHECK(level_status IN ('provisional', 'confirmed', 'dormant')) DEFAULT 'provisional',
    foundation_score REAL DEFAULT 0,
    breadth_count INTEGER DEFAULT 0,
    depth_count INTEGER DEFAULT 0,
    application_passed INTEGER DEFAULT 0,
    confirmed_at TIMESTAMP,
    last_activity_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, level_number)
);

-- ============================================================
-- PLACEMENT + SCENARIOS
-- ============================================================

CREATE TABLE IF NOT EXISTS sa_placement_v4 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL UNIQUE,
    challenge_scores_json TEXT NOT NULL,
    total_score INTEGER NOT NULL,
    placed_level INTEGER NOT NULL,
    hipo_flags_json TEXT,
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sa_scenarios (
    scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
    level_number INTEGER NOT NULL,
    role_name TEXT,
    scenario_title TEXT NOT NULL,
    scenario_text TEXT NOT NULL,
    context TEXT,
    is_active INTEGER DEFAULT 1
);

-- ============================================================
-- LIVE PROBLEMS BANK (for Application dimension)
-- ============================================================

CREATE TABLE IF NOT EXISTS sa_live_problems (
    problem_id INTEGER PRIMARY KEY AUTOINCREMENT,
    level_number INTEGER NOT NULL,
    role_name TEXT,
    department TEXT,
    problem_title TEXT NOT NULL,
    problem_description TEXT NOT NULL,
    expected_approach TEXT,
    data_sources TEXT,
    submitted_by TEXT,
    is_active INTEGER DEFAULT 1,
    times_used INTEGER DEFAULT 0,
    avg_score REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- GAMIFICATION
-- ============================================================

CREATE TABLE IF NOT EXISTS sa_user_xp (
    user_id TEXT PRIMARY KEY,
    total_xp INTEGER DEFAULT 0,
    current_level INTEGER DEFAULT 1,
    weekly_xp INTEGER DEFAULT 0,
    monthly_xp INTEGER DEFAULT 0,
    streak_days INTEGER DEFAULT 0,
    streak_multiplier REAL DEFAULT 1.0,
    last_active_date TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sa_xp_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    xp_amount INTEGER NOT NULL,
    source_type TEXT NOT NULL,
    source_id TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sa_badges_v4 (
    badge_id INTEGER PRIMARY KEY AUTOINCREMENT,
    badge_code TEXT NOT NULL UNIQUE,
    badge_name TEXT NOT NULL,
    description TEXT,
    icon TEXT,
    color_hex TEXT,
    trigger_type TEXT NOT NULL,
    trigger_value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sa_user_badges_v4 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    badge_id INTEGER NOT NULL,
    status TEXT CHECK(status IN ('provisional', 'confirmed')) DEFAULT 'provisional',
    earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confirmed_at TIMESTAMP,
    UNIQUE(user_id, badge_id),
    FOREIGN KEY (badge_id) REFERENCES sa_badges_v4(badge_id)
);

-- ============================================================
-- HIPO SIGNALS (single-row per user, 9 signals)
-- ============================================================

CREATE TABLE IF NOT EXISTS sa_hipo_signals_v4 (
    user_id TEXT PRIMARY KEY,
    velocity_score REAL DEFAULT 0,
    curiosity_score REAL DEFAULT 0,
    ambition_score REAL DEFAULT 0,
    iteration_score REAL DEFAULT 0,
    cross_pollination_score REAL DEFAULT 0,
    teaching_score REAL DEFAULT 0,
    process_thinking_score REAL DEFAULT 0,
    proactive_usage_score REAL DEFAULT 0,
    verification_strength_score REAL DEFAULT 0,
    composite_score REAL DEFAULT 0,
    quadrant TEXT DEFAULT 'early_stage',
    last_calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- PROMPT LIBRARY + MENTORING + ROLE PATHWAYS
-- ============================================================

CREATE TABLE IF NOT EXISTS sa_prompt_library (
    prompt_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    title TEXT NOT NULL,
    prompt_text TEXT NOT NULL,
    description TEXT,
    use_case TEXT,
    department TEXT,
    tags TEXT,
    rubric_score REAL,
    usage_count INTEGER DEFAULT 0,
    is_approved INTEGER DEFAULT 0,
    reviewed_by TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sa_mentoring (
    mentoring_id INTEGER PRIMARY KEY AUTOINCREMENT,
    mentor_user_id TEXT NOT NULL,
    mentee_user_id TEXT NOT NULL,
    status TEXT CHECK(status IN ('active', 'completed', 'cancelled')) DEFAULT 'active',
    mentee_start_level INTEGER NOT NULL,
    mentee_target_level INTEGER NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sa_role_pathways (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_name TEXT NOT NULL UNIQUE,
    core_modules TEXT NOT NULL,
    specialist_modules TEXT NOT NULL,
    max_target_level INTEGER NOT NULL,
    description TEXT
);

-- ============================================================
-- DAILY CHALLENGES + PEER BATTLES
-- ============================================================

CREATE TABLE IF NOT EXISTS sa_daily_challenges_v4 (
    challenge_id INTEGER PRIMARY KEY AUTOINCREMENT,
    challenge_code TEXT NOT NULL,
    title TEXT NOT NULL,
    scenario_text TEXT NOT NULL,
    options_json TEXT,
    correct_answer TEXT,
    difficulty TEXT CHECK(difficulty IN ('standard', 'stretch', 'elite')) DEFAULT 'standard',
    topic TEXT,
    xp_reward INTEGER DEFAULT 20,
    is_monthly_check INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sa_daily_completions_v4 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    challenge_id INTEGER NOT NULL,
    challenge_date TEXT NOT NULL,
    answer TEXT,
    is_correct INTEGER,
    time_seconds INTEGER,
    xp_awarded INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, challenge_date)
);

CREATE TABLE IF NOT EXISTS sa_peer_battles_v4 (
    battle_id INTEGER PRIMARY KEY AUTOINCREMENT,
    scenario_text TEXT NOT NULL,
    exercise_id INTEGER,
    user_a_id TEXT NOT NULL,
    user_a_response TEXT,
    user_b_id TEXT,
    user_b_response TEXT,
    user_a_score REAL,
    user_b_score REAL,
    winner_user_id TEXT,
    judge_feedback_json TEXT,
    status TEXT CHECK(status IN ('open', 'matched', 'scored', 'complete')) DEFAULT 'open',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_sa_exercises_module ON sa_exercises(module_id);
CREATE INDEX IF NOT EXISTS idx_sa_exercises_curveball ON sa_exercises(is_curveball);
CREATE INDEX IF NOT EXISTS idx_sa_exercise_results_user ON sa_exercise_results(user_id);
CREATE INDEX IF NOT EXISTS idx_sa_mastery_user ON sa_mastery_evidence(user_id, target_level);
CREATE INDEX IF NOT EXISTS idx_sa_verification_user ON sa_verification_status(user_id);
CREATE INDEX IF NOT EXISTS idx_sa_xp_log_user ON sa_xp_log(user_id);
CREATE INDEX IF NOT EXISTS idx_sa_battles_status ON sa_peer_battles_v4(status);
CREATE INDEX IF NOT EXISTS idx_sa_daily_comp_user ON sa_daily_completions_v4(user_id, challenge_date);
CREATE INDEX IF NOT EXISTS idx_sa_placement_user ON sa_placement_v4(user_id);
CREATE INDEX IF NOT EXISTS idx_sa_rubric_eval_user ON sa_rubric_evaluations(user_id);
CREATE INDEX IF NOT EXISTS idx_sa_prompt_lib_user ON sa_prompt_library(user_id);
"""

# ---------------------------------------------------------------------------
# Seed data
# ---------------------------------------------------------------------------

_SEED_LEVELS = [
    (1, "seed", "Seed", "I can talk to AI", "#8BC34A", 0, 50,
     "Have your first useful AI conversation."),
    (2, "sprout", "Sprout", "I use AI daily in my role", "#4CAF50", 50, 150,
     "Apply AI to real work tasks every day."),
    (3, "growing", "Growing", "I build with AI", "#388E3C", 150, 400,
     "Create multi-step workflows. Meet the 8+ standard."),
    (4, "harvest", "Harvest", "I teach others to think bigger", "#2E7D32", 400, 800,
     "Teach AI skills. Build libraries. Produce board-quality work."),
    (5, "canopy", "Canopy", "I think without limits", "#1B5E20", 800, 1500,
     "Citizen developer. Ship tools. Reimagine processes."),
    (6, "root_system", "Root System", "I deploy AI at scale safely", "#004D40", 1500, 99999,
     "Govern AI across 500 people. Scale safely."),
]

_SEED_SERIES = [
    ("L", "L-Series: Core AI Skills",
     "Master prompting, role applications, advanced techniques, rubric evaluation, and thinking without limits.",
     "#2E7D32", "\U0001f9e0"),
    ("D", "D-Series: Data + AI",
     "Turn Harris Farm data into competitive advantage through The Hub.",
     "#1565C0", "\U0001f4ca"),
]

_SEED_RUBRICS = [
    ("foundational", "Foundational Prompt Rubric",
     "The 4 Elements scored 1-5 each.", '["1","2"]',
     json.dumps([
         {"name": "Task", "description": "Clear specific verb phrase", "weight": 0.25, "scale_min": 1, "scale_max": 5},
         {"name": "Context", "description": "Background info provided", "weight": 0.25, "scale_min": 1, "scale_max": 5},
         {"name": "Format", "description": "Output structure defined", "weight": 0.25, "scale_min": 1, "scale_max": 5},
         {"name": "Constraints", "description": "Boundaries and rules set", "weight": 0.25, "scale_min": 1, "scale_max": 5},
     ]),
     0.6),
    ("advanced_output", "Advanced Output Rubric",
     "8 criteria, 1-10. The 8+ rule.", '["3","4"]',
     json.dumps([
         {"name": "Audience", "weight": 0.15, "scale_min": 1, "scale_max": 10},
         {"name": "Storytelling", "weight": 0.10, "scale_min": 1, "scale_max": 10},
         {"name": "Actionability", "weight": 0.15, "scale_min": 1, "scale_max": 10},
         {"name": "Visual Quality", "weight": 0.10, "scale_min": 1, "scale_max": 10},
         {"name": "Completeness", "weight": 0.15, "scale_min": 1, "scale_max": 10},
         {"name": "Brevity", "weight": 0.10, "scale_min": 1, "scale_max": 10},
         {"name": "Data Integrity", "weight": 0.15, "scale_min": 1, "scale_max": 10},
         {"name": "Honesty", "weight": 0.10, "scale_min": 1, "scale_max": 10},
     ]),
     0.8),
    ("multi_tier_panel", "Multi-Tier Expert Panel",
     "5 tiers for critical deliverables.", '["4","5","6"]',
     json.dumps([
         {"name": "T1: CTO Panel", "weight": 0.20, "scale_min": 1, "scale_max": 10},
         {"name": "T2: CLO Panel", "weight": 0.20, "scale_min": 1, "scale_max": 10},
         {"name": "T3: Strategic Alignment", "weight": 0.20, "scale_min": 1, "scale_max": 10},
         {"name": "T4: Implementation", "weight": 0.20, "scale_min": 1, "scale_max": 10},
         {"name": "T5: Presentation", "weight": 0.20, "scale_min": 1, "scale_max": 10},
     ]),
     0.8),
]

_SEED_BADGES = [
    ("seed_badge", "Seed", "Confirmed at Level 1", "\U0001f331", "#8BC34A", "level_confirmed", '{"level":1}'),
    ("sprout_badge", "Sprout", "Confirmed at Level 2", "\U0001f33f", "#4CAF50", "level_confirmed", '{"level":2}'),
    ("growing_badge", "Growing", "Confirmed at Level 3", "\U0001f333", "#388E3C", "level_confirmed", '{"level":3}'),
    ("harvest_badge", "Harvest", "Confirmed at Level 4", "\U0001f33e", "#2E7D32", "level_confirmed", '{"level":4}'),
    ("canopy_badge", "Canopy", "Confirmed at Level 5", "\U0001f3d7\ufe0f", "#1B5E20", "level_confirmed", '{"level":5}'),
    ("root_system_badge", "Root System", "Confirmed at Level 6", "\U0001f6e1\ufe0f", "#004D40", "level_confirmed", '{"level":6}'),
    ("first_prompt", "First Prompt", "First rubric evaluation", "\u270d\ufe0f", "#FF9800", "special", '{"action":"first_eval"}'),
    ("quality_gate", "Quality Gate", "First 8+ score", "\u2b50", "#FFD700", "special", '{"action":"first_8plus"}'),
    ("mentor", "Mentor", "Helped a colleague level up", "\U0001f91d", "#9C27B0", "special", '{"action":"first_mentee"}'),
    ("ai_first", "AI-First Thinker", "Mindset score 18+", "\U0001f9e0", "#E91E63", "special", '{"action":"mindset_18"}'),
    ("scale_builder", "Scale Builder", "Solved L6 challenge", "\U0001f3db\ufe0f", "#004D40", "special", '{"action":"l6_challenge"}'),
    ("speed_demon", "Speed Demon", "Fastest to L3", "\u26a1", "#FF5722", "special", '{"action":"speed_l3"}'),
    ("hidden_gem", "Hidden Gem", "High HiPo before L3", "\U0001f48e", "#00BCD4", "special", '{"action":"hipo_early"}'),
    ("streak_7", "7-Day Streak", "7 days running", "\U0001f525", "#F44336", "special", '{"action":"streak_7"}'),
    ("curveball_king", "Curveball King", "5/5 on 3 consecutive curveballs", "\U0001f451", "#FFC107", "special", '{"action":"curveball_streak"}'),
]

_SEED_SCENARIOS = [
    (2, None, "Monday Morning Shrink",
     "You're a store manager. It's Monday morning. Last week your fresh produce shrink was 12% -- well above the 8% target. What do you do?"),
    (2, None, "New Product Launch",
     "Marketing asks you to predict which 3 stores would perform best for a premium organic range launch next month. How do you figure this out?"),
    (3, None, "Supplier Price Increase",
     "You're a buyer. A key supplier just announced an 8% price increase effective next week. You need to decide: absorb, pass through, or find alternatives. How do you use AI?"),
    (3, None, "Customer Complaint Spike",
     "Customer complaints about product freshness tripled at 4 stores last month. You need to find the root cause. Describe your AI-powered investigation."),
    (4, None, "Onboarding a Sceptic",
     "A senior buyer with 20 years experience says 'I don't need AI -- I know my categories.' How do you get them to Level 2?"),
    (4, None, "Board Report Quality",
     "Your team produced a board report scoring 6/10 on the output rubric. The board meeting is Thursday. Walk me through your process."),
    (5, None, "Waste Reduction System",
     "Harris Farm wants to reduce food waste 30% across all 32 stores in 6 months. You have The Hub, Claude Code, all data, no constraints. What do you build?"),
    (5, None, "Autonomous Reporting",
     "The CEO wants every board report auto-generated from live data with zero manual intervention. Design the system end-to-end."),
]

_SEED_LIVE_PROBLEMS = [
    (1, "Weekly Team Brief",
     "Write 3 prompts you would use every Monday morning to prepare for your team briefing. Each must use all 4 elements."),
    (1, "Customer Question",
     "A customer asks why mangoes are more expensive this week. Write a prompt to quickly get the answer from our data."),
    (2, "Dairy Margin Check",
     "Using The Hub, find which 3 dairy products at your store had the biggest margin decline last period. Write the prompt, interpret the result in 3 sentences for your store manager."),
    (2, "Roster Efficiency",
     "Your wages were 2% above budget last week. Use AI to analyse your roster vs actual sales by hour to find the inefficiency."),
    (3, "Demographic Campaign",
     "Marketing needs customer demographics for a new campaign. Build a 3-step analysis: identify top segments, compare across regions, produce a visual summary."),
    (3, "Transport Savings",
     "Identify $200K of annual transport cost savings across the network. Build the analysis workflow end-to-end."),
    (4, "New Starter Guide",
     "Create a 15-minute AI onboarding guide for a new buyer. Include example prompts, expected outputs, how to verify accuracy."),
    (4, "Quality Recovery",
     "A team member's board report scores 5/10. Write the feedback and coach them to 8+ in 3 iterations."),
    (5, "Weekly Shrink Automator",
     "Operations manually compiles a weekly shrink report from 5 data sources. Design and prototype an automated system with data validation."),
    (5, "Demand Forecast MVP",
     "Build a proof-of-concept demand forecasting tool for produce that factors in weather, events, and historical patterns."),
]

_SEED_ROLE_PATHWAYS = [
    ("Store Manager", '["L1","L2","L4"]', '["D1","D2","D3"]', 4,
     "Store performance, rostering, shrink"),
    ("Buyer", '["L1","L2","L3","L4"]', '["D1","D2","D4"]', 4,
     "Supplier analysis, demand forecasting, margin"),
    ("Finance", '["L1","L2","L3","L4","L5"]', '["D1","D2","D3","D4"]', 5,
     "Full data proficiency, automated reporting"),
    ("Marketing", '["L1","L2","L3","L4"]', '["D1","D2","D3"]', 4,
     "Customer insights, campaign analysis"),
    ("Logistics", '["L1","L2","L3"]', '["D1","D2"]', 3,
     "Route optimisation, transport cost"),
    ("People & Culture", '["L1","L2","L4"]', '["D1"]', 4,
     "Award interpretation, policy, training"),
    ("E-Commerce", '["L1","L2","L3","L5"]', '["D1","D2","D3","D4"]', 5,
     "Online analytics, Amazon Fresh"),
    ("IT / Digital", '["L1","L2","L3","L5"]', '["D1","D2","D3","D4"]', 6,
     "Claude Code, governance, WATCHDOG"),
    ("Property", '["L1","L2","L3"]', '["D1","D2"]', 3,
     "Site analysis, demographic data, leases"),
    ("Legal", '["L1","L2"]', '["D1"]', 2,
     "Policy queries, compliance, contracts"),
]

# L-Series modules: (series_id, code, name, desc, difficulty, minutes, prereq_id, level, order)
_SEED_MODULES = [
    # L-Series: Core AI Skills
    (1, "L1", "Prompt Foundations",
     "Master the building blocks of effective AI prompting — task verbs, specificity, context.",
     "beginner", 30, None, 1, 1),
    (1, "L2", "Data-Driven Prompting",
     "Adding metrics, time periods, and data sources to prompts for business insight.",
     "beginner", 45, 1, 2, 2),
    (1, "L3", "Advanced Techniques",
     "Chain-of-thought, few-shot examples, role assignment, and constraints.",
     "intermediate", 60, 2, 3, 3),
    (1, "L4", "Output Engineering",
     "Formatting, structured outputs, tables, action plans, executive summaries.",
     "intermediate", 60, 3, 4, 4),
    (1, "L5", "Enterprise Prompting",
     "Multi-step workflows, tool integration, system prompts, guardrails.",
     "advanced", 75, 4, 5, 5),
    # D-Series: Applied Business Intelligence
    (2, "D1", "Store Performance",
     "Using AI to analyse store sales, wastage, staffing, and customer traffic.",
     "beginner", 40, None, 1, 1),
    (2, "D2", "Product Intelligence",
     "Category management, PLU analysis, supplier negotiation, seasonal planning.",
     "intermediate", 60, 6, 2, 2),
    (2, "D3", "Customer Analytics",
     "Customer segmentation, loyalty, market share interpretation, trade areas.",
     "intermediate", 60, 7, 3, 3),
    (2, "D4", "Operations Optimisation",
     "Supply chain, transport, inventory, demand forecasting.",
     "advanced", 75, 8, 4, 4),
    (2, "D5", "Strategic Decision-Making",
     "Multi-source analysis, board presentations, scenario modelling, investment cases.",
     "advanced", 90, 9, 5, 5),
]


# ---------------------------------------------------------------------------
# Init + Seed functions
# ---------------------------------------------------------------------------

def init_v4_tables(conn: sqlite3.Connection) -> None:
    """Create all v4 tables. Safe to call repeatedly."""
    conn.executescript(_TABLES)
    conn.commit()


def _count(conn: sqlite3.Connection, table: str) -> int:
    try:
        row = conn.execute("SELECT COUNT(*) FROM {}".format(table)).fetchone()
        return row[0] if row else 0
    except Exception:
        return 0


def seed_v4_levels(conn: sqlite3.Connection) -> int:
    if _count(conn, "sa_levels") > 0:
        return 0
    conn.executemany(
        "INSERT INTO sa_levels (level_number, level_code, level_name, identity_statement, "
        "color_hex, xp_threshold_min, xp_threshold_max, description) "
        "VALUES (?,?,?,?,?,?,?,?)",
        _SEED_LEVELS,
    )
    conn.commit()
    return len(_SEED_LEVELS)


def seed_v4_series(conn: sqlite3.Connection) -> int:
    if _count(conn, "sa_series") > 0:
        return 0
    conn.executemany(
        "INSERT INTO sa_series (series_code, series_name, description, color_hex, icon) "
        "VALUES (?,?,?,?,?)",
        _SEED_SERIES,
    )
    conn.commit()
    return len(_SEED_SERIES)


def seed_v4_rubrics(conn: sqlite3.Connection) -> int:
    if _count(conn, "sa_rubrics") > 0:
        return 0
    conn.executemany(
        "INSERT INTO sa_rubrics (rubric_code, rubric_name, description, applicable_levels, "
        "criteria_json, pass_threshold) VALUES (?,?,?,?,?,?)",
        _SEED_RUBRICS,
    )
    conn.commit()
    return len(_SEED_RUBRICS)


def seed_v4_badges(conn: sqlite3.Connection) -> int:
    if _count(conn, "sa_badges_v4") > 0:
        return 0
    conn.executemany(
        "INSERT INTO sa_badges_v4 (badge_code, badge_name, description, icon, color_hex, "
        "trigger_type, trigger_value) VALUES (?,?,?,?,?,?,?)",
        _SEED_BADGES,
    )
    conn.commit()
    return len(_SEED_BADGES)


def seed_v4_scenarios(conn: sqlite3.Connection) -> int:
    if _count(conn, "sa_scenarios") > 0:
        return 0
    conn.executemany(
        "INSERT INTO sa_scenarios (level_number, role_name, scenario_title, scenario_text) "
        "VALUES (?,?,?,?)",
        _SEED_SCENARIOS,
    )
    conn.commit()
    return len(_SEED_SCENARIOS)


def seed_v4_live_problems(conn: sqlite3.Connection) -> int:
    if _count(conn, "sa_live_problems") > 0:
        return 0
    conn.executemany(
        "INSERT INTO sa_live_problems (level_number, problem_title, problem_description) "
        "VALUES (?,?,?)",
        _SEED_LIVE_PROBLEMS,
    )
    conn.commit()
    return len(_SEED_LIVE_PROBLEMS)


def seed_v4_role_pathways(conn: sqlite3.Connection) -> int:
    if _count(conn, "sa_role_pathways") > 0:
        return 0
    conn.executemany(
        "INSERT INTO sa_role_pathways (role_name, core_modules, specialist_modules, "
        "max_target_level, description) VALUES (?,?,?,?,?)",
        _SEED_ROLE_PATHWAYS,
    )
    conn.commit()
    return len(_SEED_ROLE_PATHWAYS)


def seed_v4_modules(conn: sqlite3.Connection) -> int:
    """Seed / upsert module definitions. Updates names if stale, inserts missing modules."""
    inserted = 0
    for series_id, code, name, desc, diff, mins, prereq_order, level, order in _SEED_MODULES:
        existing = conn.execute(
            "SELECT module_id FROM sa_modules WHERE module_code = ?", (code,)
        ).fetchone()
        if existing:
            # Update name/desc/level if they changed
            conn.execute(
                "UPDATE sa_modules SET module_name=?, description=?, difficulty=?, "
                "estimated_minutes=?, level_number=?, display_order=? WHERE module_code=?",
                (name, desc, diff, mins, level, order, code),
            )
        else:
            prereq_id = None
            if prereq_order is not None:
                row = conn.execute(
                    "SELECT module_id FROM sa_modules WHERE display_order = ? AND series_id = ?",
                    (prereq_order, series_id),
                ).fetchone()
                if row:
                    prereq_id = row[0]
            conn.execute(
                "INSERT INTO sa_modules (series_id, module_code, module_name, description, "
                "difficulty, estimated_minutes, prerequisite_module_id, level_number, display_order) "
                "VALUES (?,?,?,?,?,?,?,?,?)",
                (series_id, code, name, desc, diff, mins, prereq_id, level, order),
            )
            inserted += 1
    conn.commit()
    return inserted


def seed_v4_exercises(conn: sqlite3.Connection, exercises: list) -> int:
    """Seed exercises from content files (incremental — skips duplicates by exercise_title).
    Each dict: module_code, tier, context_tag, is_curveball, curveball_type,
    exercise_title, scenario_text, expected_approach, rubric_code, pass_score, xp_reward."""
    inserted = 0
    for ex in exercises:
        # Resolve module_id from module_code
        row = conn.execute(
            "SELECT module_id FROM sa_modules WHERE module_code = ?",
            (ex["module_code"],),
        ).fetchone()
        if not row:
            continue
        module_id = row[0]
        # Skip if exercise_title already exists
        dup = conn.execute(
            "SELECT 1 FROM sa_exercises WHERE exercise_title = ?",
            (ex["exercise_title"],),
        ).fetchone()
        if dup:
            continue
        conn.execute(
            "INSERT INTO sa_exercises (module_id, tier, context_tag, is_curveball, "
            "curveball_type, exercise_title, scenario_text, expected_approach, "
            "rubric_code, pass_score, xp_reward) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (
                module_id,
                ex.get("tier", "standard"),
                ex.get("context_tag", "operations"),
                1 if ex.get("is_curveball") else 0,
                ex.get("curveball_type"),
                ex["exercise_title"],
                ex["scenario_text"],
                ex.get("expected_approach"),
                ex.get("rubric_code", "foundational"),
                ex.get("pass_score", 0.6),
                ex.get("xp_reward", 15),
            ),
        )
        inserted += 1
    conn.commit()
    return inserted


def seed_v4_daily_challenges(conn: sqlite3.Connection, challenges: list) -> int:
    """Seed daily challenges. Each dict: challenge_code, title, scenario_text,
    options_json, correct_answer, difficulty, topic, xp_reward."""
    if _count(conn, "sa_daily_challenges_v4") > 0:
        return 0
    for ch in challenges:
        conn.execute(
            "INSERT INTO sa_daily_challenges_v4 (challenge_code, title, scenario_text, "
            "options_json, correct_answer, difficulty, topic, xp_reward) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (
                ch["challenge_code"],
                ch["title"],
                ch["scenario_text"],
                json.dumps(ch.get("options", [])),
                ch.get("correct_answer", ""),
                ch.get("difficulty", "standard"),
                ch.get("topic", "general"),
                ch.get("xp_reward", 20),
            ),
        )
    conn.commit()
    return len(challenges)


def seed_all_v4(db_path: str) -> dict:
    """Orchestrator: init tables and seed all reference data.
    Call from backend/app.py startup."""
    conn = sqlite3.connect(db_path)
    try:
        init_v4_tables(conn)
        results = {
            "levels": seed_v4_levels(conn),
            "series": seed_v4_series(conn),
            "modules": seed_v4_modules(conn),
            "rubrics": seed_v4_rubrics(conn),
            "badges": seed_v4_badges(conn),
            "scenarios": seed_v4_scenarios(conn),
            "live_problems": seed_v4_live_problems(conn),
            "role_pathways": seed_v4_role_pathways(conn),
        }
        # Exercises and daily challenges seeded separately (from content files)
        return results
    finally:
        conn.close()
