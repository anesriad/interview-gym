"""Subprocess harness for Python/ML problems.

Reads a JSON job from stdin: {mode, code, area, function_name?, tests?, checks?}
Prints a JSON result to stdout. Run with the project venv python; cwd = project root.

mode=run    → exec the code, return stdout/stderr.
mode=submit → run hidden function tests (python) or namespace checks (ml).
"""
import io
import json
import math
import sys
import traceback
from contextlib import redirect_stdout

DATA_CSV = "data/customers.csv"


def fresh_ns(area):
    ns = {"__name__": "__main__"}
    if area == "ml":
        import numpy as np
        import pandas as pd
        ns.update(pd=pd, np=np, df=pd.read_csv(DATA_CSV))
    return ns


def deep_eq(a, b, tol=1e-4):
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b or a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if math.isnan(a) if isinstance(a, float) else False:
            return isinstance(b, float) and math.isnan(b)
        return abs(a - b) <= tol
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return len(a) == len(b) and all(deep_eq(x, y, tol) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(deep_eq(a[k], b[k], tol) for k in a)
    return a == b


def jsonable(v):
    try:
        return json.loads(json.dumps(v, default=str))
    except Exception:
        return str(v)


def main():
    job = json.load(sys.stdin)
    code, area, mode = job["code"], job.get("area", "python"), job["mode"]
    out = io.StringIO()

    ns = fresh_ns(area)
    try:
        with redirect_stdout(out):
            exec(compile(code, "<your code>", "exec"), ns)
    except Exception:
        print(json.dumps({"ok": False, "stdout": out.getvalue()[-8000:],
                          "error": traceback.format_exc(limit=3)}))
        return

    if mode == "run":
        print(json.dumps({"ok": True, "stdout": out.getvalue()[-8000:], "error": None}))
        return

    # --- submit ---
    results = []
    if job.get("tests"):  # function tests (python/DSA)
        fn = ns.get(job["function_name"])
        if not callable(fn):
            print(json.dumps({"ok": False, "stdout": out.getvalue()[-8000:],
                              "error": f"Function `{job['function_name']}` is not defined."}))
            return
        for i, t in enumerate(job["tests"]):
            try:
                with redirect_stdout(out):
                    got = fn(*[json.loads(json.dumps(a)) for a in t["args"]])  # fresh copy of args
                got_j, exp = jsonable(got), t["expected"]
                if t.get("any_order") and isinstance(got_j, list) and isinstance(exp, list):
                    got_j, exp = sorted(got_j, key=repr), sorted(exp, key=repr)
                ok = deep_eq(got_j, exp, t.get("tol", 1e-4))
            except Exception:
                results.append({"name": f"test {i+1}", "passed": False, "args": jsonable(t["args"]),
                                "expected": t["expected"], "got": traceback.format_exc(limit=2)[-1500:]})
                continue
            results.append({"name": f"test {i+1}", "passed": ok, "args": jsonable(t["args"]),
                            "expected": t["expected"], "got": got_j})
    else:  # namespace checks (ml)
        for c in job.get("checks", []):
            try:
                with redirect_stdout(out):
                    got = eval(c["expr"], ns)
                got_j = jsonable(got)
                ok = deep_eq(got_j, c["expected"], c.get("tol", 1e-4))
            except Exception:
                results.append({"name": c.get("name", c["expr"]), "passed": False,
                                "expected": c["expected"], "got": traceback.format_exc(limit=2)[-1500:]})
                continue
            results.append({"name": c.get("name", c["expr"]), "passed": ok,
                            "expected": c["expected"], "got": got_j})

    print(json.dumps({"ok": True, "stdout": out.getvalue()[-8000:], "error": None,
                      "passed": all(r["passed"] for r in results), "tests": results}))


if __name__ == "__main__":
    main()
