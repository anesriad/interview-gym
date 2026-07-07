import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import Editor from "@monaco-editor/react";
import ReactMarkdown from "react-markdown";
import { api } from "./api";
import TopTools, { RulesModal, setChatContext } from "./Tools";

export default function Problem() {
  const { id } = useParams();
  const [problem, setProblem] = useState(null);
  const [schema, setSchema] = useState(null);
  const [code, setCode] = useState("");
  const [out, setOut] = useState(null); // {kind: 'run'|'submit', ...payload}
  const [busy, setBusy] = useState(false);
  const [showSchema, setShowSchema] = useState(true);
  const [openTable, setOpenTable] = useState(null); // table whose sample rows are shown
  const [mentor, setMentor] = useState(null); // {title, text} | {loading: title}
  const [rulesOpen, setRulesOpen] = useState(false);
  const [leftW, setLeftW] = useState(() => +localStorage.getItem("leftW") || 42); // % of window
  const [edH, setEdH] = useState(() => +localStorage.getItem("edH") || 55); // % of right pane
  const rightRef = useRef(null);

  const dragCols = (e) => {
    e.preventDefault();
    const move = (ev) => {
      const pct = Math.min(70, Math.max(20, (ev.clientX / window.innerWidth) * 100));
      setLeftW(pct);
      localStorage.setItem("leftW", pct);
    };
    const up = () => { window.removeEventListener("mousemove", move); window.removeEventListener("mouseup", up); };
    window.addEventListener("mousemove", move);
    window.addEventListener("mouseup", up);
  };

  const dragRows = (e) => {
    e.preventDefault();
    const box = rightRef.current.getBoundingClientRect();
    const move = (ev) => {
      const pct = Math.min(85, Math.max(15, ((ev.clientY - box.top) / box.height) * 100));
      setEdH(pct);
      localStorage.setItem("edH", pct);
    };
    const up = () => { window.removeEventListener("mousemove", move); window.removeEventListener("mouseup", up); };
    window.addEventListener("mousemove", move);
    window.addEventListener("mouseup", up);
  };

  // keep the chat drawer aware of what's on screen
  useEffect(() => {
    if (problem) setChatContext(`Problem "${problem.title}":\n${problem.prompt}\n\nUser's code so far:\n${code}`);
  }, [problem, code]);
  const codeRef = useRef("");
  codeRef.current = code;

  useEffect(() => {
    api.problem(id).then((p) => {
      setProblem(p);
      setCode(p.draft ?? p.starter_code ?? "");
      setOut(null);
      setDone(false);
    });
    api.schema().then(setSchema);
  }, [id]);

  // autosave draft every 5s if changed
  useEffect(() => {
    let last = "";
    const t = setInterval(() => {
      if (codeRef.current && codeRef.current !== last) {
        last = codeRef.current;
        api.draft(id, codeRef.current).catch(() => {});
      }
    }, 5000);
    return () => clearInterval(t);
  }, [id]);

  const isDesign = ["design", "ai"].includes(problem?.area); // text answers: no run/submit
  const hasAnswer = problem?.area === "ai";
  const [done, setDone] = useState(false);

  const markDone = useCallback(async () => {
    try {
      await api.markDone(id, codeRef.current);
      setDone(true);
    } catch (e) {
      setMentor({ title: "Mark done", text: `⚠️ ${e.message}` });
    }
  }, [id]);

  const showAnswer = useCallback(async () => {
    setMentor({ loading: "Answer" });
    try {
      const r = await api.answer(id);
      setMentor({ title: "📗 Answer", text: r.text });
    } catch (e) {
      setMentor({ title: "📗 Answer", text: `⚠️ ${e.message}` });
    }
  }, [id]);

  const run = useCallback(async () => {
    if (isDesign) return;
    setBusy(true);
    try {
      setOut({ kind: "run", ...(await api.run(id, codeRef.current)) });
    } finally {
      setBusy(false);
    }
  }, [id, isDesign]);

  const submit = useCallback(async () => {
    if (isDesign) return;
    setBusy(true);
    try {
      setOut({ kind: "submit", ...(await api.submit(id, codeRef.current)) });
    } finally {
      setBusy(false);
    }
  }, [id, isDesign]);

  const askMentor = useCallback(async (kind) => {
    const title = kind === "hint" ? "Hint" : "AI feedback";
    setMentor({ loading: title });
    try {
      const r = await api[kind](id, codeRef.current);
      setMentor({ title: kind === "hint" ? `Hint ${r.level}/3` : title, text: r.text });
    } catch (e) {
      setMentor({ title, text: `⚠️ ${e.message}` });
    }
  }, [id]);

  if (!problem) return <div className="page muted pad">Loading…</div>;

  return (
    <div className="split-page">
      <header className="topbar">
        <Link to="/" className="back">← Problems</Link>
        <h1>{problem.title}</h1>
        <span className={`pdiff diff-${problem.difficulty.replace(" ", "-")}`}>{problem.difficulty}</span>
        <span className="muted">{problem.topic}</span>
        <TopTools />
      </header>

      <div className="split" style={{ gridTemplateColumns: `${leftW}% 6px 1fr` }}>
        {/* left: prompt + schema */}
        <div className="pane left">
          <div className="prompt">
            <ReactMarkdown>{problem.prompt}</ReactMarkdown>
          </div>
          <div className="schema" style={problem.area === "sql" ? {} : { display: "none" }}>
            <button className="schema-toggle" onClick={() => setShowSchema(!showSchema)}>
              {showSchema ? "▾" : "▸"} Database schema
            </button>
            {showSchema && schema && (
              <div className="schema-tables">
                {Object.entries(schema).map(([table, t]) => (
                  <div key={table} className="schema-table">
                    <button
                      className="schema-tname"
                      onClick={() => setOpenTable(openTable === table ? null : table)}
                      title="Click to toggle sample rows"
                    >
                      {table} <span className="muted">{openTable === table ? "hide sample" : "sample ▸"}</span>
                    </button>
                    {t.columns.map((c) => (
                      <div key={c.column} className="schema-col">
                        <span>{c.column}</span>
                        <span className="muted">{c.type.toLowerCase()}</span>
                      </div>
                    ))}
                    {openTable === table && (
                      <div className="sample-wrap">
                        <table className="sample">
                          <thead>
                            <tr>{t.columns.map((c) => <th key={c.column}>{c.column}</th>)}</tr>
                          </thead>
                          <tbody>
                            {t.sample.map((r, i) => (
                              <tr key={i}>{r.map((v, j) => <td key={j}>{v === null ? "∅" : String(v)}</td>)}</tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="divider-v" onMouseDown={dragCols} title="Drag to resize" />

        {/* right: editor + results */}
        <div className="pane right" ref={rightRef}>
          <div className="editor-wrap" style={{ flex: "none", height: `${edH}%` }}>
            <Editor
              language={problem.area === "sql" ? "sql" : isDesign ? "markdown" : "python"}
              theme="vs-dark"
              value={code}
              onChange={(v) => setCode(v ?? "")}
              onMount={(editor, monaco) => {
                editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, run);
                editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyMod.Shift | monaco.KeyCode.Enter, submit);
              }}
              options={{ minimap: { enabled: false }, fontSize: 14, scrollBeyondLastLine: false, padding: { top: 12 }, automaticLayout: true }}
            />
          </div>
          <div className="divider-h" onMouseDown={dragRows} title="Drag to resize" />

          <div className="actions">
            {!isDesign && (
              <>
                <button className="btn" onClick={run} disabled={busy}>
                  {busy ? "…" : "Run"} <kbd>⌘↩</kbd>
                </button>
                <button className="btn btn-primary" onClick={submit} disabled={busy}>
                  Submit <kbd>⌘⇧↩</kbd>
                </button>
              </>
            )}
            {isDesign && (
              <>
                <button className={`btn ${done ? "btn-done" : "btn-primary"}`} onClick={markDone} disabled={done}>
                  {done ? "✓ Done" : "✓ Mark as done"}
                </button>
                <span className="muted">
                  {hasAnswer ? "Written answer — markdown" : "Design answer — markdown; get critique with 🧠 AI feedback"}
                </span>
              </>
            )}
            <span className="spacer" />
            <button className="btn btn-mentor" onClick={() => setRulesOpen(true)}>
              📖 Rules
            </button>
            <button className="btn btn-mentor" onClick={() => askMentor("hint")} disabled={!!mentor?.loading}>
              💡 Hint
            </button>
            <button className="btn btn-mentor" onClick={() => askMentor("feedback")} disabled={!!mentor?.loading}>
              🧠 AI feedback
            </button>
            {hasAnswer && (
              <button className="btn btn-mentor" onClick={showAnswer} disabled={!!mentor?.loading}>
                📗 Show answer
              </button>
            )}
            {out?.kind === "submit" && !out.error && (
              <span className={out.passed ? "verdict pass" : "verdict fail"}>
                {out.passed
                  ? "✓ Accepted"
                  : out.tests
                  ? `✗ ${out.tests.filter((t) => t.passed).length}/${out.tests.length} checks passed`
                  : `✗ Wrong answer${out.detail ? " — " + out.detail : ""}`}
              </span>
            )}
          </div>

          {mentor && (
            <div className="mentor">
              <div className="mentor-head">
                <span>{mentor.loading ? `${mentor.loading} — thinking…` : mentor.title}</span>
                {!mentor.loading && (
                  <button className="mentor-close" onClick={() => setMentor(null)}>✕</button>
                )}
              </div>
              {mentor.loading ? (
                <div className="mentor-body muted">Local model is working (a few seconds)…</div>
              ) : (
                <div className="mentor-body"><ReactMarkdown>{mentor.text}</ReactMarkdown></div>
              )}
            </div>
          )}

          <div className="results">
            {!out && (
              <span className="muted">
                {hasAnswer
                  ? "Write your answer as you'd say it in an interview, then get 🧠 AI feedback — or reveal the model answer with 📗 Show answer."
                  : isDesign
                  ? "Sketch requirements → API → data model → scale → tradeoffs in the editor, then ask for AI feedback."
                  : problem.area === "sql" ? "Run your query to see results." : "Run your code to see output."}
              </span>
            )}
            {out?.error && <pre className="err">{out.error}</pre>}
            {out && !out.error && problem.area === "sql" && (
              <ResultTable data={out.kind === "run" ? out : out.result} />
            )}
            {out && !out.error && problem.area !== "sql" && <PyResult out={out} />}
          </div>
        </div>
      </div>
      {rulesOpen && <RulesModal onClose={() => setRulesOpen(false)} />}
    </div>
  );
}

function PyResult({ out }) {
  const show = (v) => (typeof v === "string" ? v : JSON.stringify(v));
  return (
    <div className="pyres">
      {out.tests && (
        <div className="tests">
          {out.tests.map((t, i) => (
            <div key={i} className={`test ${t.passed ? "ok" : "bad"}`}>
              <span className="test-icon">{t.passed ? "✓" : "✗"}</span>
              <span className="test-name">{t.name}</span>
              {!t.passed && (
                <span className="test-detail">
                  {t.args !== undefined && <>args: <code>{show(t.args)}</code> · </>}
                  expected <code>{show(t.expected)}</code>, got <code className="bad-val">{show(t.got)}</code>
                </span>
              )}
            </div>
          ))}
        </div>
      )}
      {out.stdout ? (
        <>
          <div className="muted stdout-label">stdout</div>
          <pre className="stdout">{out.stdout}</pre>
        </>
      ) : (
        !out.tests && <span className="muted">Ran OK — no output (use print to inspect).</span>
      )}
    </div>
  );
}

function ResultTable({ data }) {
  if (!data || !data.columns) return null;
  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>{data.columns.map((c, i) => <th key={i}>{c}</th>)}</tr>
        </thead>
        <tbody>
          {data.rows.map((r, i) => (
            <tr key={i}>{r.map((v, j) => <td key={j}>{v === null ? <em className="muted">null</em> : String(v)}</td>)}</tr>
          ))}
        </tbody>
      </table>
      <div className="muted rowcount">
        {data.rows.length} row(s){data.truncated ? " — truncated" : ""}
      </div>
    </div>
  );
}
