"""Copper Retirement Task Board — Lakebase-backed shared task board.

Stores tasks and agent messages in a Lakebase Postgres database instead
of a workspace markdown file. Provides structured CRUD endpoints for the
React frontend and a markdown-export endpoint for backward compatibility
with the scheduled agents reading .assistant_instructions.md.
"""
import asyncio
import json
import logging
import os
import re
import threading
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional

import psycopg
from databricks.sdk import WorkspaceClient
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────

SUMMARY_MODEL_ENDPOINT = os.environ.get(
    "SUMMARY_MODEL_ENDPOINT",
    "databricks-meta-llama-3-3-70b-instruct",
)
SUMMARY_ITEM_LIMIT = int(os.environ.get("SUMMARY_ITEM_LIMIT", "5"))
SCHEMA_NAME = "task_board"

_ws = WorkspaceClient()

# ── Lakebase connection ───────────────────────────────────────────────

_current_token: list[str] = [""]  # mutable container for token refresh
_pg_conninfo: str = ""  # set at startup


def _refresh_token() -> str:
    """Generate a fresh Lakebase OAuth token."""
    endpoint = os.environ.get("LAKEBASE_ENDPOINT")
    if not endpoint:
        raise RuntimeError("LAKEBASE_ENDPOINT env var not set")
    cred = _ws.postgres.generate_database_credential(endpoint=endpoint)
    _current_token[0] = cred.token
    return cred.token


def _token_refresh_loop():
    """Background thread: refresh token every 30 minutes."""
    while True:
        time.sleep(1800)
        try:
            _refresh_token()
            logger.info("Lakebase token refreshed")
        except Exception as e:
            logger.warning("Token refresh failed: %s", e)


def _get_conn() -> psycopg.Connection:
    """Get a new Postgres connection with the current token."""
    pguser = os.environ.get("PGUSER") or _ws.current_user.me().user_name
    return psycopg.connect(
        host=os.environ.get("PGHOST", ""),
        port=int(os.environ.get("PGPORT", "5432")),
        dbname=os.environ.get("PGDATABASE", "databricks_postgres"),
        user=pguser,
        password=_current_token[0],
        sslmode="require",
        autocommit=True,
    )


# ── Schema init ───────────────────────────────────────────────────────

SCHEMA_DDL = f"""
CREATE SCHEMA IF NOT EXISTS {SCHEMA_NAME};

CREATE TABLE IF NOT EXISTS {SCHEMA_NAME}.tasks (
    id          SERIAL PRIMARY KEY,
    label       TEXT NOT NULL,
    owner       TEXT NOT NULL DEFAULT 'Unassigned',
    description TEXT NOT NULL DEFAULT '',
    done        BOOLEAN NOT NULL DEFAULT FALSE,
    score       INT NOT NULL DEFAULT 0,
    reasons     TEXT[] NOT NULL DEFAULT '{{}}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS {SCHEMA_NAME}.agent_messages (
    id         SERIAL PRIMARY KEY,
    agent      TEXT NOT NULL,
    msg_date   DATE NOT NULL DEFAULT CURRENT_DATE,
    task_label TEXT NOT NULL DEFAULT '',
    body       TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS {SCHEMA_NAME}.config (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL DEFAULT ''
);
"""


def _init_schema():
    """Create the schema and tables if they don't exist."""
    conn = _get_conn()
    try:
        for stmt in SCHEMA_DDL.strip().split(";"):
            stmt = stmt.strip()
            if stmt:
                conn.execute(stmt)
        logger.info("Schema %s initialized", SCHEMA_NAME)
    finally:
        conn.close()


# ── Scoring ───────────────────────────────────────────────────────────

KEYWORD_WEIGHTS = [
    ("critical", 24, "explicitly marked critical"),
    ("blocker", 22, "contains a blocker"),
    ("go/no-go", 20, "drives a go/no-go decision"),
    ("gate", 18, "acts as a readiness gate"),
    ("depends on", 15, "has an explicit dependency"),
    ("manual", 12, "needs manual intervention"),
    ("ceo", 14, "requires executive involvement"),
    ("regulatory", 12, "has regulatory impact"),
    ("fcc", 12, "touches FCC requirements"),
    ("risk", 10, "affects risk scoring or exposure"),
    ("data quality", 12, "affects data quality confidence"),
    ("thin-slice", 12, "supports the thin-slice demo path"),
    ("missing", 10, "covers a missing dependency"),
    ("escalate", 10, "requires escalation or unblock"),
]


