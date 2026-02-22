"""
Harris Farm Markets - The Hub
AI Centre of Excellence - Backend API
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
import anthropic
import openai
import httpx
import asyncio
from datetime import datetime, timedelta
import json
import sqlite3
import os
import logging
import re
from pathlib import Path
from contextlib import asynccontextmanager
import sys
from dotenv import load_dotenv

# Ensure backend/ is on sys.path so `import auth`, `import transaction_layer` etc. work
# regardless of working directory (required when run as `python -m uvicorn backend.app:app`)
_backend_dir = os.path.dirname(os.path.abspath(__file__))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

logger = logging.getLogger("hub_api")

# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    # API Keys (set as environment variables in production)
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    GROK_API_KEY = os.getenv("GROK_API_KEY", "")
    
    # Database (configure based on Harris Farm's DB)
    DATABASE_TYPE = os.getenv("DB_TYPE", "postgresql")
    DATABASE_HOST = os.getenv("DB_HOST", "localhost")
    DATABASE_PORT = os.getenv("DB_PORT", "5432")
    DATABASE_NAME = os.getenv("DB_NAME", "harris_farm")
    DATABASE_USER = os.getenv("DB_USER", "")
    DATABASE_PASSWORD = os.getenv("DB_PASSWORD", "")
    
    # Hub Settings
    HUB_DB = os.path.join(os.path.dirname(__file__), "hub_data.db")
    MAX_QUERY_RESULTS = 1000

config = Config()

# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

def init_hub_database():
    """Initialize SQLite database for Hub metadata and learning"""
    conn = sqlite3.connect(config.HUB_DB)
    c = conn.cursor()
    
    # Query history
    c.execute('''CREATE TABLE IF NOT EXISTS queries
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  question TEXT NOT NULL,
                  query_type TEXT,
                  user_id TEXT,
                  timestamp TEXT,
                  context TEXT)''')
    
    # LLM responses for The Rubric
    c.execute('''CREATE TABLE IF NOT EXISTS llm_responses
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  query_id INTEGER,
                  provider TEXT,
                  response TEXT,
                  tokens INTEGER,
                  latency_ms REAL,
                  timestamp TEXT,
                  FOREIGN KEY (query_id) REFERENCES queries(id))''')
    
    # Chairman's decisions
    c.execute('''CREATE TABLE IF NOT EXISTS evaluations
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  query_id INTEGER,
                  winner TEXT,
                  feedback TEXT,
                  user_id TEXT,
                  timestamp TEXT,
                  FOREIGN KEY (query_id) REFERENCES queries(id))''')
    
    # User feedback for self-improvement
    c.execute('''CREATE TABLE IF NOT EXISTS feedback
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  query_id INTEGER,
                  rating INTEGER,
                  comment TEXT,
                  user_id TEXT,
                  timestamp TEXT,
                  FOREIGN KEY (query_id) REFERENCES queries(id))''')
    
    # Prompt templates library
    c.execute('''CREATE TABLE IF NOT EXISTS prompt_templates
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  title TEXT,
                  description TEXT,
                  template TEXT,
                  category TEXT,
                  difficulty TEXT,
                  uses INTEGER DEFAULT 0,
                  avg_rating REAL DEFAULT 0,
                  created_at TEXT,
                  updated_at TEXT)''')
    
    # Generated SQL queries (for learning)
    c.execute('''CREATE TABLE IF NOT EXISTS generated_queries
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  query_id INTEGER,
                  natural_language TEXT,
                  generated_sql TEXT,
                  execution_success BOOLEAN,
                  result_count INTEGER,
                  error_message TEXT,
                  timestamp TEXT,
                  FOREIGN KEY (query_id) REFERENCES queries(id))''')
    
    # Knowledge base (extracted from OneDrive documents)
    c.execute('''CREATE TABLE IF NOT EXISTS knowledge_base
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  source_path TEXT NOT NULL,
                  filename TEXT NOT NULL,
                  category TEXT,
                  doc_type TEXT,
                  content TEXT NOT NULL,
                  content_hash TEXT UNIQUE,
                  word_count INTEGER,
                  chunk_index INTEGER DEFAULT 0,
                  chunk_total INTEGER DEFAULT 1,
                  extracted_at TEXT NOT NULL)''')
    c.execute("CREATE INDEX IF NOT EXISTS idx_kb_category ON knowledge_base(category)")

    # FTS5 full-text search index (Porter stemming, Unicode-aware)
    c.execute('''CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
                 filename, category, content,
                 content=knowledge_base, content_rowid=id,
                 tokenize='porter unicode61')''')

    # Triggers to keep FTS5 in sync with knowledge_base
    c.execute('''CREATE TRIGGER IF NOT EXISTS kb_fts_insert
                 AFTER INSERT ON knowledge_base BEGIN
                     INSERT INTO knowledge_fts(rowid, filename, category, content)
                     VALUES (new.id, new.filename, new.category, new.content);
                 END''')
    c.execute('''CREATE TRIGGER IF NOT EXISTS kb_fts_delete
                 AFTER DELETE ON knowledge_base BEGIN
                     INSERT INTO knowledge_fts(knowledge_fts, rowid, filename, category, content)
                     VALUES ('delete', old.id, old.filename, old.category, old.content);
                 END''')
    c.execute('''CREATE TRIGGER IF NOT EXISTS kb_fts_update
                 AFTER UPDATE ON knowledge_base BEGIN
                     INSERT INTO knowledge_fts(knowledge_fts, rowid, filename, category, content)
                     VALUES ('delete', old.id, old.filename, old.category, old.content);
                     INSERT INTO knowledge_fts(rowid, filename, category, content)
                     VALUES (new.id, new.filename, new.category, new.content);
                 END''')

    # Chatbot conversations
    c.execute('''CREATE TABLE IF NOT EXISTS chat_messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  session_id TEXT NOT NULL,
                  role TEXT NOT NULL,
                  content TEXT NOT NULL,
                  provider TEXT,
                  category_filter TEXT,
                  kb_docs_used TEXT,
                  tokens INTEGER DEFAULT 0,
                  latency_ms REAL DEFAULT 0,
                  timestamp TEXT NOT NULL)''')
    c.execute("CREATE INDEX IF NOT EXISTS idx_chat_session ON chat_messages(session_id)")

    # Employee roles (imported from HFM Job Roles)
    c.execute('''CREATE TABLE IF NOT EXISTS employee_roles
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  function TEXT NOT NULL,
                  department TEXT NOT NULL,
                  job TEXT NOT NULL,
                  created_at TEXT NOT NULL,
                  updated_at TEXT NOT NULL,
                  UNIQUE(function, department, job))''')
    c.execute("CREATE INDEX IF NOT EXISTS idx_roles_function ON employee_roles(function)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_roles_department ON employee_roles(department)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_roles_job ON employee_roles(job)")

    # Learning modules (12 modules: L1-L4, D1-D4, K1-K4)
    c.execute('''CREATE TABLE IF NOT EXISTS learning_modules
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  code TEXT NOT NULL UNIQUE,
                  pillar TEXT NOT NULL,
                  name TEXT NOT NULL,
                  description TEXT,
                  duration_minutes INTEGER DEFAULT 30,
                  difficulty TEXT DEFAULT 'beginner',
                  prerequisites TEXT DEFAULT '[]',
                  sort_order INTEGER DEFAULT 0,
                  icon TEXT DEFAULT '',
                  created_at TEXT NOT NULL)''')
    c.execute("CREATE INDEX IF NOT EXISTS idx_lm_pillar ON learning_modules(pillar)")

    # Lessons within modules
    c.execute('''CREATE TABLE IF NOT EXISTS lessons
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  module_code TEXT NOT NULL,
                  lesson_number INTEGER NOT NULL,
                  title TEXT NOT NULL,
                  content_type TEXT DEFAULT 'theory',
                  content TEXT NOT NULL,
                  duration_minutes INTEGER DEFAULT 15,
                  sort_order INTEGER DEFAULT 0,
                  created_at TEXT NOT NULL,
                  FOREIGN KEY (module_code) REFERENCES learning_modules(code))''')
    c.execute("CREATE INDEX IF NOT EXISTS idx_lesson_module ON lessons(module_code)")

    # User progress per module
    c.execute('''CREATE TABLE IF NOT EXISTS user_progress
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id TEXT NOT NULL,
                  module_code TEXT NOT NULL,
                  status TEXT DEFAULT 'not_started',
                  completion_pct INTEGER DEFAULT 0,
                  score INTEGER DEFAULT 0,
                  time_spent_minutes INTEGER DEFAULT 0,
                  started_at TEXT,
                  completed_at TEXT,
                  updated_at TEXT NOT NULL,
                  UNIQUE(user_id, module_code),
                  FOREIGN KEY (module_code) REFERENCES learning_modules(code))''')
    c.execute("CREATE INDEX IF NOT EXISTS idx_up_user ON user_progress(user_id)")

    # Role-module priority mapping
    c.execute('''CREATE TABLE IF NOT EXISTS role_module_mapping
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  function TEXT NOT NULL,
                  department TEXT NOT NULL,
                  module_code TEXT NOT NULL,
                  priority TEXT NOT NULL,
                  FOREIGN KEY (module_code) REFERENCES learning_modules(code))''')
    c.execute("CREATE INDEX IF NOT EXISTS idx_rmm_role ON role_module_mapping(function, department)")

    # Portal tables (prompt history, gamification)
    c.execute('''CREATE TABLE IF NOT EXISTS prompt_history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id TEXT NOT NULL,
                  prompt_text TEXT NOT NULL,
                  context TEXT,
                  outcome TEXT,
                  rating INTEGER,
                  ai_review TEXT,
                  tokens INTEGER,
                  latency_ms INTEGER,
                  created_at TEXT DEFAULT (datetime('now')))''')

    c.execute('''CREATE TABLE IF NOT EXISTS portal_scores
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id TEXT NOT NULL,
                  points INTEGER NOT NULL,
                  category TEXT NOT NULL,
                  reason TEXT,
                  created_at TEXT DEFAULT (datetime('now')))''')

    c.execute('''CREATE TABLE IF NOT EXISTS portal_achievements
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id TEXT NOT NULL,
                  achievement_code TEXT NOT NULL,
                  achieved_at TEXT DEFAULT (datetime('now')),
                  UNIQUE(user_id, achievement_code))''')
    c.execute("CREATE INDEX IF NOT EXISTS idx_scores_user ON portal_scores(user_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_scores_cat ON portal_scores(category)")

    # ---- Arena Competition Tables ----
    c.execute('''CREATE TABLE IF NOT EXISTS arena_proposals
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  title TEXT NOT NULL,
                  description TEXT NOT NULL,
                  team_id TEXT NOT NULL,
                  agent_id TEXT NOT NULL,
                  department TEXT NOT NULL,
                  category TEXT NOT NULL,
                  status TEXT DEFAULT 'submitted',
                  estimated_impact_aud REAL,
                  estimated_effort_weeks REAL,
                  complexity TEXT DEFAULT 'medium',
                  total_score REAL DEFAULT 0,
                  tier_scores TEXT DEFAULT '{}',
                  submitted_at TEXT DEFAULT (datetime('now')),
                  scored_at TEXT,
                  is_seeded INTEGER DEFAULT 0)''')
    c.execute("CREATE INDEX IF NOT EXISTS idx_ap_team ON arena_proposals(team_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_ap_status ON arena_proposals(status)")

    c.execute('''CREATE TABLE IF NOT EXISTS arena_evaluations
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  proposal_id INTEGER NOT NULL,
                  tier TEXT NOT NULL,
                  evaluator TEXT NOT NULL,
                  criterion TEXT NOT NULL,
                  score INTEGER NOT NULL,
                  comment TEXT,
                  evaluated_at TEXT DEFAULT (datetime('now')),
                  FOREIGN KEY (proposal_id) REFERENCES arena_proposals(id))''')
    c.execute("CREATE INDEX IF NOT EXISTS idx_ae_proposal ON arena_evaluations(proposal_id)")

    c.execute('''CREATE TABLE IF NOT EXISTS arena_team_stats
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  team_id TEXT NOT NULL,
                  period TEXT NOT NULL,
                  total_proposals INTEGER DEFAULT 0,
                  avg_score REAL DEFAULT 0,
                  total_impact_aud REAL DEFAULT 0,
                  implementations INTEGER DEFAULT 0,
                  multiplier REAL DEFAULT 1.0,
                  rank INTEGER DEFAULT 0,
                  updated_at TEXT DEFAULT (datetime('now')),
                  UNIQUE(team_id, period))''')
    c.execute("CREATE INDEX IF NOT EXISTS idx_ats_team ON arena_team_stats(team_id)")

    c.execute('''CREATE TABLE IF NOT EXISTS arena_insights
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  agent_id TEXT NOT NULL,
                  team_id TEXT NOT NULL,
                  department TEXT NOT NULL,
                  insight_type TEXT NOT NULL,
                  title TEXT NOT NULL,
                  description TEXT NOT NULL,
                  data_source TEXT,
                  confidence REAL DEFAULT 0.8,
                  potential_impact_aud REAL,
                  status TEXT DEFAULT 'active',
                  created_at TEXT DEFAULT (datetime('now')),
                  is_seeded INTEGER DEFAULT 0)''')
    c.execute("CREATE INDEX IF NOT EXISTS idx_ai_team ON arena_insights(team_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_ai_dept ON arena_insights(department)")

    # WATCHDOG Safety tables
    c.execute('''CREATE TABLE IF NOT EXISTS watchdog_proposals
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  tracking_id TEXT UNIQUE NOT NULL,
                  source_proposal_id INTEGER,
                  agent_id TEXT NOT NULL,
                  title TEXT NOT NULL,
                  description TEXT,
                  proposal_json TEXT,
                  risk_level TEXT DEFAULT 'PENDING',
                  finding_count INTEGER DEFAULT 0,
                  report TEXT,
                  recommendation TEXT,
                  status TEXT DEFAULT 'pending_review',
                  reviewed_by TEXT,
                  reviewed_at TEXT,
                  comments TEXT,
                  created_at TEXT DEFAULT (datetime('now')))''')
    c.execute("CREATE INDEX IF NOT EXISTS idx_wp_status ON watchdog_proposals(status)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_wp_risk ON watchdog_proposals(risk_level)")

    c.execute('''CREATE TABLE IF NOT EXISTS watchdog_audit
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  tracking_id TEXT NOT NULL,
                  agent_id TEXT,
                  title TEXT,
                  risk_level TEXT,
                  finding_count INTEGER DEFAULT 0,
                  report TEXT,
                  proposal_json TEXT,
                  analyzed_at TEXT DEFAULT (datetime('now')))''')
    c.execute("CREATE INDEX IF NOT EXISTS idx_wa_tracking ON watchdog_audit(tracking_id)")

    c.execute('''CREATE TABLE IF NOT EXISTS watchdog_decisions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  tracking_id TEXT NOT NULL,
                  decision TEXT NOT NULL,
                  approver TEXT NOT NULL,
                  comments TEXT,
                  decided_at TEXT DEFAULT (datetime('now')))''')
    c.execute("CREATE INDEX IF NOT EXISTS idx_wdec_tracking ON watchdog_decisions(tracking_id)")

    # Intelligence reports (real data analysis results)
    c.execute('''CREATE TABLE IF NOT EXISTS intelligence_reports
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  analysis_type TEXT NOT NULL,
                  agent_id TEXT,
                  title TEXT NOT NULL,
                  status TEXT DEFAULT 'completed',
                  report_json TEXT NOT NULL,
                  rubric_scores_json TEXT,
                  rubric_grade TEXT,
                  rubric_average REAL,
                  store_id TEXT,
                  parameters_json TEXT,
                  created_at TEXT DEFAULT (datetime('now')))''')
    c.execute("CREATE INDEX IF NOT EXISTS idx_ir_type ON intelligence_reports(analysis_type)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_ir_grade ON intelligence_reports(rubric_grade)")

    # Agent task execution log
    c.execute('''CREATE TABLE IF NOT EXISTS agent_tasks
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_query TEXT NOT NULL,
                  status TEXT DEFAULT 'pending',
                  matched_analyses TEXT,
                  routing_confidence REAL,
                  routing_reasoning TEXT,
                  results_json TEXT,
                  watchdog_status TEXT,
                  watchdog_report_json TEXT,
                  error_message TEXT,
                  created_at TEXT DEFAULT (datetime('now')),
                  completed_at TEXT)''')
    c.execute("CREATE INDEX IF NOT EXISTS idx_at_status ON agent_tasks(status)")

    # Self-improvement: structured score tracking
    c.execute('''CREATE TABLE IF NOT EXISTS task_scores
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  task_name TEXT NOT NULL,
                  h INTEGER NOT NULL DEFAULT 0,
                  r INTEGER NOT NULL DEFAULT 0,
                  s INTEGER NOT NULL DEFAULT 0,
                  c INTEGER NOT NULL DEFAULT 0,
                  d INTEGER NOT NULL DEFAULT 0,
                  u INTEGER NOT NULL DEFAULT 0,
                  x INTEGER NOT NULL DEFAULT 0,
                  avg_score REAL NOT NULL DEFAULT 0,
                  recorded_at TEXT DEFAULT (datetime('now')))''')
    c.execute("CREATE INDEX IF NOT EXISTS idx_ts_recorded ON task_scores(recorded_at)")

    # Self-improvement: improvement cycle tracking
    c.execute('''CREATE TABLE IF NOT EXISTS improvement_cycles
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  criterion TEXT NOT NULL,
                  criterion_label TEXT,
                  before_score REAL NOT NULL,
                  after_score REAL,
                  action_taken TEXT NOT NULL,
                  attempt_number INTEGER NOT NULL DEFAULT 1,
                  status TEXT NOT NULL DEFAULT 'pending',
                  recorded_at TEXT DEFAULT (datetime('now')))''')
    c.execute("CREATE INDEX IF NOT EXISTS idx_ic_criterion ON improvement_cycles(criterion)")

    # Continuous improvement: automated audit findings
    c.execute('''CREATE TABLE IF NOT EXISTS improvement_findings
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  category TEXT NOT NULL,
                  severity TEXT NOT NULL,
                  file_path TEXT,
                  line_number INTEGER,
                  title TEXT NOT NULL,
                  detail TEXT,
                  recommendation TEXT,
                  status TEXT DEFAULT 'open',
                  content_hash TEXT UNIQUE,
                  created_at TEXT DEFAULT (datetime('now')),
                  resolved_at TEXT)''')
    c.execute("CREATE INDEX IF NOT EXISTS idx_if_status ON improvement_findings(status)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_if_category ON improvement_findings(category)")

    # Page quality scores (Academy site quality rubric)
    c.execute('''CREATE TABLE IF NOT EXISTS page_quality_scores
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  page_name TEXT NOT NULL,
                  rubric_type TEXT NOT NULL,
                  scorer TEXT DEFAULT 'anonymous',
                  scores_json TEXT NOT NULL,
                  total_score INTEGER NOT NULL,
                  max_score INTEGER NOT NULL,
                  created_at TEXT DEFAULT (datetime('now')))''')
    c.execute("CREATE INDEX IF NOT EXISTS idx_pqs_page ON page_quality_scores(page_name)")

    # Agent Control Panel: approval queue
    c.execute('''CREATE TABLE IF NOT EXISTS agent_proposals
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  agent_name TEXT NOT NULL,
                  task_type TEXT NOT NULL DEFAULT 'ANALYSIS',
                  description TEXT NOT NULL,
                  proposed_changes TEXT,
                  risk_level TEXT DEFAULT 'MEDIUM',
                  estimated_impact TEXT,
                  status TEXT DEFAULT 'PENDING',
                  created_at TEXT DEFAULT (datetime('now')),
                  reviewed_at TEXT,
                  reviewer TEXT,
                  reviewer_notes TEXT,
                  execution_result TEXT)''')
    c.execute("CREATE INDEX IF NOT EXISTS idx_agp_status ON agent_proposals(status)")

    # Agent Control Panel: per-agent performance scores
    c.execute('''CREATE TABLE IF NOT EXISTS agent_scores
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  agent_name TEXT NOT NULL,
                  metric TEXT NOT NULL,
                  score REAL NOT NULL,
                  baseline REAL,
                  evidence TEXT,
                  timestamp TEXT DEFAULT (datetime('now')))''')
    c.execute("CREATE INDEX IF NOT EXISTS idx_ags_time ON agent_scores(timestamp DESC)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_ags_agent ON agent_scores(agent_name)")

    # Game Agents: 6 competing AI agents with points and leaderboard
    c.execute('''CREATE TABLE IF NOT EXISTS game_agents
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT UNIQUE NOT NULL,
                  specialty TEXT NOT NULL,
                  category TEXT NOT NULL,
                  system_prompt TEXT,
                  total_points INTEGER DEFAULT 0,
                  reports_completed INTEGER DEFAULT 0,
                  reports_implemented INTEGER DEFAULT 0,
                  avg_rubric_score REAL DEFAULT 0.0,
                  revenue_found REAL DEFAULT 0.0,
                  active INTEGER DEFAULT 1,
                  created_at TEXT DEFAULT (datetime('now')),
                  updated_at TEXT DEFAULT (datetime('now')))''')
    c.execute("CREATE INDEX IF NOT EXISTS idx_ga_points ON game_agents(total_points DESC)")

    c.execute('''CREATE TABLE IF NOT EXISTS game_points_log
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  agent_name TEXT NOT NULL,
                  proposal_id INTEGER,
                  points INTEGER NOT NULL,
                  breakdown TEXT,
                  multiplier REAL DEFAULT 1.0,
                  created_at TEXT DEFAULT (datetime('now')))''')
    c.execute("CREATE INDEX IF NOT EXISTS idx_gpl_agent ON game_points_log(agent_name)")

    c.execute('''CREATE TABLE IF NOT EXISTS game_achievements
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  agent_name TEXT NOT NULL,
                  achievement_code TEXT NOT NULL,
                  achievement_name TEXT NOT NULL,
                  points_awarded INTEGER DEFAULT 0,
                  earned_at TEXT DEFAULT (datetime('now')),
                  UNIQUE(agent_name, achievement_code))''')
    c.execute("CREATE INDEX IF NOT EXISTS idx_gach_agent ON game_achievements(agent_name)")

    # Sustainability KPIs for Greater Goodness dashboard
    c.execute('''CREATE TABLE IF NOT EXISTS sustainability_kpis
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  kpi_name TEXT UNIQUE NOT NULL,
                  category TEXT NOT NULL,
                  target_value REAL DEFAULT 100,
                  current_value REAL DEFAULT 0,
                  unit TEXT DEFAULT '%',
                  status TEXT DEFAULT 'in_progress',
                  last_updated TEXT,
                  notes TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS watchdog_runs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  run_at TEXT NOT NULL,
                  health_api TEXT,
                  health_hub TEXT,
                  findings_total INTEGER DEFAULT 0,
                  findings_new INTEGER DEFAULT 0,
                  scores_backfilled INTEGER DEFAULT 0,
                  health_metrics_json TEXT,
                  created_at TEXT DEFAULT (datetime('now')))''')

    # ---- The Paddock: AI skills assessment tables ----
    c.execute('''CREATE TABLE IF NOT EXISTS paddock_users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  hub_user_id TEXT,
                  name TEXT NOT NULL,
                  employee_id TEXT,
                  store TEXT NOT NULL,
                  department TEXT NOT NULL,
                  role_tier INTEGER NOT NULL DEFAULT 3,
                  tech_comfort INTEGER DEFAULT 3,
                  ai_experience TEXT,
                  created_at TEXT DEFAULT (datetime('now')))''')
    c.execute("CREATE INDEX IF NOT EXISTS idx_pu_hub_user ON paddock_users(hub_user_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_pu_store ON paddock_users(store)")

    c.execute('''CREATE TABLE IF NOT EXISTS paddock_responses
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER NOT NULL,
                  module TEXT NOT NULL,
                  question_id TEXT NOT NULL,
                  answer TEXT,
                  score INTEGER DEFAULT 0,
                  time_taken_seconds INTEGER,
                  created_at TEXT DEFAULT (datetime('now')),
                  FOREIGN KEY (user_id) REFERENCES paddock_users(id))''')
    c.execute("CREATE INDEX IF NOT EXISTS idx_pr_user ON paddock_responses(user_id)")
    c.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_pr_unique ON paddock_responses(user_id, module, question_id)")

    c.execute('''CREATE TABLE IF NOT EXISTS paddock_results
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER NOT NULL,
                  maturity_level INTEGER NOT NULL,
                  awareness_score INTEGER DEFAULT 0,
                  usage_score INTEGER DEFAULT 0,
                  critical_score INTEGER DEFAULT 0,
                  applied_score INTEGER DEFAULT 0,
                  confidence_score INTEGER DEFAULT 0,
                  overall_score INTEGER DEFAULT 0,
                  created_at TEXT DEFAULT (datetime('now')),
                  FOREIGN KEY (user_id) REFERENCES paddock_users(id))''')
    c.execute("CREATE INDEX IF NOT EXISTS idx_pres_user ON paddock_results(user_id)")

    c.execute('''CREATE TABLE IF NOT EXISTS paddock_feedback
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER NOT NULL,
                  experience_rating INTEGER,
                  confusion_notes TEXT,
                  improvement_suggestions TEXT,
                  created_at TEXT DEFAULT (datetime('now')),
                  FOREIGN KEY (user_id) REFERENCES paddock_users(id))''')

    # ---- Prompt-to-Approval System tables ----

    # PtA submissions: the core workflow table
    c.execute('''CREATE TABLE IF NOT EXISTS pta_submissions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id TEXT NOT NULL,
                  user_role TEXT NOT NULL,
                  task_type TEXT NOT NULL,
                  original_prompt TEXT NOT NULL,
                  assembled_prompt TEXT,
                  data_sources TEXT DEFAULT '[]',
                  context_text TEXT,
                  analysis_types TEXT DEFAULT '[]',
                  output_format TEXT DEFAULT 'Executive Summary',
                  ai_output TEXT,
                  ai_provider TEXT DEFAULT 'claude',
                  ai_tokens INTEGER DEFAULT 0,
                  ai_latency_ms REAL DEFAULT 0,
                  human_annotations TEXT DEFAULT '[]',
                  iteration_count INTEGER DEFAULT 1,
                  version_history TEXT DEFAULT '[]',
                  rubric_scores TEXT,
                  rubric_average REAL,
                  rubric_verdict TEXT,
                  advanced_rubric_scores TEXT,
                  approval_level TEXT,
                  approver_role TEXT,
                  status TEXT DEFAULT 'draft',
                  approver_notes TEXT,
                  decided_at TEXT,
                  created_at TEXT DEFAULT (datetime('now')),
                  updated_at TEXT DEFAULT (datetime('now')))''')
    c.execute("CREATE INDEX IF NOT EXISTS idx_pta_user ON pta_submissions(user_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_pta_status ON pta_submissions(status)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_pta_type ON pta_submissions(task_type)")

    # PtA audit log: every action tracked
    c.execute('''CREATE TABLE IF NOT EXISTS pta_audit_log
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id TEXT,
                  action TEXT NOT NULL,
                  entity_type TEXT,
                  entity_id INTEGER,
                  details TEXT,
                  created_at TEXT DEFAULT (datetime('now')))''')
    c.execute("CREATE INDEX IF NOT EXISTS idx_pta_audit_entity ON pta_audit_log(entity_type, entity_id)")

    # PtA user points (staff gamification)
    c.execute('''CREATE TABLE IF NOT EXISTS pta_points_log
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id TEXT NOT NULL,
                  action TEXT NOT NULL,
                  points INTEGER NOT NULL,
                  multiplier REAL DEFAULT 1.0,
                  total_awarded INTEGER NOT NULL,
                  reference_id INTEGER,
                  reference_type TEXT,
                  created_at TEXT DEFAULT (datetime('now')))''')
    c.execute("CREATE INDEX IF NOT EXISTS idx_pta_pts_user ON pta_points_log(user_id)")

    # ---- Workflow Engine tables (Step 4 of PtA spec) ----

    # Projects: multi-project tracking
    c.execute('''CREATE TABLE IF NOT EXISTS pta_projects
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  description TEXT,
                  owner_id TEXT,
                  department TEXT,
                  strategic_pillar TEXT,
                  priority TEXT DEFAULT 'P3',
                  status TEXT DEFAULT 'active',
                  target_date TEXT,
                  health TEXT DEFAULT 'green',
                  tags TEXT DEFAULT '[]',
                  created_at TEXT DEFAULT (datetime('now')),
                  updated_at TEXT DEFAULT (datetime('now')))''')
    c.execute("CREATE INDEX IF NOT EXISTS idx_pta_proj_status ON pta_projects(status)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_pta_proj_owner ON pta_projects(owner_id)")

    # Workflow transitions: state machine history
    c.execute('''CREATE TABLE IF NOT EXISTS pta_workflow_transitions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  submission_id INTEGER NOT NULL,
                  from_stage TEXT NOT NULL,
                  to_stage TEXT NOT NULL,
                  triggered_by TEXT,
                  reason TEXT,
                  metadata TEXT,
                  created_at TEXT DEFAULT (datetime('now')),
                  FOREIGN KEY (submission_id) REFERENCES pta_submissions(id))''')
    c.execute("CREATE INDEX IF NOT EXISTS idx_pta_wf_sub ON pta_workflow_transitions(submission_id)")

    # Notifications: keep work moving
    c.execute('''CREATE TABLE IF NOT EXISTS pta_notifications
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id TEXT NOT NULL,
                  type TEXT NOT NULL,
                  title TEXT NOT NULL,
                  message TEXT NOT NULL,
                  link TEXT,
                  read INTEGER DEFAULT 0,
                  created_at TEXT DEFAULT (datetime('now')))''')
    c.execute("CREATE INDEX IF NOT EXISTS idx_pta_notif_user ON pta_notifications(user_id, read)")

    # Add workflow_stage and project_id columns to pta_submissions (safe ALTER TABLE)
    for col_def in [
        ("workflow_stage", "TEXT DEFAULT 'draft'"),
        ("project_id", "INTEGER"),
        ("implementation_owner_id", "TEXT"),
        ("implementation_status", "TEXT"),
        ("impact_measured", "TEXT"),
        ("completed_at", "TEXT"),
    ]:
        try:
            c.execute(f"ALTER TABLE pta_submissions ADD COLUMN {col_def[0]} {col_def[1]}")
        except sqlite3.OperationalError:
            pass  # Column already exists

    c.execute("CREATE INDEX IF NOT EXISTS idx_pta_stage ON pta_submissions(workflow_stage)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_pta_project ON pta_submissions(project_id)")

    # ---- Academy Gamification Tables ----
    c.execute('''CREATE TABLE IF NOT EXISTS academy_xp_log
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id TEXT NOT NULL,
                  xp_amount INTEGER NOT NULL,
                  base_amount INTEGER NOT NULL,
                  multiplier REAL DEFAULT 1.0,
                  action_type TEXT NOT NULL,
                  reference_id TEXT,
                  reference_type TEXT,
                  description TEXT,
                  created_at TEXT DEFAULT (datetime('now')))''')
    c.execute("CREATE INDEX IF NOT EXISTS idx_axp_user ON academy_xp_log(user_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_axp_action ON academy_xp_log(action_type)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_axp_created ON academy_xp_log(created_at)")

    c.execute('''CREATE TABLE IF NOT EXISTS academy_streaks
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id TEXT UNIQUE NOT NULL,
                  current_streak INTEGER DEFAULT 0,
                  longest_streak INTEGER DEFAULT 0,
                  last_active_date TEXT,
                  streak_multiplier REAL DEFAULT 1.0,
                  total_active_days INTEGER DEFAULT 0,
                  updated_at TEXT DEFAULT (datetime('now')))''')
    c.execute("CREATE INDEX IF NOT EXISTS idx_astrk_user ON academy_streaks(user_id)")

    c.execute('''CREATE TABLE IF NOT EXISTS academy_daily_challenges
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  challenge_code TEXT UNIQUE NOT NULL,
                  title TEXT NOT NULL,
                  description TEXT NOT NULL,
                  challenge_type TEXT NOT NULL,
                  difficulty TEXT DEFAULT 'beginner',
                  xp_reward INTEGER DEFAULT 20,
                  target_level TEXT,
                  metadata_json TEXT DEFAULT '{}',
                  active INTEGER DEFAULT 1,
                  created_at TEXT DEFAULT (datetime('now')))''')
    c.execute("CREATE INDEX IF NOT EXISTS idx_adc_type ON academy_daily_challenges(challenge_type)")

    c.execute('''CREATE TABLE IF NOT EXISTS academy_daily_completions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id TEXT NOT NULL,
                  challenge_id INTEGER NOT NULL,
                  challenge_date TEXT NOT NULL,
                  completed_at TEXT DEFAULT (datetime('now')),
                  xp_earned INTEGER DEFAULT 0,
                  UNIQUE(user_id, challenge_id, challenge_date),
                  FOREIGN KEY (challenge_id) REFERENCES academy_daily_challenges(id))''')
    c.execute("CREATE INDEX IF NOT EXISTS idx_adcomp_user ON academy_daily_completions(user_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_adcomp_date ON academy_daily_completions(challenge_date)")

    c.execute('''CREATE TABLE IF NOT EXISTS academy_badges
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id TEXT NOT NULL,
                  badge_code TEXT NOT NULL,
                  badge_name TEXT NOT NULL,
                  badge_icon TEXT DEFAULT '',
                  badge_description TEXT,
                  category TEXT DEFAULT 'achievement',
                  xp_awarded INTEGER DEFAULT 0,
                  earned_at TEXT DEFAULT (datetime('now')),
                  UNIQUE(user_id, badge_code))''')
    c.execute("CREATE INDEX IF NOT EXISTS idx_abadge_user ON academy_badges(user_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_abadge_code ON academy_badges(badge_code)")

    conn.commit()
    conn.close()

def seed_arena_data():
    """Seed arena tables with sample proposals and insights. Idempotent."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "dashboards"))
    from shared.agent_teams import (
        SEED_PROPOSALS, SEED_INSIGHTS, SEED_DATA_INTEL_INSIGHTS,
    )

    conn = sqlite3.connect(config.HUB_DB)
    count = conn.execute("SELECT COUNT(*) FROM arena_proposals").fetchone()[0]
    if count > 0:
        conn.close()
        return

    c = conn.cursor()
    for p in SEED_PROPOSALS:
        c.execute(
            "INSERT INTO arena_proposals (title, description, team_id, "
            "agent_id, department, category, status, estimated_impact_aud, "
            "estimated_effort_weeks, complexity, total_score, tier_scores, "
            "is_seeded) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,1)",
            (p["title"], p["description"], p["team_id"], p["agent_id"],
             p["department"], p["category"], p["status"],
             p.get("estimated_impact_aud", 0),
             p.get("estimated_effort_weeks", 0),
             p.get("complexity", "medium"),
             p.get("total_score", 0), p.get("tier_scores", "{}")),
        )

    for ins in SEED_INSIGHTS:
        c.execute(
            "INSERT INTO arena_insights (agent_id, team_id, department, "
            "insight_type, title, description, data_source, confidence, "
            "potential_impact_aud, is_seeded) VALUES (?,?,?,?,?,?,?,?,?,1)",
            (ins["agent_id"], ins["team_id"], ins["department"],
             ins["insight_type"], ins["title"], ins["description"],
             ins.get("data_source", ""), ins.get("confidence", 0.8),
             ins.get("potential_impact_aud", 0)),
        )

    # Seed Data Intelligence insights
    for ins in SEED_DATA_INTEL_INSIGHTS:
        c.execute(
            "INSERT INTO arena_insights (agent_id, team_id, department, "
            "insight_type, title, description, data_source, confidence, "
            "potential_impact_aud, is_seeded) VALUES (?,?,?,?,?,?,?,?,?,1)",
            (ins["agent_id"], ins["team_id"], ins["department"],
             ins["insight_type"], ins["title"], ins["description"],
             ins.get("data_source", ""), ins.get("confidence", 0.8),
             ins.get("potential_impact_aud", 0)),
        )

    # Calculate team stats
    for team_id in ["alpha", "beta", "gamma", "delta", "epsilon"]:
        row = conn.execute(
            "SELECT COUNT(*) AS cnt, COALESCE(AVG(total_score), 0) AS avg_s, "
            "COALESCE(SUM(estimated_impact_aud), 0) AS impact, "
            "SUM(CASE WHEN status='implemented' THEN 1 ELSE 0 END) AS impl "
            "FROM arena_proposals WHERE team_id = ?",
            (team_id,),
        ).fetchone()
        c.execute(
            "INSERT OR REPLACE INTO arena_team_stats "
            "(team_id, period, total_proposals, avg_score, total_impact_aud, "
            "implementations, rank) VALUES (?,?,?,?,?,?,?)",
            (team_id, "all_time", row[0], round(row[1], 1),
             row[2], row[3], 0),
        )

    # Assign ranks
    rows = conn.execute(
        "SELECT team_id, avg_score FROM arena_team_stats "
        "WHERE period='all_time' ORDER BY avg_score DESC"
    ).fetchall()
    for i, r in enumerate(rows):
        c.execute(
            "UPDATE arena_team_stats SET rank = ? "
            "WHERE team_id = ? AND period = 'all_time'",
            (i + 1, r[0]),
        )

    conn.commit()
    conn.close()


