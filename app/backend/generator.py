"""On-demand problem generation: local LLM writes a problem per area, we verify it
by executing the reference solution before it enters the bank. Bad output → retry
with the error fed back; still bad → skip that area (never save unverified problems).
"""
import json
import re
import threading
from pathlib import Path

from . import llm, runner, runner_py

BANK = Path(__file__).resolve().parents[2] / "problems" / "bank"
AREAS = ["sql", "python", "ml", "design"]
RETRIES = 3

# job state polled by the frontend
JOB = {"running": False, "log": [], "added": []}


def _log(msg):
    JOB["log"].append(msg)


SCHEMA_DESC = """DuckDB tables (ride-hailing + streaming):
users(user_id INT, signup_date DATE, city TEXT, plan 'free'|'standard'|'premium')
trips(trip_id INT, user_id INT, request_ts TS, complete_ts TS (NULL if cancelled), city TEXT, distance_km FLOAT, fare_usd FLOAT, status 'completed'|'cancelled')
payments(payment_id INT, user_id INT, trip_id INT, amount_usd FLOAT, paid_ts TS, method 'card'|'wallet'|'cash')
content(content_id INT, title TEXT, genre TEXT, release_date DATE, duration_min INT)
sessions_watch(session_id INT, user_id INT, content_id INT, watch_ts TS, minutes_watched INT)
~500 users, ~4000 trips, data spans 2025-01 to 2025-07."""

DF_DESC = """Preloaded pandas DataFrame `df` (3000 rows, churn dataset), with pd/np available:
customer_id INT, tenure_months INT, monthly_charge FLOAT (has ~60 NaNs), plan 'basic'|'standard'|'premium',
support_calls INT, contract 'monthly'|'annual', churned 0|1"""

SPEC = {
    "sql": f"""{SCHEMA_DESC}

Write ONE new SQL interview problem (realistic analytics flavor, e.g. Uber/Netflix style).
Output ONLY a JSON object with exactly these keys:
{{"title": str, "topic": one of ["joins/aggregation","window functions","cohort/funnel"],
"difficulty": "easy"|"medium"|"hard", "prompt": str (markdown; state exact output columns and ordering),
"reference_sql": str (a correct DuckDB query producing the answer),
"order_matters": bool (true only if the prompt specifies ordering),
"hint_notes": str (private note for a coach: key idea + common mistake)}}""",
    "python": """Write ONE new Python DSA interview problem (arrays, strings, hashing, two pointers, stacks, graphs or DP).
Output ONLY a JSON object with exactly these keys:
{"title": str, "topic": str, "difficulty": "easy"|"medium"|"hard",
"prompt": str (markdown, include one worked example),
"starter_code": "def <fn>(...):\\n    pass\\n",
"function_name": str,
"tests": [5-7 objects {"args": [list of JSON args], "expected": JSON value}] (cover edge cases: empty, single element, ties),
"reference_solution": str (correct Python defining exactly that function),
"hint_notes": str (key idea + common mistake)}
Args and expected values must be plain JSON (numbers, strings, lists, bools, dicts with string keys).""",
    "ml": f"""{DF_DESC}

Write ONE new applied ML/statistics problem on this dataframe (pandas/sklearn/scipy available).
The user must define specific variables; grading evaluates expressions on their namespace.
Output ONLY a JSON object with exactly these keys:
{{"title": str, "topic": one of ["feature engineering","model selection/eval","stats/experimentation"],
"difficulty": "easy"|"medium"|"hard",
"prompt": str (markdown; name the exact variables to define and any exact recipe like random_state=42 so results are deterministic),
"starter_code": str (comment that df is preloaded + variable stubs),
"checks": [2-4 objects {{"name": str, "expr": str (python expr over the user's variables, e.g. "round(float(x), 3)"), "expected": null, "tol": 0.005}}],
"reference_solution": str (correct code defining those variables),
"hint_notes": str}}
Set every "expected" to null — the grader fills them by running your reference_solution. The reference must be deterministic (fixed seeds).""",
    "design": """Write ONE new system-design interview problem (realistic large-scale product feature, e.g. ride-hailing surge pricing, streaming recommendations feed, chat delivery).
Output ONLY a JSON object with exactly these keys:
{"title": str, "topic": "system design"|"ML system design", "difficulty": "medium"|"hard",
"prompt": str (markdown: scenario, scale assumptions, and a numbered structure: requirements/API/data model/architecture/estimates/tradeoffs; mention a mermaid block is welcome),
"starter_code": str (markdown skeleton with those numbered section headers),
"reference_solution": str (a grading RUBRIC in prose: what a strong answer must cover, the key numbers, the classic mistakes),
"hint_notes": str}""",
}