def _score_task(label: str, description: str, owner: str) -> tuple[int, list[str]]:
    text = f"{label} {description}".lower()
    score = 0
    reasons = []
    phase_match = re.match(r"P(\d+)", label)
    if phase_match:
        phase = int(phase_match.group(1))
        score += max(0, 90 - phase * 10)
        reasons.append(f"early-phase {label.split('-')[0]} work")
    for needle, weight, reason in KEYWORD_WEIGHTS:
        if needle in text:
            score += weight
            reasons.append(reason)
    if owner in {"@pm", "@data-planner"}:
        score += 6
        reasons.append(f"owned by {owner}")
    if len(description) > 220:
        score += 4
        reasons.append("has multi-part requirements")
    return score, reasons[:3]


def _criticality_label(score: int) -> str:
    if score >= 100:
        return "Critical"
    if score >= 70:
        return "High"
    if score >= 45:
        return "Medium"
    return "Normal"


# ── Pydantic models ───────────────────────────────────────────────────

class TaskCreate(BaseModel):
    label: str
    owner: str = "Unassigned"
    description: str = ""
    done: bool = False

class TaskUpdate(BaseModel):
    label: Optional[str] = None
    owner: Optional[str] = None
    description: Optional[str] = None
    done: Optional[bool] = None

class MessageCreate(BaseModel):
    agent: str
    task_label: str = ""
    body: str = ""
    msg_date: Optional[str] = None  # ISO date string

class BulkImport(BaseModel):
    tasks: list[TaskCreate] = []
    messages: list[MessageCreate] = []


# ── DB helpers ────────────────────────────────────────────────────────

def _task_row_to_dict(row) -> dict:
    return {
        "id": row[0],
        "label": row[1],
        "owner": row[2],
        "description": row[3],
        "done": row[4],
        "score": row[5],
        "reasons": list(row[6]) if row[6] else [],
        "criticality": _criticality_label(row[5]),
        "created_at": row[7].isoformat() if row[7] else None,
        "updated_at": row[8].isoformat() if row[8] else None,
    }


def _msg_row_to_dict(row) -> dict:
    return {
        "id": row[0],
        "agent": row[1],
        "msg_date": row[2].isoformat() if row[2] else None,
        "task_label": row[3],
        "body": row[4],
        "created_at": row[5].isoformat() if row[5] else None,
    }


# ── App lifecycle ─────────────────────────────────────────────────────

_db_ready = False  # global flag: True once Lakebase is connected
_startup_error = ""  # stores error message if startup fails


@asynccontextmanager
async def lifespan(app):
    global _db_ready, _startup_error
    # Log env vars for diagnostics
    for var in ["PGHOST", "PGPORT", "PGDATABASE", "PGUSER", "PGSSLMODE", "LAKEBASE_ENDPOINT"]:
        val = os.environ.get(var, "<NOT SET>")
        logger.info("ENV %s = %s", var, val[:60] if var != "LAKEBASE_ENDPOINT" else val)
    # Startup: refresh token, init schema, start background refresh
    try:
        _refresh_token()
        logger.info("Lakebase token acquired")
        _init_schema()
        t = threading.Thread(target=_token_refresh_loop, daemon=True)
        t.start()
        _db_ready = True
        logger.info("Lakebase connection established, schema ready")
    except Exception as e:
        _startup_error = f"{type(e).__name__}: {e}"
        logger.error("Lakebase startup failed (app still serving /health): %s", e, exc_info=True)
        # Do NOT raise — let the app start so we can inspect /health
    yield


app = FastAPI(title="Copper Task Board", lifespan=lifespan)


# ── Health ────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    """Health check with diagnostics."""
    env_status = {}
    for var in ["PGHOST", "PGPORT", "PGDATABASE", "PGUSER", "PGSSLMODE", "LAKEBASE_ENDPOINT"]:
        val = os.environ.get(var)
        env_status[var] = "set" if val else "NOT SET"
    return {
        "db_ready": _db_ready,
        "startup_error": _startup_error or None,
        "env_vars": env_status,
    }


def _require_db():
    if not _db_ready:
        raise HTTPException(
            status_code=503,
            detail=f"Lakebase not ready: {_startup_error or 'initializing'}",
        )


# ── Task CRUD ─────────────────────────────────────────────────────────