def seed_agent_control_data():
    """Seed agent_proposals and agent_scores with sample data. Idempotent."""
    conn = sqlite3.connect(config.HUB_DB)
    count = conn.execute("SELECT COUNT(*) FROM agent_proposals").fetchone()[0]
    if count > 0:
        conn.close()
        return

    c = conn.cursor()
    samples = [
        ("StockoutAnalyzer", "ANALYSIS",
         "Analyse intra-day stockouts across all 34 stores for the last 14 days",
         "LOW", "$45K potential recovery"),
        ("SelfImprovementEngine", "IMPROVEMENT",
         "Review last 30 days performance and propose optimisations to Safe criterion",
         "MEDIUM", "Score improvement S: 8.4 -> 9.0"),
        ("ReportGenerator", "REPORT",
         "Generate weekly executive summary of buying intelligence for C-suite",
         "LOW", "Time saving: 4 hours/week"),
        ("BasketAnalyzer", "ANALYSIS",
         "Cross-sell opportunity detection across top 100 SKUs at Mosman and Leichhardt",
         "LOW", "$12K incremental revenue"),
    ]
    for name, ttype, desc, risk, impact in samples:
        c.execute(
            "INSERT INTO agent_proposals (agent_name, task_type, description, "
            "risk_level, estimated_impact) VALUES (?,?,?,?,?)",
            (name, ttype, desc, risk, impact),
        )

    scores = [
        ("StockoutAnalyzer", "ACCURACY", 8.5, None,
         "Correctly identified 17/20 stockout events"),
        ("StockoutAnalyzer", "SPEED", 9.1, None,
         "Analysis completed in 1.2s average"),
        ("ReportGenerator", "SPEED", 9.2, None,
         "Generated reports in 2.3s average"),
        ("ReportGenerator", "INSIGHT_QUALITY", 7.8, None,
         "Insights scored 7.8/10 by business users"),
        ("BasketAnalyzer", "ACCURACY", 8.0, None,
         "Basket patterns validated against 30-day holdout"),
        ("BasketAnalyzer", "INSIGHT_QUALITY", 8.3, None,
         "Cross-sell recommendations adopted by 3 stores"),
        ("SelfImprovementEngine", "USER_SATISFACTION", 8.7, None,
         "Admin rated improvement suggestions 8.7/10"),
    ]
    for name, metric, score, baseline, evidence in scores:
        c.execute(
            "INSERT INTO agent_scores (agent_name, metric, score, baseline, evidence) "
            "VALUES (?,?,?,?,?)",
            (name, metric, score, baseline, evidence),
        )

    conn.commit()
    conn.close()


def seed_prompt_templates():
    """Seed prompt_templates with 6 Harris Farm examples. Idempotent."""
    conn = sqlite3.connect(config.HUB_DB)
    count = conn.execute("SELECT COUNT(*) FROM prompt_templates").fetchone()[0]
    if count > 0:
        conn.close()
        return

    now = datetime.now().isoformat()
    templates = [
        {
            "title": "Daily Out-of-Stock Alert",
            "description": "Identifies products that went out of stock yesterday, calculates lost sales based on historical data",
            "template": "Show all SKUs that had zero inventory for any period yesterday, estimate lost sales using 30-day average, prioritize by revenue impact",
            "category": "retail_ops",
            "difficulty": "beginner",
        },
        {
            "title": "Weekend Fresh Produce Wastage",
            "description": "Analyzes fresh produce wastage patterns specifically on weekends to optimize Monday ordering",
            "template": "Compare weekend (Sat-Sun) wastage rates vs weekday rates for all fresh produce categories, show year-over-year trend by store",
            "category": "buying",
            "difficulty": "intermediate",
        },
        {
            "title": "Online Miss-Pick Root Cause",
            "description": "Breaks down online miss-picks by root cause to reduce substitution rates and improve customer satisfaction",
            "template": "Analyze miss-picks from last 30 days, categorize by root cause: confusing similar items, actual OOS, picker mistake. Group by store and picker",
            "category": "retail_ops",
            "difficulty": "advanced",
        },
        {
            "title": "Over-Order Prevention",
            "description": "Flags products consistently ordered in quantities 15%+ above sales to reduce waste and free up working capital",
            "template": "Compare order quantity vs actual sales for last 60 days, flag items with consistent 15%+ excess, calculate working capital impact by category",
            "category": "finance",
            "difficulty": "intermediate",
        },
        {
            "title": "Slow Mover Markdown Candidates",
            "description": "Identifies slow-moving products approaching expiry that should be marked down to reduce wastage",
            "template": "Find products with less than 50% normal sales velocity, days to expiry under 7, current stock level above 10 units, suggest markdown percentage",
            "category": "merchandising",
            "difficulty": "intermediate",
        },
        {
            "title": "Store-Specific Ordering Patterns",
            "description": "Compares ordering patterns between high and low performing stores to identify best practices",
            "template": "For each product category, compare order frequency, quantity, and wastage between top 3 and bottom 3 profitability stores",
            "category": "buying",
            "difficulty": "advanced",
        },
    ]

    c = conn.cursor()
    for t in templates:
        c.execute(
            "INSERT INTO prompt_templates "
            "(title, description, template, category, difficulty, uses, avg_rating, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, 0, 0, ?, ?)",
            (t["title"], t["description"], t["template"],
             t["category"], t["difficulty"], now, now),
        )
    conn.commit()
    conn.close()


def seed_knowledge_base():
    """Seed knowledge_base with Harris Farm operational articles. Idempotent."""
    import hashlib
    conn = sqlite3.connect(config.HUB_DB)
    count = conn.execute("SELECT COUNT(*) FROM knowledge_base").fetchone()[0]
    if count > 0:
        conn.close()
        return

    now = datetime.now().isoformat()
    articles = [
        # Fresh Produce
        ("seed/fresh_produce/golden_rules.md", "Golden Rules for Fruit and Veg.md",
         "Fresh Produce", "md",
         "Golden Rules for Fruit and Vegetables: 1. Always rotate stock using First In First Out (FIFO). "
         "2. Check for bruising and damage every morning before store opens. "
         "3. Remove any damaged or overripe product immediately and record wastage. "
         "4. Mist leafy greens every 2 hours during trading. "
         "5. Never stack heavy items on top of delicate produce like berries or stone fruit. "
         "6. Temperature: keep cold chain items below 5 degrees Celsius at all times. "
         "7. Display standards: face up product, fill gaps, maintain colour blocking."),
        ("seed/fresh_produce/stock_rotation.md", "Stock Rotation Procedures.md",
         "Fresh Produce", "md",
         "Stock Rotation Procedures: All fresh produce must follow FIFO rotation. When new deliveries arrive, "
         "pull existing stock forward before placing new stock behind. Date-mark all cartons on arrival with "
         "received date. Check use-by dates daily during morning prep. Any product past its use-by must be "
         "removed and recorded in the wastage log. Seasonal items should be given priority display positions. "
         "Notify the buyer if stock is not rotating within expected timeframes."),
        ("seed/fresh_produce/display_standards.md", "Display Standards.md",
         "Fresh Produce", "md",
         "Display Standards for Fresh Produce: Maintain full, abundant displays at all times during trading hours. "
         "Use colour blocking to create visual impact - group similar colours together. Keep all signage current "
         "with correct prices and origin information. Clean display fixtures daily. Remove any wilted, damaged "
         "or substandard product immediately. Wet displays should be misted regularly. Use props and elevation "
         "to create interest. Monitor and top up displays every 30 minutes during peak trading."),

        # Safety and Compliance
        ("seed/safety/food_safety_temperatures.md", "Food Safety Temperature Rules.md",
         "Safety and Compliance", "md",
         "Food Safety Temperature Rules: Cold food must be stored and displayed below 5 degrees Celsius. "
         "Hot food must be held above 60 degrees Celsius. The temperature danger zone is between 5 and 60 degrees. "
         "Record temperatures twice daily on the temperature log sheet. If a fridge is above 5 degrees, "
         "notify the manager immediately and do not use product until temperature is restored. "
         "Frozen goods must be stored at minus 18 degrees or below. Delivery vehicles must maintain cold chain. "
         "Reject any delivery where cold chain has been broken."),
        ("seed/safety/allergen_handling.md", "Allergen Handling Procedures.md",
         "Safety and Compliance", "md",
         "Allergen Handling: Harris Farm takes allergen management seriously. The 10 major allergens in Australia "
         "are: peanuts, tree nuts, milk, eggs, wheat, soy, fish, shellfish, sesame, and lupin. "
         "All staff handling food must be trained in allergen awareness. Use separate utensils and cutting boards "
         "for allergen-free preparation. Always check product labels when customers ask about ingredients. "
         "If unsure, direct the customer to the product label or contact the supplier. Never guess about allergens."),
        ("seed/safety/cleaning_schedules.md", "Cleaning Schedules.md",
         "Safety and Compliance", "md",
         "Cleaning Schedules: Daily cleaning tasks include: sweep and mop all floors, clean and sanitise "
         "all preparation surfaces, empty and clean all bins, wipe down display fixtures, clean glass doors "
         "and windows. Weekly tasks: deep clean cool rooms, clean behind and under equipment, sanitise drains, "
         "clean staff areas. Monthly tasks: deep clean extraction fans, defrost freezers as needed, "
         "professional pest inspection. All cleaning must be recorded on the cleaning log. "
         "Use only approved food-safe cleaning products in food areas."),

        # Store Operations
        ("seed/store_ops/opening_procedures.md", "Store Opening Procedures.md",
         "Store Operations", "md",
         "Store Opening Procedures: 1. Arrive minimum 30 minutes before trading begins. "
         "2. Disarm security system and complete security walk-through. "
         "3. Turn on all lights, equipment, and POS systems. "
         "4. Check and record all fridge and freezer temperatures. "
         "5. Check overnight deliveries and begin put-away. "
         "6. Prepare fresh departments: bread, deli, produce. "
         "7. Walk the floor to ensure displays are full and tidy. "
         "8. Brief team on daily priorities and promotions. "
         "9. Unlock doors at trading time. "
         "10. First staff member on floor must be ready to greet customers."),
        ("seed/store_ops/closing_procedures.md", "Store Closing Procedures.md",
         "Store Operations", "md",
         "Store Closing Procedures: 1. Announce store closing 15 minutes before. "
         "2. Begin reducing hot food and perishable displays. "
         "3. Process all markdowns for next-day items. "
         "4. Complete all cleaning tasks for the day. "
         "5. Record final temperature checks for all refrigeration. "
         "6. Cash up all registers and reconcile tills. "
         "7. Secure cash in safe. "
         "8. Walk the floor to check for hazards or spills. "
         "9. Set security alarm. "
         "10. Lock all doors and confirm building is secure."),
        ("seed/store_ops/customer_service.md", "Customer Service Standards.md",
         "Store Operations", "md",
         "Customer Service Standards: Harris Farm is known for exceptional customer service. "
         "Greet every customer with a smile and eye contact. Offer assistance proactively. "
         "If a customer asks for a product we do not stock, offer to order it or suggest an alternative. "
         "Handle complaints with empathy and offer a resolution immediately. Authorised team members "
         "can offer refunds or replacements up to 50 dollars without manager approval. "
         "Always thank customers and invite them back. Go above and beyond to create memorable experiences."),

        # Perishables
        ("seed/perishables/bread_baking_schedule.md", "Bread Baking Schedule.md",
         "Perishables", "md",
         "Bread Baking Schedule: First bake should be completed 30 minutes before store opens. "
         "Morning bake: sourdough, baguettes, and rolls. Mid-morning bake: specialty loaves and focaccia. "
         "Afternoon bake: rolls and baguettes for evening trade. Weekend bake: increase all quantities by 30%. "
         "Monitor stock levels hourly and adjust baking as needed. "
         "Day-old bread should be marked down by 50% and moved to the markdown section. "
         "Any bread older than 2 days must be removed and donated or composted."),
        ("seed/perishables/deli_preparation.md", "Deli Preparation Guidelines.md",
         "Perishables", "md",
         "Deli Preparation Guidelines: All deli staff must wear gloves and hair nets. "
         "Slicing machines must be cleaned and sanitised between different product types. "
         "Pre-sliced product should be wrapped and labelled with preparation date and use-by date. "
         "Maximum shelf life for sliced deli meats is 3 days from slicing. "
         "Cheese should be wrapped in appropriate materials to prevent drying out. "
         "Antipasto and salads must be prepared fresh daily. Leftover prepared items from previous "
         "day should be discarded. Maintain display temperature below 5 degrees at all times."),
        ("seed/perishables/meat_department.md", "Meat Department Rules.md",
         "Perishables", "md",
         "Meat Department Rules: All meat must be received below 5 degrees and stored immediately. "
         "Use separate cutting boards and knives for different proteins: red for red meat, blue for seafood, "
         "yellow for poultry. Clean and sanitise equipment between uses. "
         "Display cases must maintain temperature below 4 degrees. Check and record temperatures three times daily. "
         "Mince and sausages have a maximum 2-day shelf life from preparation. "
         "Whole cuts have a maximum 5-day shelf life from delivery. "
         "All trays must be labelled with weight, price per kg, total price, and packed date."),

        # Online Operations
        ("seed/online/order_picking.md", "Online Order Picking Procedures.md",
         "Online Operations", "md",
         "Online Order Picking Procedures: 1. Print pick list at scheduled time. "
         "2. Pick ambient items first, then chilled, then frozen last. "
         "3. Select the best quality product available, as if you were shopping for yourself. "
         "4. If an item is out of stock, check the substitution list for approved alternatives. "
         "5. Contact the customer if no approved substitution exists. "
         "6. Weigh all loose produce and enter exact weight in the system. "
         "7. Pack carefully: heavy items at bottom, fragile on top, cold items together. "
         "8. Label all bags with order number and customer name. "
         "9. Store completed orders in designated area at correct temperature."),
        ("seed/online/substitution_rules.md", "Substitution Rules.md",
         "Online Operations", "md",
         "Substitution Rules for Online Orders: Only substitute with a like-for-like product of equal "
         "or higher quality. Never substitute with a cheaper or lower quality item unless the customer "
         "has specifically approved it. Organic items should only be substituted with organic alternatives. "
         "Brand-specific requests should be honoured where possible. If no suitable substitution is available, "
         "mark the item as unavailable rather than substituting with an inappropriate product. "
         "Record all substitutions in the picking system so the customer is notified before delivery."),
        ("seed/online/delivery_standards.md", "Delivery Standards.md",
         "Online Operations", "md",
         "Delivery Standards: All deliveries must arrive within the scheduled delivery window. "
         "Maintain cold chain throughout delivery using insulated bags and ice packs for chilled items. "
         "Frozen items must be delivered in separate frozen bags. "
         "Present a professional appearance: clean uniform, name badge visible. "
         "Greet the customer by name and confirm the order contents. "
         "Handle any issues at the door with courtesy and record in the delivery notes. "
         "If the customer is not home, follow the safe-drop procedure or return perishables to store."),

        # HR and Training
        ("seed/hr/onboarding_checklist.md", "New Starter Onboarding Checklist.md",
         "HR and Training", "md",
         "New Starter Onboarding Checklist: Day 1: Complete paperwork including tax file declaration and "
         "superannuation choice form. Receive uniform and name badge. Tour of store including emergency exits "
         "and first aid locations. Introduction to team members and department manager. "
         "Complete food safety induction online module. Week 1: Shadow experienced team member in assigned "
         "department. Complete manual handling training. Learn POS system basics. "
         "Week 2: Begin working independently with supervision available. Complete allergen awareness module."),
        ("seed/hr/dayforce_leave.md", "Dayforce Leave Requests.md",
         "HR and Training", "md",
         "How to Process a Dayforce Leave Request: 1. Log into Dayforce at dayforce.com using your employee ID. "
         "2. Navigate to My Time Off from the main menu. 3. Click Request Time Off. "
         "4. Select the leave type: Annual Leave, Personal Leave, or Long Service Leave. "
         "5. Enter the start and end dates. 6. Add any notes for your manager. "
         "7. Click Submit. Your manager will be notified and must approve within 48 hours. "
         "8. You will receive an email notification when your leave is approved or declined. "
         "For urgent leave requests, also notify your manager directly by phone."),

        # Buying
        ("seed/buying/ordering_guidelines.md", "Ordering Guidelines.md",
         "Buying", "md",
         "Ordering Guidelines: Review sales data from the previous week before placing orders. "
         "Consider upcoming promotions, public holidays, and seasonal events that may affect demand. "
         "Order in full carton quantities where possible to reduce handling costs. "
         "Place orders by the supplier deadline to ensure next-day delivery. "
         "Review order suggestions generated by the system but adjust based on local knowledge. "
         "For new products, start with a conservative trial quantity and increase based on sales performance. "
         "Communicate with store managers about any supply issues or expected shortages."),
        ("seed/buying/seasonal_buying.md", "Seasonal Buying Tips.md",
         "Buying", "md",
         "Seasonal Buying Tips: Summer: increase stone fruit, berries, melons, and salad items by 20-30%. "
         "Stock more beverages and ice cream. Winter: increase citrus, root vegetables, and soup ingredients. "
         "Stock more comfort foods and warming items. Easter: increase chocolate, hot cross buns, and lamb. "
         "Christmas: plan ordering 6 weeks ahead for ham, turkey, seafood, and premium lines. "
         "Increase gift hamper stock from November. Mothers Day and Fathers Day: increase flowers and gift items. "
         "Always review previous year sales data when planning for seasonal events."),
    ]

    c = conn.cursor()
    for source_path, filename, category, doc_type, content in articles:
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        word_count = len(content.split())
        c.execute(
            "INSERT OR IGNORE INTO knowledge_base "
            "(source_path, filename, category, doc_type, content, "
            "content_hash, word_count, chunk_index, chunk_total, extracted_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, 0, 1, ?)",
            (source_path, filename, category, doc_type, content,
             content_hash, word_count, now),
        )
    conn.commit()
    conn.close()


