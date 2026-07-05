"""SQLite persistence: attempts history and per-problem drafts."""
import sqlite3
import time
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "app" / "progress.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    problem_id TEXT NOT NULL,
    code TEXT NOT NULL,
    passed INTEGER NOT NULL,
    ts REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS drafts (
    problem_id TEXT PRIMARY KEY,
    code TEXT NOT NULL,
    updated_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS hints (
    problem_id TEXT PRIMARY KEY,
    count INTEGER NOT NULL
);
"""


def _con():
    con = sqlite3.connect(DB_PATH)
    con.executescript(SCHEMA)
    return con


def save_attempt(problem_id: str, code: str, passed: bool):
    with _con() as con:
        con.execute(
            "INSERT INTO attempts (problem_id, code, passed, ts) VALUES (?,?,?,?)",
            (problem_id, code, int(passed), time.time()),
        )


def attempts_for(problem_id: str):
    with _con() as con:
        rows = con.execute(
            "SELECT code, passed, ts FROM attempts WHERE problem_id=? ORDER BY ts DESC LIMIT 50",
            (problem_id,),
        ).fetchall()
    return [{"code": c, "passed": bool(p), "ts": ts} for c, p, ts in rows]


def solved_map():
    """problem_id -> 'solved' | 'attempted'"""
    with _con() as con:
        rows = con.execute(
            "SELECT problem_id, MAX(passed) FROM attempts GROUP BY problem_id"
        ).fetchall()
    return {pid: ("solved" if p else "attempted") for pid, p in rows}


def save_draft(problem_id: str, code: str):
    with _con() as con:
        con.execute(
            "INSERT INTO drafts (problem_id, code, updated_at) VALUES (?,?,?) "
            "ON CONFLICT(problem_id) DO UPDATE SET code=excluded.code, updated_at=excluded.updated_at",
            (problem_id, code, time.time()),
        )


def next_hint_level(problem_id: str) -> int:
    """Increment and return the hint counter for this problem (capped later by llm.py)."""
    with _con() as con:
        con.execute(
            "INSERT INTO hints (problem_id, count) VALUES (?,1) "
            "ON CONFLICT(problem_id) DO UPDATE SET count=count+1",
            (problem_id,),
        )
        return con.execute("SELECT count FROM hints WHERE problem_id=?", (problem_id,)).fetchone()[0]


def get_draft(problem_id: str):
    with _con() as con:
        row = con.execute("SELECT code FROM drafts WHERE problem_id=?", (problem_id,)).fetchone()
    return row[0] if row else None