@app.get("/api/tasks")
async def list_tasks(done: Optional[bool] = None, owner: Optional[str] = None):
    """List tasks, optionally filtered by done status or owner."""
    _require_db()
    try:
        conn = _get_conn()
        try:
            q = f"SELECT id, label, owner, description, done, score, reasons, created_at, updated_at FROM {SCHEMA_NAME}.tasks WHERE 1=1"
            params: list = []
            if done is not None:
                q += " AND done = %s"
                params.append(done)
            if owner:
                q += " AND owner = %s"
                params.append(owner)
            q += " ORDER BY score DESC, label ASC"
            rows = conn.execute(q, params).fetchall()
            return {"tasks": [_task_row_to_dict(r) for r in rows]}
        finally:
            conn.close()
    except Exception as e:
        logger.error("List tasks failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tasks")
async def create_task(body: TaskCreate):
    """Create a new task."""
    _require_db()
    try:
        score, reasons = _score_task(body.label, body.description, body.owner)
        conn = _get_conn()
        try:
            row = conn.execute(
                f"INSERT INTO {SCHEMA_NAME}.tasks (label, owner, description, done, score, reasons) "
                f"VALUES (%s, %s, %s, %s, %s, %s) RETURNING id, label, owner, description, done, score, reasons, created_at, updated_at",
                (body.label, body.owner, body.description, body.done, score, reasons),
            ).fetchone()
            return {"task": _task_row_to_dict(row)}
        finally:
            conn.close()
    except Exception as e:
        logger.error("Create task failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/api/tasks/{task_id}")
