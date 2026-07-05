"""Interview Prep app — FastAPI backend.

Run:  .venv/bin/uvicorn app.backend.main:app --reload --port 8000
"""
import json
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from . import generator, llm, runner, runner_py, store

PRIVATE_FIELDS = ("reference_sql", "reference_solution", "hint_notes", "tests", "checks", "function_name")

ROOT = Path(__file__).resolve().parents[2]
BANK = ROOT / "problems" / "bank"

app = FastAPI(title="Interview Prep")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- problem bank ----------

def _load_problems():
    problems = {}
    for f in sorted(BANK.glob("**/*.json")):
        p = json.loads(f.read_text())
        problems[p["id"]] = p
    return problems


@app.get("/api/problems")
def list_problems():
    status = store.solved_map()
    return [
        {
            "id": p["id"], "area": p["area"], "topic": p["topic"],
            "difficulty": p["difficulty"], "title": p["title"],
            "status": status.get(p["id"], "unsolved"),
        }
        for p in _load_problems().values()
    ]


@app.get("/api/problems/{pid}")
def get_problem(pid: str):
    p = _load_problems().get(pid)
    if not p:
        raise HTTPException(404, "problem not found")
    public = {k: v for k, v in p.items() if k not in PRIVATE_FIELDS}
    public["draft"] = store.get_draft(pid)
    return public


@app.get("/api/schema")
def db_schema():
    """Tables + columns + 3 sample rows of the practice DB, for the sidebar."""
    res = runner.run_sql(
        "SELECT table_name, column_name, data_type FROM information_schema.columns "
        "WHERE table_schema='main' ORDER BY table_name, ordinal_position"
    )
    if not res["ok"]:
        raise HTTPException(500, res["error"])
    tables = {}
    for t, c, d in res["rows"]:
        tables.setdefault(t, {"columns": [], "sample": []})["columns"].append({"column": c, "type": d})
    for t in tables:
        sample = runner.run_sql(f'SELECT * FROM "{t}" LIMIT 3')
        if sample["ok"]:
            tables[t]["sample"] = sample["rows"]
    return tables


# ---------- run / submit / drafts ----------

class CodeIn(BaseModel):
    problem_id: str
    code: str


@app.post("/api/run")
def run_code(body: CodeIn):
    p = _load_problems().get(body.problem_id)
    if not p:
        raise HTTPException(404, "problem not found")
    store.save_draft(body.problem_id, body.code)
    if p["area"] == "design":
        raise HTTPException(400, "Design problems aren't executed — use AI feedback.")
    if p["area"] == "sql":
        return runner.run_sql(body.code)
    return runner_py.run_python(body.code, p)


@app.post("/api/submit")
def submit(body: CodeIn):
    p = _load_problems().get(body.problem_id)
    if not p:
        raise HTTPException(404, "problem not found")
    store.save_draft(body.problem_id, body.code)
    if p["area"] == "design":
        raise HTTPException(400, "Design problems aren't graded — use AI feedback.")
    if p["area"] == "sql":
        graded = runner.grade_sql(body.code, p["reference_sql"], p.get("order_matters", False))
        graded.pop("expected", None)  # don't leak the full expected table
    else:
        graded = runner_py.grade_python(body.code, p)
    store.save_attempt(body.problem_id, body.code, graded["passed"])
    return graded


@app.post("/api/draft")
def draft(body: CodeIn):
    store.save_draft(body.problem_id, body.code)
    return {"ok": True}


@app.post("/api/hint")
def get_hint(body: CodeIn):
    p = _load_problems().get(body.problem_id)
    if not p:
        raise HTTPException(404, "problem not found")
    store.save_draft(body.problem_id, body.code)
    level = store.next_hint_level(body.problem_id)
    try:
        return {"level": min(level, 3), "text": llm.hint(p, body.code, level)}
    except RuntimeError as e:
        raise HTTPException(503, str(e))


@app.post("/api/feedback")
def get_feedback(body: CodeIn):
    p = _load_problems().get(body.problem_id)
    if not p:
        raise HTTPException(404, "problem not found")
    store.save_draft(body.problem_id, body.code)
    if p["area"] == "design":
        summary = "(design write-up — nothing is executed; judge the text/diagram itself)"
    elif p["area"] == "sql":
        res = runner.run_sql(body.code)
        if res["ok"]:
            preview = [res["columns"]] + res["rows"][:10]
            summary = f"Query ran OK, {len(res['rows'])} row(s). First rows:\n{preview}"
        else:
            summary = f"Query FAILED with error: {res['error']}"
    else:
        res = runner_py.run_python(body.code, p)
        if res["ok"]:
            summary = f"Code ran OK. stdout (may be empty):\n{res['stdout'][:1500]}"
        else:
            summary = f"Code FAILED with error: {res['error']}"
    try:
        return {"text": llm.feedback(p, body.code, summary)}
    except RuntimeError as e:
        raise HTTPException(503, str(e))


class ChatIn(BaseModel):
    messages: list  # [{role, content}]
    context: Optional[str] = None


@app.post("/api/chat")
def chat(body: ChatIn):
    try:
        return {"text": llm.free_chat(body.messages, body.context)}
    except RuntimeError as e:
        raise HTTPException(503, str(e))


@app.post("/api/generate")
def generate_start():
    if generator.JOB["running"]:
        raise HTTPException(409, "generation already running")
    generator.start()
    return {"ok": True}


@app.get("/api/generate/status")
def generate_status():
    return generator.JOB


@app.get("/api/problems/{pid}/attempts")
def attempts(pid: str):
    return store.attempts_for(pid)
