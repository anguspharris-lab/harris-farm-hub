/**
 * Harris Farm Markets — Universal Meeting Operating System
 * "AI builds. You architect. Together we grow."
 *
 * One configurable artifact for ALL meeting types: SCR, ARR, AI Vision,
 * Strategy Sprint, Department One-Pager, Board Prep — and any future type.
 *
 * Reads window.__MEETING_CONFIG__ for everything.
 * Warm Harris Farm theme. Animated transitions. Auto-saves. Submit to BigQuery.
 */

const { useState, useEffect, useCallback, useMemo, useRef } = React;

const C = window.__MEETING_CONFIG__ || {};

/* ── Inspirational quotes that rotate ─────────────────────── */
const QUOTES = [
  { text: "We grow more than food.", attr: "Harris Farm Markets" },
  { text: "AI builds. You architect. Together we grow.", attr: "The Harris Farm Way" },
  { text: "Honest answers build better plans.", attr: "AI First Principle" },
  { text: "Think end-to-end. Own the outcome.", attr: "Harris Farming It" },
  { text: "Every voice shapes what comes next.", attr: "For the Greater Goodness" },
  { text: "The best ideas come from the people closest to the work.", attr: "The Harris Farm Way" },
];

/* ── CSS Animations (injected once) ───────────────────────── */
const STYLE_ID = "__hfm_mos_styles";
if (!document.getElementById(STYLE_ID)) {
  const style = document.createElement("style");
  style.id = STYLE_ID;
  style.textContent = `
    @keyframes hfm-fadeIn { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }
    @keyframes hfm-slideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
    @keyframes hfm-scaleIn { from { opacity: 0; transform: scale(0.95); } to { opacity: 1; transform: scale(1); } }
    @keyframes hfm-pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
    @keyframes hfm-celebrate { 0% { transform: scale(0); opacity: 0; } 50% { transform: scale(1.2); opacity: 1; } 100% { transform: scale(1); opacity: 1; } }
    @keyframes hfm-confetti {
      0% { transform: translateY(0) rotate(0deg); opacity: 1; }
      100% { transform: translateY(400px) rotate(720deg); opacity: 0; }
    }
    @keyframes hfm-shimmer {
      0% { background-position: -200% 0; }
      100% { background-position: 200% 0; }
    }
    @keyframes hfm-float {
      0%, 100% { transform: translateY(0px); }
      50% { transform: translateY(-6px); }
    }
    @keyframes hfm-progressPulse {
      0%, 100% { box-shadow: 0 0 0 0 rgba(45,106,45,0.3); }
      50% { box-shadow: 0 0 8px 2px rgba(45,106,45,0.15); }
    }
    .hfm-card-enter { animation: hfm-slideUp 0.4s ease-out both; }
    .hfm-fade-enter { animation: hfm-fadeIn 0.3s ease-out both; }
    .hfm-scale-enter { animation: hfm-scaleIn 0.3s ease-out both; }
    .hfm-float { animation: hfm-float 3s ease-in-out infinite; }

    /* Range slider styling */
    input[type="range"].hfm-slider {
      -webkit-appearance: none; appearance: none;
      height: 8px; border-radius: 4px; outline: none;
      background: linear-gradient(90deg, rgba(0,0,0,0.06) 0%, rgba(0,0,0,0.06) 100%);
      transition: background 0.2s;
    }
    input[type="range"].hfm-slider::-webkit-slider-thumb {
      -webkit-appearance: none; appearance: none;
      width: 24px; height: 24px; border-radius: 50%;
      cursor: pointer; border: 3px solid #fff;
      box-shadow: 0 2px 8px rgba(0,0,0,0.15);
      transition: transform 0.15s, box-shadow 0.15s;
    }
    input[type="range"].hfm-slider::-webkit-slider-thumb:hover {
      transform: scale(1.15);
      box-shadow: 0 3px 12px rgba(0,0,0,0.25);
    }
    input[type="range"].hfm-slider::-moz-range-thumb {
      width: 24px; height: 24px; border-radius: 50%;
      cursor: pointer; border: 3px solid #fff;
      box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    }

    /* Focus glow */
    .hfm-input:focus { box-shadow: 0 0 0 3px rgba(45,106,45,0.12); border-color: rgba(45,106,45,0.4) !important; }
    .hfm-textarea:focus { box-shadow: 0 0 0 3px rgba(45,106,45,0.12); border-color: rgba(45,106,45,0.4) !important; }

    /* Confetti pieces */
    .hfm-confetti-piece {
      position: fixed; top: -20px; width: 10px; height: 10px;
      border-radius: 2px; animation: hfm-confetti 2.5s ease-out forwards;
      pointer-events: none; z-index: 9999;
    }
  `;
  document.head.appendChild(style);
}

/* ── Reusable components ───────────────────────────────────── */

function QuoteBar({ accent }) {
  const [idx, setIdx] = useState(() => Math.floor(Math.random() * QUOTES.length));
  const q = QUOTES[idx];
  return (
    <div className="hfm-fade-enter" style={{
      textAlign: "center", padding: "16px 20px", margin: "0 0 24px",
      background: `linear-gradient(135deg, ${accent}08, ${accent}14)`,
      borderRadius: 12, borderLeft: `3px solid ${accent}40`,
    }}>
      <div style={{ fontFamily: "Georgia, serif", fontSize: 15, fontStyle: "italic", color: "#4A5568", lineHeight: 1.6 }}>
        "{q.text}"
      </div>
      <div style={{ fontSize: 11, color: "#4A4A4A", marginTop: 4, letterSpacing: "0.05em", textTransform: "uppercase" }}>
        — {q.attr}
      </div>
    </div>
  );
}

