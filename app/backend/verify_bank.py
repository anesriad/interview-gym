"""Verify every problem in the bank by running its reference solution through the
real grading pipeline. For ml checks with expected=null, fill them in from the
reference run and rewrite the JSON.

Run:  .venv/bin/python -m app.backend.verify_bank
"""
import json
import sys
from pathlib import Path

from . import runner, runner_py

BANK = Path(__file__).resolve().parents[2] / "problems" / "bank"


def main():
    failures = 0
    for f in sorted(BANK.glob("**/*.json")):
        p = json.loads(f.read_text())
        pid = p["id"]

        if p["area"] in ("design", "ai"):
            print(f"{pid}: OK ({p['area']} — not executable)")
            continue

        if p["area"] == "sql":
            res = runner.grade_sql(p["reference_sql"], p["reference_sql"], p.get("order_matters", False))
            n = len(res["result"]["rows"]) if res.get("result") else 0
            if res["passed"] and n > 0:
                print(f"{pid}: OK ({n} rows)")
            else:
                print(f"{pid}: FAIL — {res.get('error') or 'empty result'}")
                failures += 1
            continue

        # python/ml: fill expected=null checks from the reference run first
        changed = False
        if p.get("checks") and any(c["expected"] is None for c in p["checks"]):
            probe = runner_py._invoke({
                "mode": "submit", "code": p["reference_solution"], "area": p["area"],
                "checks": [{**c, "expected": "___fill___"} for c in p["checks"]],
            })
            if not probe["ok"]:
                print(f"{pid}: FAIL — reference errored: {probe['error']}")
                failures += 1
                continue
            for c, r in zip(p["checks"], probe["tests"]):
                if c["expected"] is None:
                    c["expected"] = r["got"]
                    changed = True

        graded = runner_py.grade_python(p["reference_solution"], p)
        if graded["passed"]:
            if changed:
                f.write_text(json.dumps(p, indent=2) + "\n")
            filled = [f"{c['name']}={c['expected']}" for c in p.get("checks", [])]
            print(f"{pid}: OK" + (f" — filled: {', '.join(filled)}" if changed else f" ({len(graded['tests'])} tests)"))
        else:
            bad = [t for t in graded["tests"] if not t["passed"]]
            print(f"{pid}: FAIL — {graded.get('error') or bad[:2]}")
            failures += 1

    print(f"\n{'ALL VERIFIED' if failures == 0 else f'{failures} FAILURE(S)'}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
