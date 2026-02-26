"""
Harris Farm Hub — MDHE API Endpoints
Master Data Health Engine REST API.
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional, List
import json

router = APIRouter(prefix="/api/mdhe", tags=["mdhe"])


@router.get("/scores")
async def get_scores():
    """Get latest health scores for all domains."""
    from mdhe_db import init_mdhe_db, get_latest_scores
    init_mdhe_db()
    scores = get_latest_scores()
    return {"scores": scores}


@router.get("/scores/history")
async def get_scores_history(days: int = 30):
    """Get score history for trend charts."""
    from mdhe_db import init_mdhe_db, get_score_history
    init_mdhe_db()
    history = get_score_history(days=days)
    return {"history": history}


@router.get("/validations")
async def list_validations(source_id: Optional[int] = None, layer: Optional[str] = None,
                           severity: Optional[str] = None, domain: Optional[str] = None,
                           limit: int = 500):
    """Get validation results with filtering."""
    from mdhe_db import init_mdhe_db, get_validations
    init_mdhe_db()
    results = get_validations(source_id=source_id, layer=layer, severity=severity, limit=limit)
    return {"validations": results, "count": len(results)}


@router.get("/issues")
async def list_issues(status: Optional[str] = None, domain: Optional[str] = None,
                      severity: Optional[str] = None, limit: int = 200):
    """Get issues with filtering."""
    from mdhe_db import init_mdhe_db, get_issues
    init_mdhe_db()
    issues = get_issues(status=status, domain=domain, severity=severity, limit=limit)
    return {"issues": issues, "count": len(issues)}


@router.put("/issues/{issue_id}")
async def update_issue_endpoint(issue_id: int, body: dict):
    """Update issue status/assignment."""
    from mdhe_db import init_mdhe_db, update_issue
    init_mdhe_db()
    update_issue(
        issue_id,
        status=body.get("status"),
        assigned_to=body.get("assigned_to"),
        resolved_by=body.get("resolved_by"),
    )
    return {"ok": True}


@router.get("/scan-results")
async def list_scan_results(scan_source: Optional[str] = None):
    """Get scan verification results."""
    from mdhe_db import init_mdhe_db, get_scan_results
    init_mdhe_db()
    results = get_scan_results(scan_source=scan_source)
    return {"results": results, "count": len(results)}


@router.get("/plu-records")
async def list_plu_records(include_dummy: bool = True):
    """Get PLU master records."""
    from mdhe_db import init_mdhe_db, get_plu_records
    init_mdhe_db()
    records = get_plu_records(include_dummy=include_dummy)
    return {"records": records, "count": len(records)}


@router.post("/seed-demo")
async def seed_demo():
    """Seed dummy demo data (10 PLUs with issues)."""
    from mdhe_db import init_mdhe_db, seed_dummy_data
    init_mdhe_db()
    seed_dummy_data()
    return {"ok": True, "message": "Demo data seeded with 10 PLUs"}


@router.delete("/clear-demo")
async def clear_demo():
    """Clear all dummy/demo data."""
    from mdhe_db import init_mdhe_db, clear_dummy_data
    init_mdhe_db()
    clear_dummy_data()
    return {"ok": True, "message": "Demo data cleared"}


@router.get("/sources")
async def list_sources():
    """Get upload history."""
    from mdhe_db import init_mdhe_db
    import sqlite3
    from pathlib import Path
    init_mdhe_db()
    _DB = Path(__file__).resolve().parent / "hub_data.db"
    with sqlite3.connect(str(_DB)) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM mdhe_data_sources ORDER BY uploaded_at DESC LIMIT 50"
        ).fetchall()
    return {"sources": [dict(r) for r in rows]}
