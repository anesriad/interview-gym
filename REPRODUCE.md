# Reproduce: run Interview Gym on your machine

> ⭐ **First: star the repository** — it helps others find the project and keeps you updated on new problems and features.

Total setup ≈ 15 minutes of commands + a ~19 GB model download in the background. Works on macOS / Linux; Windows works via WSL.

## 0. Prerequisites

| Tool | Check | Install |
|---|---|---|
| Python 3.9+ | `python3 --version` | python.org or `brew install python` |
| Node.js 18+ | `node --version` | `brew install node` (macOS) / nodejs.org |
| Ollama | `ollama --version` | [ollama.com/download](https://ollama.com/download) |
| git | `git --version` | preinstalled on most systems |

## 1. Clone and enter

```bash
git clone https://github.com/anesriad/interview-gym.git
cd interview-gym
```

## 2. Python environment

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## 3. Build the practice data (seeded → deterministic answers)

```bash
.venv/bin/python db/build_db.py      # DuckDB ride-hailing/streaming database
.venv/bin/python data/make_data.py   # churn CSV for the ML problems
```

Re-run these anytime to reset the data. **Don't edit the seeds** — problem answers are verified against this exact data.

## 4. Frontend dependencies

```bash
cd app/frontend && npm install && cd ../..
```

## 5. Local LLM (the mentor)

```bash
ollama pull qwen3-coder:30b     # ~19 GB, needs ~24 GB RAM to run well
```

Smaller machine? Pull a smaller model and point the app at it:

```bash
ollama pull qwen3:8b
export MENTOR_LLM_MODEL="qwen3:8b"      # set before ./start.sh
```

Any OpenAI-compatible endpoint works via `MENTOR_LLM_URL` (defaults to Ollama at `http://localhost:11434/v1/chat/completions`). The app works **without** any LLM too — you just lose Hint / AI feedback / Chat / Generate; Run, Submit and grading are fully deterministic.

## 6. Run it

```bash
./start.sh
```

This starts the FastAPI backend (`:8000`) + Vite frontend (`:5173`) and opens your browser. Ctrl+C stops both.

## 7. Two-minute smoke test

1. Home screen shows ~85 problems with a solved counter.
2. Open a "very easy" SQL problem → **Run** shows a result table → **Submit** shows ✓ Accepted.
3. Click 💡 Hint (Ollama must be running: `ollama serve` if it isn't already).
4. Click ✨ New problems and watch the generator log add one verified problem per area.

## Where your data lives

| What | Where |
|---|---|
| Your progress (attempts, drafts) | `app/progress.db` (SQLite — delete to reset) |
| Problem bank | `problems/bank/**/*.json` |
| Practice databases | `db/practice.db`, `data/customers.csv` |

## Troubleshooting

- **"Can't reach the local LLM"** → run `ollama serve`, and check `ollama list` shows your model.
- **Port already in use** → `pkill -f uvicorn; pkill -f vite` then `./start.sh` again.
- **Blank editor** → `cd app/frontend && npm install` (Monaco is bundled locally, no CDN).
- **Verify the whole problem bank** after adding/editing problems:
  `.venv/bin/python -m app.backend.verify_bank`