async def update_task(task_id: int, body: TaskUpdate):
    """Update a task by ID."""
    _require_db()
    try:
        conn = _get_conn()
        try:
            # Fetch current values
            current = conn.execute(
                f"SELECT label, owner, description, done FROM {SCHEMA_NAME}.tasks WHERE id = %s",
                (task_id,),
            ).fetchone()
            if not current:
                raise HTTPException(status_code=404, detail="Task not found")
            label = body.label if body.label is not None else current[0]
            owner = body.owner if body.owner is not None else current[1]
            description = body.description if body.description is not None else current[2]
            done = body.done if body.done is not None else current[3]
            score, reasons = _score_task(label, description, owner)
            row = conn.execute(
                f"UPDATE {SCHEMA_NAME}.tasks SET label=%s, owner=%s, description=%s, done=%s, score=%s, reasons=%s, updated_at=NOW() "
                f"WHERE id=%s RETURNING id, label, owner, description, done, score, reasons, created_at, updated_at",
                (label, owner, description, done, score, reasons, task_id),
            ).fetchone()
            return {"task": _task_row_to_dict(row)}
        finally:
            conn.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Update task failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: int):
    """Delete a task by ID."""
    _require_db()
    try:
        conn = _get_conn()
        try:
            conn.execute(f"DELETE FROM {SCHEMA_NAME}.tasks WHERE id = %s", (task_id,))
            return {"success": True}
        finally:
            conn.close()
    except Exception as e:
        logger.error("Delete task failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ── Agent messages ────────────────────────────────────────────────────

@app.get("/api/messages")
async def list_messages(agent: Optional[str] = None, limit: int = 200):
    """List agent messages, optionally filtered by agent."""
    _require_db()
    try:
        conn = _get_conn()
        try:
            q = f"SELECT id, agent, msg_date, task_label, body, created_at FROM {SCHEMA_NAME}.agent_messages WHERE 1=1"
            params: list = []
            if agent:
                q += " AND agent = %s"
                params.append(agent)
            q += " ORDER BY msg_date DESC, created_at DESC LIMIT %s"
            params.append(limit)
            rows = conn.execute(q, params).fetchall()
            return {"messages": [_msg_row_to_dict(r) for r in rows]}
        finally:
            conn.close()
    except Exception as e:
        logger.error("List messages failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/messages")
async def create_message(body: MessageCreate):
    """Create a new agent message."""
    _require_db()
    try:
        conn = _get_conn()
        try:
            msg_date = body.msg_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
            row = conn.execute(
                f"INSERT INTO {SCHEMA_NAME}.agent_messages (agent, msg_date, task_label, body) "
                f"VALUES (%s, %s, %s, %s) RETURNING id, agent, msg_date, task_label, body, created_at",
                (body.agent, msg_date, body.task_label, body.body),
            ).fetchone()
            return {"message": _msg_row_to_dict(row)}
        finally:
            conn.close()
    except Exception as e:
        logger.error("Create message failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ── Bulk import (for migration from markdown) ─────────────────────────

@app.post("/api/import")
async def bulk_import(body: BulkImport):
    """Import tasks and messages in bulk (for migration from markdown)."""
    _require_db()
    try:
        conn = _get_conn()
        try:
            task_count = 0
            for t in body.tasks:
                score, reasons = _score_task(t.label, t.description, t.owner)
                conn.execute(
                    f"INSERT INTO {SCHEMA_NAME}.tasks (label, owner, description, done, score, reasons) "
                    f"VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
                    (t.label, t.owner, t.description, t.done, score, reasons),
                )
                task_count += 1
            msg_count = 0
            for m in body.messages:
                msg_date = m.msg_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
                conn.execute(
                    f"INSERT INTO {SCHEMA_NAME}.agent_messages (agent, msg_date, task_label, body) "
                    f"VALUES (%s, %s, %s, %s)",
                    (m.agent, msg_date, m.task_label, m.body),
                )
                msg_count += 1
            return {"imported_tasks": task_count, "imported_messages": msg_count}
        finally:
            conn.close()
    except Exception as e:
        logger.error("Bulk import failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ── Summary ───────────────────────────────────────────────────────────

def _build_summary_from_tasks(tasks: list[dict]) -> dict:
    """Build heuristic summary from task list."""
    top = [t for t in tasks if not t["done"]][:SUMMARY_ITEM_LIMIT]
    if not top:
        return {
            "mode": "heuristic",
            "headline": "No outstanding tasks found",
            "summary": "The task board currently has no unchecked items.",
            "items": [],
        }
    headline_bits = []
    joined = " ".join(t["description"].lower() for t in top)
    if "thin-slice" in joined or "go/no-go" in joined:
        headline_bits.append("thin-slice readiness")
    if "regulatory" in joined or "fcc" in joined:
        headline_bits.append("regulatory readiness")
    if "manual" in joined or "depends on" in joined:
        headline_bits.append("dependency clearing")
    if not headline_bits:
        headline_bits.append("critical path execution")
    items = []
    for idx, t in enumerate(top, 1):
        items.append({
            "rank": idx,
            "label": t["label"],
            "owner": t["owner"],
            "summary": t["description"],
            "criticality": _criticality_label(t["score"]),
            "rationale": "; ".join(t["reasons"]) or "High-ranked open task",
        })
    return {
        "mode": "heuristic",
        "headline": f"Top outstanding work is concentrated around {', '.join(headline_bits)}.",
        "summary": "Tasks ranked by phase, blocker, dependency, and regulatory signals.",
        "items": items,
    }


async def _maybe_ai_summary(tasks: list[dict]) -> dict | None:
    open_tasks = [t for t in tasks if not t["done"]]
    if not open_tasks:
        return None
    candidates = [
        {"label": t["label"], "owner": t["owner"], "description": t["description"],
         "heuristic_score": t["score"], "signals": t["reasons"]}
        for t in open_tasks[:8]
    ]
    prompt = (
        "Summarize the most critical outstanding tasks for the top of an internal app. "
        "Return strict JSON with keys headline, summary, and items. "
        "items must be an array ordered by criticality descending and each item must include "
        "label, owner, summary, criticality, and rationale. Use 3 to 5 items total. "
        "Be concise, concrete, and do not mention completed work.\n\n"
        f"Outstanding task candidates:\n{json.dumps(candidates, indent=2)}"
    )
    try:
        response = await asyncio.to_thread(
            _ws.api_client.do,
            method="POST",
            path=f"/api/2.0/serving-endpoints/{SUMMARY_MODEL_ENDPOINT}/invocations",
            body={
                "messages": [
                    {"role": "system", "content": "You are a concise project-management summarizer. Output valid JSON only."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
                "max_tokens": 700,
            },
        )
        content = ""
        choices = response.get("choices") or []
        if choices:
            msg = choices[0].get("message") or {}
            c = msg.get("content")
            if isinstance(c, str):
                content = c
        if not content:
            return None
        start = content.find("{")
        end = content.rfind("}")
        if start == -1 or end == -1:
            return None
        payload = json.loads(content[start:end + 1])
        if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
            return None
        cleaned = []
        for idx, item in enumerate(payload["items"][:SUMMARY_ITEM_LIMIT], 1):
            if not isinstance(item, dict):
                continue
            cleaned.append({
                "rank": idx,
                "label": item.get("label", "Unlabeled"),
                "owner": item.get("owner", "Unassigned"),
                "summary": item.get("summary", ""),
                "criticality": item.get("criticality", "High"),
                "rationale": item.get("rationale", ""),
            })
        if not cleaned:
            return None
        return {
            "mode": "ai",
            "headline": payload.get("headline", "Outstanding tasks ranked by criticality"),
            "summary": payload.get("summary", ""),
            "items": cleaned,
        }
    except Exception as e:
        logger.warning("AI summary unavailable: %s", e)
        return None


_PRIORITY_SCORES = {"critical": 150, "high": 100, "medium": 60, "low": 30}


def _agent_task_to_dict(row) -> dict:
    """Map an agent_tasks row to the dict shape used by summary functions."""
    priority = row[6] or "medium"
    return {
        "id": row[0],
        "label": row[1],
        "owner": row[2],
        "description": (row[3] or "") + ("\n" + row[11] if row[11] else ""),
        "done": row[4] == "completed",
        "score": _PRIORITY_SCORES.get(priority, 60),
        "reasons": [f"priority: {priority}"] + ([f"depends on: {row[7]}"] if row[7] else []),
        "criticality": "Critical" if priority == "critical" else priority.capitalize(),
        "created_at": row[13].isoformat() if row[13] else None,
        "updated_at": row[14].isoformat() if row[14] else None,
    }


@app.get("/api/summary")
async def get_summary():
    """Summarize the most critical outstanding tasks.

    Tries the authoritative public.agent_tasks first; falls back to
    task_board.tasks if the SP lacks permission on public schema.
    """
    _require_db()
    try:
        conn = _get_conn()
        source = "agent_tasks"
        try:
            try:
                rows = conn.execute(
                    "SELECT id, task_code, agent_role, title, status, phase, priority, "
                    "depends_on, assigned_by, assigned_date, completed_date, status_notes, "
                    "demo_beat, created_at, updated_at "
                    "FROM public.agent_tasks "
                    "ORDER BY CASE priority "
                    "  WHEN 'critical' THEN 1 WHEN 'high' THEN 2 "
                    "  WHEN 'medium' THEN 3 ELSE 4 END, task_code ASC"
                ).fetchall()
                tasks = [_agent_task_to_dict(r) for r in rows]
            except Exception as agent_err:
                logger.warning("agent_tasks not accessible (%s), falling back to task_board.tasks", agent_err)
                source = "task_board"
                rows = conn.execute(
                    f"SELECT id, label, owner, description, done, score, reasons, created_at, updated_at "
                    f"FROM {SCHEMA_NAME}.tasks ORDER BY score DESC, label ASC"
                ).fetchall()
                tasks = [_task_row_to_dict(r) for r in rows]
        finally:
            conn.close()
        payload = await _maybe_ai_summary(tasks)
        if payload is None:
            payload = _build_summary_from_tasks(tasks)
        payload["outstanding_count"] = sum(1 for t in tasks if not t["done"])
        payload["total_count"] = len(tasks)
        payload["source"] = source
        payload["generated_at"] = datetime.now(timezone.utc).isoformat()
        return payload
    except Exception as e:
        logger.error("Summary failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ── Stats ─────────────────────────────────────────────────────────────

@app.get("/api/stats")
async def get_stats():
    """Quick stats for the header bar.

    Tries public.agent_tasks first; falls back to task_board.tasks.
    """
    _require_db()
    try:
        conn = _get_conn()
        try:
            try:
                row = conn.execute(
                    "SELECT COUNT(*), "
                    "SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END), "
                    "COUNT(DISTINCT agent_role) "
                    "FROM public.agent_tasks"
                ).fetchone()
            except Exception:
                row = conn.execute(
                    f"SELECT COUNT(*), SUM(CASE WHEN done THEN 1 ELSE 0 END), "
                    f"COUNT(DISTINCT owner) FROM {SCHEMA_NAME}.tasks"
                ).fetchone()
            return {
                "tasks": row[0] or 0,
                "done": row[1] or 0,
                "agents": row[2] or 0,
            }
        finally:
            conn.close()
    except Exception as e:
        logger.error("Stats failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ── Static frontend ──────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    html_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "static", "index.html"
    )
    with open(html_path, "r") as fh:
        return HTMLResponse(content=fh.read())


# ── Entrypoint ───────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("DATABRICKS_APP_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
