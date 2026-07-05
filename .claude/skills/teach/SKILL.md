---
name: teach
description: Deep-dive teach one concept the user is weak on, with a "when you see X reach for Y" heuristic, then a fresh confirming problem. Args - optional "concept" (else picks a recurring weakness).
---

Act as the **mentor** agent in **teach mode** (see `.claude/agents/mentor.md`).

1. Concept: use the arg, else the top recurring tag in `profile/skills-map.md` (seen ≥2×).
2. Explain the mental model **concisely** with a concrete "when you see X, reach for Y" heuristic
   and the 1–2 traps that trip people up. Tight, not a lecture.
3. Create ONE fresh problem (notebook or design doc) that *requires* this pattern. Let the user
   attempt solo, then `/review`.
4. Add/refresh the concept in `profile/spaced-repetition.md` (interval 1) so it resurfaces.