function Slider({ label, help, value, onChange, color }) {
  const pct = ((value - 1) / 9) * 100;
  const trackBg = `linear-gradient(90deg, ${color} ${pct}%, rgba(0,0,0,0.06) ${pct}%)`;
  return (
    <div style={{ marginBottom: 24 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 4 }}>
        <span style={{ fontWeight: 600, fontSize: 14, color: "#1A1A1A" }}>{label}</span>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <span style={{
            fontSize: 24, fontWeight: 800, color,
            fontFamily: "Georgia, serif", minWidth: 32, textAlign: "right",
            textShadow: `0 1px 2px ${color}20`,
          }}>{value}</span>
          <ScoreBadge score={value} />
        </div>
      </div>
      {help && <div style={{ fontSize: 12, color: "#4A4A4A", marginBottom: 8, lineHeight: 1.4 }}>{help}</div>}
      <input
        type="range" min="1" max="10" value={value}
        onChange={e => onChange(parseInt(e.target.value))}
        className="hfm-slider"
        style={{ width: "100%", background: trackBg, accentColor: color, cursor: "pointer" }}
      />
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: "#666666", marginTop: 4 }}>
        <span>1 — Critical</span><span>10 — Strong</span>
      </div>
    </div>
  );
}

function TextArea({ label, help, value, onChange, rows = 3, placeholder }) {
  return (
    <div style={{ marginBottom: 20 }}>
      <label style={{ fontWeight: 600, fontSize: 14, color: "#1A1A1A", display: "block", marginBottom: 4 }}>{label}</label>
      {help && <div style={{ fontSize: 12, color: "#4A4A4A", marginBottom: 6, lineHeight: 1.4 }}>{help}</div>}
      <textarea
        value={value} onChange={e => onChange(e.target.value)} rows={rows}
        placeholder={placeholder || "Share your thoughts..."}
        className="hfm-textarea"
        style={{
          width: "100%", background: "#FFFFFF", border: "1.5px solid rgba(0,0,0,0.08)",
          borderRadius: 10, padding: "12px 16px", color: "#1A1A1A", fontSize: 14,
          fontFamily: "'Trebuchet MS', sans-serif", resize: "vertical",
          transition: "border-color 0.2s, box-shadow 0.2s",
        }}
      />
    </div>
  );
}

function TextField({ label, help, value, onChange, placeholder = "", type = "text", required }) {
  return (
    <div style={{ marginBottom: 16 }}>
      <label style={{ fontWeight: 600, fontSize: 14, color: "#1A1A1A", display: "block", marginBottom: 4 }}>
        {label}{required && <span style={{ color: "#DC2626", marginLeft: 3 }}>*</span>}
      </label>
      {help && <div style={{ fontSize: 12, color: "#4A4A4A", marginBottom: 6, lineHeight: 1.4 }}>{help}</div>}
      <input
        type={type} value={value} onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        className="hfm-input"
        style={{
          width: "100%", background: "#FFFFFF", border: "1.5px solid rgba(0,0,0,0.08)",
          borderRadius: 10, padding: "12px 16px", color: "#1A1A1A", fontSize: 14,
          fontFamily: "'Trebuchet MS', sans-serif",
          transition: "border-color 0.2s, box-shadow 0.2s",
        }}
      />
    </div>
  );
}

function SelectField({ label, help, value, onChange, options = [], placeholder = "", required }) {
  return (
    <div style={{ marginBottom: 16 }}>
      <label style={{ fontWeight: 600, fontSize: 14, color: "#1A1A1A", display: "block", marginBottom: 4 }}>
        {label}{required && <span style={{ color: "#DC2626", marginLeft: 3 }}>*</span>}
      </label>
      {help && <div style={{ fontSize: 12, color: "#4A4A4A", marginBottom: 6, lineHeight: 1.4 }}>{help}</div>}
      <select
        value={value} onChange={e => onChange(e.target.value)}
        className="hfm-input"
        style={{
          width: "100%", background: "#FFFFFF", border: "1.5px solid rgba(0,0,0,0.08)",
          borderRadius: 10, padding: "12px 16px", color: value ? "#1A1A1A" : "#A0AEC0", fontSize: 14,
          fontFamily: "'Trebuchet MS', sans-serif",
          transition: "border-color 0.2s, box-shadow 0.2s",
          cursor: "pointer",
        }}
      >
        <option value="">{placeholder || "Select..."}</option>
        {options.map(opt => <option key={opt} value={opt}>{opt}</option>)}
      </select>
    </div>
  );
}

function Card({ title, children, color, icon, delay = 0 }) {
  return (
    <div className="hfm-card-enter" style={{
      background: "#FFFFFF",
      border: "1px solid rgba(0,0,0,0.05)",
      borderRadius: 16, padding: "28px 32px", marginBottom: 24,
      boxShadow: "0 1px 3px rgba(0,0,0,0.04), 0 4px 12px rgba(0,0,0,0.02)",
      animationDelay: `${delay * 0.1}s`,
      position: "relative", overflow: "hidden",
    }}>
      {/* Accent bar at top */}
      {title && <div style={{
        position: "absolute", top: 0, left: 0, right: 0, height: 3,
        background: `linear-gradient(90deg, ${color}, ${color}80)`,
      }} />}
      {title && (
        <h3 style={{
          fontFamily: "Georgia, serif", color, fontSize: 19, fontWeight: 600,
          marginTop: 4, marginBottom: 16, display: "flex", alignItems: "center", gap: 8,
        }}>
          {icon && <span style={{ fontSize: 22 }}>{icon}</span>}
          {title}
        </h3>
      )}
      {children}
    </div>
  );
}

