---
name: diagnose
description: Run a quick diagnostic across Python+DSA, SQL, ML/DS, and system design to build or refresh the weakness map. Use at the start, or every ~2 weeks.
---

Act as the **mentor** agent (see `.claude/agents/mentor.md` for full pedagogy).

1. Read `profile/goals.md` and `profile/skills-map.md`.
2. Ask 1–2 short probing questions per area (8 total max) — conceptual, to reveal intuition,
   not trivia. Let the user answer in chat.
3. Grade by root cause. Update `profile/skills-map.md` levels + tags.
4. Output a 3-line summary: strongest area, weakest area, what to focus on first.

Keep it brisk — this is triage, not a full session.
