---
name: review
description: Review the user's attempt at the active problem - read their code/query + real output, verify correctness against ground truth, critique the reasoning, and update the skills map. Args - optional path to the problem file.
---

Act as the **mentor** agent (see `.claude/agents/mentor.md`).

1. Read the active problem file (the one just practiced, or the path arg). Read it now since the
   user has changed it.
2. **Verify ground truth**: run the expected SQL/Python via Bash against `db/practice.db` or
   `data/customers.csv` and compare to the user's output. Don't guess correctness.
3. Critique the **approach**, not just pass/fail: correctness, complexity, edge cases, and the
   idiomatic/scalable alternative. Assign root-cause tag(s).
4. Write feedback to `feedback.md` next to the problem AND summarize in chat.
   **Do not edit the user's notebook** unless they explicitly asked.
5. Update `profile/skills-map.md` (level + tags + last seen) and append to today's
   `sessions/YYYY-MM-DD.md`. If a tag has now appeared ≥2×, suggest running `/teach` on it.
6. If the concept warrants spaced repetition, add/update a row in `profile/spaced-repetition.md`.
