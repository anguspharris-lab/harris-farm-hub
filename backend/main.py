"""
Harris Farm Markets - AI Centre of Excellence Hub
Backend API Server
"""

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import anthropic
import openai
import httpx
import asyncio
from datetime import datetime
import json
import sqlite3
import pandas as pd
from enum import Enum

app = FastAPI(title="Harris Farm Hub API", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# DATA MODELS
# ============================================================================

class LLMProvider(str, Enum):
    CLAUDE = "claude"
    CHATGPT = "chatgpt"
    GROK = "grok"

class QueryRequest(BaseModel):
    question: str
    context: Optional[str] = None
    providers: List[LLMProvider] = [LLMProvider.CLAUDE, LLMProvider.CHATGPT]

class LLMResponse(BaseModel):
    provider: str
    response: str
    timestamp: str
    tokens_used: Optional[int] = None
    latency_ms: Optional[float] = None

class EvaluationRequest(BaseModel):
    query_id: str
    winner: str
    feedback: Optional[str] = None
    user_id: str

class DataQueryRequest(BaseModel):
    query: str
    dataset: str  # "sales", "profitability", "transport", etc.
    filters: Optional[Dict[str, Any]] = None

class DashboardRequest(BaseModel):
    dashboard_type: str  # "sales_overview", "store_profitability", "transport_costs"
    date_range: Optional[Dict[str, str]] = None

class PromptTemplate(BaseModel):
    title: str
    description: str
    template: str
    category: str  # "retail_ops", "buying", "merchandising", "finance"
    difficulty: str  # "beginner", "intermediate", "advanced"

# ============================================================================
# DATABASE SETUP
# ============================================================================

def init_db():
    """Initialize SQLite database for Hub metadata"""
    conn = sqlite3.connect('hub_data.db')
    c = conn.cursor()
    
    # Query history
    c.execute('''CREATE TABLE IF NOT EXISTS query_history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  question TEXT,
                  timestamp TEXT,
                  user_id TEXT,
                  query_type TEXT)''')
    
    # LLM responses
    c.execute('''CREATE TABLE IF NOT EXISTS llm_responses
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  query_id INTEGER,
                  provider TEXT,
                  response TEXT,
                  tokens INTEGER,
                  latency_ms REAL,
                  timestamp TEXT,
                  FOREIGN KEY (query_id) REFERENCES query_history(id))''')
    
    # Evaluations (Chairman's decisions)
    c.execute('''CREATE TABLE IF NOT EXISTS evaluations
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  query_id INTEGER,
                  winner TEXT,
                  feedback TEXT,
                  user_id TEXT,
                  timestamp TEXT,
                  FOREIGN KEY (query_id) REFERENCES query_history(id))''')
    
    # Prompt templates
    c.execute('''CREATE TABLE IF NOT EXISTS prompt_templates
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  title TEXT,
                  description TEXT,
                  template TEXT,
                  category TEXT,
                  difficulty TEXT,
                  uses