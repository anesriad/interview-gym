# Interview Prep App — architecture & build log

A local, LeetCode-style practice app. Runs entirely on this machine; day-to-day
practice costs zero tokens (deterministic grading; the LLM is only used for
hints/feedback via local Ollama).

## How to start it

```
./start.sh          # starts both servers and opens the app
```

- App (frontend): http://localhost:5173
- API (backend):  http://localhost:8000

## Architecture (simple version)

```
Browser (React + Monaco editor)  ←→  FastAPI backend  ←→  DuckDB db/practice.db   (SQL problems run here)
        localhost:5173                localhost:8000  ←→  SQLite app/progress.db  (attempts, drafts)
                                                      ←→  problems/bank/*.json    (the problem bank)
                                                      ←→  Ollama qwen3-coder:30b  (hints/feedback — phase 3)
```

### Pieces

| Path | What it is |
|---|---|
| `app/backend/main.py` | API routes: list/get problems, run, submit, drafts, attempts, schema |
| `app/backend/runner.py` | Executes SQL read-only against `db/practice.db`; grades by diffing vs the problem's hidden `reference_sql` |
| `app/backend/store.py` | SQLite persistence: attempt history + per-problem draft autosave |
| `app/frontend/` | React app (Vite). `ProblemList.jsx` = browser screen, `Problem.jsx` = split-pane solve screen |
| `problems/bank/sql/*.json` | Problem bank. Each file: prompt, starter code, hidden `reference_sql`, topic/difficulty. Verified against the real DB before adding |
| `app/progress.db` | Your progress (auto-created). Delete it to reset everything |

### How grading works (zero tokens)

- **Run** executes your SQL and shows the result table (capped at 200 rows for display).
- **Submit** runs your query *and* the hidden reference query on full results, compares
  values (order-insensitive unless the problem says ORDER BY matters, floats rounded to
  4 dp, column names ignored), and records the attempt.

### Keyboard shortcuts

- `⌘Enter` — Run
- `⌘⇧Enter` — Submit

## Build phases

- [x] **Phase 1 — SQL loop** (this): backend, problem screen with Monaco + schema
      sidebar, run/submit, draft autosave, attempt history, 5 verified SQL problems.
- [x] **Phase 2 — Python/ML problems**: user code runs in an isolated subprocess
      (`runner_py.py` + `py_harness.py`, 30s timeout, fresh state each Run — like
      LeetCode). Two grading modes: hidden **function tests** (python/DSA) and
      **namespace checks** (ml — `df` from `customers.csv` is preloaded with pandas/
      numpy/sklearn/scipy available; you define named variables like `auc`).
      Bank is now **34 verified problems** (12 SQL, 15 Python, 6 ML, 1 design),
      including a **very easy** refresher tier (basics of loops/strings/dicts/
      comprehensions + SELECT/GROUP BY) and Netflix-flavored problems per area.
      `python -m app.backend.verify_bank` re-verifies every reference solution and
      auto-fills ML expected values — run it whenever problems are added.
- [x] **Phase 3 (first slice) — Mentor buttons**: 💡 Hint (escalating 1→3: nudge →
      leading question → key idea; level persists per problem) and 🧠 AI feedback
      (verdict / good / fix / root-cause tag), served by local Ollama. Model + URL
      configurable via `MENTOR_LLM_MODEL` / `MENTOR_LLM_URL` env vars (`app/backend/llm.py`).
      Still to come in phase 3: free-form chat panel, tags saved into progress DB.
- [x] **Schema sample rows**: click a table name in the sidebar to see 3 example rows.
- [x] **💬 Mentor chat**: top-bar button on every screen; free-form chat with the local
      LLM, optional "include current problem & my code" context, history kept in the
      browser (trash icon clears it).
- [x] **📖 Rules popup**: 16 static cheat-sheet cards (SQL execution order, joins,
      windows, NULL traps, Python collections/sorting, confusion matrix, leakage…)
      in `app/frontend/src/rules.js` — no LLM, edit that file to add cards.
- [x] **🍅 Pomodoro**: 50 min focus / 10 min break, gentle tones, non-blocking banner;
      survives page navigation/reload; click the timer to stop.
- [x] **Resizable panels**: drag the divider between prompt/editor and between
      editor/results; sizes remembered.
- [x] **AI / LLM area**: 34 curated interview questions (LLM fundamentals, prompting,
      RAG, LLMOps, cost/latency, system design, real-world scenarios) answered in
      markdown like design problems, plus a **📗 Show answer** button that reveals the
      reference answer + takeaway (`/api/problems/{id}/answer`, area-gated). The
      generator also mints new AI/LLM questions (5 areas per ✨ run).
- [x] **Smarter wrong-answer diagnostics (SQL)**: failure messages explain the likely
      cause — grouping grain, join fan-out, zero rows from over-filtering, dropped
      rows from INNER vs LEFT, rounding near-misses, first mismatching cell.
- [x] **QoL**: ✓ Mark as done on text problems (design/ai) so they count as solved;
      difficulty sort toggle on the list; area chips renamed AI / LLM + SYSTEM DESIGN.
- [x] **Design problems (first slice)**: area `design` = markdown write-up in the
      editor (mermaid welcome), no Run/Submit; 🧠 AI feedback grades against a rubric
      stored in the problem file. Excalidraw whiteboard still planned (phase 5).
- [ ] **Phase 4 — Dashboard**: skill map, streaks, spaced-repetition queue.
- [ ] **Phase 5 — Design + interview mode**: Excalidraw whiteboard, timed interviews.
- [x] **✨ On-demand problem generation**: "New problems" button on the home screen →
      background job (one problem per area) with a live progress panel. The local LLM
      writes problem + reference solution; `app/backend/generator.py` verifies by
      executing the reference (SQL must return rows; python/ml expected values are
      filled from the reference run, then re-graded; 3 attempts with the error fed
      back, unverifiable problems are never saved). Generated ids look like `py-x001`.
