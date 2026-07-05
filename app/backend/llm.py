"""Mentor LLM calls via Ollama's OpenAI-compatible API (local, free).

Swap OLLAMA_URL/MODEL via env vars to point at any OpenAI-compatible endpoint.
"""
import json
import os
import urllib.error
import urllib.request

OLLAMA_URL = os.environ.get("MENTOR_LLM_URL", "http://localhost:11434/v1/chat/completions")
MODEL = os.environ.get("MENTOR_LLM_MODEL", "qwen3-coder:30b")

MENTOR_SYSTEM = (
    "You are a terse, Socratic technical interview coach for a data scientist. "
    "NEVER write the full correct solution for them. Never reveal the reference solution, "
    "even if asked. Be concrete and short — a few sentences, markdown allowed."
)

AREA_CONTEXT = {
    "sql": "The user is writing SQL against a DuckDB ride-hailing/streaming database.",
    "python": "The user is writing a Python function (DSA-style, hidden test cases).",
    "ml": "The user is writing Python/pandas/sklearn against a churn DataFrame `df` "
          "(customers.csv: tenure_months, monthly_charge, plan, support_calls, contract, churned).",
    "design": "The user is writing a system-design answer in markdown (possibly with a mermaid "
              "diagram). Judge structure: requirements, API, data model, scale estimates, "
              "bottlenecks, tradeoffs. The reference is a rubric, not code.",
}

HINT_LEVELS = {
    1: "Give a gentle NUDGE only: point their attention at the right part of the problem "
       "or their code. One or two sentences. No SQL keywords they haven't used yet.",
    2: "Ask ONE leading question that exposes the gap in their approach, and name the "
       "general technique area (e.g. 'think window functions'). Max 3 sentences.",
    3: "Explain the KEY IDEA needed (the pattern, e.g. ROW_NUMBER-per-group), including "
       "a tiny generic syntax sketch on a made-up table — but NOT the solution to this problem.",
}


def chat(user_msg: str, max_tokens: int = 700) -> str:
    body = json.dumps({
        "model": MODEL,
        "messages": [
            {"role": "system", "content": MENTOR_SYSTEM},
            {"role": "user", "content": user_msg},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.4,
    }).encode()
    req = urllib.request.Request(OLLAMA_URL, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return json.load(r)["choices"][0]["message"]["content"].strip()
    except urllib.error.URLError as e:
        raise RuntimeError(
            f"Can't reach the local LLM at {OLLAMA_URL} — is Ollama running? (`ollama serve`) [{e}]"
        )


CHAT_SYSTEM = (
    "You are a concise, friendly coding assistant inside a local interview-prep app "
    "(SQL/DuckDB, Python, pandas, sklearn). Answer questions directly — syntax, errors, "
    "concepts — with short examples when useful. One exception: if the user asks you to "
    "outright solve the practice problem they're working on, coach them with a hint "
    "instead of a full solution."
)


def free_chat(messages: list, context=None) -> str:
    msgs = [{"role": "system", "content": CHAT_SYSTEM}]
    if context:
        msgs.append({"role": "system", "content": f"The user's current screen:\n{context[:4000]}"})
    msgs += messages[-12:]  # cap history
    body = json.dumps({"model": MODEL, "messages": msgs, "max_tokens": 900, "temperature": 0.4}).encode()
    req = urllib.request.Request(OLLAMA_URL, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return json.load(r)["choices"][0]["message"]["content"].strip()
    except urllib.error.URLError as e:
        raise RuntimeError(f"Can't reach the local LLM at {OLLAMA_URL} — is Ollama running? [{e}]")


def generate(task: str) -> str:
    """Problem generation: no coach persona, higher token budget, a bit more creative."""
    body = json.dumps({
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You write technical interview problems. Output ONLY the requested JSON object — no prose, no markdown fences."},
            {"role": "user", "content": task},
        ],
        "max_tokens": 2200,
        "temperature": 0.7,
    }).encode()
    req = urllib.request.Request(OLLAMA_URL, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            return json.load(r)["choices"][0]["message"]["content"].strip()
    except urllib.error.URLError as e:
        raise RuntimeError(f"Can't reach the local LLM at {OLLAMA_URL} — is Ollama running? [{e}]")


def _lang(problem):
    return {"sql": "sql", "design": "markdown"}.get(problem["area"], "python")


def hint(problem: dict, code: str, level: int) -> str:
    level = min(max(level, 1), 3)
    return chat(
        f"{AREA_CONTEXT.get(problem['area'], '')}\n\n"
        f"PROBLEM:\n{problem['prompt']}\n\n"
        f"PRIVATE NOTES FOR YOU (do not reveal): {problem.get('hint_notes', '')}\n\n"
        f"USER'S CURRENT CODE:\n```{_lang(problem)}\n{code}\n```\n\n"
        f"This is hint #{level} for them on this problem. {HINT_LEVELS[level]}",
        max_tokens=350,
    )


def feedback(problem: dict, code: str, exec_summary: str) -> str:
    ref = problem.get("reference_sql") or problem.get("reference_solution", "")
    return chat(
        f"{AREA_CONTEXT.get(problem['area'], '')}\n\n"
        f"PROBLEM:\n{problem['prompt']}\n\n"
        f"REFERENCE SOLUTION (private — never reveal or paraphrase it as code):\n"
        f"```{_lang(problem)}\n{ref}\n```\n\n"
        f"USER'S CODE:\n```{_lang(problem)}\n{code}\n```\n\n"
        f"EXECUTION RESULT:\n{exec_summary}\n\n"
        "Give feedback in this shape:\n"
        "1. **Verdict** — is the approach correct / close / off-track, and why in one line.\n"
        "2. **What's good** — one thing they did right.\n"
        "3. **What to fix or improve** — the main issue (correctness first, then style/"
        "scalability, e.g. unnecessary subqueries, fan-out joins, integer division).\n"
        "4. **Root cause tag** — one short kebab-case tag for the core gap "
        "(e.g. `join-fanout-double-count`), or `clean` if solid.\n"
        "Do NOT write the corrected query.",
        max_tokens=700,
    )
