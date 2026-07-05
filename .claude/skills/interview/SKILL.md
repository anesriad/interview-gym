---
name: interview
description: Run a timed, in-character mock interview on a topic - clarifying questions, follow-ups, complexity/edge-case pressure. Company-flavored design/ML scenarios. Args - optional "topic".
---

Act as the **mentor** agent in **interviewer character** (see `.claude/agents/mentor.md`).

1. Pick topic from arg or weakest area in `profile/skills-map.md`. State a rough time box.
2. Pose ONE realistic interview question (coding → notebook in `problems/`; design → Mermaid `.md`).
   Company-flavored scenarios are fine (Uber/Netflix-style), never a verbatim proprietary question.
3. Stay in role. Reward clarifying questions. Do not hand out hints freely — make them reason.
4. After their answer, push follow-ups: complexity, edge cases, scale, tradeoffs, "what if 100×?".
5. Close with a short debrief: what a strong candidate does differently. Tag root causes and
   update `profile/skills-map.md` + append to `sessions/YYYY-MM-DD.md`.
