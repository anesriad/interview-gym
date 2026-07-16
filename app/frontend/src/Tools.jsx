// Shared top-bar tools: Pomodoro timer + LLM chat drawer + Rules popup.
import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import { api } from "./api";
import { RULES } from "./rules";

/* ---------- gentle WebAudio tones (no files, quiet) ---------- */
let audioCtx;
function tone(freq, dur = 0.18, when = 0, gain = 0.04) {
  audioCtx = audioCtx || new (window.AudioContext || window.webkitAudioContext)();
  const o = audioCtx.createOscillator();
  const g = audioCtx.createGain();
  o.type = "sine";
  o.frequency.value = freq;
  g.gain.setValueAtTime(gain, audioCtx.currentTime + when);
  g.gain.exponentialRampToValueAtTime(0.0001, audioCtx.currentTime + when + dur);
  o.connect(g).connect(audioCtx.destination);
  o.start(audioCtx.currentTime + when);
  o.stop(audioCtx.currentTime + when + dur);
}
const sndStart = () => tone(660, 0.1);                       // soft click
const sndFocusDone = () => { tone(523, 0.25); tone(392, 0.3, 0.28); };  // gentle down-chime
const sndBreakDone = () => { tone(392, 0.2); tone(523, 0.25, 0.22); };  // gentle up-chime

/* ---------- pomodoro (state in localStorage → survives navigation/reload) ---------- */
const FOCUS_S = 50 * 60, BREAK_S = 10 * 60;
const loadPomo = () => JSON.parse(localStorage.getItem("pomo") || "null");
const savePomo = (p) => p ? localStorage.setItem("pomo", JSON.stringify(p)) : localStorage.removeItem("pomo");

/* ---------- chat history + screen context (module scope: shared across pages) ---------- */
let chatContext = null;
export const setChatContext = (ctx) => { chatContext = ctx; };
// sessionStorage: survives reloads, cleared when the tab/app is closed
const loadChat = () => JSON.parse(sessionStorage.getItem("chat") || "[]");

export default function TopTools() {
  /* pomodoro */
  const [pomo, setPomo] = useState(loadPomo);
  const [banner, setBanner] = useState(null);
  const [, tick] = useState(0);

  useEffect(() => {
    const t = setInterval(() => {
      const p = loadPomo();
      if (p && Date.now() >= p.endsAt) {
        if (p.phase === "focus") {
          sndFocusDone();
          const next = { phase: "break", endsAt: Date.now() + BREAK_S * 1000 };
          savePomo(next); setPomo(next);
          setBanner("🌿 50 minutes done — stand up, stretch, look away. Break is running (or keep going, it won't stop you).");
        } else {
          sndBreakDone();
          savePomo(null); setPomo(null);
          setBanner("☕ Break over — click the timer when you're ready for the next focus block.");
        }
      }
      tick((x) => x + 1);
    }, 1000);
    return () => clearInterval(t);
  }, []);

  const togglePomo = () => {
    if (pomo) { savePomo(null); setPomo(null); setBanner(null); return; }
    sndStart();
    const p = { phase: "focus", endsAt: Date.now() + FOCUS_S * 1000 };
    savePomo(p); setPomo(p);
  };

  const remaining = pomo ? Math.max(0, Math.round((pomo.endsAt - Date.now()) / 1000)) : null;
  const mmss = remaining !== null
    ? `${String(Math.floor(remaining / 60)).padStart(2, "0")}:${String(remaining % 60).padStart(2, "0")}`
    : null;

  /* chat */
  const [chatOpen, setChatOpen] = useState(false);

  return (
    <span className="toptools">
      <button
        className={`btn tool ${pomo ? (pomo.phase === "focus" ? "pomo-focus" : "pomo-break") : ""}`}
        onClick={togglePomo}
        title={pomo ? "Click to stop/reset" : "Start a 50-min focus block"}
      >
        {pomo ? `${pomo.phase === "focus" ? "🍅" : "🌿"} ${mmss}` : "🍅 Focus"}
      </button>
      <button className="btn tool" onClick={() => setChatOpen(!chatOpen)}>💬 Chat</button>

      {banner && (
        <div className="banner">
          <span>{banner}</span>
          <button className="mentor-close" onClick={() => setBanner(null)}>✕</button>
        </div>
      )}
      {chatOpen && <ChatDrawer onClose={() => setChatOpen(false)} />}
    </span>
  );
}