def _extract_json(text):
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        raise ValueError("no JSON object in LLM output")
    return json.loads(m.group(0))


def _next_id(area):
    prefix = {"sql": "sql", "python": "py", "ml": "ml", "design": "design"}[area]
    nums = [int(m.group(1)) for f in BANK.glob(f"{area}/{prefix}-x*.json")
            if (m := re.match(rf"{prefix}-x(\d+)", f.stem))]
    return f"{prefix}-x{(max(nums) + 1) if nums else 1:03d}"


def _existing_titles(area):
    return [json.loads(f.read_text()).get("title", "") for f in BANK.glob(f"{area}/*.json")]


def _verify(area, p):
    """Returns (ok, error). Mutates p to auto-fill expected values from the reference."""
    if area == "sql":
        res = runner.run_sql(p["reference_sql"])
        if not res["ok"]:
            return False, f"reference_sql failed: {res['error']}"
        if not res["rows"]:
            return False, "reference_sql returns 0 rows — the problem has an empty answer on this data; pick a different question"
        return True, None

    if area == "design":
        return (len(p.get("prompt", "")) > 200 and len(p.get("reference_solution", "")) > 200), "prompt or rubric too thin"

    # python / ml: run reference, auto-fill expected values, then re-grade
    probe = runner_py._invoke({
        "mode": "submit", "code": p["reference_solution"], "area": area,
        "function_name": p.get("function_name"),
        "tests": p.get("tests"),
        "checks": [{**c, "expected": "___fill___"} for c in p["checks"]] if p.get("checks") else None,
    })
    if not probe["ok"]:
        return False, f"reference_solution errored: {probe['error']}"
    key = "tests" if p.get("tests") else "checks"
    for spec_item, result in zip(p[key], probe["tests"]):
        if isinstance(result["got"], str) and "Traceback" in result["got"]:
            return False, f"reference raised on {result['name']}: {result['got'][:400]}"
        spec_item["expected"] = result["got"]
    graded = runner_py.grade_python(p["reference_solution"], {**p, "area": area})
    if not graded["passed"]:
        return False, "reference doesn't pass its own tests after fill (nondeterministic?)"
    return True, None


def _gen_area(area):
    avoid = ", ".join(t for t in _existing_titles(area) if t)[:600]
    base = SPEC[area] + f"\n\nDo NOT duplicate these existing problems: {avoid}\nBe creative but keep it solvable in 15-30 minutes."
    err = None
    for attempt in range(1, RETRIES + 1):
        _log(f"[{area}] generating (attempt {attempt}/{RETRIES})…")
        msg = base if not err else base + f"\n\nYour previous attempt failed verification: {err}\nFix that and output the corrected JSON."
        try:
            raw = llm.generate(msg)
            p = _extract_json(raw)
            required = {"title", "prompt", "hint_notes"} | (
                {"reference_sql"} if area == "sql" else {"reference_solution"})
            missing = required - set(p)
            if missing:
                err = f"missing keys: {missing}"
                continue
            ok, err = _verify(area, p)
            if not ok:
                _log(f"[{area}] ✗ rejected: {str(err)[:140]}")
                continue
            pid = _next_id(area)
            p.update(id=pid, area=area,
                     topic=p.get("topic", area), difficulty=p.get("difficulty", "medium"))
            (BANK / area / f"{pid}.json").write_text(json.dumps(p, indent=2) + "\n")
            JOB["added"].append(pid)
            _log(f"[{area}] ✓ added: “{p['title']}” ({pid})")
            return
        except Exception as e:
            err = str(e)[:300]
            _log(f"[{area}] ✗ error: {err[:140]}")
    _log(f"[{area}] gave up after {RETRIES} attempts — nothing saved for this area.")


def _run():
    try:
        for area in AREAS:
            _gen_area(area)
        _log(f"Done — {len(JOB['added'])} problem(s) added.")
    finally:
        JOB["running"] = False


def start():
    JOB["running"] = True
    JOB["log"] = []
    JOB["added"] = []
    threading.Thread(target=_run, daemon=True).start()
