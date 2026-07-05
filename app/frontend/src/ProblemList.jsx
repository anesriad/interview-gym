import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "./api";
import TopTools, { setChatContext } from "./Tools";

const DIFF_COLOR = { "very easy": "#5eead4", easy: "var(--green)", medium: "var(--yellow)", hard: "var(--red)" };
const STATUS_ICON = { solved: "✓", attempted: "◐", unsolved: "" };

export default function ProblemList() {
  const [problems, setProblems] = useState([]);
  const [area, setArea] = useState("all");
  const [gen, setGen] = useState(null); // job status while generating

  const refresh = () => api.problems().then(setProblems).catch(console.error);

  useEffect(() => {
    refresh();
    setChatContext(null); // no active problem on this screen
    // resume polling if a generation job is already running (e.g. after a reload)
    api.generateStatus().then((s) => s.running && setGen(s)).catch(() => {});
  }, []);

  useEffect(() => {
    if (!gen?.running) return;
    const t = setInterval(async () => {
      const s = await api.generateStatus();
      setGen(s);
      if (!s.running) { clearInterval(t); refresh(); }
    }, 2000);
    return () => clearInterval(t);
  }, [gen?.running]);

  const startGen = async () => {
    try {
      await api.generate();
      setGen({ running: true, log: ["starting…"], added: [] });
    } catch (e) {
      setGen({ running: false, log: [`⚠️ ${e.message}`], added: [] });
    }
  };

  const areas = ["all", ...new Set(problems.map((p) => p.area))];
  const shown = problems.filter((p) => area === "all" || p.area === area);
  const solved = problems.filter((p) => p.status === "solved").length;

  return (
    <div className="page">
      <header className="topbar">
        <h1>Interview Prep</h1>
        <span className="muted">
          {solved} / {problems.length} solved
        </span>
        <span className="toptools">
          <button className="btn tool" onClick={startGen} disabled={gen?.running}
                  title="Local LLM writes + verifies one new problem per area (takes a few minutes)">
            {gen?.running ? "✨ Generating…" : "✨ New problems"}
          </button>
          <TopTools />
        </span>
      </header>

      {gen && (
        <div className="gen-panel">
          <div className="gen-head">
            <span>✨ Problem generator {gen.running && <span className="gen-spin">— working, ~1 min per area</span>}</span>
            {!gen.running && <button className="mentor-close" onClick={() => setGen(null)}>✕</button>}
          </div>
          <div className="gen-bar"><div className="gen-fill" style={{ width: `${Math.min(100, (gen.added?.length ?? 0) * 25 + (gen.running ? 5 : 0))}%` }} /></div>
          <div className="gen-log">
            {gen.log?.slice(-6).map((l, i) => <div key={i}>{l}</div>)}
          </div>
        </div>
      )}

      <div className="filters">
        {areas.map((a) => (
          <button key={a} className={`chip ${a === area ? "chip-on" : ""}`} onClick={() => setArea(a)}>
            {a.toUpperCase()}
          </button>
        ))}
      </div>

      <div className="plist">
        {shown.map((p) => (
          <Link to={`/problem/${p.id}`} key={p.id} className="prow">
            <span className={`pstatus ${p.status}`}>{STATUS_ICON[p.status]}</span>
            <span className="ptitle">{p.title}</span>
            <span className="ptopic muted">{p.topic}</span>
            <span className="pdiff" style={{ color: DIFF_COLOR[p.difficulty] }}>
              {p.difficulty}
            </span>
          </Link>
        ))}
        {shown.length === 0 && <p className="muted pad">No problems yet.</p>}
      </div>
    </div>
  );
}