def seed_sustainability_kpis():
    """Seed FY26 sustainability targets. Idempotent."""
    conn = sqlite3.connect(config.HUB_DB)
    count = conn.execute("SELECT COUNT(*) FROM sustainability_kpis").fetchone()[0]
    if count > 0:
        conn.close()
        return
    now = datetime.now().isoformat()
    kpis = [
        ("100% Renewable Energy", "Energy", 100, 100, "%", "completed",
         "All stores and DC switched to 100% renewable electricity"),
        ("B Corp Certification", "Governance", 100, 75, "%", "in_progress",
         "Board approval Feb/Mar 2026. Compass Studio engaged for purpose activation"),
        ("50% Landfill Diversion", "Waste", 100, 45, "%", "in_progress",
         "Food rescue partnerships, composting, recycling programs across all stores"),
        ("20% Wastage Reduction", "Waste", 100, 35, "%", "in_progress",
         "Too Good To Go partnership, AI waste prediction, markdown optimisation"),
        ("ARL on All HFM Packaging", "Packaging", 100, 25, "%", "in_progress",
         "Australasian Recycling Label rollout across all Harris Farm branded packaging"),
        ("Scope 3 Decarbonisation Plan", "Climate", 100, 40, "%", "in_progress",
         "Mapping supply chain emissions, supplier engagement program underway"),
        ("Sustainability Hub (Public)", "Transparency", 100, 60, "%", "in_progress",
         "Public-facing sustainability reporting hub in development"),
        ("Modern Slavery Statement", "Governance", 100, 100, "%", "completed",
         "Published and compliant with Modern Slavery Act 2018"),
        ("WGEA Gender Equity Targets", "People", 100, 55, "%", "in_progress",
         "Inclusive hiring practices, pay equity review, leadership pipeline targets"),
        ("10% Reduction in Incidents", "Safety", 100, 30, "%", "in_progress",
         "Team and customer safety incident reduction program"),
    ]
    c = conn.cursor()
    for name, cat, target, current, unit, status, notes in kpis:
        c.execute(
            """INSERT INTO sustainability_kpis
               (kpi_name, category, target_value, current_value, unit, status, last_updated, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (name, cat, target, current, unit, status, now, notes),
        )
    conn.commit()
    conn.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_hub_database()
    # Auto-ingest audit scores into task_scores (idempotent)
    try:
        from self_improvement import backfill_scores_from_audit
        _backfilled = backfill_scores_from_audit()
        if _backfilled:
            print(f"  Backfilled {_backfilled} score entries from audit.log")
    except Exception:
        pass  # Non-critical — scores still readable from audit.log
    seed_learning_data()
    seed_arena_data()
    seed_agent_control_data()
    seed_prompt_templates()
    seed_knowledge_base()
    seed_sustainability_kpis()
    # Seed Academy daily challenges
    try:
        from academy_engine import seed_daily_challenges
        _seeded = seed_daily_challenges(config.HUB_DB)
        if _seeded:
            print(f"  Seeded {_seeded} Academy daily challenges")
    except Exception as e:
        print(f"  Academy challenge seeding skipped: {e}")
    # Initialize auth database
    import auth as auth_module
    auth_module.init_auth_db()
    auth_module.cleanup_expired_sessions()
    print(f"✅ Auth database initialized (enabled={auth_module.is_auth_enabled()})")
    # Initialize transaction store (DuckDB → parquet)
    from transaction_layer import TransactionStore
    app.state.txn_store = TransactionStore()
    avail = list(app.state.txn_store.available_fys.keys())
    print(f"✅ Hub database initialized")
    print(f"✅ Transaction store: {len(avail)} fiscal years ({', '.join(avail)})")
    # Start scheduled analysis cycle
    import threading
    schedule_hours = int(os.getenv("ANALYSIS_SCHEDULE_HOURS", "168"))
    if schedule_hours > 0:
        def _scheduled_trigger():
            try:
                conn = sqlite3.connect(config.HUB_DB)
                sched_tasks = [
                    ("StockoutAnalyzer", "ANALYSIS", "Auto-scheduled: Stockout scan", "LOW", "Lost revenue"),
                    ("BasketAnalyzer", "ANALYSIS", "Auto-scheduled: Cross-sell scan", "LOW", "Revenue growth"),
                    ("DemandAnalyzer", "ANALYSIS", "Auto-scheduled: Demand pattern scan", "LOW", "Optimisation"),
                    ("PriceAnalyzer", "ANALYSIS", "Auto-scheduled: Price dispersion scan", "LOW", "Margin recovery"),
                    ("SlowMoverAnalyzer", "ANALYSIS", "Auto-scheduled: Slow mover review", "LOW", "Range optimisation"),
                    ("HaloAnalyzer", "ANALYSIS", "Auto-scheduled: Halo effect scan", "LOW", "Basket growth"),
                    ("SpecialsAnalyzer", "ANALYSIS", "Auto-scheduled: Specials uplift forecast", "LOW", "Ordering"),
                    ("MarginAnalyzer", "ANALYSIS", "Auto-scheduled: Margin erosion scan", "LOW", "Margin recovery"),
                    ("CustomerAnalyzer", "ANALYSIS", "Auto-scheduled: Customer segmentation", "LOW", "Retention"),
                    ("StoreBenchmarkAnalyzer", "ANALYSIS", "Auto-scheduled: Store benchmark", "LOW", "Benchmarking"),
                ]
                for agent, ttype, desc, risk, impact in sched_tasks:
                    conn.execute(
                        "INSERT INTO agent_proposals (agent_name, task_type, description, "
                        "risk_level, estimated_impact) VALUES (?,?,?,?,?)",
                        (agent, ttype, desc, risk, impact),
                    )
                conn.commit()
                conn.close()
                print("Scheduled analysis cycle: {} proposals created".format(len(sched_tasks)))
            except Exception as e:
                print("Scheduled trigger failed: {}".format(e))
            t = threading.Timer(schedule_hours * 3600, _scheduled_trigger)
            t.daemon = True
            t.start()

        _timer = threading.Timer(300, _scheduled_trigger)
        _timer.daemon = True
        _timer.start()
        print("Scheduled analysis: every {} hours (first run in 5 min)".format(schedule_hours))
    # Start WATCHDOG background scheduler
    from watchdog_scheduler import WatchdogScheduler
    watchdog_hours = int(os.getenv("WATCHDOG_INTERVAL_HOURS", "6"))
    if watchdog_hours > 0:
        app.state.watchdog = WatchdogScheduler(
            interval_hours=watchdog_hours, db_path=config.HUB_DB
        )
        app.state.watchdog.start(delay=120)
        print("🐕 WATCHDOG scheduler: every {}h (first run in 2 min)".format(watchdog_hours))
    yield
    # Shutdown
    if hasattr(app.state, "watchdog"):
        app.state.watchdog.stop()
    print("👋 Hub shutting down")

# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="Harris Farm Hub API",
    description="AI Centre of Excellence - Backend",
    version="1.0.0",
    lifespan=lifespan
)

_cors_origins = [
    "http://localhost:8000",
    "http://localhost:8500",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:8500",
]
# Allow Render domain (set RENDER_EXTERNAL_URL automatically by Render)
_render_url = os.getenv("RENDER_EXTERNAL_URL")
if _render_url:
    _cors_origins.append(_render_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "X-Auth-Token"],
)

# ============================================================================
# DATA MODELS
# ============================================================================

class NaturalLanguageQuery(BaseModel):
    question: str = Field(..., description="Natural language question about the data")
    dataset: str = Field(
        default="sales",
        description="Page context / dataset: sales, profitability, customers, "
                    "market_share, trending, store_ops, product_intel, "
                    "revenue_bridge, buying_hub, general"
    )
    user_id: str = Field(default="finance_team")

class RubricRequest(BaseModel):
    prompt: str = Field(..., description="Question to evaluate across multiple LLMs")
    context: Optional[str] = Field(None, description="Additional context")
    providers: List[Literal["claude", "chatgpt", "grok"]] = Field(
        default=["claude", "chatgpt"],
        description="Which LLMs to query"
    )
    user_id: str = Field(default="chairman")
    use_knowledge_base: bool = Field(default=True, description="Auto-inject relevant knowledge base context")

class ChairmanDecision(BaseModel):
    query_id: int
    winner: str
    feedback: Optional[str] = None
    user_id: str = Field(default="chairman")

class UserFeedback(BaseModel):
    query_id: int
    rating: int = Field(..., ge=1, le=5, description="1-5 star rating")
    comment: Optional[str] = None
    user_id: str

class PromptTemplate(BaseModel):
    title: str
    description: str
    template: str
    category: Literal["retail_ops", "buying", "merchandising", "finance", "general"]
    difficulty: Literal["beginner", "intermediate", "advanced"]

class ChatMessage(BaseModel):
    role: Literal["user", "assistant"] = Field(..., description="Message role")
    content: str = Field(..., description="Message content")

class ChatRequest(BaseModel):
    message: str = Field(..., description="User's question")
    history: List[ChatMessage] = Field(default=[], description="Previous conversation messages")
    category: Optional[str] = Field(None, description="Filter KB search to a specific category")
    provider: Literal["claude", "chatgpt", "grok"] = Field(default="claude", description="LLM provider")
    user_id: str = Field(default="staff")

# ============================================================================
# THE RUBRIC - MULTI-LLM EVALUATION SYSTEM
# ============================================================================

class RubricEvaluator:
    """Multi-LLM evaluation system"""
    
    def __init__(self):
        self.claude_client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY) if config.ANTHROPIC_API_KEY else None
        self.openai_client = openai.OpenAI(api_key=config.OPENAI_API_KEY) if config.OPENAI_API_KEY else None
    
    async def query_claude(self, prompt: str, context: str = "") -> Dict[str, Any]:
        if not self.claude_client:
            return {"provider": "Claude", "response": "API key not configured. Check .env in project root.", "status": "error", "tokens": 0, "latency_ms": 0, "timestamp": datetime.now().isoformat()}
        
        start = datetime.now()
        try:
            full_prompt = f"{context}\n\n{prompt}" if context else prompt
            message = self.claude_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                messages=[{"role": "user", "content": full_prompt}]
            )
            
            latency = (datetime.now() - start).total_seconds() * 1000
            
            return {
                "provider": "Claude Sonnet 4.5",
                "response": message.content[0].text,
                "tokens": message.usage.input_tokens + message.usage.output_tokens,
                "latency_ms": round(latency, 2),
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            return {
                "provider": "Claude Sonnet 4.5",
                "response": "Unable to generate response. Please try again.",
                "tokens": 0,
                "latency_ms": round((datetime.now() - start).total_seconds() * 1000, 2),
                "status": "error",
                "timestamp": datetime.now().isoformat()
            }
    
    async def query_chatgpt(self, prompt: str, context: str = "") -> Dict[str, Any]:
        if not self.openai_client:
            return {"provider": "ChatGPT", "response": "API key not configured. Check .env in project root.", "status": "error", "tokens": 0, "latency_ms": 0, "timestamp": datetime.now().isoformat()}
        
        start = datetime.now()
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": context or "You are a helpful AI assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=4000
            )
            
            latency = (datetime.now() - start).total_seconds() * 1000
            
            return {
                "provider": "ChatGPT-4 Turbo",
                "response": response.choices[0].message.content,
                "tokens": response.usage.total_tokens,
                "latency_ms": round(latency, 2),
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            }
        except Exception as e:
            logger.error(f"ChatGPT API error: {e}")
            return {
                "provider": "ChatGPT-4 Turbo",
                "response": "Unable to generate response. Please try again.",
                "tokens": 0,
                "latency_ms": round((datetime.now() - start).total_seconds() * 1000, 2),
                "status": "error",
                "timestamp": datetime.now().isoformat()
            }
    
    async def query_grok(self, prompt: str, context: str = "") -> Dict[str, Any]:
        if not config.GROK_API_KEY:
            return {"provider": "Grok", "response": "API key not configured. Check .env in project root.", "status": "error", "tokens": 0, "latency_ms": 0, "timestamp": datetime.now().isoformat()}
        
        start = datetime.now()
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.x.ai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {config.GROK_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "grok-beta",
                        "messages": [
                            {"role": "system", "content": context or "You are Grok."},
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": 4000
                    },
                    timeout=60.0
                )
                
                result = response.json()
                latency = (datetime.now() - start).total_seconds() * 1000
                
                return {
                    "provider": "Grok (xAI)",
                    "response": result["choices"][0]["message"]["content"],
                    "tokens": result.get("usage", {}).get("total_tokens", 0),
                    "latency_ms": round(latency, 2),
                    "timestamp": datetime.now().isoformat(),
                    "status": "success"
                }
        except Exception as e:
            logger.error(f"Grok API error: {e}")
            return {
                "provider": "Grok (xAI)",
                "response": "Unable to generate response. Please try again.",
                "tokens": 0,
                "latency_ms": round((datetime.now() - start).total_seconds() * 1000, 2),
                "status": "error",
                "timestamp": datetime.now().isoformat()
            }
    
    async def run_evaluation(self, prompt: str, context: str, providers: List[str]) -> Dict[str, Any]:
        """Run the rubric across selected LLMs"""
        tasks = []
        
        if "claude" in providers:
            tasks.append(self.query_claude(prompt, context))
        if "chatgpt" in providers:
            tasks.append(self.query_chatgpt(prompt, context))
        if "grok" in providers:
            tasks.append(self.query_grok(prompt, context))
        
        responses = await asyncio.gather(*tasks)
        
        return {
            "prompt": prompt,
            "context": context,
            "timestamp": datetime.now().isoformat(),
            "responses": responses,
            "awaiting_chairman_decision": True
        }

rubric = RubricEvaluator()

# ============================================================================
# NATURAL LANGUAGE → SQL QUERY SYSTEM
# ============================================================================

class QueryGenerator:
    """Convert natural language to SQL using Claude, then execute against
    the real Harris Farm databases (SQLite for aggregated data, DuckDB for
    transaction-level parquet data)."""

    # Pages that query DuckDB transaction parquets
    DUCKDB_PAGES = {"store_ops", "product_intel", "revenue_bridge", "buying_hub"}

    # Blocked SQL keywords (read-only enforcement)
    BLOCKED_KW = {
        "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE",
        "TRUNCATE", "GRANT", "REVOKE", "EXEC", "EXECUTE",
        "ATTACH", "DETACH", "COPY", "IMPORT", "LOAD", "PRAGMA",
    }

    def __init__(self):
        self.claude_client = (
            anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
            if config.ANTHROPIC_API_KEY else None
        )
        # Path to the main business database
        self._harris_db = os.path.join(
            os.path.dirname(__file__), "..", "data", "harris_farm.db"
        )
        # Lazy-loaded transaction store (DuckDB)
        self._txn_store = None

    def _get_txn_store(self):
        """Lazy-load the TransactionStore for DuckDB queries."""
        if self._txn_store is None:
            try:
                from transaction_layer import TransactionStore
                self._txn_store = TransactionStore()
            except Exception as exc:
                logger.warning("TransactionStore unavailable: %s", exc)
        return self._txn_store

    # ---- schema context (imported from shared module) ----

    def _import_schema_context(self):
        """Import the shared schema_context module."""
        import sys
        _dash_shared = os.path.join(os.path.dirname(__file__), "..", "dashboards", "shared")
        if _dash_shared not in sys.path:
            sys.path.insert(0, _dash_shared)
        import schema_context
        return schema_context

    def get_schema_prompt(self, page_context: str, question: str = None) -> tuple:
        """Return the full schema prompt for a page context.

        Returns (prompt: str, effective_db: str) where effective_db is
        'sqlite' or 'duckdb' — may differ from the page default if a
        product-level query was auto-routed to DuckDB.
        """
        sc = self._import_schema_context()
        return sc.get_schema_for_page(page_context, question=question)

    # ---- SQL generation ----

    async def generate_sql(self, question: str, page_context: str) -> Dict[str, Any]:
        """Generate SQL from a natural language question using Claude.

        Auto-routes product-level queries to DuckDB even if the page
        normally uses SQLite.
        """
        if not self.claude_client:
            return {"error": "Claude API key not configured. Set ANTHROPIC_API_KEY in .env"}

        schema_prompt, effective_db = self.get_schema_prompt(page_context, question=question)

        prompt = (
            f"{schema_prompt}\n\n"
            f"Convert this question to a single SQL query:\n"
            f"\"{question}\"\n\n"
            f"Return ONLY the SQL. No explanation, no markdown, no backticks."
        )

        try:
            message = self.claude_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}],
            )
            sql = message.content[0].text.strip()

            # Strip markdown fences if present
            if sql.startswith("```"):
                sql = re.sub(r"^```(?:sql)?\s*", "", sql)
                sql = re.sub(r"\s*```$", "", sql)

            return {
                "sql": sql,
                "page_context": page_context,
                "effective_db": effective_db,
                "generated_at": datetime.now().isoformat(),
            }
        except Exception as e:
            return {"error": str(e)}

    # ---- SQL validation ----

    def validate_sql(self, sql: str) -> tuple:
        """Ensure SQL is read-only. Returns (ok, message)."""
        sql_upper = sql.upper()
        for kw in self.BLOCKED_KW:
            if f" {kw} " in f" {sql_upper} " or sql_upper.lstrip().startswith(f"{kw} "):
                return False, f"Only SELECT queries are allowed (found {kw})."
        if not sql_upper.lstrip().startswith("SELECT"):
            return False, "Query must start with SELECT."
        return True, "OK"

    # ---- SQL execution ----

    def execute_sql(self, sql: str, page_context: str,
                    effective_db: str = None) -> List[Dict]:
        """Execute validated SQL against the appropriate database.

        Args:
            sql: The SQL to execute.
            page_context: The dashboard page context.
            effective_db: If provided ('sqlite' or 'duckdb'), overrides
                the default database routing for this page. Used for
                auto-routed product queries.
        """
        if effective_db == "duckdb" or (
            effective_db is None and page_context in self.DUCKDB_PAGES
        ):
            return self._execute_duckdb(sql)
        return self._execute_sqlite(sql)

    def _execute_sqlite(self, sql: str) -> List[Dict]:
        """Execute read-only SQL against harris_farm.db."""
        conn = sqlite3.connect(self._harris_db)
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.execute(sql)
            cols = [d[0] for d in cursor.description] if cursor.description else []
            rows = cursor.fetchmany(1000)
            return [dict(zip(cols, row)) for row in rows]
        finally:
            conn.close()

    def _execute_duckdb(self, sql: str) -> List[Dict]:
        """Execute read-only SQL via the TransactionStore (DuckDB)."""
        store = self._get_txn_store()
        if store is None:
            raise RuntimeError(
                "Transaction data is not available. "
                "Ensure parquet files are in data/transactions/ or the Desktop path."
            )
        return store.query(sql, max_rows=1000)

    # ---- explanation ----

    async def explain_results(self, question: str, results: List[Dict],
                              sql: str) -> str:
        """Generate a natural-language explanation of query results."""
        if not self.claude_client:
            return f"Query returned {len(results)} rows."

        # Truncate results for the prompt
        sample = json.dumps(results[:20], indent=2, default=str)

        prompt = (
            "You are a retail analytics expert at Harris Farm Markets "
            "(Australian premium grocer, 30+ stores).\n\n"
            f"The user asked: \"{question}\"\n\n"
            f"SQL executed:\n{sql}\n\n"
            f"Results ({len(results)} rows, first 20 shown):\n{sample}\n\n"
            "Provide a clear, concise answer to their question.\n"
            "- Lead with the key insight / direct answer\n"
            "- Include specific numbers\n"
            "- Add one actionable recommendation if relevant\n"
            "- Use Australian English\n"
            "- Keep it to 2-3 short paragraphs max\n"
            "- If the results look wrong or empty, say so honestly"
        )

        try:
            message = self.claude_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=600,
                messages=[{"role": "user", "content": prompt}],
            )
            return message.content[0].text.strip()
        except Exception as e:
            return f"Query returned {len(results)} rows."

query_generator = QueryGenerator()

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    return {
        "service": "Harris Farm Hub API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "natural_language_query": "/api/query",
            "rubric_evaluation": "/api/rubric",
            "chairman_decision": "/api/decision",
            "user_feedback": "/api/feedback",
            "prompt_templates": "/api/templates",
            "analytics": "/api/analytics",
            "chatbot": "/api/chat",
            "knowledge_search": "/api/knowledge/search",
            "knowledge_stats": "/api/knowledge/stats"
        }
    }

@app.post("/api/query")
async def natural_language_query(request: NaturalLanguageQuery):
    """
    Convert natural language question to SQL, execute against the real
    database, and return results with a natural-language explanation.
    """

    # Store query in hub_data.db for audit trail
    conn = sqlite3.connect(config.HUB_DB)
    c = conn.cursor()
    c.execute(
        "INSERT INTO queries (question, query_type, user_id, timestamp) VALUES (?, ?, ?, ?)",
        (request.question, "nl_query", request.user_id, datetime.now().isoformat())
    )
    query_id = c.lastrowid
    conn.commit()

    # 1. Generate SQL via Claude
    sql_result = await query_generator.generate_sql(request.question, request.dataset)

    if "error" in sql_result:
        conn.close()
        raise HTTPException(status_code=500, detail=sql_result["error"])

    sql = sql_result["sql"]
    effective_db = sql_result.get("effective_db")

    # 2. Validate SQL (read-only check)
    is_valid, validation_msg = query_generator.validate_sql(sql)
    if not is_valid:
        conn.close()
        raise HTTPException(status_code=400, detail=validation_msg)

    # 3. Execute against real database (effective_db may override page default)
    execution_success = True
    error_detail = None
    results = []

    try:
        results = query_generator.execute_sql(sql, request.dataset,
                                               effective_db=effective_db)
    except Exception as exc:
        execution_success = False
        error_detail = str(exc)
        logger.warning("NL query execution failed: %s\nSQL: %s", exc, sql)

    # 4. Log generated query
    c.execute(
        """INSERT INTO generated_queries
           (query_id, natural_language, generated_sql, execution_success, result_count, timestamp)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (query_id, request.question, sql, execution_success,
         len(results), datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

    # 5. If execution failed, return the error with the SQL for debugging
    if not execution_success:
        return {
            "query_id": query_id,
            "question": request.question,
            "generated_sql": sql,
            "results": [],
            "result_count": 0,
            "explanation": f"The query could not be executed: {error_detail}",
            "dataset": request.dataset,
            "effective_db": effective_db,
        }

    # 6. Generate natural-language explanation
    explanation = await query_generator.explain_results(
        request.question, results, sql
    )

    return {
        "query_id": query_id,
        "question": request.question,
        "generated_sql": sql,
        "results": results,
        "result_count": len(results),
        "explanation": explanation,
        "dataset": request.dataset,
        "effective_db": effective_db,
    }

@app.post("/api/rubric")
async def run_rubric(request: RubricRequest):
    """
    THE RUBRIC: Query multiple LLMs and present for chairman's decision
    """
    
    # Store query
    conn = sqlite3.connect(config.HUB_DB)
    c = conn.cursor()
    c.execute(
        "INSERT INTO queries (question, query_type, user_id, timestamp, context) VALUES (?, ?, ?, ?, ?)",
        (request.prompt, "rubric", request.user_id, datetime.now().isoformat(), request.context)
    )
    query_id = c.lastrowid
    conn.commit()
    
    # Auto-inject knowledge base context if enabled
    context = request.context or ""
    kb_docs_used = []
    if request.use_knowledge_base:
        kb_context = get_knowledge_context(request.prompt, limit=3)
        if kb_context:
            context = f"{kb_context}\n\n{context}" if context else kb_context
            kb_docs_used = search_knowledge_base(request.prompt, limit=3)

    # Run evaluation
    result = await rubric.run_evaluation(request.prompt, context, request.providers)
    result["knowledge_base_docs"] = [{"filename": d["filename"], "category": d["category"]} for d in kb_docs_used]
    
    # Store all responses
    for response in result["responses"]:
        c.execute(
            """INSERT INTO llm_responses 
               (query_id, provider, response, tokens, latency_ms, timestamp)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                query_id,
                response.get("provider", "unknown"),
                response.get("response", ""),
                response.get("tokens", 0),
                response.get("latency_ms", 0),
                response.get("timestamp", datetime.now().isoformat())
            )
        )
    
    conn.commit()
    conn.close()
    
    return {
        "query_id": query_id,
        **result
    }

@app.post("/api/decision")
async def chairman_decision(decision: ChairmanDecision):
    """Record the chairman's decision on which LLM won"""
    
    conn = sqlite3.connect(config.HUB_DB)
    c = conn.cursor()
    
    c.execute(
        """INSERT INTO evaluations (query_id, winner, feedback, user_id, timestamp)
           VALUES (?, ?, ?, ?, ?)""",
        (decision.query_id, decision.winner, decision.feedback, decision.user_id, datetime.now().isoformat())
    )
    
    conn.commit()
    conn.close()
    
    _award_points(decision.user_id, 15, "evaluation", f"Evaluated LLMs on query #{decision.query_id}")

    return {"status": "recorded", "query_id": decision.query_id, "winner": decision.winner}

@app.post("/api/feedback")
async def submit_feedback(feedback: UserFeedback):
    """Submit user feedback for self-improvement system"""
    
    conn = sqlite3.connect(config.HUB_DB)
    c = conn.cursor()
    
    c.execute(
        """INSERT INTO feedback (query_id, rating, comment, user_id, timestamp)
           VALUES (?, ?, ?, ?, ?)""",
        (feedback.query_id, feedback.rating, feedback.comment, feedback.user_id, datetime.now().isoformat())
    )
    
    conn.commit()
    conn.close()
    
    _award_points(feedback.user_id, 10, "feedback", f"Gave feedback on query #{feedback.query_id}")

    return {"status": "recorded", "query_id": feedback.query_id, "rating": feedback.rating}

@app.get("/api/templates")
async def get_templates(category: Optional[str] = None, difficulty: Optional[str] = None):
    """Get prompt templates library"""
    
    conn = sqlite3.connect(config.HUB_DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    query = "SELECT * FROM prompt_templates WHERE 1=1"
    params = []
    
    if category:
        query += " AND category = ?"
        params.append(category)
    
    if difficulty:
        query += " AND difficulty = ?"
        params.append(difficulty)
    
    query += " ORDER BY uses DESC, avg_rating DESC"
    
    c.execute(query, params)
    templates = [dict(row) for row in c.fetchall()]
    
    conn.close()
    
    return {"templates": templates, "count": len(templates)}

@app.post("/api/templates")
async def create_template(template: PromptTemplate):
    """Add new prompt template to library"""
    
    conn = sqlite3.connect(config.HUB_DB)
    c = conn.cursor()
    
    now = datetime.now().isoformat()
    
    c.execute(
        """INSERT INTO prompt_templates 
           (title, description, template, category, difficulty, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (template.title, template.description, template.template, 
         template.category, template.difficulty, now, now)
    )
    
    template_id = c.lastrowid
    conn.commit()
    conn.close()

    _award_points("template_author", 15, "template", f"Created template: {template.title}")

    return {"status": "created", "template_id": template_id}


@app.post("/api/templates/{template_id}/use")
async def track_template_use(template_id: int):
    """Increment template usage counter."""
    conn = sqlite3.connect(config.HUB_DB)
    conn.execute(
        "UPDATE prompt_templates SET uses = uses + 1, updated_at = ? WHERE id = ?",
        (datetime.now().isoformat(), template_id),
    )
    conn.commit()
    conn.close()
    return {"status": "tracked"}


@app.get("/api/analytics/performance")
async def get_performance_analytics():
    """Self-improvement analytics: what's working, what's not"""
    
    conn = sqlite3.connect(config.HUB_DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Top rated queries
    c.execute("""
        SELECT q.question, AVG(f.rating) as avg_rating, COUNT(f.id) as feedback_count
        FROM queries q
        JOIN feedback f ON q.id = f.query_id
        GROUP BY q.id
        HAVING feedback_count >= 2
        ORDER BY avg_rating DESC
        LIMIT 10
    """)
    top_queries = [dict(row) for row in c.fetchall()]
    
    # LLM win rates (from chairman decisions)
    c.execute("""
        SELECT winner, COUNT(*) as wins
        FROM evaluations
        GROUP BY winner
        ORDER BY wins DESC
    """)
    llm_wins = [dict(row) for row in c.fetchall()]
    
    # Most used templates
    c.execute("""
        SELECT title, category, uses, avg_rating
        FROM prompt_templates
        WHERE uses > 0
        ORDER BY uses DESC
        LIMIT 10
    """)
    popular_templates = [dict(row) for row in c.fetchall()]
    
    conn.close()
    
    return {
        "top_queries": top_queries,
        "llm_performance": llm_wins,
        "popular_templates": popular_templates,
        "generated_at": datetime.now().isoformat()
    }

@app.get("/api/analytics/weekly-report")
async def weekly_report():
    """Weekly self-improvement report"""
    
    week_ago = (datetime.now() - timedelta(days=7)).isoformat()
    
    conn = sqlite3.connect(config.HUB_DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Queries this week
    c.execute("SELECT COUNT(*) as count FROM queries WHERE timestamp > ?", (week_ago,))
    total_queries = c.fetchone()["count"]
    
    # Average rating
    c.execute("SELECT AVG(rating) as avg FROM feedback WHERE timestamp > ?", (week_ago,))
    avg_rating = c.fetchone()["avg"] or 0
    
    # Success rate
    c.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN execution_success = 1 THEN 1 ELSE 0 END) as successful
        FROM generated_queries WHERE timestamp > ?
    """, (week_ago,))
    success_data = dict(c.fetchone())
    success_rate = (success_data["successful"] / success_data["total"] * 100) if success_data["total"] > 0 else 0
    
    conn.close()
    
    return {
        "week_ending": datetime.now().strftime("%Y-%m-%d"),
        "total_queries": total_queries,
        "average_rating": round(avg_rating, 2),
        "sql_success_rate": round(success_rate, 1),
        "insights": [
            f"Users ran {total_queries} queries this week",
            f"Average satisfaction: {avg_rating:.1f}/5.0 stars",
            f"SQL generation success rate: {success_rate:.1f}%"
        ]
    }

# ============================================================================
# KNOWLEDGE BASE
# ============================================================================

STOP_WORDS = frozenset({
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "shall",
    "should", "may", "might", "can", "could", "must", "need",
    "i", "me", "my", "we", "our", "you", "your", "he", "she", "it",
    "they", "them", "this", "that", "what", "which", "who", "how",
    "not", "no", "nor", "and", "or", "but", "if", "then", "so",
    "for", "of", "at", "by", "from", "in", "on", "to", "with", "about",
})


def _extract_keywords(query):
    """Extract meaningful keywords from a query, stripping stop words and punctuation."""
    keywords = []
    for w in query.split():
        clean = re.sub(r'[^\w]', '', w.strip().lower())
        if clean and len(clean) > 1 and clean not in STOP_WORDS:
            keywords.append(clean)
    return keywords[:10]


def _search_knowledge_base_like(query, category, limit, conn):
    """Fallback LIKE-based search when FTS5 is not available."""
    keywords = _extract_keywords(query)
    if not keywords:
        return []

    conditions = []
    params = []
    for kw in keywords:
        conditions.append("LOWER(content) LIKE ?")
        params.append(f"%{kw}%")

    where = " OR ".join(conditions)

    relevance_parts = []
    for kw in keywords:
        relevance_parts.append("(CASE WHEN LOWER(content) LIKE ? THEN 1 ELSE 0 END)")
        relevance_parts.append("(CASE WHEN LOWER(filename) LIKE ? THEN 2 ELSE 0 END)")
        params.extend([f"%{kw}%", f"%{kw}%"])

    relevance_expr = " + ".join(relevance_parts)

    sql = f"""
        SELECT id, filename, category, doc_type, word_count, chunk_index, chunk_total,
               SUBSTR(content, 1, 500) as snippet,
               ({relevance_expr}) as relevance
        FROM knowledge_base
        WHERE ({where})
    """

    if category:
        sql += " AND category = ?"
        params.append(category)

    sql += " ORDER BY relevance DESC, word_count DESC LIMIT ?"
    params.append(limit)

    return [dict(r) for r in conn.execute(sql, params).fetchall()]


def search_knowledge_base(query, category=None, limit=5):
    """Search knowledge_base using FTS5 with BM25 ranking.

    Falls back to LIKE-based search if the FTS5 table doesn't exist.
    """
    conn = sqlite3.connect(config.HUB_DB)
    conn.row_factory = sqlite3.Row

    keywords = _extract_keywords(query)
    if not keywords:
        conn.close()
        return []

    fts_query = " OR ".join(keywords)

    try:
        sql = """
            SELECT kb.id, kb.filename, kb.category, kb.doc_type,
                   kb.word_count, kb.chunk_index, kb.chunk_total,
                   SUBSTR(kb.content, 1, 500) as snippet,
                   fts.rank as relevance
            FROM knowledge_fts fts
            JOIN knowledge_base kb ON kb.id = fts.rowid
            WHERE knowledge_fts MATCH ?
        """
        params = [fts_query]

        if category:
            sql += " AND kb.category = ?"
            params.append(category)

        sql += " ORDER BY fts.rank LIMIT ?"
        params.append(limit)

        results = [dict(r) for r in conn.execute(sql, params).fetchall()]
    except Exception:
        results = _search_knowledge_base_like(query, category, limit, conn)

    conn.close()
    return results


def get_knowledge_context(query, limit=3):
    """Retrieve top knowledge base docs via FTS5, formatted as context for LLMs."""
    conn = sqlite3.connect(config.HUB_DB)
    conn.row_factory = sqlite3.Row

    count = conn.execute("SELECT COUNT(*) FROM knowledge_base").fetchone()[0]
    if count == 0:
        conn.close()
        return ""

    keywords = _extract_keywords(query)
    if not keywords:
        conn.close()
        return ""

    fts_query = " OR ".join(keywords)

    try:
        rows = conn.execute("""
            SELECT kb.filename, kb.category, kb.content
            FROM knowledge_fts fts
            JOIN knowledge_base kb ON kb.id = fts.rowid
            WHERE knowledge_fts MATCH ?
            ORDER BY fts.rank
            LIMIT ?
        """, [fts_query, limit]).fetchall()
    except Exception:
        # Fallback to LIKE
        like_results = _search_knowledge_base_like(query, None, limit, conn)
        rows = []
        if like_results:
            ids = [r["id"] for r in like_results]
            placeholders = ",".join("?" * len(ids))
            rows = conn.execute(
                f"SELECT filename, category, content FROM knowledge_base WHERE id IN ({placeholders})",
                ids,
            ).fetchall()

    conn.close()

    if not rows:
        return ""

    parts = ["--- Harris Farm Knowledge Base ---"]
    for r in rows:
        # Truncate each doc to ~800 words to avoid token bloat
        words = r["content"].split()
        truncated = " ".join(words[:800])
        parts.append(f"\n[{r['category']} / {r['filename']}]\n{truncated}")

    return "\n".join(parts)


@app.get("/api/knowledge/search")
async def knowledge_search(q: str = "", category: str = None, limit: int = 5):
    """Search the knowledge base for relevant documents."""
    if not q:
        return {"results": [], "count": 0}
    results = search_knowledge_base(q, category=category, limit=limit)
    return {"results": results, "count": len(results), "query": q}


@app.get("/api/knowledge/stats")
async def knowledge_stats():
    """Get knowledge base statistics."""
    conn = sqlite3.connect(config.HUB_DB)
    conn.row_factory = sqlite3.Row

    total = conn.execute("SELECT COUNT(*) as n FROM knowledge_base").fetchone()["n"]
    total_words = conn.execute("SELECT COALESCE(SUM(word_count), 0) as n FROM knowledge_base").fetchone()["n"]
    categories = [
        dict(r) for r in conn.execute(
            "SELECT category, COUNT(*) as doc_count, SUM(word_count) as words FROM knowledge_base GROUP BY category ORDER BY doc_count DESC"
        ).fetchall()
    ]

    conn.close()
    return {
        "total_documents": total,
        "total_words": total_words,
        "categories": categories,
    }


# ============================================================================
# SUSTAINABILITY KPIs — GREATER GOODNESS
# ============================================================================

@app.get("/api/sustainability/kpis")
async def get_sustainability_kpis():
    """Get all sustainability KPIs for the Greater Goodness dashboard."""
    conn = sqlite3.connect(config.HUB_DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM sustainability_kpis ORDER BY id"
    ).fetchall()
    conn.close()
    return {"kpis": [dict(r) for r in rows]}


@app.post("/api/sustainability/kpis/{kpi_id}")
async def update_sustainability_kpi(
    kpi_id: int, current_value: float, status: str = None, notes: str = None,
):
    """Update a sustainability KPI's progress."""
    conn = sqlite3.connect(config.HUB_DB)
    now = datetime.now().isoformat()
    updates = ["current_value = ?", "last_updated = ?"]
    params = [current_value, now]
    if status:
        updates.append("status = ?")
        params.append(status)
    if notes:
        updates.append("notes = ?")
        params.append(notes)
    params.append(kpi_id)
    conn.execute(f"UPDATE sustainability_kpis SET {', '.join(updates)} WHERE id = ?", params)
    conn.commit()
    conn.close()
    return {"status": "updated", "kpi_id": kpi_id}


# ============================================================================
# HUB ASSISTANT — KNOWLEDGE BASE CHATBOT
# ============================================================================

async def _chat_claude(system_prompt: str, messages: list) -> dict:
    """Multi-turn Claude chat with system prompt."""
    if not rubric.claude_client:
        return {"provider": "Claude", "response": "API key not configured. Set ANTHROPIC_API_KEY in .env", "status": "error", "tokens": 0, "latency_ms": 0}
    start = datetime.now()
    try:
        message = rubric.claude_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            system=system_prompt,
            messages=messages
        )
        latency = (datetime.now() - start).total_seconds() * 1000
        return {
            "provider": "Claude",
            "response": message.content[0].text,
            "tokens": message.usage.input_tokens + message.usage.output_tokens,
            "latency_ms": round(latency, 2),
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Chat Claude error: {e}")
        return {"provider": "Claude", "response": "Unable to generate response. Please try again.", "status": "error", "tokens": 0, "latency_ms": round((datetime.now() - start).total_seconds() * 1000, 2)}


async def _chat_chatgpt(system_prompt: str, messages: list) -> dict:
    """Multi-turn ChatGPT chat with system prompt."""
    if not rubric.openai_client:
        return {"provider": "ChatGPT", "response": "API key not configured. Set OPENAI_API_KEY in .env", "status": "error", "tokens": 0, "latency_ms": 0}
    start = datetime.now()
    try:
        oai_messages = [{"role": "system", "content": system_prompt}] + messages
        response = rubric.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=oai_messages,
            max_tokens=4000
        )
        latency = (datetime.now() - start).total_seconds() * 1000
        return {
            "provider": "ChatGPT",
            "response": response.choices[0].message.content,
            "tokens": response.usage.total_tokens,
            "latency_ms": round(latency, 2),
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Chat ChatGPT error: {e}")
        return {"provider": "ChatGPT", "response": "Unable to generate response. Please try again.", "status": "error", "tokens": 0, "latency_ms": round((datetime.now() - start).total_seconds() * 1000, 2)}


async def _chat_grok(system_prompt: str, messages: list) -> dict:
    """Multi-turn Grok chat with system prompt."""
    if not config.GROK_API_KEY:
        return {"provider": "Grok", "response": "API key not configured. Set GROK_API_KEY in .env", "status": "error", "tokens": 0, "latency_ms": 0}
    start = datetime.now()
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.x.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {config.GROK_API_KEY}", "Content-Type": "application/json"},
                json={
                    "model": "grok-beta",
                    "messages": [{"role": "system", "content": system_prompt}] + messages,
                    "max_tokens": 4000
                },
                timeout=60.0
            )
            result = response.json()
            latency = (datetime.now() - start).total_seconds() * 1000
            return {
                "provider": "Grok",
                "response": result["choices"][0]["message"]["content"],
                "tokens": result.get("usage", {}).get("total_tokens", 0),
                "latency_ms": round(latency, 2),
                "status": "success"
            }
    except Exception as e:
        logger.error(f"Chat Grok error: {e}")
        return {"provider": "Grok", "response": "Unable to generate response. Please try again.", "status": "error", "tokens": 0, "latency_ms": round((datetime.now() - start).total_seconds() * 1000, 2)}


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Knowledge-base-grounded chatbot for Harris Farm staff."""

    # 1. Retrieve KB context
    kb_docs = search_knowledge_base(request.message, category=request.category, limit=5)
    kb_context = get_knowledge_context(request.message, limit=3)

    # 2. Build system prompt
    system_prompt = (
        "You are the Harris Farm Hub Assistant, an AI helper for Harris Farm Markets staff. "
        "Answer questions using ONLY the Harris Farm knowledge base documents provided below. "
        "If the documents do not contain enough information to answer, say so honestly. "
        "Be concise, practical, and specific to Harris Farm operations. "
        "When referencing a procedure, mention the document name.\n\n"
    )
    if kb_context:
        system_prompt += kb_context
    else:
        system_prompt += "(No matching documents found in the knowledge base for this query.)"

    # 3. Build messages (cap at last 10 for token management)
    messages = [{"role": m.role, "content": m.content} for m in request.history[-10:]]
    messages.append({"role": "user", "content": request.message})

    # 4. Call selected LLM
    provider_fn = {"claude": _chat_claude, "chatgpt": _chat_chatgpt, "grok": _chat_grok}
    result = await provider_fn[request.provider](system_prompt, messages)

    # 5. Store in database for audit trail
    now = datetime.now().isoformat()
    conn = sqlite3.connect(config.HUB_DB)
    c = conn.cursor()
    kb_filenames = json.dumps([d["filename"] for d in kb_docs])

    c.execute(
        """INSERT INTO chat_messages
           (session_id, role, content, provider, category_filter, kb_docs_used, timestamp)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (request.user_id, "user", request.message, request.provider, request.category, kb_filenames, now)
    )
    c.execute(
        """INSERT INTO chat_messages
           (session_id, role, content, provider, category_filter, kb_docs_used, tokens, latency_ms, timestamp)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (request.user_id, "assistant", result["response"], request.provider,
         request.category, kb_filenames, result.get("tokens", 0), result.get("latency_ms", 0), now)
    )
    conn.commit()
    conn.close()

    # 6. Return response
    return {
        "response": result["response"],
        "provider": result["provider"],
        "status": result["status"],
        "tokens": result.get("tokens", 0),
        "latency_ms": result.get("latency_ms", 0),
        "kb_docs_used": [
            {"filename": d["filename"], "category": d["category"], "snippet": d.get("snippet", "")[:200]}
            for d in kb_docs
        ],
        "timestamp": now
    }


# ============================================================================
# EMPLOYEE ROLES
# ============================================================================

@app.get("/api/roles")
async def get_roles(function: Optional[str] = None, department: Optional[str] = None):
    """List employee roles with optional filters."""
    conn = sqlite3.connect(config.HUB_DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    query = "SELECT * FROM employee_roles WHERE 1=1"
    params = []

    if function:
        query += " AND function = ?"
        params.append(function)
    if department:
        query += " AND department = ?"
        params.append(department)

    query += " ORDER BY function, department, job"
    c.execute(query, params)
    roles = [dict(row) for row in c.fetchall()]
    conn.close()

    return {"roles": roles, "count": len(roles)}


@app.get("/api/roles/metadata")
async def get_roles_metadata():
    """Role taxonomy summary: unique values and counts."""
    conn = sqlite3.connect(config.HUB_DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT COUNT(*) as total FROM employee_roles")
    total = c.fetchone()["total"]

    c.execute("SELECT DISTINCT function FROM employee_roles ORDER BY function")
    functions = [row["function"] for row in c.fetchall()]

    c.execute("SELECT DISTINCT department FROM employee_roles ORDER BY department")
    departments = [row["department"] for row in c.fetchall()]

    c.execute("SELECT DISTINCT job FROM employee_roles ORDER BY job")
    jobs = [row["job"] for row in c.fetchall()]

    c.execute("SELECT MIN(created_at) as first_import FROM employee_roles")
    row = c.fetchone()
    first_import = row["first_import"] if row else None

    conn.close()

    return {
        "total_roles": total,
        "unique_functions": len(functions),
        "unique_departments": len(departments),
        "unique_jobs": len(jobs),
        "functions": functions,
        "departments": departments,
        "jobs": jobs,
        "import_timestamp": first_import,
        "source_file": "HFM Job Roles.xlsx",
    }


@app.post("/api/roles/import")
async def import_roles(mode: str = "replace"):
    """Import employee roles from HFM Job Roles.xlsx. Mode: replace or append."""
    if mode not in ("replace", "append"):
        raise HTTPException(status_code=400, detail="mode must be 'replace' or 'append'")

    from import_roles import run_import
    result = run_import(db_path=config.HUB_DB, mode=mode)

    if result.get("error"):
        raise HTTPException(status_code=500, detail=result["error"])

    return result


# ============================================================================
# LEARNING CENTRE
# ============================================================================

def seed_learning_data():
    """Seed learning modules and lessons from learning_content.py if not already present."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent / "dashboards"))
    from shared.learning_content import MODULES, LESSONS

    conn = sqlite3.connect(config.HUB_DB)
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM learning_modules")
    if c.fetchone()[0] > 0:
        conn.close()
        return  # already seeded

    now = datetime.now().isoformat()

    for m in MODULES:
        c.execute(
            """INSERT OR IGNORE INTO learning_modules
               (code, pillar, name, description, duration_minutes, difficulty,
                prerequisites, sort_order, icon, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (m["code"], m["pillar"], m["name"], m["description"],
             m["duration_minutes"], m["difficulty"], m["prerequisites"],
             m["sort_order"], m.get("icon", ""), now),
        )

    for ls in LESSONS:
        c.execute(
            """INSERT OR IGNORE INTO lessons
               (module_code, lesson_number, title, content_type, content,
                duration_minutes, sort_order, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (ls["module_code"], ls["lesson_number"], ls["title"],
             ls["content_type"], ls["content"], ls["duration_minutes"],
             ls.get("sort_order", ls["lesson_number"]), now),
        )

    conn.commit()
    conn.close()


@app.get("/api/learning/modules")
async def get_learning_modules(pillar: Optional[str] = None, difficulty: Optional[str] = None):
    """List learning modules with optional filters."""
    conn = sqlite3.connect(config.HUB_DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    query = "SELECT * FROM learning_modules WHERE 1=1"
    params = []

    if pillar:
        query += " AND pillar = ?"
        params.append(pillar)
    if difficulty:
        query += " AND difficulty = ?"
        params.append(difficulty)

    query += " ORDER BY sort_order"
    c.execute(query, params)
    modules = [dict(row) for row in c.fetchall()]
    conn.close()

    return {"modules": modules, "count": len(modules)}


@app.get("/api/learning/modules/{code}")
async def get_learning_module(code: str):
    """Get a single module with its lessons."""
    conn = sqlite3.connect(config.HUB_DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT * FROM learning_modules WHERE code = ?", (code.upper(),))
    module = c.fetchone()
    if not module:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Module {code} not found")

    module = dict(module)

    c.execute(
        "SELECT * FROM lessons WHERE module_code = ? ORDER BY lesson_number",
        (code.upper(),),
    )
    module["lessons"] = [dict(row) for row in c.fetchall()]
    conn.close()

    return module


@app.get("/api/learning/progress/{user_id}")
async def get_user_progress(user_id: str):
    """Get a user's progress across all modules."""
    conn = sqlite3.connect(config.HUB_DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute(
        """SELECT up.*, lm.name as module_name, lm.pillar, lm.difficulty, lm.icon
           FROM user_progress up
           JOIN learning_modules lm ON up.module_code = lm.code
           WHERE up.user_id = ?
           ORDER BY lm.sort_order""",
        (user_id,),
    )
    progress = [dict(row) for row in c.fetchall()]

    # Summary stats
    total_modules = 12
    completed = sum(1 for p in progress if p["status"] == "completed")
    in_progress = sum(1 for p in progress if p["status"] == "in_progress")
    total_time = sum(p.get("time_spent_minutes", 0) for p in progress)

    conn.close()

    return {
        "user_id": user_id,
        "progress": progress,
        "summary": {
            "total_modules": total_modules,
            "completed": completed,
            "in_progress": in_progress,
            "not_started": total_modules - completed - in_progress,
            "completion_pct": round(completed / total_modules * 100) if total_modules else 0,
            "total_time_minutes": total_time,
        },
    }


@app.post("/api/learning/progress/{user_id}/{module_code}")
async def update_user_progress(
    user_id: str,
    module_code: str,
    status: str = "in_progress",
    completion_pct: int = 0,
    score: int = 0,
    time_spent_minutes: int = 0,
):
    """Update a user's progress on a module."""
    valid_statuses = ("not_started", "in_progress", "completed")
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"status must be one of {valid_statuses}")

    conn = sqlite3.connect(config.HUB_DB)
    c = conn.cursor()

    now = datetime.now().isoformat()

    # Check if record exists
    c.execute(
        "SELECT id, started_at FROM user_progress WHERE user_id = ? AND module_code = ?",
        (user_id, module_code.upper()),
    )
    existing = c.fetchone()

    if existing:
        started_at = existing[1]
        completed_at = now if status == "completed" else None
        c.execute(
            """UPDATE user_progress
               SET status = ?, completion_pct = ?, score = ?,
                   time_spent_minutes = time_spent_minutes + ?,
                   completed_at = COALESCE(?, completed_at),
                   updated_at = ?
               WHERE user_id = ? AND module_code = ?""",
            (status, completion_pct, score, time_spent_minutes,
             completed_at, now, user_id, module_code.upper()),
        )
    else:
        started_at = now if status != "not_started" else None
        completed_at = now if status == "completed" else None
        c.execute(
            """INSERT INTO user_progress
               (user_id, module_code, status, completion_pct, score,
                time_spent_minutes, started_at, completed_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, module_code.upper(), status, completion_pct, score,
             time_spent_minutes, started_at, completed_at, now),
        )

    conn.commit()
    conn.close()

    # Award gamification points on module completion
    if status == "completed":
        _award_points(user_id, 20, "learning", f"Completed module {module_code.upper()}")
        # Academy XP engine hook
        try:
            from academy_engine import on_module_complete
            on_module_complete(config.HUB_DB, user_id, module_code.upper())
        except Exception:
            pass

    return {"status": "updated", "user_id": user_id, "module_code": module_code.upper()}


@app.get("/api/learning/recommended/{function}/{department}/{job}")
async def get_recommended_modules(function: str, department: str, job: str):
    """Get role-based module recommendations."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent / "dashboards"))
    from shared.learning_content import get_role_priorities

    priorities = get_role_priorities(function, department)

    conn = sqlite3.connect(config.HUB_DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT * FROM learning_modules ORDER BY sort_order")
    all_modules = {row["code"]: dict(row) for row in c.fetchall()}
    conn.close()

    result = {"essential": [], "recommended": [], "optional": []}
    for priority_level in ("essential", "recommended", "optional"):
        for code in priorities[priority_level]:
            if code in all_modules:
                mod = all_modules[code]
                mod["priority"] = priority_level
                result[priority_level].append(mod)

    return {
        "role": {"function": function, "department": department, "job": job},
        **result,
    }


# ============================================================================
# TRANSACTION DATA (DuckDB → Parquet, 383M rows)
# ============================================================================

@app.get("/api/transactions/summary")
async def transactions_summary():
    """Overview: row counts, date ranges, store counts per fiscal year."""
    try:
        return app.state.txn_store.summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/transactions/stores")
async def transactions_stores():
    """All stores with transaction counts and total revenue."""
    try:
        from transaction_layer import STORE_NAMES
        stores = app.state.txn_store.get_stores()
        return {"stores": stores, "count": len(stores)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/transactions/top-items")
async def transactions_top_items(
    start: str,
    end: str,
    store_id: Optional[str] = None,
    limit: int = 20,
    sort_by: str = "revenue",
):
    """Top N items by revenue, quantity, or gross profit."""
    if sort_by not in ("revenue", "quantity", "gp", "transactions"):
        raise HTTPException(status_code=400,
                            detail="sort_by must be: revenue, quantity, gp, transactions")
    if limit < 1 or limit > 500:
        raise HTTPException(status_code=400, detail="limit must be 1-500")
    try:
        items = app.state.txn_store.top_items(
            start, end, store_id=store_id, limit=limit, sort_by=sort_by)
        return {"items": items, "count": len(items),
                "filters": {"start": start, "end": end,
                             "store_id": store_id, "sort_by": sort_by}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/transactions/store-trend")
async def transactions_store_trend(
    store_id: str,
    start: str,
    end: str,
    grain: str = "daily",
):
    """Time-series revenue and transaction trend for a store."""
    if grain not in ("daily", "weekly", "monthly"):
        raise HTTPException(status_code=400,
                            detail="grain must be: daily, weekly, monthly")
    try:
        from transaction_layer import STORE_NAMES
        trend = app.state.txn_store.store_trend(store_id, start, end, grain)
        return {
            "store_id": store_id,
            "store_name": STORE_NAMES.get(store_id, f"Store {store_id}"),
            "grain": grain,
            "periods": trend,
            "count": len(trend),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/transactions/plu/{plu_id}")
async def transactions_plu(
    plu_id: str,
    start: Optional[str] = None,
    end: Optional[str] = None,
):
    """Performance summary for a single PLU item across all stores."""
    try:
        return app.state.txn_store.plu_performance(plu_id, start, end)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class FreeformQuery(BaseModel):
    sql: str = Field(..., description="Read-only SELECT query against transactions view")
    params: List = Field(default_factory=list, description="Query parameters")
    limit: int = Field(default=1000, ge=1, le=10000, description="Max rows to return")


@app.post("/api/transactions/query")
async def transactions_freeform(body: FreeformQuery):
    """Execute a validated read-only SQL query against transaction data."""
    from transaction_layer import TransactionStore
    error = TransactionStore.validate_freeform_sql(body.sql)
    if error:
        raise HTTPException(status_code=400, detail=error)
    try:
        results = app.state.txn_store.query(
            body.sql, body.params, max_rows=body.limit)
        return {"results": results, "count": len(results),
                "truncated": len(results) >= body.limit}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Query error: {e}")


@app.get("/api/transactions/query-catalog")
async def transactions_query_catalog():
    """Return list of available pre-built queries with descriptions."""
    from transaction_queries import get_query_catalog
    return {"queries": get_query_catalog(), "count": len(get_query_catalog())}


@app.get("/api/transactions/run/{query_name}")
async def transactions_run_query(
    query_name: str,
    start: str = None,
    end: str = None,
    store_id: str = None,
    plu_id: str = None,
    limit: int = 20,
    threshold: int = 10,
    customer_code: str = None,
    dept_code: str = None,
    major_code: str = None,
    fin_year: int = None,
    fin_year_2: int = None,
):
    """Execute a named query from the query catalog."""
    from transaction_queries import run_query, QUERIES
    if query_name not in QUERIES:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown query: {query_name}. "
                   f"Available: {list(QUERIES.keys())}")
    kwargs = {}
    if start:
        kwargs["start"] = start
    if end:
        kwargs["end"] = end
    if store_id:
        kwargs["store_id"] = store_id
    if plu_id:
        kwargs["plu_id"] = plu_id
    if limit:
        kwargs["limit"] = limit
    if threshold:
        kwargs["threshold"] = threshold
    if customer_code:
        kwargs["customer_code"] = customer_code
    if dept_code:
        kwargs["dept_code"] = dept_code
    if major_code:
        kwargs["major_code"] = major_code
    if fin_year:
        kwargs["fin_year"] = fin_year
    if fin_year_2:
        kwargs["fin_year_2"] = fin_year_2
    try:
        results = run_query(app.state.txn_store, query_name, **kwargs)
        return {"query": query_name, "results": results, "count": len(results)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query error: {e}")


# ============================================================================
# PRODUCT HIERARCHY API
# ============================================================================

@app.get("/api/hierarchy/departments")
async def hierarchy_departments():
    """List all departments with product counts."""
    try:
        from product_hierarchy import get_departments
        depts = get_departments()
        return {"departments": depts, "count": len(depts)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/hierarchy/browse/{dept_code}")
async def hierarchy_browse_dept(dept_code: str):
    """Major groups within a department."""
    try:
        from product_hierarchy import get_major_groups
        groups = get_major_groups(dept_code)
        if not groups:
            raise HTTPException(
                status_code=404,
                detail=f"No department with code: {dept_code}")
        return {"dept_code": dept_code, "major_groups": groups,
                "count": len(groups)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/hierarchy/browse/{dept_code}/{major_code}")
async def hierarchy_browse_major(dept_code: str, major_code: str):
    """Minor groups within a major group."""
    try:
        from product_hierarchy import get_minor_groups
        groups = get_minor_groups(dept_code, major_code)
        if not groups:
            raise HTTPException(
                status_code=404,
                detail=f"No major group {major_code} in dept {dept_code}")
        return {"dept_code": dept_code, "major_code": major_code,
                "minor_groups": groups, "count": len(groups)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/hierarchy/search")
async def hierarchy_search(q: str, limit: int = 20):
    """Search products by name."""
    if len(q) < 2:
        raise HTTPException(
            status_code=400,
            detail="Search query must be at least 2 characters")
    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=400, detail="limit must be 1-100")
    try:
        from product_hierarchy import search_products
        results = search_products(q, limit=limit)
        return {"query": q, "results": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/hierarchy/stats")
async def hierarchy_stats_endpoint():
    """Hierarchy coverage statistics."""
    try:
        from product_hierarchy import hierarchy_stats
        return hierarchy_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =========================================================================
# FISCAL CALENDAR ENDPOINTS
# =========================================================================

@app.get("/api/fiscal-calendar/years")
async def fiscal_calendar_years():
    """Available fiscal years with date ranges."""
    try:
        from fiscal_calendar import get_fiscal_years, get_fy_date_range, is_long_year
        years = get_fiscal_years()
        result = []
        for fy in years:
            start, end = get_fy_date_range(fy)
            result.append({
                "fin_year": fy,
                "start": start,
                "end": end,
                "is_long_year": is_long_year(fy),
            })
        return {"count": len(result), "years": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/fiscal-calendar/periods/{fin_year}")
async def fiscal_calendar_periods(fin_year: int):
    """Months, quarters, and weeks for a fiscal year."""
    try:
        from fiscal_calendar import (
            get_fiscal_months, get_fiscal_quarters, get_fiscal_weeks,
            get_fy_date_range, is_long_year,
        )
        start, end = get_fy_date_range(fin_year)
        if not start:
            raise HTTPException(status_code=404, detail=f"FY{fin_year} not found")
        return {
            "fin_year": fin_year,
            "start": start,
            "end": end,
            "is_long_year": is_long_year(fin_year),
            "months": get_fiscal_months(fin_year),
            "quarters": get_fiscal_quarters(fin_year),
            "weeks": get_fiscal_weeks(fin_year),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/fiscal-calendar/current")
async def fiscal_calendar_current():
    """Current fiscal period context."""
    try:
        from fiscal_calendar import get_current_fiscal_period
        return get_current_fiscal_period()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

class SiteCheckRequest(BaseModel):
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class LogoutRequest(BaseModel):
    token: str

class CreateUserRequest(BaseModel):
    email: str
    name: str
    password: str
    role: str = "user"

class UpdateUserRequest(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    active: Optional[int] = None
    password: Optional[str] = None

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str

class ResetPasswordRequest(BaseModel):
    email: str
    new_password: str
    site_password: str

class UpdateSettingsRequest(BaseModel):
    site_password: Optional[str] = None
    session_timeout: Optional[int] = None
    require_site_password: Optional[bool] = None


def _get_client_ip(request: Request):
    """Extract client IP from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else ""


async def _require_admin(request: Request):
    """Validate admin token from X-Auth-Token header. Raises HTTPException."""
    import auth as auth_module
    token = request.headers.get("X-Auth-Token")
    if not token:
        raise HTTPException(status_code=401, detail="No auth token")
    user = auth_module.verify_session(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


@app.post("/api/auth/site-check")
async def auth_site_check(req: SiteCheckRequest):
    """Verify site-wide access password."""
    import auth as auth_module
    valid = auth_module.check_site_password(req.password)
    return {"valid": valid}


@app.post("/api/auth/login")
async def auth_login(req: LoginRequest, request: Request):
    """Authenticate user and create session."""
    import auth as auth_module
    ip = _get_client_ip(request)

    user = auth_module.authenticate_user(req.email, req.password)
    if not user:
        auth_module.log_auth_event("login_failed", req.email, ip, "Invalid credentials")
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = auth_module.create_session(user["id"], ip)
    auth_module.log_auth_event("login", user["email"], ip, "Login successful")
    return {"token": token, "user": user}


@app.get("/api/auth/verify")
async def auth_verify(token: str = ""):
    """Validate a session token."""
    import auth as auth_module
    if not token:
        return {"valid": False}
    user = auth_module.verify_session(token)
    if user:
        return {"valid": True, "user": user}
    return {"valid": False}


@app.post("/api/auth/logout")
async def auth_logout(req: LogoutRequest, request: Request):
    """Revoke a session token."""
    import auth as auth_module
    ip = _get_client_ip(request)
    user = auth_module.verify_session(req.token)
    email = user["email"] if user else ""
    auth_module.revoke_session(req.token)
    auth_module.log_auth_event("logout", email, ip, "Session revoked")
    return {"ok": True}


@app.post("/api/auth/register")
async def auth_register(req: RegisterRequest, request: Request):
    """Self-register a new user account."""
    import auth as auth_module
    ip = _get_client_ip(request)

    if len(req.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    try:
        user = auth_module.create_user(req.email, req.name, req.password, role="user")
        token = auth_module.create_session(user["id"], ip)
        auth_module.log_auth_event("register", req.email, ip, "Self-registration")
        return {"token": token, "user": user}
    except ValueError:
        raise HTTPException(status_code=409, detail="An account with this email already exists")


@app.post("/api/auth/reset-password")
async def auth_reset_password(req: ResetPasswordRequest, request: Request):
    """Reset password using the site access code as verification."""
    import auth as auth_module
    ip = _get_client_ip(request)

    if not auth_module.check_site_password(req.site_password):
        auth_module.log_auth_event("reset_failed", req.email, ip, "Invalid site password")
        raise HTTPException(status_code=403, detail="Invalid site access code")

    if len(req.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    if not auth_module.reset_password(req.email, req.new_password):
        raise HTTPException(status_code=404, detail="No account found with that email")

    auth_module.log_auth_event("password_reset", req.email, ip, "Password reset via site code")
    return {"ok": True, "message": "Password has been reset. You can now sign in."}



@app.get("/api/auth/me")
async def auth_me(request: Request):
    """Get current user info from X-Auth-Token header."""
    import auth as auth_module
    token = request.headers.get("X-Auth-Token")
    if not token:
        raise HTTPException(status_code=401, detail="No auth token")
    user = auth_module.verify_session(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return {"user": user}


@app.get("/api/auth/site-password-required")
async def auth_site_password_required():
    """Check if site password is required."""
    import auth as auth_module
    return {"required": auth_module.is_site_password_required()}


# --- Admin endpoints ---

@app.get("/api/auth/admin/users")
async def admin_list_users(request: Request):
    """List all users (admin only)."""
    import auth as auth_module
    await _require_admin(request)
    return {"users": auth_module.list_users()}


@app.post("/api/auth/admin/users")
async def admin_create_user(req: CreateUserRequest, request: Request):
    """Create a new user (admin only)."""
    import auth as auth_module
    admin = await _require_admin(request)
    ip = _get_client_ip(request)
    try:
        user = auth_module.create_user(req.email, req.name, req.password, req.role)
        auth_module.log_auth_event(
            "user_created", req.email, ip,
            f"Created by {admin['email']}, role={req.role}",
        )
        return {"user": user}
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@app.put("/api/auth/admin/users/{user_id}")
async def admin_update_user(user_id: int, req: UpdateUserRequest, request: Request):
    """Update a user (admin only)."""
    import auth as auth_module
    admin = await _require_admin(request)
    ip = _get_client_ip(request)

    updates = {}
    if req.name is not None:
        updates["name"] = req.name
    if req.role is not None:
        updates["role"] = req.role
    if req.active is not None:
        updates["active"] = req.active
    if req.password is not None:
        updates["password"] = req.password

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    auth_module.update_user(user_id, **updates)
    target = auth_module.get_user_by_id(user_id)
    target_email = target["email"] if target else str(user_id)
    auth_module.log_auth_event(
        "user_updated", target_email, ip,
        f"Updated by {admin['email']}: {list(updates.keys())}",
    )
    return {"ok": True}


@app.delete("/api/auth/admin/users/{user_id}")
async def admin_deactivate_user(user_id: int, request: Request):
    """Deactivate a user and revoke all sessions (admin only)."""
    import auth as auth_module
    admin = await _require_admin(request)
    ip = _get_client_ip(request)

    auth_module.update_user(user_id, active=0)
    auth_module.revoke_all_sessions(user_id)

    target = auth_module.get_user_by_id(user_id)
    target_email = target["email"] if target else str(user_id)
    auth_module.log_auth_event(
        "user_deactivated", target_email, ip,
        f"Deactivated by {admin['email']}",
    )
    return {"ok": True}


@app.get("/api/auth/admin/sessions")
async def admin_list_sessions(request: Request):
    """List active sessions (admin only)."""
    import auth as auth_module
    await _require_admin(request)
    sessions = auth_module.list_active_sessions()
    # Mask tokens — only show first 8 chars
    for s in sessions:
        if "token" in s:
            s["token"] = s["token"][:8] + "..."
    return {"sessions": sessions}


@app.delete("/api/auth/admin/sessions/{session_id}")
async def admin_kill_session(session_id: int, request: Request):
    """Kill a specific session by ID (admin only)."""
    import auth as auth_module
    admin = await _require_admin(request)
    ip = _get_client_ip(request)

    # Find the session to get the full token
    conn = auth_module._get_conn()
    row = conn.execute("SELECT token, user_id FROM sessions WHERE id = ?", (session_id,)).fetchone()
    conn.close()

    if row:
        auth_module.revoke_session(row["token"])
        user = auth_module.get_user_by_id(row["user_id"])
        email = user["email"] if user else str(row["user_id"])
        auth_module.log_auth_event(
            "session_killed", email, ip,
            f"Session killed by {admin['email']}",
        )
    return {"ok": True}


@app.get("/api/auth/admin/audit")
async def admin_audit_log(request: Request, limit: int = 100):
    """Get auth audit log (admin only)."""
    import auth as auth_module
    await _require_admin(request)
    return {"entries": auth_module.get_auth_audit(limit)}


@app.put("/api/auth/admin/settings")
async def admin_update_settings(req: UpdateSettingsRequest, request: Request):
    """Update auth settings (admin only)."""
    import auth as auth_module
    admin = await _require_admin(request)
    ip = _get_client_ip(request)

    changes = []
    if req.site_password is not None:
        auth_module.update_site_password(req.site_password)
        changes.append("site_password")
    if req.session_timeout is not None:
        auth_module.update_session_timeout(req.session_timeout)
        changes.append(f"session_timeout={req.session_timeout}h")
    if req.require_site_password is not None:
        auth_module.update_require_site_password(req.require_site_password)
        changes.append(f"require_site_password={req.require_site_password}")

    if changes:
        auth_module.log_auth_event(
            "settings_updated", admin["email"], ip,
            f"Changed: {', '.join(changes)}",
        )
    return {"ok": True, "changes": changes}


# ============================================================================
# PORTAL API — Prompt History & Gamification
# ============================================================================

@app.post("/api/portal/prompt-history")
async def save_prompt_history(request: Request):
    """Save a prompt to history."""
    data = await request.json()
    conn = sqlite3.connect(config.HUB_DB)
    c = conn.cursor()
    c.execute(
        "INSERT INTO prompt_history (user_id, prompt_text, context, outcome, "
        "rating, ai_review, tokens, latency_ms) VALUES (?,?,?,?,?,?,?,?)",
        (data.get("user_id", "anonymous"), data["prompt_text"],
         data.get("context"), data.get("outcome"), data.get("rating"),
         data.get("ai_review"), data.get("tokens"), data.get("latency_ms")),
    )
    row_id = c.lastrowid
    conn.commit()
    conn.close()
    return {"ok": True, "id": row_id}


@app.get("/api/portal/prompt-history")
async def get_prompt_history(user_id: str = "anonymous", limit: int = 50):
    """Retrieve prompt history for a user."""
    conn = sqlite3.connect(config.HUB_DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM prompt_history WHERE user_id = ? "
        "ORDER BY created_at DESC LIMIT ?",
        (user_id, limit),
    ).fetchall()
    conn.close()
    return {"prompts": [dict(r) for r in rows]}


def _award_points(user_id: str, points: int, category: str, reason: str):
    """Internal helper to award gamification points to a user."""
    try:
        conn = sqlite3.connect(config.HUB_DB)
        conn.execute(
            "INSERT INTO portal_scores (user_id, points, category, reason) VALUES (?,?,?,?)",
            (user_id, points, category, reason),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


@app.post("/api/portal/score")
async def award_score(request: Request):
    """Award points to a user or AI."""
    data = await request.json()
    conn = sqlite3.connect(config.HUB_DB)
    c = conn.cursor()
    c.execute(
        "INSERT INTO portal_scores (user_id, points, category, reason) "
        "VALUES (?,?,?,?)",
        (data.get("user_id", "anonymous"), data["points"],
         data["category"], data.get("reason")),
    )
    conn.commit()

    # Check total and return current level
    total = conn.execute(
        "SELECT COALESCE(SUM(points), 0) FROM portal_scores WHERE user_id = ?",
        (data.get("user_id", "anonymous"),),
    ).fetchone()[0]
    conn.close()
    return {"ok": True, "total_points": total}


@app.get("/api/portal/leaderboard")
async def get_leaderboard(period: str = "all"):
    """Aggregate scores by user, return ranked list."""
    conn = sqlite3.connect(config.HUB_DB)
    conn.row_factory = sqlite3.Row

    where = ""
    if period == "week":
        where = "WHERE created_at >= datetime('now', '-7 days')"
    elif period == "month":
        where = "WHERE created_at >= datetime('now', '-30 days')"

    rows = conn.execute(
        "SELECT user_id, category, SUM(points) AS total_points, "
        "COUNT(*) AS actions "
        "FROM portal_scores {} "
        "GROUP BY user_id, category "
        "ORDER BY total_points DESC".format(where)
    ).fetchall()
    conn.close()
    return {"leaderboard": [dict(r) for r in rows]}


@app.get("/api/portal/achievements/{user_id}")
async def get_achievements(user_id: str):
    """Return earned achievements for a user."""
    conn = sqlite3.connect(config.HUB_DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM portal_achievements WHERE user_id = ? "
        "ORDER BY achieved_at DESC",
        (user_id,),
    ).fetchall()
    conn.close()
    return {"achievements": [dict(r) for r in rows]}


@app.post("/api/portal/achievements")
async def award_achievement(request: Request):
    """Award an achievement to a user (idempotent)."""
    data = await request.json()
    conn = sqlite3.connect(config.HUB_DB)
    try:
        conn.execute(
            "INSERT OR IGNORE INTO portal_achievements "
            "(user_id, achievement_code) VALUES (?,?)",
            (data.get("user_id", "anonymous"), data["achievement_code"]),
        )
        conn.commit()
    finally:
        conn.close()
    return {"ok": True}


# ============================================================================
# ARENA — Agent Competition System API
# ============================================================================

@app.get("/api/arena/teams")
async def arena_teams():
    """Return all 5 agent teams with current stats."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "dashboards"))
    from shared.agent_teams import AGENT_TEAMS, get_agents_by_team

    conn = sqlite3.connect(config.HUB_DB)
    conn.row_factory = sqlite3.Row
    stats_rows = conn.execute(
        "SELECT * FROM arena_team_stats WHERE period = 'all_time'"
    ).fetchall()
    conn.close()

    stats_map = {r["team_id"]: dict(r) for r in stats_rows}
    result = []
    for t in AGENT_TEAMS:
        team = dict(t)
        team["stats"] = stats_map.get(t["id"], {})
        team["agent_count"] = len(get_agents_by_team(t["id"]))
        result.append(team)
    return {"teams": result}


@app.get("/api/arena/teams/{team_id}")
async def arena_team_detail(team_id: str):
    """Return a single team with proposals, agents, and stats."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "dashboards"))
    from shared.agent_teams import get_team, get_agents_by_team

    team = get_team(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    conn = sqlite3.connect(config.HUB_DB)
    conn.row_factory = sqlite3.Row
    proposals = conn.execute(
        "SELECT * FROM arena_proposals WHERE team_id = ? "
        "ORDER BY total_score DESC",
        (team_id,),
    ).fetchall()
    stats = conn.execute(
        "SELECT * FROM arena_team_stats WHERE team_id = ? AND period = 'all_time'",
        (team_id,),
    ).fetchone()
    conn.close()

    return {
        "team": dict(team),
        "agents": get_agents_by_team(team_id),
        "proposals": [dict(p) for p in proposals],
        "stats": dict(stats) if stats else {},
    }


@app.get("/api/arena/leaderboard")
async def arena_leaderboard(period: str = "all_time"):
    """Return team rankings for a period."""
    conn = sqlite3.connect(config.HUB_DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM arena_team_stats WHERE period = ? ORDER BY rank ASC",
        (period,),
    ).fetchall()
    conn.close()
    return {"leaderboard": [dict(r) for r in rows]}


@app.get("/api/arena/proposals")
async def arena_proposals(
    team_id: str = None,
    status: str = None,
    category: str = None,
    limit: int = 50,
):
    """List proposals with optional filters."""
    conn = sqlite3.connect(config.HUB_DB)
    conn.row_factory = sqlite3.Row

    query = "SELECT * FROM arena_proposals WHERE 1=1"
    params = []
    if team_id:
        query += " AND team_id = ?"
        params.append(team_id)
    if status:
        query += " AND status = ?"
        params.append(status)
    if category:
        query += " AND category = ?"
        params.append(category)
    query += " ORDER BY total_score DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return {"proposals": [dict(r) for r in rows]}


@app.get("/api/arena/proposals/{proposal_id}")
async def arena_proposal_detail(proposal_id: int):
    """Return a single proposal with all evaluations."""
    conn = sqlite3.connect(config.HUB_DB)
    conn.row_factory = sqlite3.Row
    proposal = conn.execute(
        "SELECT * FROM arena_proposals WHERE id = ?", (proposal_id,)
    ).fetchone()
    if not proposal:
        conn.close()
        raise HTTPException(status_code=404, detail="Proposal not found")

    evaluations = conn.execute(
        "SELECT * FROM arena_evaluations WHERE proposal_id = ? "
        "ORDER BY tier, criterion",
        (proposal_id,),
    ).fetchall()
    conn.close()
    return {
        "proposal": dict(proposal),
        "evaluations": [dict(e) for e in evaluations],
    }


@app.post("/api/arena/proposals")
async def arena_submit_proposal(request: Request):
    """Submit a new proposal. All proposals are automatically routed
    through WATCHDOG safety analysis before entering the review queue."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "dashboards"))
    from shared.watchdog_safety import WatchdogService

    data = await request.json()
    required = ["title", "description", "team_id", "agent_id",
                 "department", "category"]
    for field in required:
        if field not in data:
            raise HTTPException(status_code=400,
                                detail="Missing field: {}".format(field))

    # WATCHDOG GATE: Analyze proposal before accepting
    watchdog = WatchdogService(db_path=config.HUB_DB)
    safety_result = watchdog.analyze_proposal(data)

    conn = sqlite3.connect(config.HUB_DB)
    c = conn.cursor()

    # Set initial status based on WATCHDOG analysis
    if safety_result["blocked"]:
        initial_status = "blocked"
    else:
        initial_status = "pending_review"

    c.execute(
        "INSERT INTO arena_proposals (title, description, team_id, "
        "agent_id, department, category, status, estimated_impact_aud, "
        "estimated_effort_weeks, complexity, total_score, tier_scores) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,0,'{}')",
        (data["title"], data["description"], data["team_id"],
         data["agent_id"], data["department"], data["category"],
         initial_status,
         data.get("estimated_impact_aud", 0),
         data.get("estimated_effort_weeks", 0),
         data.get("complexity", "medium")),
    )
    proposal_id = c.lastrowid

    # Store WATCHDOG report in watchdog_proposals
    c.execute(
        "INSERT INTO watchdog_proposals "
        "(tracking_id, source_proposal_id, agent_id, title, description, "
        "proposal_json, risk_level, finding_count, report, recommendation, "
        "status) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (
            safety_result["tracking_id"],
            proposal_id,
            safety_result["agent_id"],
            safety_result["title"],
            data.get("description", ""),
            json.dumps(data),
            safety_result["risk_level"],
            safety_result["finding_count"],
            safety_result["report"],
            json.dumps(safety_result["recommendation"]),
            "blocked" if safety_result["blocked"] else "pending_review",
        ),
    )

    conn.commit()
    conn.close()

    return {
        "ok": True,
        "proposal_id": proposal_id,
        "watchdog": {
            "tracking_id": safety_result["tracking_id"],
            "risk_level": safety_result["risk_level"],
            "risk_icon": safety_result["risk_icon"],
            "finding_count": safety_result["finding_count"],
            "blocked": safety_result["blocked"],
            "status": "BLOCKED — proposal cannot proceed"
                      if safety_result["blocked"]
                      else "Pending human review",
        },
    }


@app.post("/api/arena/evaluate")
async def arena_evaluate(request: Request):
    """Submit tier evaluations for a proposal. Recalculates total score.
    WATCHDOG GATE: Only approved proposals can be evaluated."""
    data = await request.json()
    proposal_id = data.get("proposal_id")
    evaluations = data.get("evaluations", [])
    evaluator = data.get("evaluator", "anonymous")

    if not proposal_id or not evaluations:
        raise HTTPException(status_code=400,
                            detail="proposal_id and evaluations required")

    conn = sqlite3.connect(config.HUB_DB)
    conn.row_factory = sqlite3.Row
    proposal = conn.execute(
        "SELECT * FROM arena_proposals WHERE id = ?", (proposal_id,)
    ).fetchone()
    if not proposal:
        conn.close()
        raise HTTPException(status_code=404, detail="Proposal not found")

    # WATCHDOG GATE: Block evaluation of unapproved proposals
    proposal_status = dict(proposal)["status"]
    if proposal_status in ("blocked", "pending_review"):
        conn.close()
        raise HTTPException(
            status_code=403,
            detail="Proposal is '{}'. Only WATCHDOG-approved proposals "
                   "can be evaluated.".format(proposal_status)
        )

    c = conn.cursor()
    for ev in evaluations:
        c.execute(
            "INSERT INTO arena_evaluations "
            "(proposal_id, tier, evaluator, criterion, score, comment) "
            "VALUES (?,?,?,?,?,?)",
            (proposal_id, ev["tier"], evaluator,
             ev["criterion"], ev["score"], ev.get("comment", "")),
        )

    # Recalculate score from all evaluations
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "dashboards"))
    from shared.agent_teams import calculate_proposal_score

    all_evals = conn.execute(
        "SELECT tier, criterion, score FROM arena_evaluations "
        "WHERE proposal_id = ?",
        (proposal_id,),
    ).fetchall()
    score_data = calculate_proposal_score([dict(e) for e in all_evals])

    new_status = "scored"
    if dict(proposal)["status"] == "submitted":
        new_status = "evaluating"
    # Check if all 5 tiers have evaluations
    tiers_present = set(e["tier"] for e in all_evals)
    if len(tiers_present) >= 5:
        new_status = "scored"

    c.execute(
        "UPDATE arena_proposals SET total_score = ?, tier_scores = ?, "
        "status = ?, scored_at = datetime('now') WHERE id = ?",
        (score_data["total"], json.dumps(score_data["tier_scores"]),
         new_status, proposal_id),
    )

    # Recalculate team stats
    team_id = dict(proposal)["team_id"]
    row = conn.execute(
        "SELECT COUNT(*) AS cnt, COALESCE(AVG(total_score), 0) AS avg_s, "
        "COALESCE(SUM(estimated_impact_aud), 0) AS impact, "
        "SUM(CASE WHEN status='implemented' THEN 1 ELSE 0 END) AS impl "
        "FROM arena_proposals WHERE team_id = ?",
        (team_id,),
    ).fetchone()
    c.execute(
        "INSERT OR REPLACE INTO arena_team_stats "
        "(team_id, period, total_proposals, avg_score, total_impact_aud, "
        "implementations, rank) VALUES (?,?,?,?,?,?,?)",
        (team_id, "all_time", row[0], round(row[1], 1), row[2], row[3], 0),
    )

    conn.commit()
    conn.close()
    return {"ok": True, "score": score_data}


@app.get("/api/arena/agents")
async def arena_agents(
    business_unit: str = None,
    department: str = None,
    team_id: str = None,
):
    """List agents with optional filters."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "dashboards"))
    from shared.agent_teams import DEPARTMENT_AGENTS

    result = DEPARTMENT_AGENTS
    if business_unit:
        result = [a for a in result if a["business_unit"] == business_unit]
    if department:
        result = [a for a in result if a["department"] == department]
    if team_id:
        result = [a for a in result if a["team_id"] == team_id]
    return {"agents": result}


@app.get("/api/arena/agents/{agent_id}")
async def arena_agent_detail(agent_id: str):
    """Return agent detail with proposals and insights."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "dashboards"))
    from shared.agent_teams import get_agent

    agent = get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    conn = sqlite3.connect(config.HUB_DB)
    conn.row_factory = sqlite3.Row
    proposals = conn.execute(
        "SELECT * FROM arena_proposals WHERE agent_id = ? "
        "ORDER BY total_score DESC",
        (agent_id,),
    ).fetchall()
    insights = conn.execute(
        "SELECT * FROM arena_insights WHERE agent_id = ? "
        "ORDER BY confidence DESC",
        (agent_id,),
    ).fetchall()
    conn.close()

    return {
        "agent": agent,
        "proposals": [dict(p) for p in proposals],
        "insights": [dict(i) for i in insights],
    }


@app.get("/api/arena/insights")
async def arena_insights(
    department: str = None,
    insight_type: str = None,
    limit: int = 50,
):
    """List insights with optional filters."""
    conn = sqlite3.connect(config.HUB_DB)
    conn.row_factory = sqlite3.Row

    query = "SELECT * FROM arena_insights WHERE 1=1"
    params = []
    if department:
        query += " AND department = ?"
        params.append(department)
    if insight_type:
        query += " AND insight_type = ?"
        params.append(insight_type)
    query += " ORDER BY confidence DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return {"insights": [dict(r) for r in rows]}


@app.get("/api/arena/stats")
async def arena_stats():
    """Aggregate arena statistics."""
    conn = sqlite3.connect(config.HUB_DB)
    conn.row_factory = sqlite3.Row

    proposals = conn.execute(
        "SELECT COUNT(*) AS total, "
        "COALESCE(AVG(CASE WHEN total_score > 0 THEN total_score END), 0) AS avg_score, "
        "COALESCE(SUM(estimated_impact_aud), 0) AS total_impact, "
        "SUM(CASE WHEN status='implemented' THEN 1 ELSE 0 END) AS implemented, "
        "SUM(CASE WHEN status='scored' THEN 1 ELSE 0 END) AS scored, "
        "SUM(CASE WHEN status='evaluating' THEN 1 ELSE 0 END) AS evaluating, "
        "SUM(CASE WHEN status='submitted' THEN 1 ELSE 0 END) AS submitted "
        "FROM arena_proposals"
    ).fetchone()

    insights = conn.execute(
        "SELECT COUNT(*) AS total, "
        "COALESCE(AVG(confidence), 0) AS avg_confidence, "
        "COALESCE(SUM(potential_impact_aud), 0) AS total_impact "
        "FROM arena_insights"
    ).fetchone()

    categories = conn.execute(
        "SELECT category, COUNT(*) AS count, "
        "COALESCE(SUM(estimated_impact_aud), 0) AS impact "
        "FROM arena_proposals GROUP BY category ORDER BY impact DESC"
    ).fetchall()

    conn.close()

    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "dashboards"))
    from shared.agent_teams import DEPARTMENT_AGENTS

    return {
        "proposals": dict(proposals),
        "insights": dict(insights),
        "categories": [dict(c) for c in categories],
        "total_agents": len(DEPARTMENT_AGENTS),
    }


@app.get("/api/arena/data-intelligence")
async def arena_data_intelligence():
    """Return Data Intelligence Team status, agents, and insights."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "dashboards"))
    from shared.agent_teams import (
        DATA_INTELLIGENCE_AGENTS, DATA_INTEL_CATEGORIES,
    )

    conn = sqlite3.connect(config.HUB_DB)
    conn.row_factory = sqlite3.Row

    # Get Data Intelligence insights (agent_ids starting with di_)
    di_agent_ids = [a["id"] for a in DATA_INTELLIGENCE_AGENTS]
    placeholders = ",".join("?" * len(di_agent_ids))
    insights = conn.execute(
        "SELECT * FROM arena_insights WHERE agent_id IN ({}) "
        "ORDER BY confidence DESC".format(placeholders),
        di_agent_ids,
    ).fetchall()

    # Aggregate metrics by category
    category_stats = {}
    for ins in insights:
        d = dict(ins)
        # Map insight to category based on agent
        agent_id = d["agent_id"]
        if agent_id == "di_lost_sales":
            cat = "lost_sales"
        elif agent_id == "di_overorder":
            cat = "waste_prevention"
        elif agent_id == "di_buying":
            cat = "margin_improvement"
        elif agent_id == "di_range":
            cat = "range_optimisation"
        elif agent_id == "di_stocktake":
            cat = "shrinkage_reduction"
        elif agent_id == "di_transactions":
            cat = "cross_sell"
        else:
            cat = "other"

        if cat not in category_stats:
            category_stats[cat] = {
                "count": 0, "total_impact": 0, "avg_confidence": 0,
            }
        category_stats[cat]["count"] += 1
        category_stats[cat]["total_impact"] += d.get(
            "potential_impact_aud", 0)

    # Calculate averages
    for cat, stats in category_stats.items():
        cat_insights = [
            dict(i) for i in insights
            if dict(i).get("agent_id", "").startswith("di_")
        ]
        if cat_insights:
            cat_specific = [
                i for i in cat_insights
                if _agent_to_category(i["agent_id"]) == cat
            ]
            if cat_specific:
                stats["avg_confidence"] = round(
                    sum(i.get("confidence", 0) for i in cat_specific)
                    / len(cat_specific), 2)

    conn.close()

    total_impact = sum(
        dict(i).get("potential_impact_aud", 0) for i in insights)
    avg_confidence = (
        sum(dict(i).get("confidence", 0) for i in insights) / len(insights)
    ) if insights else 0

    return {
        "agents": DATA_INTELLIGENCE_AGENTS,
        "categories": DATA_INTEL_CATEGORIES,
        "insights": [dict(i) for i in insights],
        "summary": {
            "total_agents": len(DATA_INTELLIGENCE_AGENTS),
            "total_insights": len(insights),
            "total_impact": total_impact,
            "avg_confidence": round(avg_confidence, 2),
        },
        "category_stats": category_stats,
    }


def _agent_to_category(agent_id):
    """Map data intelligence agent_id to category."""
    mapping = {
        "di_lost_sales": "lost_sales",
        "di_overorder": "waste_prevention",
        "di_buying": "margin_improvement",
        "di_range": "range_optimisation",
        "di_stocktake": "shrinkage_reduction",
        "di_transactions": "cross_sell",
    }
    return mapping.get(agent_id, "other")


# ============================================================================
# WATCHDOG SAFETY SYSTEM API
# ============================================================================

@app.get("/api/watchdog/status")
async def watchdog_status():
    """Return WATCHDOG system status and metrics."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "dashboards"))
    from shared.watchdog_safety import get_system_status

    conn = sqlite3.connect(config.HUB_DB)
    conn.row_factory = sqlite3.Row

    # Count proposals by status
    total = conn.execute(
        "SELECT COUNT(*) FROM watchdog_proposals"
    ).fetchone()[0]
    pending = conn.execute(
        "SELECT COUNT(*) FROM watchdog_proposals WHERE status = 'pending_review'"
    ).fetchone()[0]
    approved = conn.execute(
        "SELECT COUNT(*) FROM watchdog_proposals WHERE status = 'approved'"
    ).fetchone()[0]
    rejected = conn.execute(
        "SELECT COUNT(*) FROM watchdog_proposals WHERE status = 'rejected'"
    ).fetchone()[0]
    blocked = conn.execute(
        "SELECT COUNT(*) FROM watchdog_proposals WHERE risk_level = 'BLOCKED'"
    ).fetchone()[0]

    # Risk distribution
    risk_dist = conn.execute(
        "SELECT risk_level, COUNT(*) AS cnt FROM watchdog_proposals "
        "GROUP BY risk_level"
    ).fetchall()

    conn.close()

    return {
        "system": get_system_status(),
        "metrics": {
            "total_proposals": total,
            "pending_review": pending,
            "approved": approved,
            "rejected": rejected,
            "blocked_by_watchdog": blocked,
        },
        "risk_distribution": {
            r["risk_level"]: r["cnt"] for r in risk_dist
        },
    }


@app.post("/api/watchdog/analyze")
async def watchdog_analyze(request: Request):
    """Submit a proposal for WATCHDOG safety analysis.

    This is the MANDATORY first step before any agent action.
    """
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "dashboards"))
    from shared.watchdog_safety import WatchdogService

    data = await request.json()
    if not data.get("title"):
        raise HTTPException(status_code=400, detail="title is required")
    if not data.get("agent_id"):
        raise HTTPException(status_code=400, detail="agent_id is required")

    watchdog = WatchdogService(db_path=config.HUB_DB)
    result = watchdog.analyze_proposal(data)

    # Store in watchdog_proposals for the review queue
    conn = sqlite3.connect(config.HUB_DB)
    conn.execute(
        "INSERT INTO watchdog_proposals "
        "(tracking_id, source_proposal_id, agent_id, title, description, "
        "proposal_json, risk_level, finding_count, report, recommendation, "
        "status) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (
            result["tracking_id"],
            data.get("source_proposal_id"),
            result["agent_id"],
            result["title"],
            data.get("description", ""),
            json.dumps(data),
            result["risk_level"],
            result["finding_count"],
            result["report"],
            json.dumps(result["recommendation"]),
            "blocked" if result["blocked"] else "pending_review",
        ),
    )
    conn.commit()
    conn.close()

    return {
        "ok": True,
        "tracking_id": result["tracking_id"],
        "risk_level": result["risk_level"],
        "risk_icon": result["risk_icon"],
        "finding_count": result["finding_count"],
        "recommendation": result["recommendation"],
        "blocked": result["blocked"],
        "report": result["report"],
    }


@app.get("/api/watchdog/pending")
async def watchdog_pending():
    """Return all proposals awaiting human review."""
    conn = sqlite3.connect(config.HUB_DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, tracking_id, agent_id, title, description, "
        "risk_level, finding_count, recommendation, status, created_at "
        "FROM watchdog_proposals WHERE status = 'pending_review' "
        "ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return {"pending": [dict(r) for r in rows]}


@app.get("/api/watchdog/proposals")
async def watchdog_all_proposals(
    status: str = None,
    risk_level: str = None,
    limit: int = 50,
):
    """List all WATCHDOG-reviewed proposals."""
    conn = sqlite3.connect(config.HUB_DB)
    conn.row_factory = sqlite3.Row

    query = "SELECT * FROM watchdog_proposals WHERE 1=1"
    params = []
    if status:
        query += " AND status = ?"
        params.append(status)
    if risk_level:
        query += " AND risk_level = ?"
        params.append(risk_level)
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return {"proposals": [dict(r) for r in rows]}


@app.get("/api/watchdog/proposals/{tracking_id}")
async def watchdog_proposal_detail(tracking_id: str):
    """Return full WATCHDOG report for a proposal."""
    conn = sqlite3.connect(config.HUB_DB)
    conn.row_factory = sqlite3.Row

    proposal = conn.execute(
        "SELECT * FROM watchdog_proposals WHERE tracking_id = ?",
        (tracking_id,),
    ).fetchone()
    if not proposal:
        conn.close()
        raise HTTPException(status_code=404, detail="Proposal not found")

    decisions = conn.execute(
        "SELECT * FROM watchdog_decisions WHERE tracking_id = ? "
        "ORDER BY decided_at DESC",
        (tracking_id,),
    ).fetchall()

    audit = conn.execute(
        "SELECT * FROM watchdog_audit WHERE tracking_id = ?",
        (tracking_id,),
    ).fetchall()

    conn.close()
    return {
        "proposal": dict(proposal),
        "decisions": [dict(d) for d in decisions],
        "audit": [dict(a) for a in audit],
    }


@app.post("/api/watchdog/approve")
async def watchdog_approve(request: Request):
    """Approve a proposal after WATCHDOG review.

    Requires: tracking_id, approver
    Optional: comments
    """
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "dashboards"))
    from shared.watchdog_safety import WatchdogService

    data = await request.json()
    tracking_id = data.get("tracking_id")
    approver = data.get("approver")
    comments = data.get("comments", "")

    if not tracking_id or not approver:
        raise HTTPException(
            status_code=400,
            detail="tracking_id and approver are required")

    # Verify proposal exists and isn't blocked
    conn = sqlite3.connect(config.HUB_DB)
    conn.row_factory = sqlite3.Row
    proposal = conn.execute(
        "SELECT * FROM watchdog_proposals WHERE tracking_id = ?",
        (tracking_id,),
    ).fetchone()

    if not proposal:
        conn.close()
        raise HTTPException(status_code=404, detail="Proposal not found")

    if dict(proposal)["risk_level"] == "BLOCKED":
        conn.close()
        raise HTTPException(
            status_code=403,
            detail="BLOCKED proposals cannot be approved")

    # Record decision
    watchdog = WatchdogService(db_path=config.HUB_DB)
    watchdog.log_decision(tracking_id, "approved", approver, comments)

    # Also update the linked arena proposal status to 'submitted'
    source_id = dict(proposal).get("source_proposal_id")
    if source_id:
        conn2 = sqlite3.connect(config.HUB_DB)
        conn2.execute(
            "UPDATE arena_proposals SET status = 'submitted' "
            "WHERE id = ? AND status = 'pending_review'",
            (source_id,),
        )
        conn2.commit()
        conn2.close()

    conn.close()
    return {"ok": True, "tracking_id": tracking_id, "decision": "approved"}


@app.post("/api/watchdog/reject")
async def watchdog_reject(request: Request):
    """Reject a proposal after WATCHDOG review."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "dashboards"))
    from shared.watchdog_safety import WatchdogService

    data = await request.json()
    tracking_id = data.get("tracking_id")
    approver = data.get("approver")
    comments = data.get("comments", "")

    if not tracking_id or not approver:
        raise HTTPException(
            status_code=400,
            detail="tracking_id and approver are required")

    # Look up the proposal to find linked arena proposal
    conn = sqlite3.connect(config.HUB_DB)
    conn.row_factory = sqlite3.Row
    proposal = conn.execute(
        "SELECT * FROM watchdog_proposals WHERE tracking_id = ?",
        (tracking_id,),
    ).fetchone()

    watchdog = WatchdogService(db_path=config.HUB_DB)
    watchdog.log_decision(tracking_id, "rejected", approver, comments)

    # Also update the linked arena proposal status to 'rejected'
    if proposal:
        source_id = dict(proposal).get("source_proposal_id")
        if source_id:
            conn.execute(
                "UPDATE arena_proposals SET status = 'rejected' "
                "WHERE id = ? AND status IN ('pending_review', 'blocked')",
                (source_id,),
            )
            conn.commit()
    conn.close()

    return {"ok": True, "tracking_id": tracking_id, "decision": "rejected"}


@app.get("/api/watchdog/audit")
async def watchdog_audit_trail(limit: int = 100):
    """Return WATCHDOG audit trail."""
    conn = sqlite3.connect(config.HUB_DB)
    conn.row_factory = sqlite3.Row

    audits = conn.execute(
        "SELECT * FROM watchdog_audit ORDER BY analyzed_at DESC LIMIT ?",
        (limit,),
    ).fetchall()

    decisions = conn.execute(
        "SELECT * FROM watchdog_decisions ORDER BY decided_at DESC LIMIT ?",
        (limit,),
    ).fetchall()

    conn.close()
    return {
        "audits": [dict(a) for a in audits],
        "decisions": [dict(d) for d in decisions],
    }


@app.get("/api/watchdog/scheduler/status")
async def watchdog_scheduler_status():
    """Return WATCHDOG background scheduler status."""
    if not hasattr(app.state, "watchdog"):
        return {"running": False, "message": "Scheduler not initialized"}
    return app.state.watchdog.status()


@app.post("/api/watchdog/scheduler/run")
async def watchdog_scheduler_trigger():
    """Trigger an immediate WATCHDOG cycle (admin)."""
    if not hasattr(app.state, "watchdog"):
        raise HTTPException(status_code=503, detail="Scheduler not initialized")
    import threading
    t = threading.Thread(target=app.state.watchdog._run_cycle, daemon=True)
    t.start()
    return {"triggered": True, "message": "WATCHDOG cycle started"}


# ---------------------------------------------------------------------------
# INTELLIGENCE / DATA ANALYSIS ENDPOINTS
# ---------------------------------------------------------------------------

VALID_ANALYSIS_TYPES = [
    "basket_analysis", "stockout_detection", "price_dispersion",
    "demand_pattern", "slow_movers", "intraday_stockout",
    "halo_effect", "specials_uplift",
    "margin_analysis", "customer_analysis", "store_benchmark",
]


@app.post("/api/intelligence/run/{analysis_type}")
async def intelligence_run(analysis_type: str, request: Request):
    """Run a real data analysis, score it with the rubric, and store the result."""
    if analysis_type not in VALID_ANALYSIS_TYPES:
        raise HTTPException(status_code=400, detail="Invalid analysis_type. "
                            "Valid: {}".format(", ".join(VALID_ANALYSIS_TYPES)))

    body = {}
    try:
        body = await request.json()
    except Exception:
        pass

    store_id = body.get("store_id")
    days = body.get("days", 30)
    params = {"store_id": store_id, "days": days}

    from data_analysis import (
        run_basket_analysis, run_stockout_detection, run_price_dispersion,
        run_demand_pattern, run_slow_movers, run_intraday_stockout,
        run_halo_effect, run_specials_uplift,
        run_margin_analysis, run_customer_analysis, run_store_benchmark,
        ANALYSIS_TYPES,
    )
    from report_generator import generate_markdown_report
    from presentation_rubric import evaluate_report

    runners = {
        "basket_analysis": run_basket_analysis,
        "stockout_detection": run_stockout_detection,
        "price_dispersion": run_price_dispersion,
        "demand_pattern": run_demand_pattern,
        "slow_movers": run_slow_movers,
        "intraday_stockout": run_intraday_stockout,
        "halo_effect": run_halo_effect,
        "specials_uplift": run_specials_uplift,
        "margin_analysis": run_margin_analysis,
        "customer_analysis": run_customer_analysis,
        "store_benchmark": run_store_benchmark,
    }

    runner = runners[analysis_type]

    # Build kwargs based on analysis type
    kwargs = {}
    if analysis_type in ("basket_analysis", "stockout_detection",
                         "demand_pattern", "slow_movers",
                         "intraday_stockout", "halo_effect",
                         "specials_uplift",
                         "margin_analysis", "customer_analysis"):
        if store_id:
            kwargs["store_id"] = store_id
        kwargs["days"] = days
    elif analysis_type in ("price_dispersion", "store_benchmark"):
        kwargs["days"] = days

    if "min_support" in body:
        kwargs["min_support"] = body["min_support"]
    if "min_velocity" in body:
        kwargs["min_velocity"] = body["min_velocity"]
    if "threshold" in body:
        kwargs["threshold"] = body["threshold"]
    if "limit" in body:
        kwargs["limit"] = body["limit"]
    if "min_baskets" in body:
        kwargs["min_baskets"] = body["min_baskets"]
    if "min_special_days" in body:
        kwargs["min_special_days"] = body["min_special_days"]
    if "discount_threshold" in body:
        kwargs["discount_threshold"] = body["discount_threshold"]
    if "gp_threshold" in body:
        kwargs["gp_threshold"] = body["gp_threshold"]

    try:
        result = runner(**kwargs)
    except Exception as e:
        logger.error("Intelligence analysis %s failed: %s", analysis_type, e)
        raise HTTPException(status_code=500,
                            detail="Analysis failed: {}".format(str(e)[:200]))

    # Score with rubric
    rubric = evaluate_report(result)

    # Store in database
    conn = sqlite3.connect(config.HUB_DB)
    agent_id = ANALYSIS_TYPES.get(analysis_type, {}).get("agent_id", "")
    conn.execute(
        "INSERT INTO intelligence_reports "
        "(analysis_type, agent_id, title, status, report_json, "
        "rubric_scores_json, rubric_grade, rubric_average, store_id, "
        "parameters_json) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (
            analysis_type,
            agent_id,
            result.get("title", ""),
            "completed",
            json.dumps(result, default=str),
            json.dumps(rubric, default=str),
            rubric.get("grade", "Draft"),
            rubric.get("average", 0),
            store_id,
            json.dumps(params, default=str),
        ),
    )
    report_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.commit()
    conn.close()

    return {
        "id": report_id,
        "analysis_type": analysis_type,
        "title": result.get("title", ""),
        "executive_summary": result.get("executive_summary", ""),
        "evidence_tables": result.get("evidence_tables", []),
        "financial_impact": result.get("financial_impact", {}),
        "recommendations": result.get("recommendations", []),
        "methodology": result.get("methodology", {}),
        "confidence_level": result.get("confidence_level", 0),
        "rubric": rubric,
        "generated_at": result.get("generated_at", ""),
    }


@app.get("/api/intelligence/reports")
async def intelligence_list(analysis_type: str = None, limit: int = 50):
    """List stored intelligence reports."""
    conn = sqlite3.connect(config.HUB_DB)
    conn.row_factory = sqlite3.Row

    if analysis_type:
        rows = conn.execute(
            "SELECT id, analysis_type, agent_id, title, status, "
            "rubric_grade, rubric_average, store_id, created_at "
            "FROM intelligence_reports WHERE analysis_type = ? "
            "ORDER BY created_at DESC LIMIT ?",
            (analysis_type, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, analysis_type, agent_id, title, status, "
            "rubric_grade, rubric_average, store_id, created_at "
            "FROM intelligence_reports "
            "ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()

    conn.close()
    return {"reports": [dict(r) for r in rows]}


@app.get("/api/intelligence/reports/{report_id}")
async def intelligence_detail(report_id: int):
    """Get full intelligence report with evidence and rubric."""
    conn = sqlite3.connect(config.HUB_DB)
    conn.row_factory = sqlite3.Row

    row = conn.execute(
        "SELECT * FROM intelligence_reports WHERE id = ?",
        (report_id,),
    ).fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Report not found")

    row_dict = dict(row)
    row_dict["report"] = json.loads(row_dict.pop("report_json", "{}"))
    row_dict["rubric_scores"] = json.loads(
        row_dict.pop("rubric_scores_json", "{}"))
    row_dict["parameters"] = json.loads(
        row_dict.pop("parameters_json", "{}"))

    return row_dict


@app.get("/api/intelligence/export/{report_id}/{fmt}")
async def intelligence_export(report_id: int, fmt: str):
    """Export an intelligence report in the specified format."""
    from starlette.responses import Response

    if fmt not in ("html", "csv", "json", "markdown"):
        raise HTTPException(status_code=400,
                            detail="Format must be one of: html, csv, json, markdown")

    conn = sqlite3.connect(config.HUB_DB)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT report_json FROM intelligence_reports WHERE id = ?",
        (report_id,),
    ).fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Report not found")

    result = json.loads(row["report_json"])

    from report_generator import (
        generate_markdown_report, generate_html_report,
        generate_csv_export, generate_json_export,
    )

    if fmt == "markdown":
        content = generate_markdown_report(result)
        return Response(content=content, media_type="text/markdown",
                        headers={"Content-Disposition":
                                 "attachment; filename=report_{}.md".format(report_id)})
    elif fmt == "html":
        content = generate_html_report(result)
        return Response(content=content, media_type="text/html",
                        headers={"Content-Disposition":
                                 "attachment; filename=report_{}.html".format(report_id)})
    elif fmt == "csv":
        content = generate_csv_export(result)
        return Response(content=content, media_type="text/csv",
                        headers={"Content-Disposition":
                                 "attachment; filename=report_{}.csv".format(report_id)})
    elif fmt == "json":
        content = generate_json_export(result)
        return Response(content=content, media_type="application/json",
                        headers={"Content-Disposition":
                                 "attachment; filename=report_{}.json".format(report_id)})


# ---------------------------------------------------------------------------
# AGENT TASKS — On-demand execution from natural language
# ---------------------------------------------------------------------------

class AgentTaskRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=500)
    store_id: Optional[str] = None
    days: int = Field(default=30, ge=7, le=90)


@app.post("/api/agent-tasks")
async def agent_task_create(req: AgentTaskRequest):
    """Accept NL query, route it, execute matched analyses, score, WATCHDOG review."""
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).parent.parent / "dashboards"))

    from agent_router import route_query
    from data_analysis import (
        run_basket_analysis, run_stockout_detection, run_price_dispersion,
        run_demand_pattern, run_slow_movers, run_intraday_stockout,
        ANALYSIS_TYPES as AT_REGISTRY,
    )
    from presentation_rubric import evaluate_report
    from shared.watchdog_safety import WatchdogService

    runners = {
        "basket_analysis": run_basket_analysis,
        "stockout_detection": run_stockout_detection,
        "price_dispersion": run_price_dispersion,
        "demand_pattern": run_demand_pattern,
        "slow_movers": run_slow_movers,
        "intraday_stockout": run_intraday_stockout,
    }

    # Step 1: Route the query
    routing = route_query(req.query)
    matched = routing["matched_analyses"]

    # Step 2: Create task record (status=running)
    conn = sqlite3.connect(config.HUB_DB)
    conn.execute(
        "INSERT INTO agent_tasks (user_query, status, matched_analyses, "
        "routing_confidence, routing_reasoning) VALUES (?,?,?,?,?)",
        (req.query, "running", json.dumps(matched),
         routing["confidence"], routing["reasoning"]),
    )
    task_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.commit()

    # Step 3: Execute each matched analysis
    report_ids = []
    errors = []

    for analysis_type in matched:
        runner = runners.get(analysis_type)
        if not runner:
            errors.append("Unknown analysis: {}".format(analysis_type))
            continue

        kwargs = {"days": req.days}
        if analysis_type != "price_dispersion" and req.store_id:
            kwargs["store_id"] = req.store_id

        try:
            result = runner(**kwargs)
        except Exception as e:
            errors.append("{}: {}".format(analysis_type, str(e)[:100]))
            continue

        # Score with rubric
        rubric = evaluate_report(result)

        # Store in intelligence_reports
        agent_id = AT_REGISTRY.get(analysis_type, {}).get("agent_id", "")
        conn.execute(
            "INSERT INTO intelligence_reports "
            "(analysis_type, agent_id, title, status, report_json, "
            "rubric_scores_json, rubric_grade, rubric_average, store_id, "
            "parameters_json) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                analysis_type, agent_id,
                result.get("title", ""),
                "completed",
                json.dumps(result, default=str),
                json.dumps(rubric, default=str),
                rubric.get("grade", "Draft"),
                rubric.get("average", 0),
                req.store_id,
                json.dumps({"days": req.days, "store_id": req.store_id},
                           default=str),
            ),
        )
        rpt_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.commit()

        report_ids.append({
            "id": rpt_id,
            "analysis_type": analysis_type,
            "title": result.get("title", ""),
            "grade": rubric.get("grade", "Draft"),
            "average": rubric.get("average", 0),
            "executive_summary": result.get("executive_summary", ""),
            "evidence_tables": result.get("evidence_tables", []),
            "financial_impact": result.get("financial_impact", {}),
            "recommendations": result.get("recommendations", []),
            "rubric": rubric,
        })

    # Step 4: WATCHDOG safety review
    watchdog = WatchdogService(db_path=config.HUB_DB)
    proposal = {
        "agent_id": "agent_task_executor",
        "proposal_type": "analysis_report",
        "title": "Agent Task: {}".format(req.query[:80]),
        "description": "Auto-executed analyses: {}. {} reports generated.".format(
            ", ".join(matched), len(report_ids)),
        "expected_impact": "Read-only analysis of transaction data",
    }
    wd_result = watchdog.analyze_proposal(proposal)

    # Step 5: Update task record
    status = "completed" if report_ids else "failed"
    error_msg = "; ".join(errors) if errors else None

    conn.execute(
        "UPDATE agent_tasks SET status = ?, results_json = ?, "
        "watchdog_status = ?, watchdog_report_json = ?, "
        "error_message = ?, completed_at = datetime('now') "
        "WHERE id = ?",
        (
            status,
            json.dumps([r["id"] for r in report_ids]),
            wd_result.get("risk_level", "SAFE"),
            json.dumps(wd_result, default=str),
            error_msg,
            task_id,
        ),
    )
    conn.commit()
    conn.close()

    return {
        "task_id": task_id,
        "status": status,
        "routing": routing,
        "reports": report_ids,
        "watchdog": {
            "risk_level": wd_result.get("risk_level", "SAFE"),
            "risk_icon": wd_result.get("risk_icon", ""),
            "finding_count": wd_result.get("finding_count", 0),
            "recommendation": wd_result.get("recommendation", {}),
        },
        "errors": errors,
    }


@app.get("/api/agent-tasks")
async def agent_task_list(limit: int = 20):
    """List recent agent tasks with status."""
    conn = sqlite3.connect(config.HUB_DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, user_query, status, matched_analyses, "
        "routing_confidence, watchdog_status, error_message, "
        "created_at, completed_at "
        "FROM agent_tasks ORDER BY created_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return {"tasks": [dict(r) for r in rows]}


@app.get("/api/agent-tasks/{task_id}")
async def agent_task_detail(task_id: int):
    """Full task detail with all report data."""
    conn = sqlite3.connect(config.HUB_DB)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM agent_tasks WHERE id = ?", (task_id,)
    ).fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Task not found")

    task = dict(row)
    task["matched_analyses"] = json.loads(
        task.get("matched_analyses") or "[]")
    task["results_json"] = json.loads(task.get("results_json") or "[]")
    task["watchdog_report_json"] = json.loads(
        task.get("watchdog_report_json") or "{}")
    return task


# ============================================================================
# SELF-IMPROVEMENT ENGINE ENDPOINTS
# ============================================================================

@app.get("/api/self-improvement/status")
async def self_improvement_status():
    """Full self-improvement loop status: averages, weakest criterion,
    attempt counts, recommendations."""
    from self_improvement import get_improvement_status
    return get_improvement_status()


@app.get("/api/self-improvement/history")
async def self_improvement_history(limit: int = 20):
    """Improvement cycle history and score trends."""
    from self_improvement import get_improvement_history, get_score_trends
    return {
        "cycles": get_improvement_history(limit),
        "score_trends": get_score_trends(limit),
    }


@app.post("/api/self-improvement/record-scores")
async def record_task_scores(request: Request):
    """Record H/R/S/C/D/U/X scores for a completed task."""
    body = await request.json()
    task_name = body.get("task_name", "")
    if not task_name:
        raise HTTPException(status_code=422, detail="task_name required")

    scores = {}
    for c in ["H", "R", "S", "C", "D", "U", "X"]:
        val = body.get(c, body.get(c.lower(), 0))
        if not isinstance(val, (int, float)) or val < 0 or val > 10:
            raise HTTPException(
                status_code=422,
                detail="{} must be 0-10".format(c),
            )
        scores[c] = int(val)

    from self_improvement import store_task_scores
    return store_task_scores(task_name, scores)


@app.post("/api/self-improvement/record-cycle")
async def record_improvement_cycle_endpoint(request: Request):
    """Record an improvement attempt (success or failure)."""
    body = await request.json()
    criterion = body.get("criterion", "")
    if criterion not in ["H", "R", "S", "C", "D", "U", "X"]:
        raise HTTPException(
            status_code=422,
            detail="criterion must be one of H/R/S/C/D/U/X",
        )
    before = body.get("before_score", 0)
    after = body.get("after_score", 0)
    action = body.get("action", "")
    success = body.get("success", False)

    if not action:
        raise HTTPException(status_code=422, detail="action required")

    from self_improvement import record_improvement_cycle
    return record_improvement_cycle(criterion, before, after, action, success)


@app.post("/api/self-improvement/backfill")
async def backfill_scores():
    """One-time backfill: parse audit.log scores into task_scores table."""
    from self_improvement import backfill_scores_from_audit
    inserted = backfill_scores_from_audit()
    return {"status": "completed", "rows_inserted": inserted}


# ============================================================================
# PAGE QUALITY SCORING ENDPOINTS
# ============================================================================

@app.post("/api/page-quality/score")
async def submit_page_quality_score(request: Request):
    """Submit a page quality score against dashboard or content rubric."""
    body = await request.json()
    page_name = body.get("page_name", "")
    rubric_type = body.get("rubric_type", "")
    scorer = body.get("scorer", "anonymous")
    scores = body.get("scores", {})

    if not page_name or rubric_type not in ("dashboard", "content"):
        raise HTTPException(
            status_code=422,
            detail="page_name and rubric_type ('dashboard' or 'content') required",
        )

    import json as _json
    total = sum(scores.values())
    max_score = 35 if rubric_type == "dashboard" else 25

    conn = sqlite3.connect(config.HUB_DB)
    conn.execute(
        "INSERT INTO page_quality_scores "
        "(page_name, rubric_type, scorer, scores_json, total_score, max_score) "
        "VALUES (?,?,?,?,?,?)",
        (page_name, rubric_type, scorer, _json.dumps(scores), total, max_score),
    )
    conn.commit()
    conn.close()
    return {"stored": True, "total": total, "max": max_score,
            "pct": round(total / max_score * 100, 1) if max_score else 0}


@app.get("/api/page-quality/scores")
async def page_quality_scores(page_name: str = "", limit: int = 20):
    """Get page quality score history, optionally filtered by page."""
    conn = sqlite3.connect(config.HUB_DB)
    conn.row_factory = sqlite3.Row
    if page_name:
        rows = conn.execute(
            "SELECT * FROM page_quality_scores WHERE page_name = ? "
            "ORDER BY id DESC LIMIT ?", (page_name, limit)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM page_quality_scores ORDER BY id DESC LIMIT ?",
            (limit,)
        ).fetchall()
    conn.close()

    import json as _json
    results = []
    for r in [dict(row) for row in rows]:
        r["scores"] = _json.loads(r.pop("scores_json", "{}"))
        results.append(r)
    return results


# ============================================================================
# CONTINUOUS IMPROVEMENT ENDPOINTS
# ============================================================================

@app.post("/api/continuous-improvement/audit")
async def ci_run_audit():
    """Run full continuous improvement audit across safety, docs, performance."""
    from continuous_improvement import run_full_audit
    result = run_full_audit(db_path=config.HUB_DB)
    # Return summary without full findings list for brevity
    return {
        "timestamp": result["timestamp"],
        "findings_count": result["findings_count"],
        "new_findings": result["new_findings"],
        "by_category": result["by_category"],
        "by_severity": result["by_severity"],
        "health_metrics": result["health_metrics"],
    }


@app.get("/api/continuous-improvement/metrics")
async def ci_health_metrics():
    """Quick health metrics (no audit scan)."""
    from continuous_improvement import HealthMetricsCollector
    collector = HealthMetricsCollector()
    return collector.collect()


@app.get("/api/continuous-improvement/findings")
async def ci_list_findings(status: Optional[str] = None,
                           category: Optional[str] = None,
                           limit: int = 50):
    """List improvement findings with optional filters."""
    from continuous_improvement import FindingsManager
    manager = FindingsManager(db_path=config.HUB_DB)
    findings = manager.get_findings(status=status, category=category,
                                    limit=limit)
    return {"findings": findings, "count": len(findings)}


@app.post("/api/continuous-improvement/findings/{finding_id}/status")
async def ci_update_finding_status(finding_id: int, request: Request):
    """Update a finding's status (open -> acknowledged -> resolved | promoted)."""
    body = await request.json()
    new_status = body.get("status", "")
    if not new_status:
        raise HTTPException(status_code=422, detail="status required")

    from continuous_improvement import FindingsManager
    manager = FindingsManager(db_path=config.HUB_DB)

    if new_status == "promoted":
        return manager.promote_to_proposal(finding_id)
    return manager.update_status(finding_id, new_status)


# ============================================================================
# GAMIFIED AGENT ECOSYSTEM ENDPOINTS
# ============================================================================

@app.get("/api/game/leaderboard")
async def game_leaderboard():
    """Ranked list of all 6 game agents with stats."""
    from agent_game import get_game_leaderboard
    agents = get_game_leaderboard(config.HUB_DB)
    return {"agents": agents, "count": len(agents)}


@app.get("/api/game/agents/{name}")
async def game_agent_detail(name: str):
    """Full stats for a single game agent."""
    from agent_game import get_agent_game_detail
    detail = get_agent_game_detail(config.HUB_DB, name)
    if not detail:
        raise HTTPException(status_code=404, detail="Agent not found")
    return detail


@app.post("/api/game/seed")
async def game_seed():
    """Seed 6 game agents and 18 initial tasks.  Idempotent."""
    from agent_game import seed_game_agents, seed_initial_tasks
    agents_inserted = seed_game_agents(config.HUB_DB)
    tasks_inserted = seed_initial_tasks(config.HUB_DB)
    return {
        "success": True,
        "agents_inserted": agents_inserted,
        "tasks_inserted": tasks_inserted,
    }


@app.get("/api/game/achievements")
async def game_achievements():
    """All achievements earned across all agents."""
    from agent_game import get_all_achievements
    achievements = get_all_achievements(config.HUB_DB)
    return {"achievements": achievements, "count": len(achievements)}


@app.get("/api/game/status")
async def game_status():
    """Aggregate game statistics."""
    from agent_game import get_game_status
    return get_game_status(config.HUB_DB)


# ============================================================================
# AGENT CONTROL PANEL ENDPOINTS
# ============================================================================

@app.get("/api/admin/agent-proposals")
async def list_agent_proposals(status: Optional[str] = None, limit: int = 50):
    """List agent proposals, optionally filtered by status."""
    conn = sqlite3.connect(config.HUB_DB)
    conn.row_factory = sqlite3.Row
    if status:
        rows = conn.execute(
            "SELECT * FROM agent_proposals WHERE status = ? "
            "ORDER BY CASE risk_level WHEN 'HIGH' THEN 1 "
            "WHEN 'MEDIUM' THEN 2 WHEN 'LOW' THEN 3 END, "
            "created_at ASC LIMIT ?",
            (status.upper(), limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM agent_proposals ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    conn.close()
    return {"proposals": [dict(r) for r in rows]}


@app.post("/api/admin/agent-proposals/{proposal_id}/approve")
async def approve_agent_proposal(proposal_id: int, request: Request):
    """Approve an agent proposal for execution."""
    body = await request.json()
    notes = body.get("notes", "")
    reviewer = body.get("reviewer", "Gus Harris")

    conn = sqlite3.connect(config.HUB_DB)
    row = conn.execute(
        "SELECT id, status FROM agent_proposals WHERE id = ?",
        (proposal_id,),
    ).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Proposal not found")
    if row[1] != "PENDING":
        conn.close()
        raise HTTPException(
            status_code=400,
            detail="Only PENDING proposals can be approved (current: {})".format(row[1]),
        )

    conn.execute(
        "UPDATE agent_proposals SET status = 'APPROVED', "
        "reviewed_at = ?, reviewer = ?, reviewer_notes = ? WHERE id = ?",
        (datetime.now().isoformat(), reviewer, notes, proposal_id),
    )
    conn.commit()
    conn.close()
    return {"success": True, "message": "Proposal approved and queued for execution"}


@app.post("/api/admin/agent-proposals/{proposal_id}/reject")
async def reject_agent_proposal(proposal_id: int, request: Request):
    """Reject an agent proposal."""
    body = await request.json()
    notes = body.get("notes", "")
    reviewer = body.get("reviewer", "Gus Harris")

    if not notes:
        raise HTTPException(status_code=422, detail="Rejection requires notes")

    conn = sqlite3.connect(config.HUB_DB)
    row = conn.execute(
        "SELECT id, status FROM agent_proposals WHERE id = ?",
        (proposal_id,),
    ).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Proposal not found")
    if row[1] != "PENDING":
        conn.close()
        raise HTTPException(
            status_code=400,
            detail="Only PENDING proposals can be rejected (current: {})".format(row[1]),
        )

    conn.execute(
        "UPDATE agent_proposals SET status = 'REJECTED', "
        "reviewed_at = ?, reviewer = ?, reviewer_notes = ? WHERE id = ?",
        (datetime.now().isoformat(), reviewer, notes, proposal_id),
    )
    conn.commit()
    conn.close()
    return {"success": True, "message": "Proposal rejected"}


@app.get("/api/admin/agent-scores")
async def list_agent_scores(agent_name: Optional[str] = None, days: int = 30):
    """Get agent performance scores."""
    conn = sqlite3.connect(config.HUB_DB)
    conn.row_factory = sqlite3.Row

    if agent_name:
        rows = conn.execute(
            "SELECT * FROM agent_scores WHERE agent_name = ? "
            "AND timestamp > datetime('now', '-' || ? || ' days') "
            "ORDER BY timestamp DESC",
            (agent_name, days),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM agent_scores "
            "WHERE timestamp > datetime('now', '-' || ? || ' days') "
            "ORDER BY timestamp DESC",
            (days,),
        ).fetchall()

    # Also compute per-agent averages
    avg_rows = conn.execute(
        "SELECT agent_name, AVG(score) as avg_score, COUNT(*) as measurements "
        "FROM agent_scores "
        "WHERE timestamp > datetime('now', '-' || ? || ' days') "
        "GROUP BY agent_name ORDER BY avg_score DESC",
        (days,),
    ).fetchall()

    conn.close()
    return {
        "scores": [dict(r) for r in rows],
        "agent_averages": [dict(r) for r in avg_rows],
    }


@app.post("/api/admin/agent-scores")
async def record_agent_score(request: Request):
    """Record a performance score for an agent."""
    body = await request.json()
    agent_name = body.get("agent_name", "")
    metric = body.get("metric", "")
    score = body.get("score", 0)
    evidence = body.get("evidence", "")

    if not agent_name or not metric:
        raise HTTPException(status_code=422, detail="agent_name and metric required")
    if not isinstance(score, (int, float)) or score < 0 or score > 10:
        raise HTTPException(status_code=422, detail="score must be 0-10")

    valid_metrics = ["ACCURACY", "SPEED", "INSIGHT_QUALITY", "USER_SATISFACTION"]
    if metric.upper() not in valid_metrics:
        raise HTTPException(
            status_code=422,
            detail="metric must be one of: {}".format(", ".join(valid_metrics)),
        )

    conn = sqlite3.connect(config.HUB_DB)
    # Get previous score as baseline
    prev = conn.execute(
        "SELECT score FROM agent_scores WHERE agent_name = ? AND metric = ? "
        "ORDER BY timestamp DESC LIMIT 1",
        (agent_name, metric.upper()),
    ).fetchone()
    baseline = prev[0] if prev else None

    conn.execute(
        "INSERT INTO agent_scores (agent_name, metric, score, baseline, evidence) "
        "VALUES (?,?,?,?,?)",
        (agent_name, metric.upper(), score, baseline, evidence),
    )
    conn.commit()
    conn.close()
    return {"success": True, "agent_name": agent_name, "metric": metric.upper(),
            "score": score, "baseline": baseline}


@app.post("/api/admin/trigger-analysis")
async def trigger_analysis_cycle(request: Request):
    """Trigger a new analysis/improvement cycle — creates pending proposals."""
    body = await request.json() if request.headers.get("content-type") == "application/json" else {}
    cycle_type = body.get("type", "all")

    conn = sqlite3.connect(config.HUB_DB)
    c = conn.cursor()
    created = []

    if cycle_type in ("all", "analysis"):
        analysis_tasks = [
            ("StockoutAnalyzer", "ANALYSIS",
             "Scheduled: Analyse intra-day stockouts across all stores (last 14 days)",
             "LOW", "Lost revenue recovery"),
            ("BasketAnalyzer", "ANALYSIS",
             "Scheduled: Cross-sell opportunity scan for top 200 SKUs",
             "LOW", "Incremental revenue"),
            ("DemandAnalyzer", "ANALYSIS",
             "Scheduled: Demand pattern analysis — peak/trough days and hours across network",
             "LOW", "Staffing and stock optimisation"),
            ("PriceAnalyzer", "ANALYSIS",
             "Scheduled: Price dispersion scan — identify pricing inconsistencies across stores",
             "LOW", "Margin recovery"),
            ("SlowMoverAnalyzer", "ANALYSIS",
             "Scheduled: Slow mover range review — flag underperforming SKUs for delisting",
             "LOW", "Range optimisation"),
            ("ReportGenerator", "REPORT",
             "Scheduled: Weekly executive demand summary for leadership review",
             "LOW", "Executive reporting"),
            ("HaloAnalyzer", "ANALYSIS",
             "Scheduled: Halo effect scan — identify products that grow basket value",
             "LOW", "Basket growth strategy"),
            ("SpecialsAnalyzer", "ANALYSIS",
             "Scheduled: Specials uplift forecast — predict demand multipliers for price drops",
             "LOW", "Promotional ordering optimisation"),
            ("MarginAnalyzer", "ANALYSIS",
             "Scheduled: Margin erosion scan — products with GP% below department average",
             "LOW", "Margin recovery"),
            ("CustomerAnalyzer", "ANALYSIS",
             "Scheduled: Customer segmentation — RFM analysis for retention targeting",
             "LOW", "Customer retention"),
            ("StoreBenchmarkAnalyzer", "ANALYSIS",
             "Scheduled: Store benchmark — rank all stores across revenue, basket, GP% KPIs",
             "LOW", "Performance benchmarking"),
        ]
        for agent, ttype, desc, risk, impact in analysis_tasks:
            c.execute(
                "INSERT INTO agent_proposals (agent_name, task_type, description, "
                "risk_level, estimated_impact) VALUES (?,?,?,?,?)",
                (agent, ttype, desc, risk, impact),
            )
            created.append("{}:{}".format(agent, ttype))

    if cycle_type in ("all", "improvement"):
        c.execute(
            "INSERT INTO agent_proposals (agent_name, task_type, description, risk_level, "
            "estimated_impact) VALUES (?,?,?,?,?)",
            ("SelfImprovementEngine", "IMPROVEMENT",
             "Scheduled: Review last 30 days performance, propose criterion optimisations",
             "MEDIUM", "Score improvement"),
        )
        created.append("SelfImprovementEngine:IMPROVEMENT")

    conn.commit()
    conn.close()
    return {"success": True, "message": "{} new tasks created".format(len(created)),
            "tasks": created}


@app.post("/api/admin/executor/run")
async def run_executor_once():
    """Execute all approved proposals immediately (single pass)."""
    from agent_executor import run_once
    count = run_once()
    return {"success": True, "executed": count,
            "message": "{} proposal(s) executed".format(count)}


@app.get("/api/admin/executor/status")
async def executor_status():
    """Summary of executor queue: approved, completed, failed counts."""
    conn = sqlite3.connect(config.HUB_DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT status, COUNT(*) as cnt FROM agent_proposals GROUP BY status"
    ).fetchall()
    counts = {r["status"]: r["cnt"] for r in rows}

    # Recent completions
    recent = conn.execute(
        "SELECT id, agent_name, task_type, execution_result, reviewed_at "
        "FROM agent_proposals WHERE status = 'COMPLETED' "
        "ORDER BY reviewed_at DESC LIMIT 5"
    ).fetchall()
    conn.close()

    return {
        "queue": counts,
        "approved_waiting": counts.get("APPROVED", 0),
        "completed_total": counts.get("COMPLETED", 0),
        "pending_total": counts.get("PENDING", 0),
        "recent_completions": [dict(r) for r in recent],
    }


# ============================================================================
# PROMPT-TO-APPROVAL SYSTEM ENDPOINTS
# ============================================================================


class PtaGenerateRequest(BaseModel):
    """Request to generate AI output from a structured prompt."""
    user_id: str = "staff"
    user_role: str = "Store Manager"
    task_type: str
    prompt_text: str
    context: Optional[str] = None
    data_sources: Optional[List[str]] = None
    analysis_types: Optional[List[str]] = None
    output_format: str = "Executive Summary"
    provider: str = "claude"


class PtaScoreRequest(BaseModel):
    """Request to score an AI output against the rubric."""
    submission_id: Optional[int] = None
    output_text: str
    task_type: Optional[str] = None
    user_role: Optional[str] = None


class PtaSubmitRequest(BaseModel):
    """Request to submit for approval."""
    submission_id: int
    human_annotations: Optional[List[str]] = None


@app.post("/api/pta/generate")
async def pta_generate(request: PtaGenerateRequest):
    """Generate AI analysis from a structured prompt and auto-score it."""

    # Build system prompt with role context
    system_prompt = (
        f"You are a senior business analyst at Harris Farm Markets, Australia's premium "
        f"fresh food retailer. You are producing a {request.output_format} for a "
        f"{request.user_role}.\n\n"
        f"Task type: {request.task_type}\n"
    )
    if request.data_sources:
        system_prompt += f"Data sources available: {', '.join(request.data_sources)}\n"
    if request.analysis_types:
        system_prompt += f"Analysis approach: {', '.join(request.analysis_types)}\n"
    if request.context:
        system_prompt += f"\nAdditional context: {request.context}\n"

    system_prompt += (
        "\n\nProvide a thorough, professional analysis. Use markdown formatting. "
        "Include specific numbers where possible. Be honest about limitations. "
        "End with clear, actionable recommendations with owners and timelines."
    )

    messages = [{"role": "user", "content": request.prompt_text}]

    # Call selected LLM
    provider_fn = {"claude": _chat_claude, "chatgpt": _chat_chatgpt, "grok": _chat_grok}
    fn = provider_fn.get(request.provider, _chat_claude)
    result = await fn(system_prompt, messages)

    if result["status"] == "error":
        return {
            "status": "error",
            "message": result["response"],
            "submission_id": None,
        }

    # Store submission in database
    now = datetime.now().isoformat()
    conn = sqlite3.connect(config.HUB_DB)
    c = conn.cursor()
    c.execute(
        """INSERT INTO pta_submissions
           (user_id, user_role, task_type, original_prompt, assembled_prompt,
            data_sources, context_text, analysis_types, output_format,
            ai_output, ai_provider, ai_tokens, ai_latency_ms, status, created_at, updated_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            request.user_id, request.user_role, request.task_type,
            request.prompt_text, system_prompt,
            json.dumps(request.data_sources or []),
            request.context,
            json.dumps(request.analysis_types or []),
            request.output_format,
            result["response"], result["provider"],
            result.get("tokens", 0), result.get("latency_ms", 0),
            "generated", now, now,
        ),
    )
    submission_id = c.lastrowid

    # Log the action
    c.execute(
        "INSERT INTO pta_audit_log (user_id, action, entity_type, entity_id, details, created_at) "
        "VALUES (?,?,?,?,?,?)",
        (request.user_id, "generate", "submission", submission_id,
         json.dumps({"task_type": request.task_type, "provider": request.provider}), now),
    )
    conn.commit()
    conn.close()

    return {
        "status": "success",
        "submission_id": submission_id,
        "output": result["response"],
        "provider": result["provider"],
        "tokens": result.get("tokens", 0),
        "latency_ms": result.get("latency_ms", 0),
    }


@app.post("/api/pta/score")
async def pta_score(request: PtaScoreRequest):
    """Score an AI output against the 8-criteria standard rubric using Claude."""

    scoring_prompt = (
        'You are a senior business analyst scoring an AI-generated analysis for Harris Farm Markets.\n\n'
        'Score this output against these 8 criteria, each rated 1-10:\n'
        '1. Audience Fit: Tailored to the reader\'s role and decision needs?\n'
        '2. Storytelling: Clear narrative arc from problem to solution?\n'
        '3. Actionability: Specific next steps with owners and timelines?\n'
        '4. Visual Quality: Professional formatting, effective data presentation?\n'
        '5. Completeness: All necessary information present?\n'
        '6. Brevity: Concise — every sentence earns its place?\n'
        '7. Data Integrity: Claims backed by sourced data?\n'
        '8. Honesty: Transparent about limitations and risks?\n\n'
        'Respond in this exact JSON format (no markdown fencing):\n'
        '{"scores":{"audience_fit":{"score":8,"rationale":"..."},"storytelling":{"score":7,"rationale":"..."},'
        '"actionability":{"score":9,"rationale":"..."},"visual_quality":{"score":7,"rationale":"..."},'
        '"completeness":{"score":8,"rationale":"..."},"brevity":{"score":8,"rationale":"..."},'
        '"data_integrity":{"score":6,"rationale":"..."},"honesty":{"score":9,"rationale":"..."}},'
        '"average":7.8,"verdict":"REVISE","improvements":["suggestion1","suggestion2"]}\n\n'
        'Verdicts: "SHIP" if average >= 8.0, "REVISE" if 5.0-7.9, "REJECT" if < 5.0'
    )

    if request.user_role:
        scoring_prompt += f"\n\nTarget audience role: {request.user_role}"
    if request.task_type:
        scoring_prompt += f"\nTask type: {request.task_type}"

    messages = [{"role": "user", "content": f"Score this output:\n\n{request.output_text[:8000]}"}]

    result = await _chat_claude(scoring_prompt, messages)

    if result["status"] == "error":
        return {"status": "error", "message": result["response"]}

    # Parse the JSON response
    try:
        raw = result["response"].strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        if raw.startswith("json"):
            raw = raw[4:]
        scores_data = json.loads(raw.strip())
    except (json.JSONDecodeError, Exception):
        # Fallback: try to extract JSON from the response
        import re as _re
        match = _re.search(r'\{[\s\S]*\}', result["response"])
        if match:
            try:
                scores_data = json.loads(match.group())
            except json.JSONDecodeError:
                return {"status": "error", "message": "Could not parse rubric scores from AI response"}
        else:
            return {"status": "error", "message": "Could not parse rubric scores from AI response"}

    # Update submission if ID provided
    if request.submission_id:
        now = datetime.now().isoformat()
        conn = sqlite3.connect(config.HUB_DB)
        c = conn.cursor()
        c.execute(
            """UPDATE pta_submissions
               SET rubric_scores = ?, rubric_average = ?, rubric_verdict = ?,
                   status = 'scored', updated_at = ?
               WHERE id = ?""",
            (json.dumps(scores_data), scores_data.get("average", 0),
             scores_data.get("verdict", "REVISE"), now, request.submission_id),
        )
        c.execute(
            "INSERT INTO pta_audit_log (user_id, action, entity_type, entity_id, details, created_at) "
            "VALUES (?,?,?,?,?,?)",
            ("system", "score", "submission", request.submission_id,
             json.dumps({"average": scores_data.get("average"), "verdict": scores_data.get("verdict")}), now),
        )

        # Auto-save to prompt library if score >= 9.0
        avg_score = scores_data.get("average", 0)
        if avg_score >= 9.0:
            sub_row = c.execute(
                "SELECT original_prompt, task_type, user_role, output_format FROM pta_submissions WHERE id = ?",
                (request.submission_id,),
            ).fetchone()
            if sub_row:
                prompt_text, task_type, role, fmt = sub_row
                title = "{} (auto-saved, {}/10)".format(
                    task_type.replace("_", " ").title(), avg_score
                )
                c.execute(
                    "INSERT INTO prompt_templates (title, description, template, category, difficulty, uses, avg_rating, created_at, updated_at) "
                    "VALUES (?,?,?,?,?,?,?,?,?)",
                    (title, "Auto-saved from PtA — scored {}/10".format(avg_score),
                     prompt_text, task_type, "advanced", 0, avg_score, now, now),
                )
                c.execute(
                    "INSERT INTO pta_audit_log (user_id, action, entity_type, entity_id, details, created_at) "
                    "VALUES (?,?,?,?,?,?)",
                    ("system", "auto_save_library", "submission", request.submission_id,
                     json.dumps({"avg_score": avg_score}), now),
                )

                # Award points for library save
                c.execute(
                    "SELECT user_id FROM pta_submissions WHERE id = ?", (request.submission_id,)
                )
                user_row = c.fetchone()
                if user_row:
                    c.execute(
                        "INSERT INTO pta_points_log (user_id, action, points, multiplier, total_awarded, reference_id, reference_type, created_at) "
                        "VALUES (?,?,?,?,?,?,?,?)",
                        (user_row[0], "prompt_saved_to_library", 200, 1.0, 200, request.submission_id, "submission", now),
                    )

        conn.commit()
        conn.close()

    return {
        "status": "success",
        "scores": scores_data,
        "auto_saved_to_library": scores_data.get("average", 0) >= 9.0,
    }


@app.post("/api/pta/submit")
async def pta_submit(request: PtaSubmitRequest):
    """Submit a scored output for approval."""
    conn = sqlite3.connect(config.HUB_DB)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM pta_submissions WHERE id = ?", (request.submission_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Submission not found")

    # Require at least one human annotation
    annotations = request.human_annotations or []
    existing = json.loads(row["human_annotations"] or "[]")
    all_annotations = existing + annotations
    if not all_annotations:
        conn.close()
        raise HTTPException(
            status_code=400,
            detail="At least one human annotation is required before submitting. "
                   "Your human judgment is what makes this valuable.",
        )

    now = datetime.now().isoformat()
    conn.execute(
        """UPDATE pta_submissions
           SET status = 'pending_approval', human_annotations = ?, updated_at = ?
           WHERE id = ?""",
        (json.dumps(all_annotations), now, request.submission_id),
    )
    conn.execute(
        "INSERT INTO pta_audit_log (user_id, action, entity_type, entity_id, details, created_at) "
        "VALUES (?,?,?,?,?,?)",
        (row["user_id"], "submit_for_approval", "submission", request.submission_id,
         json.dumps({"annotations_count": len(all_annotations)}), now),
    )
    conn.commit()
    conn.close()

    return {"status": "success", "message": "Submitted for approval", "submission_id": request.submission_id}


@app.get("/api/pta/submissions")
async def pta_list_submissions(
    status: Optional[str] = None,
    user_id: Optional[str] = None,
    task_type: Optional[str] = None,
    limit: int = 50,
):
    """List PtA submissions with optional filters."""
    conn = sqlite3.connect(config.HUB_DB)
    conn.row_factory = sqlite3.Row

    query = "SELECT id, user_id, user_role, task_type, output_format, rubric_average, rubric_verdict, status, created_at FROM pta_submissions WHERE 1=1"
    params = []

    if status:
        query += " AND status = ?"
        params.append(status)
    if user_id:
        query += " AND user_id = ?"
        params.append(user_id)
    if task_type:
        query += " AND task_type = ?"
        params.append(task_type)

    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(query, params).fetchall()
    conn.close()

    return {"submissions": [dict(r) for r in rows]}


@app.get("/api/pta/submissions/{submission_id}")
async def pta_get_submission(submission_id: int):
    """Get full details of a single PtA submission."""
    conn = sqlite3.connect(config.HUB_DB)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM pta_submissions WHERE id = ?", (submission_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Submission not found")
    result = dict(row)
    # Parse JSON fields
    for field in ("data_sources", "analysis_types", "human_annotations", "version_history", "rubric_scores", "advanced_rubric_scores"):
        if result.get(field):
            try:
                result[field] = json.loads(result[field])
            except (json.JSONDecodeError, TypeError):
                pass
    return result


@app.post("/api/pta/approve/{submission_id}")
async def pta_approve(submission_id: int, approver: str = "manager", notes: Optional[str] = None):
    """Approve a pending submission."""
    conn = sqlite3.connect(config.HUB_DB)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM pta_submissions WHERE id = ?", (submission_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Submission not found")
    if row["status"] != "pending_approval":
        conn.close()
        raise HTTPException(status_code=400, detail=f"Cannot approve submission in '{row['status']}' status")

    now = datetime.now().isoformat()
    conn.execute(
        """UPDATE pta_submissions
           SET status = 'approved', approver_notes = ?, decided_at = ?, updated_at = ?
           WHERE id = ?""",
        (notes, now, now, submission_id),
    )
    conn.execute(
        "INSERT INTO pta_audit_log (user_id, action, entity_type, entity_id, details, created_at) "
        "VALUES (?,?,?,?,?,?)",
        (approver, "approve", "submission", submission_id, json.dumps({"notes": notes}), now),
    )

    # Award points for first-time approval
    avg = row["rubric_average"] or 0
    points = 25  # approved_first_time base
    if avg >= 9.0:
        points += 100
    elif avg >= 8.0:
        points += 50
    conn.execute(
        "INSERT INTO pta_points_log (user_id, action, points, multiplier, total_awarded, reference_id, reference_type, created_at) "
        "VALUES (?,?,?,?,?,?,?,?)",
        (row["user_id"], "approved_first_time", points, 1.0, points, submission_id, "submission", now),
    )

    conn.commit()
    conn.close()
    return {"status": "success", "message": "Submission approved", "points_awarded": points}


@app.post("/api/pta/request-changes/{submission_id}")
async def pta_request_changes(submission_id: int, approver: str = "manager", notes: str = ""):
    """Send a submission back for revision."""
    now = datetime.now().isoformat()
    conn = sqlite3.connect(config.HUB_DB)
    conn.execute(
        """UPDATE pta_submissions
           SET status = 'revision_requested', approver_notes = ?, updated_at = ?
           WHERE id = ?""",
        (notes, now, submission_id),
    )
    conn.execute(
        "INSERT INTO pta_audit_log (user_id, action, entity_type, entity_id, details, created_at) "
        "VALUES (?,?,?,?,?,?)",
        (approver, "request_changes", "submission", submission_id, json.dumps({"notes": notes}), now),
    )
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Changes requested"}


@app.get("/api/pta/user-stats/{user_id}")
async def pta_user_stats(user_id: str):
    """Get PtA stats and points for a user."""
    conn = sqlite3.connect(config.HUB_DB)

    total_points = conn.execute(
        "SELECT COALESCE(SUM(total_awarded), 0) FROM pta_points_log WHERE user_id = ?", (user_id,)
    ).fetchone()[0]

    submissions_count = conn.execute(
        "SELECT COUNT(*) FROM pta_submissions WHERE user_id = ?", (user_id,)
    ).fetchone()[0]

    approved_count = conn.execute(
        "SELECT COUNT(*) FROM pta_submissions WHERE user_id = ? AND status = 'approved'", (user_id,)
    ).fetchone()[0]

    avg_score = conn.execute(
        "SELECT COALESCE(AVG(rubric_average), 0) FROM pta_submissions WHERE user_id = ? AND rubric_average IS NOT NULL",
        (user_id,),
    ).fetchone()[0]

    conn.close()

    # Determine ninja level
    level = "Prompt Apprentice"
    if total_points > 2000:
        level = "AI Ninja"
    elif total_points > 500:
        level = "Prompt Master"
    elif total_points > 100:
        level = "Prompt Specialist"

    return {
        "user_id": user_id,
        "total_points": total_points,
        "level": level,
        "submissions": submissions_count,
        "approved": approved_count,
        "avg_rubric_score": round(avg_score, 1),
    }


@app.get("/api/pta/leaderboard")
async def pta_leaderboard(limit: int = 20):
    """Get PtA leaderboard — top users by points."""
    conn = sqlite3.connect(config.HUB_DB)
    rows = conn.execute(
        """SELECT user_id, SUM(total_awarded) as total_points,
                  COUNT(*) as actions
           FROM pta_points_log
           GROUP BY user_id
           ORDER BY total_points DESC
           LIMIT ?""",
        (limit,),
    ).fetchall()

    leaders = []
    for r in rows:
        uid, pts, actions = r
        level = "AI Ninja" if pts > 2000 else "Prompt Master" if pts > 500 else "Prompt Specialist" if pts > 100 else "Prompt Apprentice"
        leaders.append({
            "user_id": uid,
            "total_points": pts,
            "level": level,
            "actions": actions,
        })

    conn.close()
    return {"leaderboard": leaders}


# ============================================================================
# WORKFLOW ENGINE — Step 4 of PtA Spec
# Multi-project tracking, 4P state machine, Talent Radar, Notifications
# ============================================================================

# Valid 4P workflow transitions
VALID_TRANSITIONS = {
    "draft": ["prompting"],
    "prompting": ["proving"],
    "proving": ["proposing", "prompting"],
    "proposing": ["approved", "revision", "escalated"],
    "revision": ["proving"],
    "escalated": ["approved", "revision"],
    "approved": ["progressing"],
    "progressing": ["completed", "blocked"],
    "blocked": ["progressing", "revision"],
    "completed": ["archived"],
    "archived": [],
}

WORKFLOW_STAGES = {
    "prompting": {"name": "Prompt", "colour": "#579BFC", "icon": "\u270d\ufe0f"},
    "proving": {"name": "Prove", "colour": "#00C875", "icon": "\U0001f4ca"},
    "proposing": {"name": "Propose", "colour": "#FDAB3D", "icon": "\U0001f4e4"},
    "progressing": {"name": "Progress", "colour": "#E040FB", "icon": "\U0001f680"},
}

# Escalation rules
ESCALATION_RULES = {
    "board_paper": "Auto-escalate to L3 — board-level output",
    "new_store_feasibility": "Auto-escalate to L3 — strategic decision",
    "it_architecture_proposal": "Auto-add CIO review",
    "amazon_partnership_review": "Auto-escalate to L3 — partnership impact",
}


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    owner_id: Optional[str] = None
    department: Optional[str] = None
    strategic_pillar: Optional[str] = None
    priority: str = "P3"
    target_date: Optional[str] = None
    tags: Optional[list] = []


class WorkflowTransition(BaseModel):
    submission_id: int
    to_stage: str
    triggered_by: Optional[str] = None
    reason: Optional[str] = None


# --- Projects ---

@app.post("/api/workflow/projects")
async def create_project(project: ProjectCreate):
    """Create a new project for multi-project tracking."""
    conn = sqlite3.connect(config.HUB_DB)
    c = conn.cursor()
    c.execute(
        """INSERT INTO pta_projects (name, description, owner_id, department,
           strategic_pillar, priority, target_date, tags)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (project.name, project.description, project.owner_id, project.department,
         project.strategic_pillar, project.priority, project.target_date,
         json.dumps(project.tags or [])),
    )
    project_id = c.lastrowid

    # Audit
    c.execute(
        "INSERT INTO pta_audit_log (user_id, action, entity_type, entity_id, details) VALUES (?, ?, ?, ?, ?)",
        (project.owner_id, "project_created", "project", project_id, json.dumps({"name": project.name})),
    )
    conn.commit()
    conn.close()
    return {"id": project_id, "name": project.name, "status": "active"}


@app.get("/api/workflow/projects")
async def list_projects(status: str = "active", limit: int = 50):
    """List projects with health status."""
    conn = sqlite3.connect(config.HUB_DB)
    conn.row_factory = sqlite3.Row

    query = "SELECT * FROM pta_projects WHERE 1=1"
    params = []
    if status != "all":
        query += " AND status = ?"
        params.append(status)
    query += " ORDER BY CASE priority WHEN 'P1' THEN 1 WHEN 'P2' THEN 2 WHEN 'P3' THEN 3 ELSE 4 END, created_at DESC LIMIT ?"
    params.append(limit)

    projects = []
    for row in conn.execute(query, params).fetchall():
        p = dict(row)
        # Calculate health from linked submissions
        sub_stats = conn.execute(
            """SELECT COUNT(*) as total,
                      SUM(CASE WHEN workflow_stage = 'completed' THEN 1 ELSE 0 END) as completed,
                      SUM(CASE WHEN workflow_stage = 'blocked' THEN 1 ELSE 0 END) as blocked,
                      SUM(CASE WHEN workflow_stage = 'proposing' AND updated_at < datetime('now', '-2 days') THEN 1 ELSE 0 END) as stale,
                      AVG(CASE WHEN rubric_average IS NOT NULL THEN rubric_average END) as avg_quality
               FROM pta_submissions WHERE project_id = ?""",
            (p["id"],),
        ).fetchone()
        p["items_total"] = sub_stats["total"] or 0
        p["items_completed"] = sub_stats["completed"] or 0
        p["items_blocked"] = sub_stats["blocked"] or 0
        p["items_stale"] = sub_stats["stale"] or 0
        p["avg_quality"] = round(sub_stats["avg_quality"] or 0, 1)

        # Auto-calculate health
        if (sub_stats["blocked"] or 0) > 0:
            p["health"] = "red"
        elif (sub_stats["stale"] or 0) > 0:
            p["health"] = "amber"
        else:
            p["health"] = "green"

        projects.append(p)

    conn.close()
    return {"projects": projects}


@app.get("/api/workflow/projects/{project_id}")
async def get_project(project_id: int):
    """Get project details with all linked submissions."""
    conn = sqlite3.connect(config.HUB_DB)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM pta_projects WHERE id = ?", (project_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(404, "Project not found")

    project = dict(row)

    # Get linked submissions
    subs = conn.execute(
        """SELECT id, user_id, user_role, task_type, workflow_stage, rubric_average,
                  rubric_verdict, status, created_at, updated_at
           FROM pta_submissions WHERE project_id = ?
           ORDER BY created_at DESC""",
        (project_id,),
    ).fetchall()
    project["submissions"] = [dict(s) for s in subs]

    conn.close()
    return project


@app.put("/api/workflow/projects/{project_id}")
async def update_project(project_id: int, name: Optional[str] = None,
                         status: Optional[str] = None, priority: Optional[str] = None,
                         target_date: Optional[str] = None):
    """Update project fields."""
    conn = sqlite3.connect(config.HUB_DB)
    updates = []
    params = []
    if name:
        updates.append("name = ?")
        params.append(name)
    if status:
        updates.append("status = ?")
        params.append(status)
    if priority:
        updates.append("priority = ?")
        params.append(priority)
    if target_date:
        updates.append("target_date = ?")
        params.append(target_date)

    if not updates:
        conn.close()
        return {"updated": False}

    updates.append("updated_at = datetime('now')")
    params.append(project_id)
    conn.execute(f"UPDATE pta_projects SET {', '.join(updates)} WHERE id = ?", params)
    conn.commit()
    conn.close()
    return {"updated": True}


# --- Workflow Transitions ---

@app.post("/api/workflow/transition")
async def transition_workflow(t: WorkflowTransition):
    """Transition a submission through the 4P workflow state machine."""
    conn = sqlite3.connect(config.HUB_DB)
    conn.row_factory = sqlite3.Row

    row = conn.execute(
        "SELECT id, workflow_stage, status FROM pta_submissions WHERE id = ?",
        (t.submission_id,),
    ).fetchone()
    if not row:
        conn.close()
        raise HTTPException(404, "Submission not found")

    current_stage = row["workflow_stage"] or "draft"

    # Validate transition
    allowed = VALID_TRANSITIONS.get(current_stage, [])
    if t.to_stage not in allowed:
        conn.close()
        raise HTTPException(
            400,
            f"Invalid transition: {current_stage} -> {t.to_stage}. "
            f"Allowed: {allowed}",
        )

    # Execute transition
    now = datetime.utcnow().isoformat()
    conn.execute(
        "UPDATE pta_submissions SET workflow_stage = ?, updated_at = ? WHERE id = ?",
        (t.to_stage, now, t.submission_id),
    )

    # Map workflow_stage to status for backward compatibility
    stage_to_status = {
        "draft": "draft",
        "prompting": "draft",
        "proving": "generated",
        "proposing": "pending_approval",
        "approved": "approved",
        "revision": "revision_requested",
        "escalated": "pending_approval",
        "progressing": "approved",
        "completed": "approved",
        "blocked": "approved",
        "archived": "approved",
    }
    new_status = stage_to_status.get(t.to_stage, row["status"])
    conn.execute(
        "UPDATE pta_submissions SET status = ? WHERE id = ?",
        (new_status, t.submission_id),
    )

    # Record transition
    conn.execute(
        """INSERT INTO pta_workflow_transitions
           (submission_id, from_stage, to_stage, triggered_by, reason)
           VALUES (?, ?, ?, ?, ?)""",
        (t.submission_id, current_stage, t.to_stage, t.triggered_by, t.reason),
    )

    # Audit log
    conn.execute(
        "INSERT INTO pta_audit_log (user_id, action, entity_type, entity_id, details) VALUES (?, ?, ?, ?, ?)",
        (t.triggered_by, "workflow_transition", "submission", t.submission_id,
         json.dumps({"from": current_stage, "to": t.to_stage, "reason": t.reason})),
    )

    # If completed, record completion time
    if t.to_stage == "completed":
        conn.execute(
            "UPDATE pta_submissions SET completed_at = ? WHERE id = ?",
            (now, t.submission_id),
        )

    conn.commit()
    conn.close()

    return {
        "submission_id": t.submission_id,
        "from_stage": current_stage,
        "to_stage": t.to_stage,
        "valid": True,
    }


@app.get("/api/workflow/transitions/{submission_id}")
async def get_transitions(submission_id: int):
    """Get full transition history for a submission."""
    conn = sqlite3.connect(config.HUB_DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM pta_workflow_transitions WHERE submission_id = ? ORDER BY created_at",
        (submission_id,),
    ).fetchall()
    conn.close()
    return {"transitions": [dict(r) for r in rows]}


# --- Pipeline / Kanban views ---

@app.get("/api/workflow/pipeline")
async def workflow_pipeline(project_id: Optional[int] = None, user_id: Optional[str] = None):
    """Get all submissions grouped by workflow stage — for kanban/pipeline views."""
    conn = sqlite3.connect(config.HUB_DB)
    conn.row_factory = sqlite3.Row

    query = """SELECT id, user_id, user_role, task_type, workflow_stage, rubric_average,
                      rubric_verdict, status, project_id, created_at, updated_at
               FROM pta_submissions WHERE workflow_stage IS NOT NULL"""
    params = []
    if project_id:
        query += " AND project_id = ?"
        params.append(project_id)
    if user_id:
        query += " AND user_id = ?"
        params.append(user_id)
    query += " ORDER BY updated_at DESC"

    rows = conn.execute(query, params).fetchall()
    conn.close()

    # Group by stage
    pipeline = {stage: [] for stage in VALID_TRANSITIONS}
    for r in rows:
        d = dict(r)
        stage = d.get("workflow_stage", "draft")
        if stage in pipeline:
            pipeline[stage].append(d)
        else:
            pipeline.setdefault(stage, []).append(d)

    return {"pipeline": pipeline}


@app.get("/api/workflow/velocity")
async def workflow_velocity(days: int = 30):
    """Calculate workflow velocity metrics — avg time per stage, bottlenecks."""
    conn = sqlite3.connect(config.HUB_DB)
    conn.row_factory = sqlite3.Row

    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()

    # Average time between transitions per stage
    rows = conn.execute(
        """SELECT wt1.from_stage, wt1.to_stage,
                  AVG(julianday(wt2.created_at) - julianday(wt1.created_at)) * 24 as avg_hours
           FROM pta_workflow_transitions wt1
           LEFT JOIN pta_workflow_transitions wt2
             ON wt1.submission_id = wt2.submission_id
             AND wt2.from_stage = wt1.to_stage
           WHERE wt1.created_at > ? AND wt2.created_at IS NOT NULL
           GROUP BY wt1.from_stage, wt1.to_stage""",
        (cutoff,),
    ).fetchall()

    velocity = [dict(r) for r in rows]

    # Bottleneck: items stuck in each stage
    stuck = conn.execute(
        """SELECT workflow_stage, COUNT(*) as count,
                  MIN(updated_at) as oldest
           FROM pta_submissions
           WHERE workflow_stage NOT IN ('completed', 'archived', 'draft')
             AND updated_at < datetime('now', '-2 days')
           GROUP BY workflow_stage
           ORDER BY count DESC""",
    ).fetchall()

    # Overall throughput
    completed_count = conn.execute(
        "SELECT COUNT(*) FROM pta_submissions WHERE completed_at > ? AND workflow_stage = 'completed'",
        (cutoff,),
    ).fetchone()[0]

    total_submitted = conn.execute(
        "SELECT COUNT(*) FROM pta_submissions WHERE created_at > ?",
        (cutoff,),
    ).fetchone()[0]

    conn.close()
    return {
        "stage_velocity": velocity,
        "bottlenecks": [dict(s) for s in stuck],
        "completed_last_n_days": completed_count,
        "submitted_last_n_days": total_submitted,
        "throughput_pct": round(completed_count / max(total_submitted, 1) * 100, 1),
    }


# --- Notifications ---

@app.get("/api/workflow/notifications/{user_id}")
async def get_notifications(user_id: str, unread_only: bool = True, limit: int = 50):
    """Get notifications for a user."""
    conn = sqlite3.connect(config.HUB_DB)
    conn.row_factory = sqlite3.Row
    query = "SELECT * FROM pta_notifications WHERE user_id = ?"
    params = [user_id]
    if unread_only:
        query += " AND read = 0"
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return {"notifications": [dict(r) for r in rows]}


@app.post("/api/workflow/notifications/read")
async def mark_notifications_read(user_id: str, notification_ids: Optional[list] = None):
    """Mark notifications as read."""
    conn = sqlite3.connect(config.HUB_DB)
    if notification_ids:
        placeholders = ",".join("?" for _ in notification_ids)
        conn.execute(
            f"UPDATE pta_notifications SET read = 1 WHERE id IN ({placeholders}) AND user_id = ?",
            notification_ids + [user_id],
        )
    else:
        conn.execute("UPDATE pta_notifications SET read = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    return {"marked_read": True}


def _create_notification(conn, user_id: str, ntype: str, title: str, message: str, link: str = None):
    """Internal helper to create a notification."""
    conn.execute(
        "INSERT INTO pta_notifications (user_id, type, title, message, link) VALUES (?, ?, ?, ?, ?)",
        (user_id, ntype, title, message, link),
    )


# --- Talent Radar / Ninja Finder ---

@app.get("/api/workflow/talent-radar")
async def talent_radar(days: int = 30):
    """Talent Radar — surfaces rising stars, top performers, and adoption gaps."""
    conn = sqlite3.connect(config.HUB_DB)
    conn.row_factory = sqlite3.Row

    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()

    # Per-user metrics
    users = conn.execute(
        """SELECT user_id, user_role,
                  COUNT(*) as submissions,
                  SUM(CASE WHEN workflow_stage = 'completed' OR status = 'approved' THEN 1 ELSE 0 END) as completed,
                  AVG(CASE WHEN rubric_average IS NOT NULL THEN rubric_average END) as avg_quality,
                  SUM(CASE WHEN status = 'approved' AND approver_notes IS NULL THEN 1 ELSE 0 END) as first_time_approvals,
                  SUM(CASE WHEN status IN ('approved', 'revision_requested') THEN 1 ELSE 0 END) as total_decided,
                  COUNT(DISTINCT project_id) as projects_involved
           FROM pta_submissions
           WHERE created_at > ?
           GROUP BY user_id
           ORDER BY submissions DESC""",
        (cutoff,),
    ).fetchall()

    # Build talent profiles
    talent = []
    for u in users:
        d = dict(u)
        total_decided = d.get("total_decided") or 0
        d["first_time_approval_rate"] = round(
            (d.get("first_time_approvals") or 0) / max(total_decided, 1), 2
        )
        d["avg_quality"] = round(d.get("avg_quality") or 0, 1)

        # Get points
        pts = conn.execute(
            "SELECT COALESCE(SUM(total_awarded), 0) FROM pta_points_log WHERE user_id = ?",
            (d["user_id"],),
        ).fetchone()[0]
        d["total_points"] = pts
        d["level"] = (
            "AI Ninja" if pts > 2000
            else "Prompt Master" if pts > 500
            else "Prompt Specialist" if pts > 100
            else "Prompt Apprentice"
        )

        # Ninja signals
        d["ninja_score"] = _calculate_ninja_score(d)
        talent.append(d)

    # Sort by ninja score
    talent.sort(key=lambda x: x["ninja_score"], reverse=True)

    # Rising stars: biggest improvement — compare to prior period
    prior_cutoff = (datetime.utcnow() - timedelta(days=days * 2)).isoformat()
    rising = []
    for t in talent[:20]:
        prior_avg = conn.execute(
            """SELECT AVG(rubric_average) FROM pta_submissions
               WHERE user_id = ? AND created_at BETWEEN ? AND ? AND rubric_average IS NOT NULL""",
            (t["user_id"], prior_cutoff, cutoff),
        ).fetchone()[0]
        if prior_avg:
            t["quality_improvement"] = round((t.get("avg_quality") or 0) - prior_avg, 1)
        else:
            t["quality_improvement"] = 0
        rising.append(t)

    rising.sort(key=lambda x: x["quality_improvement"], reverse=True)

    # Department adoption
    dept_adoption = conn.execute(
        """SELECT user_role as department,
                  COUNT(DISTINCT user_id) as active_users,
                  COUNT(*) as total_submissions,
                  AVG(CASE WHEN rubric_average IS NOT NULL THEN rubric_average END) as avg_quality
           FROM pta_submissions
           WHERE created_at > ?
           GROUP BY user_role
           ORDER BY active_users DESC""",
        (cutoff,),
    ).fetchall()

    conn.close()
    return {
        "top_performers": talent[:10],
        "rising_stars": [r for r in rising[:5] if r["quality_improvement"] > 0],
        "department_adoption": [dict(d) for d in dept_adoption],
        "total_active_users": len(talent),
        "total_ninjas": sum(1 for t in talent if t["level"] == "AI Ninja"),
        "total_masters": sum(1 for t in talent if t["level"] == "Prompt Master"),
    }


def _calculate_ninja_score(user_data: dict) -> float:
    """Calculate composite ninja score from multiple signals."""
    submissions = user_data.get("submissions", 0)
    avg_quality = user_data.get("avg_quality", 0)
    ftar = user_data.get("first_time_approval_rate", 0)
    completed = user_data.get("completed", 0)
    projects = user_data.get("projects_involved", 0)

    # Weighted composite (0-100)
    score = (
        min(submissions / 10, 1.0) * 20  # Volume (max 20)
        + min(avg_quality / 10, 1.0) * 30  # Quality (max 30)
        + ftar * 20  # First-time approval (max 20)
        + min(completed / 5, 1.0) * 15  # Completion (max 15)
        + min(projects / 3, 1.0) * 15  # Cross-project (max 15)
    )
    return round(score, 1)


# --- Weekly/Monthly Report Generation ---

@app.get("/api/workflow/report/weekly")
async def weekly_hub_report():
    """Auto-generated weekly Hub report — submissions, approvals, performers, gaps."""
    conn = sqlite3.connect(config.HUB_DB)
    conn.row_factory = sqlite3.Row

    week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
    two_weeks = (datetime.utcnow() - timedelta(days=14)).isoformat()

    # This week vs last week
    this_week = conn.execute(
        "SELECT COUNT(*) FROM pta_submissions WHERE created_at > ?", (week_ago,)
    ).fetchone()[0]
    last_week = conn.execute(
        "SELECT COUNT(*) FROM pta_submissions WHERE created_at BETWEEN ? AND ?",
        (two_weeks, week_ago),
    ).fetchone()[0]

    approved_this_week = conn.execute(
        "SELECT COUNT(*) FROM pta_submissions WHERE decided_at > ? AND status = 'approved'",
        (week_ago,),
    ).fetchone()[0]

    avg_quality = conn.execute(
        "SELECT AVG(rubric_average) FROM pta_submissions WHERE created_at > ? AND rubric_average IS NOT NULL",
        (week_ago,),
    ).fetchone()[0]

    # Top performers
    top = conn.execute(
        """SELECT user_id, SUM(total_awarded) as pts
           FROM pta_points_log WHERE created_at > ?
           GROUP BY user_id ORDER BY pts DESC LIMIT 5""",
        (week_ago,),
    ).fetchall()

    # Dept with lowest submissions (the gap)
    all_roles = conn.execute(
        "SELECT DISTINCT user_role FROM pta_submissions"
    ).fetchall()
    role_counts = conn.execute(
        """SELECT user_role, COUNT(*) as cnt FROM pta_submissions
           WHERE created_at > ? GROUP BY user_role""",
        (week_ago,),
    ).fetchall()
    active_roles = {r["user_role"] for r in role_counts}
    gap_roles = [r[0] for r in all_roles if r[0] not in active_roles]

    conn.close()

    return {
        "period": "last_7_days",
        "submissions_this_week": this_week,
        "submissions_last_week": last_week,
        "change_pct": round((this_week - last_week) / max(last_week, 1) * 100, 1),
        "approved_this_week": approved_this_week,
        "avg_quality": round(avg_quality or 0, 1),
        "top_performers": [{"user_id": r["user_id"], "points": r["pts"]} for r in top],
        "adoption_gaps": gap_roles,
    }


@app.get("/api/workflow/report/monthly")
async def monthly_board_report():
    """Monthly board summary — adoption, time savings, quality, ROI."""
    conn = sqlite3.connect(config.HUB_DB)
    conn.row_factory = sqlite3.Row

    month_ago = (datetime.utcnow() - timedelta(days=30)).isoformat()

    total_users = conn.execute(
        "SELECT COUNT(DISTINCT user_id) FROM pta_submissions WHERE created_at > ?",
        (month_ago,),
    ).fetchone()[0]
    total_subs = conn.execute(
        "SELECT COUNT(*) FROM pta_submissions WHERE created_at > ?", (month_ago,)
    ).fetchone()[0]
    total_approved = conn.execute(
        "SELECT COUNT(*) FROM pta_submissions WHERE decided_at > ? AND status = 'approved'",
        (month_ago,),
    ).fetchone()[0]

    avg_quality = conn.execute(
        "SELECT AVG(rubric_average) FROM pta_submissions WHERE created_at > ? AND rubric_average IS NOT NULL",
        (month_ago,),
    ).fetchone()[0]

    # Level distribution
    levels = {"AI Ninja": 0, "Prompt Master": 0, "Prompt Specialist": 0, "Prompt Apprentice": 0}
    user_pts = conn.execute(
        "SELECT user_id, SUM(total_awarded) as pts FROM pta_points_log GROUP BY user_id"
    ).fetchall()
    for u in user_pts:
        pts = u["pts"]
        lvl = "AI Ninja" if pts > 2000 else "Prompt Master" if pts > 500 else "Prompt Specialist" if pts > 100 else "Prompt Apprentice"
        levels[lvl] += 1

    # Time savings estimate: 2 hours saved per approved submission (conservative)
    est_hours_saved = total_approved * 2

    conn.close()
    return {
        "period": "last_30_days",
        "active_users": total_users,
        "total_submissions": total_subs,
        "total_approved": total_approved,
        "avg_quality": round(avg_quality or 0, 1),
        "level_distribution": levels,
        "est_hours_saved": est_hours_saved,
        "est_cost_saving_aud": est_hours_saved * 75,  # $75/hr avg loaded cost
    }


# --- Link submission to project ---

@app.post("/api/workflow/link")
async def link_submission_to_project(submission_id: int, project_id: int):
    """Link a submission to a project."""
    conn = sqlite3.connect(config.HUB_DB)
    conn.execute(
        "UPDATE pta_submissions SET project_id = ?, updated_at = datetime('now') WHERE id = ?",
        (project_id, submission_id),
    )
    conn.commit()
    conn.close()
    return {"linked": True, "submission_id": submission_id, "project_id": project_id}


# ============================================================================
# ACADEMY GAMIFICATION ENGINE
# XP system, streaks, daily challenges, badges, leaderboards
# ============================================================================

@app.post("/api/academy/xp/award")
async def academy_award_xp(user_id: str, action_type: str,
                            base_xp: Optional[int] = None,
                            reference_id: Optional[str] = None,
                            reference_type: Optional[str] = None,
                            description: Optional[str] = None):
    """Award XP to a user with streak multiplier auto-applied."""
    from academy_engine import award_xp
    result = award_xp(config.HUB_DB, user_id, action_type, base_xp=base_xp,
                      reference_id=reference_id, reference_type=reference_type,
                      description=description)
    return result


@app.get("/api/academy/xp/{user_id}")
async def academy_get_xp(user_id: str):
    """Get user's total XP and level info."""
    from academy_engine import get_user_xp
    return get_user_xp(config.HUB_DB, user_id)


@app.get("/api/academy/profile/{user_id}")
async def academy_profile(user_id: str):
    """Full profile: XP, level, streak, badges, recent activity."""
    from academy_engine import get_full_profile
    return get_full_profile(config.HUB_DB, user_id)


@app.post("/api/academy/streak/checkin")
async def academy_streak_checkin(user_id: str):
    """Record daily engagement and update streak."""
    from academy_engine import update_streak
    return update_streak(config.HUB_DB, user_id)


@app.get("/api/academy/streak/{user_id}")
async def academy_get_streak(user_id: str):
    """Get streak data for a user."""
    from academy_engine import get_streak
    return get_streak(config.HUB_DB, user_id)


@app.get("/api/academy/leaderboard")
async def academy_leaderboard(period: str = "all", limit: int = 50):
    """Individual leaderboard ranked by XP."""
    from academy_engine import get_leaderboard
    return {"leaderboard": get_leaderboard(config.HUB_DB, period=period, limit=limit)}


@app.get("/api/academy/daily-challenge")
async def academy_daily_challenge(user_id: str):
    """Get today's challenge and whether the user has completed it."""
    from academy_engine import get_todays_challenge
    challenge = get_todays_challenge(config.HUB_DB, user_id)
    if not challenge:
        return {"challenge": None, "message": "No challenges available. Check back soon!"}
    return {"challenge": challenge}


@app.post("/api/academy/daily-challenge/complete")
async def academy_complete_challenge(user_id: str, challenge_id: int):
    """Mark today's challenge complete and award XP."""
    from academy_engine import complete_daily_challenge
    return complete_daily_challenge(config.HUB_DB, user_id, challenge_id)


@app.get("/api/academy/badges/{user_id}")
async def academy_badges(user_id: str):
    """Get earned and locked badges for a user."""
    from academy_engine import get_user_badges
    return get_user_badges(config.HUB_DB, user_id)


@app.post("/api/academy/badges/check")
async def academy_check_badges(user_id: str):
    """Run badge eligibility check and award new badges."""
    from academy_engine import check_and_award_badges
    newly = check_and_award_badges(config.HUB_DB, user_id)
    return {"newly_awarded": [b["name"] for b in newly], "count": len(newly)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
