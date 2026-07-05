---
name: practice
description: Generate one practice problem (topic optional; else pick from weakest area) as a notebook or design doc, then step back so the user solves solo. Args - optional "topic difficulty".
---

Act as the **mentor** agent (see `.claude/agents/mentor.md`).

1. Topic: use the arg if given; else read `profile/skills-map.md` and pick the weakest / due topic.
2. Create the problem file, then **stop touching it**:
   - Python/DSA/ML → a `.ipynb` in `problems/<area>/` with: prompt cell, setup cell
     (loads `data/customers.csv` or the `%sql` connection to `db/practice.db` as needed),
     hidden/expected-answer note for yourself, and an empty solution cell.
   - System design → a `.md` in `problems/design/` with the scenario + an empty Mermaid block.
3. Tell the user (in chat, briefly) the file path and that they should solve solo, then run
   `/review` when ready. Do NOT hint yet.
4. Stay quiet until they ask for a hint or run `/review`. Hints escalate; never dump the solution.
