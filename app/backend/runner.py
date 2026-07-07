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


def _mismatch_detail(u, r):
    """Same shape, wrong values: say where and, if it smells like rounding, say so."""
    numeric_close = True
    for ru, rr in zip(u, r):
        for a, b in zip(ru, rr):
            if a == b:
                continue
            if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
                if abs(a - b) > 0.51:
                    numeric_close = False
            else:
                numeric_close = False
    if numeric_close:
        return "Values are very close but not exact — check your rounding (round the aggregate, not each row) and decimal places."
    for i, (ru, rr) in enumerate(zip(u, r)):
        for j, (a, b) in enumerate(zip(ru, rr)):
            if a != b and not (isinstance(a, (int, float)) and isinstance(b, (int, float))
                               and not isinstance(a, bool) and abs(a - b) <= 1e-4):
                return (f"Right shape, wrong values — first difference at row {i + 1}, column {j + 1} "
                        f"(yours: {a!r}). Ask 🧠 AI feedback to interpret your approach.")
    return "Row values don't match the expected result."


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
        nu, nr = len(user["rows"]), len(ref["rows"])
        if nu != nr:
            detail = f"Expected {nr} row(s), your query returned {nu}."
            if nu > nr * 3:
                detail += " That's a much finer grain than asked — are you grouping by extra columns (or missing the GROUP BY entirely)?"
            elif nu > nr:
                detail += " A few extra rows — check for a join fan-out or a missing filter."
            elif nu == 0:
                detail += " Zero rows — your WHERE clause probably filters everything out."
            else:
                detail += " Missing rows — check your filters, or a JOIN dropping rows (INNER vs LEFT)."
        elif len(user["columns"]) != len(ref["columns"]):
            detail = f"Expected {len(ref['columns'])} column(s), got {len(user['columns'])}. Column names don't matter, but the count and order do."
        else:
            detail = _mismatch_detail(u, r)
    if len(user["rows"]) > ROW_LIMIT:  # cap what goes back to the UI
        user = {**user, "rows": user["rows"][:ROW_LIMIT], "truncated": True}
    return {"passed": passed, "error": None, "detail": detail, "result": user, "expected": ref}
