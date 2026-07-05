"""Run Python/ML problems in an isolated subprocess with a timeout."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HARNESS = Path(__file__).parent / "py_harness.py"
PYTHON = ROOT / ".venv" / "bin" / "python"
TIMEOUT = 30  # seconds; ML training on 3k rows is well under this


def _invoke(job: dict):
    try:
        proc = subprocess.run(
            [str(PYTHON), str(HARNESS)],
            input=json.dumps(job), capture_output=True, text=True,
            timeout=TIMEOUT, cwd=ROOT,
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "stdout": "", "error": f"Timed out after {TIMEOUT}s — infinite loop?"}
    if proc.returncode != 0 or not proc.stdout.strip():
        return {"ok": False, "stdout": "", "error": (proc.stderr or "crashed with no output")[-3000:]}
    return json.loads(proc.stdout)


def run_python(code: str, problem: dict):
    return _invoke({"mode": "run", "code": code, "area": problem["area"]})


def grade_python(code: str, problem: dict):
    res = _invoke({
        "mode": "submit", "code": code, "area": problem["area"],
        "function_name": problem.get("function_name"),
        "tests": problem.get("tests"), "checks": problem.get("checks"),
    })
    if not res["ok"]:
        return {"passed": False, "error": res["error"], "stdout": res.get("stdout", ""), "tests": []}
    return {"passed": res["passed"], "error": None, "stdout": res.get("stdout", ""), "tests": res["tests"]}
