"""Execute user SQL against the practice DuckDB and grade against a reference query."""
import math
import duckdb

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PRACTICE_DB = ROOT / "db" / "practice.db"

ROW_LIMIT = 200  # rows returned to the UI


def run_sql(sql: str, limit: int = ROW_LIMIT):
    """Run SQL read-only. limit=None fetches everything (used for grading)."""
    try:
        con = duckdb.connect(str(PRACTICE_DB), read_only=True)
        try:
            cur = con.execute(sql)
            columns = [d[0] for d in cur.description] if cur.description else []
            rows = cur.fetchall() if limit is None else cur.fetchmany(limit + 1)
        finally:
            con.close()
    except Exception as e:
        return {"ok": False, "error": str(e)}
    truncated = limit is not None and len(rows) > limit
    if truncated:
        rows = rows[:limit]
    return {
        "ok": True,
        "columns": columns,
        "rows": [[_jsonable(v) for v in row] for row in rows],
        "truncated": truncated,
    }


def _jsonable(v):
    if v is None or isinstance(v, (int, float, str, bool)):
        return v
    return str(v)  # dates, timestamps, decimals


def _norm_cell(v):
    """Normalize a cell for comparison: round floats, stringify the rest."""
    if isinstance(v, bool):
        return v
    if isinstance(v, float):
        if math.isnan(v):
            return "nan"
        return round(v, 4)
    return v if isinstance(v, (int, str)) or v is None else str(v)


def _norm_rows(rows):
    return [tuple(_norm_cell(c) for c in row) for row in rows]


def grade_sql(user_sql: str, reference_sql: str, order_matters: bool = False):
    """Run both queries; compare results (values only, column names ignored)."""
    user = run_sql(user_sql, limit=None)
    if not user["ok"]:
        return {"passed": False, "error": user["error"], "result": None}
    ref = run_sql(reference_sql, limit=None)
    if not ref["ok"]:
        return {"passed": False, "error": f"internal: reference query failed: {ref['error']}", "result": user}

    u, r = _norm_rows(user["rows"]), _norm_rows(ref["rows"])
    if not order_matters:
        u, r = sorted(u, key=repr), sorted(r, key=repr)
    passed = u == r

    detail = None
    if not passed:
        if len(user["rows"]) != len(ref["rows"]):
            detail = f"Expected {len(ref['rows'])} row(s), got {len(user['rows'])}."
        elif len(user["columns"]) != len(ref["columns"]):
            detail = f"Expected {len(ref['columns'])} column(s), got {len(user['columns'])}."
        else:
            detail = "Row values don't match the expected result."
    if len(user["rows"]) > ROW_LIMIT:  # cap what goes back to the UI
        user = {**user, "rows": user["rows"][:ROW_LIMIT], "truncated": True}
    return {"passed": passed, "error": None, "detail": detail, "result": user, "expected": ref}
