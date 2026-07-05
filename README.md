# 🏋️ Interview Gym

A **local, offline, LeetCode-style practice app** for data science / ML engineer interviews — SQL, Python/DSA, applied ML, and system design — with an AI mentor that runs entirely on your own machine.

Built for daily grinding: open the app, pick a problem, write code in a real editor, hit **Run**, hit **Submit**, get graded instantly. When you're stuck, ask the built-in mentor for an escalating hint. Everything stays on your laptop; nothing costs tokens.

## Why it exists

Interview prep platforms are great until you want: your own dataset flavor, an AI coach that doesn't dump solutions, zero subscription, and privacy. This runs against a seeded ride-hailing + streaming DuckDB database and a churn CSV — realistic enough for Uber/Netflix-style questions — and uses a local LLM (via Ollama) for hints, feedback, chat, and even **generating new verified problems on demand**.

## Features

- **LeetCode-style problem screen** — prompt left, Monaco editor right, results below; drag-resizable panels; ⌘↩ Run / ⌘⇧↩ Submit
- **Four problem areas** — SQL (graded against a hidden reference query), Python/DSA (hidden test cases), applied ML (checks on the variables you define), system design (markdown write-up + AI rubric critique)
- **38+ verified problems**, from "very easy" refreshers to hard, incl. Netflix-flavored ones
- **✨ Generate new problems** — one button; the local LLM writes a problem per area and the backend *executes the reference solution to verify it* before it enters the bank
- **AI mentor, 100% local** — escalating Socratic hints (never dumps the answer), structured feedback with root-cause tags, and a free-form chat drawer that can see your current code
- **📖 Rules popup** — 16 instant cheat-sheets (SQL execution order, window functions, NULL traps, Python collections, confusion matrix, leakage…)
- **🍅 Pomodoro** — 50/10 with gentle sounds, survives reloads
- **Progress saved automatically** — every attempt, draft autosave, solved/attempted status, all in a local SQLite file

## Stack

FastAPI + DuckDB + SQLite backend · React (Vite) + Monaco frontend · Ollama (`qwen3-coder:30b` by default) for the mentor. No cloud, no accounts, no telemetry.

## Get started

See **[REPRODUCE.md](REPRODUCE.md)** for full setup (~15 minutes + model download). Then:

```bash
./start.sh          # opens http://localhost:5173
```

## Does it need internet?

Only for initial setup (downloading dependencies and the LLM). After that: **no** — solving, grading, progress, hints, chat, and problem generation all run offline.

## License / status

Personal project, shared as-is. Problems are original or classic-pattern reimplementations. PRs and issues welcome.
