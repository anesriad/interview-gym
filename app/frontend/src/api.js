const BASE = "http://localhost:8000/api";

async function j(path, opts) {
  const res = await fetch(BASE + path, opts);
  if (!res.ok) throw new Error((await res.text()) || res.statusText);
  return res.json();
}

const post = (path, body) =>
  j(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });

export const api = {
  problems: () => j("/problems"),
  problem: (id) => j(`/problems/${id}`),
  schema: () => j("/schema"),
  attempts: (id) => j(`/problems/${id}/attempts`),
  run: (problem_id, code) => post("/run", { problem_id, code }),
  submit: (problem_id, code) => post("/submit", { problem_id, code }),
  draft: (problem_id, code) => post("/draft", { problem_id, code }),
  hint: (problem_id, code) => post("/hint", { problem_id, code }),
  feedback: (problem_id, code) => post("/feedback", { problem_id, code }),
  chat: (messages, context) => post("/chat", { messages, context }),
  generate: () => post("/generate", {}),
  generateStatus: () => j("/generate/status"),
};