function ScoreBadge({ score }) {
  let bg, color, text;
  if (score >= 8) { bg = "rgba(45,106,45,0.10)"; color = "#2D6A2D"; text = "Strong"; }
  else if (score >= 6) { bg = "rgba(146,113,10,0.10)"; color = "#7A6209"; text = "Adequate"; }
  else if (score >= 4) { bg = "rgba(249,115,22,0.10)"; color = "#F97316"; text = "Gap"; }
  else { bg = "rgba(220,38,38,0.08)"; color = "#DC2626"; text = "Critical"; }
  return (
    <span style={{
      fontSize: 10, fontWeight: 700, color, background: bg,
      padding: "2px 8px", borderRadius: 10, letterSpacing: "0.03em",
      textTransform: "uppercase",
    }}>{text}</span>
  );
}

function ConfettiExplosion() {
  const colors = ["#2D6A2D", "#E8B84B", "#F97316", "#3B82F6", "#8B5CF6", "#06B6D4", "#DC2626"];
  const pieces = Array.from({ length: 40 }, (_, i) => ({
    id: i,
    left: Math.random() * 100,
    color: colors[Math.floor(Math.random() * colors.length)],
    delay: Math.random() * 0.8,
    size: 6 + Math.random() * 8,
    rotation: Math.random() * 360,
  }));
  return (
    <>
      {pieces.map(p => (
        <div key={p.id} className="hfm-confetti-piece" style={{
          left: `${p.left}%`, backgroundColor: p.color,
          animationDelay: `${p.delay}s`,
          width: p.size, height: p.size * 0.6,
          borderRadius: p.id % 3 === 0 ? "50%" : "2px",
          transform: `rotate(${p.rotation}deg)`,
        }} />
      ))}
    </>
  );
}

/* ── Build initial data from config ────────────────────────── */

function buildDefault() {
  const d = {};
  (C.welcomeFields || []).forEach(f => { d[f.key] = f.type === "slider" ? (f.default || 5) : (f.default || ""); });
  (C.sections || []).forEach(sec => {
    const allQ = [];
    if (sec.questions) allQ.push(...sec.questions);
    if (sec.cards) sec.cards.forEach(c => { if (c.questions) allQ.push(...c.questions); });
    allQ.forEach(q => { d[q.key] = q.type === "slider" ? (q.default || 5) : ""; });
  });
  return d;
}

/* ── Main App ──────────────────────────────────────────────── */