function ChatDrawer({ onClose }) {
  const [msgs, setMsgs] = useState(loadChat);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [useCtx, setUseCtx] = useState(true);
  const [width, setWidth] = useState(() => +localStorage.getItem("chatW") || 400);
  const endRef = useRef();

  useEffect(() => { endRef.current?.scrollIntoView(); }, [msgs, busy]);
  const persist = (m) => { sessionStorage.setItem("chat", JSON.stringify(m.slice(-40))); setMsgs(m); };

  const send = async () => {
    const q = input.trim();
    if (!q || busy) return;
    const next = [...msgs, { role: "user", content: q }];
    persist(next); setInput(""); setBusy(true);
    try {
      const r = await api.chat(next, useCtx ? chatContext : null);
      persist([...next, { role: "assistant", content: r.text }]);
    } catch (e) {
      persist([...next, { role: "assistant", content: `⚠️ ${e.message}` }]);
    } finally { setBusy(false); }
  };

  const dragWidth = (e) => {
    e.preventDefault();
    const move = (ev) => {
      const w = Math.min(900, Math.max(300, window.innerWidth - ev.clientX));
      setWidth(w);
      localStorage.setItem("chatW", w);
    };
    const up = () => { window.removeEventListener("mousemove", move); window.removeEventListener("mouseup", up); };
    window.addEventListener("mousemove", move);
    window.addEventListener("mouseup", up);
  };

  return (
    <div className="chat-drawer" style={{ width: `${width}px` }}>
      <div className="chat-resize" onMouseDown={dragWidth} title="Drag to resize" />
      <div className="chat-head">
        <span>💬 Mentor chat <span className="muted">(local LLM)</span></span>
        <span>
          <button className="mentor-close" title="Clear conversation"
                  onClick={() => persist([])}>🗑</button>
          <button className="mentor-close" onClick={onClose}>✕</button>
        </span>
      </div>
      <div className="chat-msgs">
        {msgs.length === 0 && (
          <div className="muted pad">Ask anything — syntax, an error message, a concept. Costs nothing, stays local.</div>
        )}
        {msgs.map((m, i) => (
          <div key={i} className={`chat-msg ${m.role}`}>
            <ReactMarkdown>{m.content}</ReactMarkdown>
          </div>
        ))}
        {busy && <div className="chat-msg assistant muted">thinking…</div>}
        <div ref={endRef} />
      </div>
      <label className="chat-ctx muted" title="Sends the current problem's prompt and your editor code as context to the mentor">
        <input type="checkbox" checked={useCtx} onChange={(e) => setUseCtx(e.target.checked)} />
        include current problem &amp; my code
        {useCtx && !chatContext && <span className="chat-ctx-warn"> (no problem open right now)</span>}
      </label>
      <div className="chat-input-row">
        <textarea
          className="chat-input" rows={2} value={input} placeholder="Ask… (Enter to send)"
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }}
        />
        <button className="btn btn-primary chat-send" onClick={send} disabled={busy || !input.trim()}>
          {busy ? "…" : "Send"}
        </button>
      </div>
    </div>
  );
}

export function RulesModal({ onClose }) {
  const [active, setActive] = useState(null);
  const areas = [...new Set(RULES.map((r) => r.area))];
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-head">
          <span>{active ? active.label : "📖 Quick rules"}</span>
          <span>
            {active && <button className="mentor-close" onClick={() => setActive(null)}>← back</button>}
            <button className="mentor-close" onClick={onClose}>✕</button>
          </span>
        </div>
        {!active ? (
          <div className="rule-grid">
            {areas.map((a) => (
              <div key={a} className="rule-area">
                <div className="muted rule-area-label">{a}</div>
                {RULES.filter((r) => r.area === a).map((r) => (
                  <button key={r.id} className="btn rule-btn" onClick={() => setActive(r)}>{r.label}</button>
                ))}
              </div>
            ))}
          </div>
        ) : (
          <div className="rule-body"><ReactMarkdown>{active.body}</ReactMarkdown></div>
        )}
      </div>
    </div>
  );
}