function App() {
  const accent = C.accent || "#2D6A2D";
  const sections = C.sections || [];
  const welcomeFields = C.welcomeFields || [
    { key: "name", label: "Full Name", placeholder: "Your full name", required: true },
    { key: "role", label: "Role / Title", placeholder: "e.g. Store Manager, Buyer", required: true },
    { key: "department", label: "Department", placeholder: "e.g. Operations, Buying" },
  ];
  if (C.emailRequired !== false) {
    const hasEmail = welcomeFields.some(f => f.key === "email");
    if (!hasEmail) {
      welcomeFields.splice(1, 0, {
        key: "email", label: "Email", placeholder: "you@harrisfarm.com.au",
        type: "email", required: true, help: "Must be a @harrisfarm.com.au address",
      });
    }
  }

  const showSummary = C.showSummary !== false;
  const stepLabels = [
    { key: "welcome", label: "Welcome", icon: "\u{1F44B}" },
    ...sections.map(s => ({ key: s.key, label: s.label, icon: s.icon || "" })),
    ...(showSummary ? [{ key: "summary", label: "Review & Submit", icon: "\u2705" }] : []),
  ];

  const [step, setStep] = useState(0);
  const [stepKey, setStepKey] = useState(0); // for re-triggering animations
  const [data, setData] = useState(() => {
    try {
      const saved = localStorage.getItem(C.storageKey);
      if (saved) return { ...buildDefault(), ...JSON.parse(saved) };
    } catch {}
    return buildDefault();
  });
  const [submitted, setSubmitted] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState("");
  const [error, setError] = useState("");
  const [showConfetti, setShowConfetti] = useState(false);

  useEffect(() => {
    try { localStorage.setItem(C.storageKey, JSON.stringify(data)); } catch {}
  }, [data]);

  const set = (key, val) => setData(prev => ({ ...prev, [key]: val }));

  const goToStep = (newStep) => {
    setStep(newStep);
    setStepKey(k => k + 1);
    // Scroll to top of iframe
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const welcomeValid = useMemo(() => {
    return welcomeFields.filter(f => f.required).filter(f => {
      // Skip validation for conditionally hidden fields
      if (f.showIf && data[f.showIf.key] !== f.showIf.value) return false;
      return true;
    }).every(f => {
      const v = data[f.key] || "";
      if (f.key === "email") return v.endsWith("@harrisfarm.com.au");
      return v.trim().length > 0;
    });
  }, [data, welcomeFields]);

  // Collect all sliders for summary
  const allSliders = useMemo(() => {
    const result = [];
    sections.forEach(sec => {
      const allQ = [];
      if (sec.questions) allQ.push(...sec.questions);
      if (sec.cards) sec.cards.forEach(c => { if (c.questions) allQ.push(...c.questions); });
      allQ.forEach(q => {
        if (q.type === "slider") result.push({ ...q, section: sec.label, value: data[q.key] || 5 });
      });
    });
    return result;
  }, [data, sections]);

  const avgScore = useMemo(() => {
    if (allSliders.length === 0) return 0;
    return (allSliders.reduce((s, q) => s + q.value, 0) / allSliders.length).toFixed(1);
  }, [allSliders]);

  /* ── Submit ── */
  const downloadJSON = () => {
    const blob = new Blob([JSON.stringify({
      ...data,
      _meta: { type: C.meetingType, ts: new Date().toISOString(), version: "2.0" }
    }, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    const safeName = (data.name || data.email || "anon").replace(/[^a-zA-Z0-9]/g, "_").substring(0, 30);
    a.download = `${(C.meetingType || "meeting").toLowerCase()}_${safeName}_${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const buildPayload = () => {
    if (C.submitFormat === "mapped" && C.submitMap) {
      const payload = {};
      for (const [cfField, dataKey] of Object.entries(C.submitMap)) {
        if (dataKey.startsWith("_LITERAL:")) {
          payload[cfField] = dataKey.slice(9);
        } else {
          payload[cfField] = data[dataKey] !== undefined ? String(data[dataKey]) : "";
        }
      }
      return payload;
    }
    // Default: JSON blob for meeting-os CF
    const responses = {};
    const scores = {};
    // Include welcome fields beyond the standard top-level ones
    const standardKeys = new Set(["name", "email", "role", "department"]);
    (C.welcomeFields || []).forEach(f => {
      if (!standardKeys.has(f.key) && data[f.key]) {
        if (f.type === "slider") scores[f.key] = data[f.key];
        else responses[f.key] = data[f.key];
      }
    });
    sections.forEach(sec => {
      const allQ = [];
      if (sec.questions) allQ.push(...sec.questions);
      if (sec.cards) sec.cards.forEach(c => { if (c.questions) allQ.push(...c.questions); });
      allQ.forEach(q => {
        if (q.type === "slider") scores[q.key] = data[q.key];
        else responses[q.key] = data[q.key];
      });
    });
    return {
      meeting_type: C.meetingType,
      transformation_type: data.transformation_type || "",
      email: data.email || "",
      name: data.name || "",
      role: data.role || data.role_level || "",
      department: data.department || "",
      responses_json: JSON.stringify(responses),
      scores_json: JSON.stringify(scores),
    };
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    setError("");
    setSubmitStatus("");

    try {
      downloadJSON();

      if (C.submitUrl) {
        const payload = buildPayload();

        if (C.submitFormat === "mapped") {
          // Legacy: URLSearchParams via sendBeacon (same as bespoke SCR/ARR)
          const sep = C.submitUrl.includes("?") ? "&" : "?";
          const fullUrl = `${C.submitUrl}${sep}api_key=${C.apiKey || ""}`;
          const params = new URLSearchParams(payload);
          const sent = navigator.sendBeacon && navigator.sendBeacon(fullUrl, params.toString());
          if (!sent) {
            await fetch(fullUrl, {
              method: "POST",
              headers: { "Content-Type": "text/plain" },
              body: params.toString(),
            });
          }
          setSubmitStatus("success");
        } else {
          // New: JSON via fetch
          const sep = C.submitUrl.includes("?") ? "&" : "?";
          const url = `${C.submitUrl}${sep}api_key=${C.apiKey || ""}`;
          try {
            const resp = await fetch(url, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(payload),
            });
            if (!resp.ok) {
              const err = await resp.json().catch(() => ({}));
              throw new Error(err.error || `HTTP ${resp.status}`);
            }
            setSubmitStatus("success");
          } catch (fetchErr) {
            const sent = navigator.sendBeacon && navigator.sendBeacon(url, JSON.stringify(payload));
            setSubmitStatus(sent ? "success" : "error");
            if (!sent) throw fetchErr;
          }
        }
      } else {
        setSubmitStatus("success");
      }

      localStorage.removeItem(C.storageKey);
      setShowConfetti(true);
      setTimeout(() => setSubmitted(true), 600);
    } catch (e) {
      setError(e.message || "Submission failed");
      setSubmitStatus("error");
    } finally {
      setSubmitting(false);
    }
  };

  const handleReset = () => {
    if (confirm("Clear all responses and start fresh?")) {
      setData(buildDefault());
      goToStep(0);
      localStorage.removeItem(C.storageKey);
      setSubmitted(false);
      setSubmitStatus("");
    }
  };

  /* ── Thank-you screen ── */
  if (submitted) {
    const firstName = data.name ? data.name.split(" ")[0] : "";

    // Build ADKAR summary — one line per dimension from the user's own answers
    const adkarSummary = [];
    sections.forEach(sec => {
      const allQ = [];
      if (sec.questions) allQ.push(...sec.questions);
      if (sec.cards) sec.cards.forEach(c => { if (c.questions) allQ.push(...c.questions); });
      // Find a representative answer for this section
      const slider = allQ.find(q => q.type === "slider");
      const text = allQ.find(q => q.type === "text" && (data[q.key] || "").trim());
      let summary = "";
      if (slider && data[slider.key]) {
        const score = data[slider.key];
        const label = score >= 8 ? "Strong" : score >= 6 ? "Adequate" : score >= 4 ? "Gap" : "Critical";
        summary += `${score}/10 (${label})`;
      }
      if (text && data[text.key]) {
        const snippet = data[text.key].trim();
        const short = snippet.length > 80 ? snippet.substring(0, 80) + "\u2026" : snippet;
        summary += (summary ? " \u2014 " : "") + `"${short}"`;
      }
      if (summary) {
        adkarSummary.push({ label: sec.label, icon: sec.icon || "", summary });
      }
    });

    return (
      <div style={{
        minHeight: "100vh", background: "#FAFAF7",
        display: "flex", alignItems: "center", justifyContent: "center", padding: 40,
      }}>
        {showConfetti && <ConfettiExplosion />}
        <div className="hfm-scale-enter" style={{ textAlign: "center", maxWidth: 620 }}>
          <div className="hfm-float" style={{ fontSize: 72, marginBottom: 16 }}>&#127822;</div>
          <h2 style={{
            color: accent, fontFamily: "Georgia, serif", fontSize: 30,
            marginBottom: 12, lineHeight: 1.3,
          }}>
            Thank you{firstName ? `, ${firstName}` : ""}.
          </h2>
          <p style={{ color: "#4A5568", fontSize: 17, lineHeight: 1.7, marginBottom: 4 }}>
            Your voice is shaping our future.
          </p>
          <p style={{ color: "#4A4A4A", fontSize: 15, lineHeight: 1.7, marginBottom: 8 }}>
            The Harris Farm AI First transformation starts with honest conversations like this one.
            {submitStatus === "error" && <><br /><span style={{ color: "#F97316" }}>Database save failed — your JSON backup has been downloaded.</span></>}
          </p>

          {/* ADKAR answer summary */}
          {adkarSummary.length > 0 && (
            <div style={{
              textAlign: "left", marginTop: 24,
              background: "#FFFFFF",
              border: "1px solid rgba(0,0,0,0.06)",
              borderRadius: 14, padding: "20px 24px",
              boxShadow: "0 1px 4px rgba(0,0,0,0.03)",
            }}>
              <div style={{
                fontSize: 12, color: "#4A4A4A", fontWeight: 700,
                textTransform: "uppercase", letterSpacing: "0.06em",
                marginBottom: 14, textAlign: "center",
              }}>
                Your Response Summary
              </div>
              {adkarSummary.map((item, i) => (
                <div key={i} style={{
                  display: "flex", alignItems: "flex-start", gap: 10,
                  padding: "8px 0",
                  borderTop: i > 0 ? "1px solid rgba(0,0,0,0.04)" : "none",
                }}>
                  <span style={{ fontSize: 18, flexShrink: 0, marginTop: 1 }}>{item.icon}</span>
                  <div>
                    <div style={{ fontSize: 12, fontWeight: 700, color: accent, textTransform: "uppercase", letterSpacing: "0.04em" }}>
                      {item.label}
                    </div>
                    <div style={{ fontSize: 14, color: "#4A5568", lineHeight: 1.5, marginTop: 2 }}>
                      {item.summary}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          <div style={{
            background: `linear-gradient(135deg, ${accent}0A, ${accent}18)`,
            borderRadius: 12, padding: "16px 24px", marginTop: 24,
            border: `1px solid ${accent}20`,
          }}>
            <div style={{ fontFamily: "Georgia, serif", fontStyle: "italic", fontSize: 15, color: "#4A5568", lineHeight: 1.6 }}>
              "We grow more than food. We grow ideas, capability, and each other."
            </div>
            <div style={{ fontSize: 11, color: "#4A4A4A", marginTop: 8, letterSpacing: "0.05em", textTransform: "uppercase" }}>
              Harris Farm Markets — For the Greater Goodness
            </div>
          </div>
        </div>
      </div>
    );
  }

  /* ── Progress / Stepper ── */
  const progress = Math.round(((step + 1) / stepLabels.length) * 100);

  const renderStepper = () => (
    <div style={{ marginBottom: 28 }}>
      {/* Step pills */}
      <div style={{ display: "flex", gap: 6, marginBottom: 10, flexWrap: "wrap", justifyContent: "center" }}>
        {stepLabels.map((s, i) => {
          const isActive = i === step;
          const isDone = i < step;
          return (
            <button
              key={s.key}
              onClick={() => i <= step && goToStep(i)}
              style={{
                background: isActive
                  ? `linear-gradient(135deg, ${accent}, ${accent}DD)`
                  : isDone ? `${accent}15` : "rgba(0,0,0,0.03)",
                color: isActive ? "#FFFFFF" : isDone ? accent : "#666666",
                border: isActive ? "none" : isDone ? `1px solid ${accent}30` : "1px solid rgba(0,0,0,0.05)",
                borderRadius: 24, padding: isActive ? "8px 18px" : "7px 14px",
                fontSize: 12, fontWeight: isActive ? 700 : isDone ? 600 : 400,
                cursor: i <= step ? "pointer" : "default",
                transition: "all 0.3s ease",
                whiteSpace: "nowrap",
                boxShadow: isActive ? `0 2px 8px ${accent}30` : "none",
                transform: isActive ? "scale(1.02)" : "scale(1)",
              }}
            >
              {isDone ? "\u2713" : `${i + 1}`} {s.label}
            </button>
          );
        })}
      </div>
      {/* Progress bar */}
      <div style={{
        background: "rgba(0,0,0,0.04)", borderRadius: 6, height: 6,
        overflow: "hidden", position: "relative",
      }}>
        <div style={{
          width: `${progress}%`, height: "100%", borderRadius: 6,
          background: `linear-gradient(90deg, ${accent}, ${accent}CC)`,
          transition: "width 0.5s cubic-bezier(0.4, 0, 0.2, 1)",
          boxShadow: `0 0 10px ${accent}40`,
        }} />
      </div>
      <div style={{ textAlign: "right", fontSize: 11, color: "#666666", marginTop: 4 }}>
        {progress}% complete
      </div>
    </div>
  );

  /* ── Welcome section ── */
  const renderWelcome = () => (
    <div key={stepKey}>
      <QuoteBar accent={accent} />
      <Card title={C.welcomeTitle || "About You"} color={accent} icon={"\u{1F33F}"} delay={0}>
        {C.welcomeDescription && (
          <div style={{
            background: `linear-gradient(135deg, ${accent}08, ${accent}12)`,
            borderRadius: 10, padding: "14px 18px", marginBottom: 20,
            fontSize: 13, color: "#4A5568", lineHeight: 1.7,
            borderLeft: `3px solid ${accent}30`,
          }}>
            {C.welcomeDescription}
          </div>
        )}
        {welcomeFields.map(f => {
          if (f.showIf && data[f.showIf.key] !== f.showIf.value) return null;
          if (f.type === "textarea") {
            return <TextArea key={f.key} label={f.label} help={f.help} value={data[f.key] || ""}
              onChange={v => set(f.key, v)} rows={f.rows || 3} placeholder={f.placeholder} />;
          }
          if (f.type === "slider") {
            return <Slider key={f.key} label={f.label} help={f.help} value={data[f.key] || 5}
              onChange={v => set(f.key, v)} color={f.color || accent} />;
          }
          if (f.type === "select") {
            return <SelectField key={f.key} label={f.label} help={f.help} value={data[f.key] || ""}
              onChange={v => set(f.key, v)} options={f.options || []} placeholder={f.placeholder} required={f.required} />;
          }
          return (
            <React.Fragment key={f.key}>
              <TextField label={f.label} help={f.help} value={data[f.key] || ""}
                onChange={v => set(f.key, v)} placeholder={f.placeholder} type={f.type || "text"} required={f.required} />
              {f.key === "email" && data.email && !data.email.endsWith("@harrisfarm.com.au") && data.email.includes("@") && (
                <div style={{
                  color: "#DC2626", fontSize: 13, marginTop: -10, marginBottom: 12,
                  padding: "6px 12px", background: "rgba(220,38,38,0.05)", borderRadius: 8,
                }}>
                  Only @harrisfarm.com.au email addresses are accepted
                </div>
              )}
            </React.Fragment>
          );
        })}
      </Card>
    </div>
  );

  /* ── Dynamic section renderer ── */
  const renderSection = (sec) => (
    <div key={`${sec.key}-${stepKey}`}>
      {/* Section header with description */}
      {sec.description && (
        <div className="hfm-fade-enter" style={{
          textAlign: "center", marginBottom: 20, padding: "0 20px",
        }}>
          <div style={{
            fontSize: 14, color: "#2D2D2D", lineHeight: 1.6,
            fontStyle: "italic",
          }}>
            {sec.description}
          </div>
        </div>
      )}

      {(sec.cards || [{ title: null, description: null, questions: sec.questions, color: sec.color || accent }]).map((card, ci) => (
        <Card key={ci} title={card.title || (sec.cards ? null : null)} color={card.color || sec.color || accent} icon={card.icon} delay={ci}>
          {card.description && (
            <div style={{
              fontSize: 13, color: "#4A5568", marginBottom: 18, lineHeight: 1.6,
              background: `${(card.color || sec.color || accent)}08`,
              padding: "12px 16px", borderRadius: 8,
              borderLeft: `3px solid ${(card.color || sec.color || accent)}30`,
            }}>{card.description}</div>
          )}
          {(card.questions || []).map(q => {
            if (q.type === "slider") {
              return <Slider key={q.key} label={q.label} help={q.help} value={data[q.key] || 5}
                onChange={v => set(q.key, v)} color={q.color || card.color || sec.color || accent} />;
            }
            return <TextArea key={q.key} label={q.label} help={q.help} value={data[q.key] || ""}
              onChange={v => set(q.key, v)} rows={q.rows || 3} placeholder={q.placeholder} />;
          })}
        </Card>
      ))}
    </div>
  );

  /* ── Summary + Submit ── */
  const renderSummary = () => {
    const slidersBySection = {};
    sections.forEach(sec => {
      const allQ = [];
      if (sec.questions) allQ.push(...sec.questions);
      if (sec.cards) sec.cards.forEach(c => { if (c.questions) allQ.push(...c.questions); });
      const sliders = allQ.filter(q => q.type === "slider");
      if (sliders.length) {
        slidersBySection[sec.label] = sliders.map(q => ({
          label: q.label, value: data[q.key] || 5, key: q.key,
        }));
      }
    });

    const sectionNames = Object.keys(slidersBySection);
    const sortedSliders = [...allSliders].sort((a, b) => a.value - b.value);
    const gaps = sortedSliders.filter(g => g.value < 7).slice(0, 5);
    const strengths = [...allSliders].sort((a, b) => b.value - a.value).filter(g => g.value >= 8).slice(0, 3);

    return (
      <div key={stepKey}>
        {/* Overall score hero */}
        {allSliders.length > 0 && (
          <div className="hfm-scale-enter" style={{
            textAlign: "center", marginBottom: 24, padding: "32px 24px",
            background: `linear-gradient(135deg, ${accent}08, ${accent}18)`,
            borderRadius: 16, border: `1px solid ${accent}20`,
          }}>
            <div style={{ fontSize: 48, fontWeight: 800, fontFamily: "Georgia, serif", color: accent }}>
              {avgScore}
            </div>
            <div style={{ fontSize: 13, color: "#4A4A4A", letterSpacing: "0.08em", textTransform: "uppercase", marginTop: 4 }}>
              Overall Average Score
            </div>
            <div style={{ display: "flex", justifyContent: "center", gap: 12, marginTop: 12 }}>
              <span style={{
                fontSize: 11, padding: "4px 12px", borderRadius: 12,
                background: "rgba(45,106,45,0.08)", color: "#2D6A2D", fontWeight: 600,
              }}>
                {allSliders.filter(s => s.value >= 8).length} Strong
              </span>
              <span style={{
                fontSize: 11, padding: "4px 12px", borderRadius: 12,
                background: "rgba(146,113,10,0.08)", color: "#7A6209", fontWeight: 600,
              }}>
                {allSliders.filter(s => s.value >= 4 && s.value < 8).length} Building
              </span>
              <span style={{
                fontSize: 11, padding: "4px 12px", borderRadius: 12,
                background: "rgba(220,38,38,0.06)", color: "#DC2626", fontWeight: 600,
              }}>
                {allSliders.filter(s => s.value < 4).length} Critical
              </span>
            </div>
          </div>
        )}

        {/* Detailed scores by section */}
        {sectionNames.length > 0 && (
          <Card title="Score Breakdown" color={accent} icon={"\u{1F4CA}"} delay={0}>
            <div style={{
              display: "grid",
              gridTemplateColumns: sectionNames.length > 1 ? "1fr 1fr" : "1fr",
              gap: 20,
            }}>
              {sectionNames.map(secName => (
                <div key={secName}>
                  <div style={{
                    fontSize: 11, color: "#4A4A4A", marginBottom: 8, fontWeight: 700,
                    textTransform: "uppercase", letterSpacing: "0.08em",
                    paddingBottom: 6, borderBottom: `2px solid ${accent}20`,
                  }}>{secName}</div>
                  {slidersBySection[secName].map(s => (
                    <div key={s.key} style={{
                      display: "flex", justifyContent: "space-between", alignItems: "center",
                      padding: "6px 0", fontSize: 13, color: "#4A5568",
                    }}>
                      <span style={{ flex: 1 }}>{s.label}</span>
                      <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                        <div style={{
                          width: 40, height: 6, borderRadius: 3,
                          background: "rgba(0,0,0,0.04)", overflow: "hidden",
                        }}>
                          <div style={{
                            width: `${s.value * 10}%`, height: "100%",
                            background: s.value >= 8 ? "#2D6A2D" : s.value >= 6 ? "#92710A" : s.value >= 4 ? "#C2410C" : "#DC2626",
                            borderRadius: 3,
                          }} />
                        </div>
                        <strong style={{ color: "#1A1A1A", minWidth: 20, textAlign: "right" }}>{s.value}</strong>
                        <ScoreBadge score={s.value} />
                      </div>
                    </div>
                  ))}
                </div>
              ))}
            </div>

            {/* Attention areas */}
            {gaps.length > 0 && (
              <div style={{ marginTop: 20, paddingTop: 16, borderTop: "1px solid rgba(0,0,0,0.05)" }}>
                <div style={{ fontSize: 11, color: "#4A4A4A", marginBottom: 8, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em" }}>
                  Areas Needing Attention
                </div>
                <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                  {gaps.map(g => (
                    <span key={g.key} style={{
                      background: g.value < 4 ? "rgba(220,38,38,0.06)" : "rgba(249,115,22,0.06)",
                      color: g.value < 4 ? "#DC2626" : "#F97316",
                      padding: "5px 12px", borderRadius: 12, fontSize: 12, fontWeight: 600,
                      border: `1px solid ${g.value < 4 ? "rgba(220,38,38,0.15)" : "rgba(249,115,22,0.15)"}`,
                    }}>
                      {g.label}: {g.value}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {gaps.length === 0 && allSliders.length > 0 && (
              <div style={{
                marginTop: 16, paddingTop: 12, borderTop: "1px solid rgba(0,0,0,0.05)",
                textAlign: "center", color: "#2D6A2D", fontSize: 14, fontWeight: 600,
              }}>
                All scores 7+ — looking strong!
              </div>
            )}
          </Card>
        )}

        {/* Submit card */}
        <Card title="Ready to Submit" color={accent} icon={"\u{1F680}"} delay={1}>
          <div style={{
            fontSize: 14, color: "#4A5568", marginBottom: 20, lineHeight: 1.7,
          }}>
            Submitting saves your response to the database and downloads a backup JSON file.
            <br />
            <span style={{ fontStyle: "italic", color: "#4A4A4A" }}>
              Your voice shapes what comes next.
            </span>
          </div>
          <div style={{ display: "flex", gap: 12 }}>
            <button onClick={handleSubmit} disabled={submitting || !welcomeValid}
              style={{
                flex: 1,
                background: (!submitting && welcomeValid)
                  ? `linear-gradient(135deg, ${accent}, ${accent}DD)`
                  : "#E2E8F0",
                color: (!submitting && welcomeValid) ? "#fff" : "#A0AEC0",
                border: "none", borderRadius: 12, padding: "16px 28px",
                fontSize: 17, fontWeight: 700, fontFamily: "Georgia, serif",
                cursor: (!submitting && welcomeValid) ? "pointer" : "not-allowed",
                boxShadow: (!submitting && welcomeValid) ? `0 4px 14px ${accent}30` : "none",
                transition: "all 0.3s ease",
                transform: (!submitting && welcomeValid) ? "translateY(0)" : "none",
              }}>
              {submitting ? "Submitting..." : "\u{1F33F} Submit Response"}
            </button>
            <button onClick={handleReset}
              style={{
                background: "transparent", color: "#666666",
                border: "1px solid rgba(0,0,0,0.08)", borderRadius: 12,
                padding: "16px 18px", fontSize: 13, cursor: "pointer",
                transition: "all 0.2s",
              }}>
              Reset
            </button>
          </div>
          {!welcomeValid && (
            <div style={{
              fontSize: 12, color: "#F97316", marginTop: 10, padding: "8px 12px",
              background: "rgba(249,115,22,0.05)", borderRadius: 8,
            }}>
              Please complete all required fields in the Welcome section before submitting.
            </div>
          )}
          {error && (
            <div style={{
              background: "rgba(220,38,38,0.05)", border: "1px solid rgba(220,38,38,0.15)",
              borderRadius: 10, padding: "12px 16px", marginTop: 14, color: "#DC2626", fontSize: 13,
            }}>
              {error}
            </div>
          )}
        </Card>
      </div>
    );
  };

  /* ── Navigation buttons ── */
  const isLast = step === stepLabels.length - 1;
  const isSummary = showSummary && isLast;
  const canNext = step === 0 ? welcomeValid : true;

  const renderNav = () => {
    if (isSummary) {
      return (
        <div style={{ display: "flex", justifyContent: "flex-start", marginTop: 24 }}>
          <button onClick={() => goToStep(step - 1)}
            style={{
              background: "rgba(0,0,0,0.03)", color: "#4A5568",
              border: "1px solid rgba(0,0,0,0.06)", borderRadius: 10,
              padding: "12px 28px", fontSize: 14, cursor: "pointer",
              transition: "all 0.2s",
            }}>
            &larr; Back to Edit
          </button>
        </div>
      );
    }
    return (
      <div style={{ display: "flex", justifyContent: "space-between", marginTop: 24 }}>
        <button onClick={() => goToStep(step - 1)} disabled={step === 0}
          style={{
            background: step === 0 ? "transparent" : "rgba(0,0,0,0.03)",
            color: step === 0 ? "#D1D5DB" : "#4A5568",
            border: step === 0 ? "1px solid rgba(0,0,0,0.03)" : "1px solid rgba(0,0,0,0.06)",
            borderRadius: 10, padding: "12px 28px", fontSize: 14,
            cursor: step === 0 ? "default" : "pointer",
            transition: "all 0.2s",
          }}>
          &larr; Back
        </button>
        <button onClick={() => goToStep(step + 1)} disabled={!canNext}
          style={{
            background: canNext
              ? `linear-gradient(135deg, ${accent}, ${accent}DD)`
              : "#E2E8F0",
            color: canNext ? "#fff" : "#A0AEC0",
            border: "none", borderRadius: 10, padding: "12px 32px",
            fontSize: 14, fontWeight: 700, cursor: canNext ? "pointer" : "not-allowed",
            boxShadow: canNext ? `0 2px 8px ${accent}25` : "none",
            transition: "all 0.3s ease",
          }}>
          Next &rarr;
        </button>
      </div>
    );
  };

  /* ── Main render ── */
  return (
    <div style={{
      maxWidth: 960, margin: "0 auto",
      fontFamily: "'Trebuchet MS', 'Segoe UI', sans-serif",
      color: "#1A1A1A", padding: "20px 20px 48px",
      background: "#FAFAF7", minHeight: "100vh",
    }}>
      {/* Hero header */}
      <div className="hfm-fade-enter" style={{ textAlign: "center", marginBottom: 28, position: "relative" }}>
        <div style={{ fontSize: 36, marginBottom: 8 }}>{C.headerEmoji || "\u{1F33F}"}</div>
        <h1 style={{
          fontFamily: "Georgia, serif", fontSize: 30, fontWeight: 700,
          marginBottom: 6, lineHeight: 1.3,
          background: `linear-gradient(135deg, ${accent}, ${accent}BB)`,
          WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent",
          backgroundClip: "text",
        }}>
          {C.title || "Meeting Form"}
        </h1>
        {C.subtitle && (
          <p style={{ color: "#2D2D2D", fontSize: 15, maxWidth: 500, margin: "0 auto", lineHeight: 1.5 }}>
            {C.subtitle}
          </p>
        )}
        {/* AI First badge */}
        <div style={{
          display: "inline-flex", alignItems: "center", gap: 6,
          background: "rgba(0,0,0,0.03)", borderRadius: 20,
          padding: "4px 14px", marginTop: 10,
          fontSize: 11, color: "#666666", letterSpacing: "0.04em",
        }}>
          <span style={{ fontSize: 13 }}>&#x1F916;</span>
          AI-First Meeting OS &middot; The Harris Farm Way
        </div>
      </div>

      {renderStepper()}

      {/* Content */}
      {step === 0 && renderWelcome()}
      {step > 0 && step <= sections.length && renderSection(sections[step - 1])}
      {isSummary && renderSummary()}

      {renderNav()}

      {/* Footer */}
      <div style={{
        textAlign: "center", marginTop: 32, padding: "16px 0",
        borderTop: "1px solid rgba(0,0,0,0.04)",
      }}>
        <div style={{ fontSize: 12, color: "#666666", lineHeight: 1.8 }}>
          <span style={{ fontSize: 14 }}>&#127822;</span> Harris Farm Markets &middot; The Harris Farm Way
          <br />
          <span style={{ fontStyle: "italic" }}>Built by our people, powered by AI, grown with purpose.</span>
        </div>
      </div>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
