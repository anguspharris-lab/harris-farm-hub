/**
 * Harris Farm Markets — AI Readiness Review (ARR)
 * Version 1.0 — March 2026
 *
 * Self-contained React artifact for Claude.ai AND Hub embedding.
 * 5-section stepper: Welcome -> Current State -> ADKAR -> Vision -> Capability Ratings
 * Auto-saves to localStorage. Download JSON + submit to BigQuery on complete.
 * HFM dark theme (navy #0A0F0A, blue-green #06B6D4 accent for AI).
 */

const { useState, useEffect, useCallback } = React;

const STORAGE_KEY = "hfm_arr_interview_v1";

const AI_CAPABILITIES = [
  { key: "data_literacy", label: "Data Literacy", help: "Team's ability to understand, interpret, and work with data day-to-day" },
  { key: "tool_exposure", label: "AI Tool Familiarity", help: "Current exposure to AI tools (ChatGPT, Copilot, Claude, automation)" },
  { key: "process_readiness", label: "Process Readiness", help: "How ready are current workflows for AI-assisted automation?" },
  { key: "data_quality", label: "Data Quality for AI", help: "Is our data clean, structured, and accessible enough for AI to use?" },
  { key: "digital_skills", label: "Digital Skills", help: "General digital competency across the team (Excel, systems, platforms)" },
  { key: "change_appetite", label: "Change Appetite", help: "Willingness to try new tools and adopt new ways of working" },
  { key: "governance", label: "AI Governance & Trust", help: "Understanding of AI risks, data privacy, ethics, and when NOT to use AI" },
  { key: "use_case_clarity", label: "Use Case Clarity", help: "How clear is it where AI can genuinely add value vs. where it can't?" },
];

const SECTIONS = [
  { key: "welcome", label: "Welcome", num: 1 },
  { key: "current", label: "Current State", num: 2 },
  { key: "adkar", label: "Change Readiness", num: 3 },
  { key: "vision", label: "The Vision", num: 4 },
  { key: "ratings", label: "AI Capabilities", num: 5 },
];

const defaultData = () => ({
  meta: { version: "1.0", tool: "hfm-arr-interview", timestamp: "" },
  respondent: { name: "", role: "", department: "", ai_touchpoint: "" },
  current_state: { current_tools: "", pain_points: "", external_pressures: "" },
  scores: {
    confidence: 5, leverage: 5, urgency: 5,
    desire: 5, clarity: 5, readiness: 5, sustain: 5,
  },
  capabilities: Object.fromEntries(AI_CAPABILITIES.map(c => [c.key, 5])),
  qualitative: {
    opportunities: "", concerns: "",
    ideal_5yr: "", one_big_thing: "", impact_if_successful: "",
    training_needs: "", additional_comments: "",
  },
});

function Slider({ label, help, value, onChange, color = "#06B6D4" }) {
  return (
    <div style={{ marginBottom: 18 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 4 }}>
        <span style={{ fontWeight: 600, fontSize: 14, color: "#F1F8E9" }}>{label}</span>
        <span style={{ fontSize: 22, fontWeight: 700, color, minWidth: 32, textAlign: "right" }}>{value}</span>
      </div>
      {help && <div style={{ fontSize: 12, color: "#8899AA", marginBottom: 6 }}>{help}</div>}
      <input
        type="range" min="1" max="10" value={value} onChange={e => onChange(parseInt(e.target.value))}
        style={{ width: "100%", accentColor: color, cursor: "pointer" }}
      />
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: "#6B7B8D" }}>
        <span>Critical</span><span>Strong</span>
      </div>
    </div>
  );
}

function TextArea({ label, help, value, onChange, rows = 3 }) {
  return (
    <div style={{ marginBottom: 16 }}>
      <label style={{ fontWeight: 600, fontSize: 14, color: "#F1F8E9", display: "block", marginBottom: 4 }}>{label}</label>
      {help && <div style={{ fontSize: 12, color: "#8899AA", marginBottom: 6 }}>{help}</div>}
      <textarea
        value={value} onChange={e => onChange(e.target.value)} rows={rows}
        style={{
          width: "100%", background: "#111A11", border: "1px solid rgba(255,255,255,0.12)",
          borderRadius: 8, padding: "10px 12px", color: "#F1F8E9", fontSize: 14,
          fontFamily: "'Trebuchet MS', sans-serif", resize: "vertical",
        }}
        placeholder="Type your response..."
      />
    </div>
  );
}

function TextInput({ label, value, onChange, placeholder = "" }) {
  return (
    <div style={{ marginBottom: 14 }}>
      <label style={{ fontWeight: 600, fontSize: 14, color: "#F1F8E9", display: "block", marginBottom: 4 }}>{label}</label>
      <input
        type="text" value={value} onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        style={{
          width: "100%", background: "#111A11", border: "1px solid rgba(255,255,255,0.12)",
          borderRadius: 8, padding: "10px 12px", color: "#F1F8E9", fontSize: 14,
          fontFamily: "'Trebuchet MS', sans-serif",
        }}
      />
    </div>
  );
}

function Card({ title, children, color = "#06B6D4" }) {
  return (
    <div style={{
      background: "#0D150D", border: "1px solid rgba(255,255,255,0.08)",
      borderRadius: 12, padding: "20px 24px", marginBottom: 20,
      borderTop: `3px solid ${color}`,
    }}>
      {title && <h3 style={{ fontFamily: "Georgia, serif", color, fontSize: 18, fontWeight: 600, marginTop: 0, marginBottom: 14 }}>{title}</h3>}
      {children}
    </div>
  );
}

function ScoreInterpretation({ score }) {
  let color, text;
  if (score >= 8) { color = "#2ECC71"; text = "Strong"; }
  else if (score >= 6) { color = "#F1C40F"; text = "Adequate"; }
  else if (score >= 4) { color = "#F97316"; text = "Gap"; }
  else { color = "#EF4444"; text = "Critical"; }
  return <span style={{ fontSize: 11, fontWeight: 600, color, marginLeft: 8 }}>{text}</span>;
}

function AIReadinessInterview() {
  const [step, setStep] = useState(0);
  const [data, setData] = useState(defaultData);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) setData(JSON.parse(stored));
    } catch (e) { /* ignore */ }
  }, []);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
    } catch (e) { /* ignore */ }
  }, [data]);

  const update = useCallback((path, value) => {
    setData(prev => {
      const copy = JSON.parse(JSON.stringify(prev));
      const keys = path.split(".");
      let obj = copy;
      for (let i = 0; i < keys.length - 1; i++) obj = obj[keys[i]];
      obj[keys[keys.length - 1]] = value;
      return copy;
    });
  }, []);

  const [submitting, setSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState("");

  const submitToBigQuery = async (output) => {
    const CF_URL = "https://australia-southeast1-oval-blend-488902-p2.cloudfunctions.net/hfm-scr-insert?api_key=hfm-scr-2026";
    const params = new URLSearchParams({
      name: output.respondent?.name || "",
      role: output.respondent?.role || "",
      sc_touch: output.respondent?.ai_touchpoint || "",
      meeting_type: "ARR",
      // ADKAR scores (shared with SCR)
      five_year_confidence: String(output.scores?.confidence || ""),
      leverage_strengths: String(output.scores?.leverage || ""),
      urgency: String(output.scores?.urgency || ""),
      desire_score: String(output.scores?.desire || ""),
      clarity_score: String(output.scores?.clarity || ""),
      readiness_score: String(output.scores?.readiness || ""),
      sustain_score: String(output.scores?.sustain || ""),
      // AI capability ratings
      ai_data_literacy: String(output.capabilities?.data_literacy || ""),
      ai_tool_exposure: String(output.capabilities?.tool_exposure || ""),
      ai_process_readiness: String(output.capabilities?.process_readiness || ""),
      ai_data_quality: String(output.capabilities?.data_quality || ""),
      ai_digital_skills: String(output.capabilities?.digital_skills || ""),
      ai_change_appetite: String(output.capabilities?.change_appetite || ""),
      ai_governance: String(output.capabilities?.governance || ""),
      ai_use_case_clarity: String(output.capabilities?.use_case_clarity || ""),
      // AI qualitative fields
      ai_current_tools: output.current_state?.current_tools || "",
      ai_pain_points: output.current_state?.pain_points || "",
      ai_opportunities: output.qualitative?.opportunities || "",
      ai_concerns: output.qualitative?.concerns || "",
      ai_training_needs: output.qualitative?.training_needs || "",
      // Shared qualitative (reuse existing columns)
      protect_processes: "",
      external_pressures: output.current_state?.external_pressures || "",
      worries: output.qualitative?.concerns || "",
      ideal_5yr: output.qualitative?.ideal_5yr || "",
      one_big_thing: output.qualitative?.one_big_thing || "",
      customer_impact: output.qualitative?.impact_if_successful || "",
      additional: output.qualitative?.additional_comments || "",
    });
    if (navigator.sendBeacon) {
      const sent = navigator.sendBeacon(CF_URL, params.toString());
      if (sent) return { success: true };
    }
    const resp = await fetch(CF_URL, {
      method: "POST",
      headers: { "Content-Type": "text/plain" },
      body: params.toString(),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return resp.json();
  };

  const handleDownload = async () => {
    const output = { ...data, meta: { ...data.meta, timestamp: new Date().toISOString() } };

    const blob = new Blob([JSON.stringify(output, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `arr-interview-${(data.respondent.name || "unknown").toLowerCase().replace(/\s+/g, "-")}-${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);

    setSubmitting(true);
    setSubmitStatus("");
    try {
      await submitToBigQuery(output);
      setSubmitStatus("success");
    } catch (e) {
      setSubmitStatus("error");
      console.error("BigQuery submit failed:", e);
    }
    setSubmitting(false);
    setSaved(true);
  };

  const handleReset = () => {
    if (confirm("Clear all responses and start fresh?")) {
      setData(defaultData());
      setStep(0);
      localStorage.removeItem(STORAGE_KEY);
      setSaved(false);
    }
  };

  const progress = Math.round(((step + 1) / SECTIONS.length) * 100);
  const isComplete = data.respondent.name && data.respondent.role;

  return (
    <div style={{
      maxWidth: 720, margin: "0 auto", fontFamily: "'Trebuchet MS', 'Segoe UI', sans-serif",
      color: "#F1F8E9", padding: "0 12px",
    }}>
      {/* Header */}
      <div style={{ textAlign: "center", marginBottom: 24 }}>
        <h1 style={{ fontFamily: "Georgia, serif", color: "#06B6D4", fontSize: 28, fontWeight: 700, marginBottom: 4 }}>
          AI Readiness Review
        </h1>
        <p style={{ color: "#8899AA", fontSize: 14 }}>Harris Farm Markets — Stakeholder Interview</p>
      </div>

      {/* Progress */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
          {SECTIONS.map((s, i) => (
            <button
              key={s.key}
              onClick={() => setStep(i)}
              style={{
                background: i === step ? "#06B6D4" : i < step ? "rgba(6,182,212,0.3)" : "rgba(255,255,255,0.05)",
                color: i === step ? "#0A0F0A" : i < step ? "#06B6D4" : "#6B7B8D",
                border: "none", borderRadius: 20, padding: "6px 12px",
                fontSize: 12, fontWeight: i === step ? 700 : 400, cursor: "pointer",
                transition: "all 0.2s",
              }}
            >
              {s.num}. {s.label}
            </button>
          ))}
        </div>
        <div style={{ background: "rgba(255,255,255,0.08)", borderRadius: 4, height: 4, overflow: "hidden" }}>
          <div style={{ width: `${progress}%`, background: "#06B6D4", height: "100%", transition: "width 0.3s", borderRadius: 4 }} />
        </div>
      </div>

      {/* Section 1: Welcome */}
      {step === 0 && (
        <div>
          <Card title="About You" color="#06B6D4">
            <div style={{ background: "rgba(6,182,212,0.08)", borderRadius: 8, padding: 14, marginBottom: 18, fontSize: 13, color: "#B0BEC5", lineHeight: 1.5 }}>
              This interview takes 10-15 minutes. Your responses will help us understand where Harris Farm is today
              with AI and technology, and where we should focus next. All answers are confidential.
            </div>
            <TextInput label="Your Name" value={data.respondent.name} onChange={v => update("respondent.name", v)} placeholder="Full name" />
            <TextInput label="Your Role" value={data.respondent.role} onChange={v => update("respondent.role", v)} placeholder="e.g. Buyer, Store Manager, Head of Operations" />
            <TextInput label="Department" value={data.respondent.department} onChange={v => update("respondent.department", v)} placeholder="e.g. Buying, Operations, IT, Supply Chain" />
          </Card>
          <Card title="Your AI Touchpoint" color="#3B82F6">
            <TextArea
              label="How does AI or technology touch your day-to-day work?"
              help="Think broadly — spreadsheets, reporting tools, automation, AI chatbots, anything digital"
              value={data.respondent.ai_touchpoint}
              onChange={v => update("respondent.ai_touchpoint", v)}
            />
            <Slider
              label="5-Year Confidence" value={data.scores.confidence}
              help="How confident are you that HFM's current technology and tools can support our growth over the next 5 years?"
              onChange={v => update("scores.confidence", v)}
            />
          </Card>
        </div>
      )}

      {/* Section 2: Current State */}
      {step === 1 && (
        <div>
          <Card title="What AI/Tech Do You Use Today?" color="#06B6D4">
            <TextArea
              label="What tools and technology do you currently use?"
              help="List everything — Excel, ChatGPT, Power BI, D365, email, Slack, any apps or AI tools"
              value={data.current_state.current_tools}
              onChange={v => update("current_state.current_tools", v)}
              rows={4}
            />
          </Card>
          <Card title="Pain Points & Time Wasters" color="#F97316">
            <TextArea
              label="What tasks waste the most time or cause the most frustration?"
              help="Repetitive reporting, manual data entry, chasing information, slow approvals..."
              value={data.current_state.pain_points}
              onChange={v => update("current_state.pain_points", v)}
              rows={4}
            />
            <TextArea
              label="What external pressures are driving the need for AI/technology?"
              help="Competitor moves, customer expectations, cost pressures, speed-to-market..."
              value={data.current_state.external_pressures}
              onChange={v => update("current_state.external_pressures", v)}
              rows={3}
            />
          </Card>
          <Card title="Scores" color="#F1C40F">
            <Slider
              label="Leverage" value={data.scores.leverage}
              help="How well do we leverage the technology and data we already have?"
              onChange={v => update("scores.leverage", v)} color="#F1C40F"
            />
            <Slider
              label="Urgency" value={data.scores.urgency}
              help="How urgent is AI adoption for HFM right now?"
              onChange={v => update("scores.urgency", v)} color="#F97316"
            />
          </Card>
        </div>
      )}

      {/* Section 3: ADKAR Change Readiness */}
      {step === 2 && (
        <div>
          <Card title="Change Readiness (ADKAR)" color="#8B5CF6">
            <div style={{ background: "rgba(139,92,246,0.08)", borderRadius: 8, padding: 14, marginBottom: 18, fontSize: 13, color: "#B0BEC5", lineHeight: 1.5 }}>
              ADKAR measures five dimensions of change readiness. Rate each on a 1-10 scale
              for AI adoption at Harris Farm.
            </div>
            <TextArea
              label="Where do you see the biggest opportunities for AI at HFM?"
              value={data.qualitative.opportunities}
              onChange={v => update("qualitative.opportunities", v)}
              rows={3}
            />
            <TextArea
              label="What concerns you most about AI adoption?"
              value={data.qualitative.concerns}
              onChange={v => update("qualitative.concerns", v)}
              rows={3}
            />
          </Card>
          <Card title="ADKAR Dimensions" color="#8B5CF6">
            <Slider
              label="Awareness" value={data.scores.urgency}
              help="Does the team understand WHY AI adoption is important for HFM?"
              onChange={v => update("scores.urgency", v)} color="#EF4444"
            />
            <Slider
              label="Desire" value={data.scores.desire}
              help="Does the team WANT to adopt AI tools and new ways of working?"
              onChange={v => update("scores.desire", v)} color="#F97316"
            />
            <Slider
              label="Knowledge" value={data.scores.clarity}
              help="Does the team know WHAT AI can do and HOW to use it effectively?"
              onChange={v => update("scores.clarity", v)} color="#F1C40F"
            />
            <Slider
              label="Ability" value={data.scores.readiness}
              help="Can the organisation EXECUTE an AI rollout right now?"
              onChange={v => update("scores.readiness", v)} color="#3B82F6"
            />
            <Slider
              label="Reinforcement" value={data.scores.sustain}
              help="Will AI adoption STICK? Can we sustain new tools and habits?"
              onChange={v => update("scores.sustain", v)} color="#8B5CF6"
            />
          </Card>
        </div>
      )}

      {/* Section 4: Vision */}
      {step === 3 && (
        <div>
          <Card title="The AI Vision" color="#06B6D4">
            <TextArea
              label="What does AI-enabled Harris Farm look like in 5 years?"
              help="Paint the picture. How would your day-to-day be different? What would customers notice?"
              value={data.qualitative.ideal_5yr}
              onChange={v => update("qualitative.ideal_5yr", v)}
              rows={5}
            />
            <TextArea
              label="If you could automate or AI-enable ONE thing, what would it be?"
              help="The single highest-impact use case for AI in your area"
              value={data.qualitative.one_big_thing}
              onChange={v => update("qualitative.one_big_thing", v)}
              rows={3}
            />
            <TextArea
              label="If we get AI right, what's the impact on customers and the team?"
              help="What does success look like for the people who matter most?"
              value={data.qualitative.impact_if_successful}
              onChange={v => update("qualitative.impact_if_successful", v)}
              rows={3}
            />
          </Card>
        </div>
      )}

      {/* Section 5: AI Capability Ratings + Submit */}
      {step === 4 && (
        <div>
          <Card title="AI Capability Assessment" color="#F1C40F">
            <div style={{ fontSize: 13, color: "#B0BEC5", marginBottom: 16 }}>
              Rate each AI readiness dimension from 1 (critical gap) to 10 (well-prepared).
            </div>
            {AI_CAPABILITIES.map(cap => (
              <Slider
                key={cap.key}
                label={cap.label}
                help={cap.help}
                value={data.capabilities[cap.key]}
                onChange={v => update(`capabilities.${cap.key}`, v)}
                color="#F1C40F"
              />
            ))}
          </Card>
          <Card title="Training & Support" color="#8B5CF6">
            <TextArea
              label="What training or support would help you most with AI?"
              help="Workshops, 1-on-1 coaching, online courses, hands-on practice, prompt writing..."
              value={data.qualitative.training_needs}
              onChange={v => update("qualitative.training_needs", v)}
              rows={3}
            />
            <TextArea
              label="Anything else?"
              help="Any other thoughts about AI at Harris Farm"
              value={data.qualitative.additional_comments}
              onChange={v => update("qualitative.additional_comments", v)}
              rows={3}
            />
          </Card>

          {/* Summary */}
          <Card title="Response Summary" color="#06B6D4">
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 16 }}>
              <div>
                <div style={{ fontSize: 12, color: "#8899AA", marginBottom: 4 }}>ADKAR Scores</div>
                {[
                  ["Awareness", data.scores.urgency],
                  ["Desire", data.scores.desire],
                  ["Knowledge", data.scores.clarity],
                  ["Ability", data.scores.readiness],
                  ["Reinforcement", data.scores.sustain],
                ].map(([label, score]) => (
                  <div key={label} style={{ display: "flex", justifyContent: "space-between", padding: "3px 0", fontSize: 13, color: "#B0BEC5" }}>
                    <span>{label}</span>
                    <span><strong style={{ color: "#F1F8E9" }}>{score}</strong><ScoreInterpretation score={score} /></span>
                  </div>
                ))}
              </div>
              <div>
                <div style={{ fontSize: 12, color: "#8899AA", marginBottom: 4 }}>Top AI Capability Gaps</div>
                {Object.entries(data.capabilities)
                  .sort((a, b) => a[1] - b[1])
                  .slice(0, 4)
                  .map(([key, score]) => (
                    <div key={key} style={{ display: "flex", justifyContent: "space-between", padding: "3px 0", fontSize: 13, color: "#B0BEC5" }}>
                      <span>{AI_CAPABILITIES.find(c => c.key === key)?.label}</span>
                      <span><strong style={{ color: "#F1F8E9" }}>{score}</strong><ScoreInterpretation score={score} /></span>
                    </div>
                  ))}
              </div>
            </div>

            <div style={{ display: "flex", gap: 10, marginTop: 16 }}>
              <button
                onClick={handleDownload}
                disabled={!isComplete}
                style={{
                  flex: 1, background: isComplete ? "#06B6D4" : "#333",
                  color: isComplete ? "#0A0F0A" : "#666",
                  border: "none", borderRadius: 8, padding: "14px 20px",
                  fontSize: 16, fontWeight: 700, cursor: isComplete ? "pointer" : "not-allowed",
                  fontFamily: "Georgia, serif",
                }}
              >
                {submitting ? "Submitting..." : saved ? "Submitted" : "Submit Response"}
              </button>
              <button
                onClick={handleReset}
                style={{
                  background: "transparent", color: "#EF4444",
                  border: "1px solid rgba(239,68,68,0.3)", borderRadius: 8,
                  padding: "14px 16px", fontSize: 13, cursor: "pointer",
                }}
              >
                Reset
              </button>
            </div>
            {!isComplete && (
              <div style={{ fontSize: 12, color: "#F97316", marginTop: 8 }}>
                Please enter your name and role in Section 1 before submitting.
              </div>
            )}
            {submitting && (
              <div style={{ fontSize: 13, color: "#3B82F6", marginTop: 8, textAlign: "center" }}>
                Saving to database...
              </div>
            )}
            {saved && (
              <div style={{ fontSize: 13, color: "#06B6D4", marginTop: 8, textAlign: "center" }}>
                {submitStatus === "success"
                  ? "Response saved to database and downloaded. You can close this page."
                  : submitStatus === "error"
                  ? "Downloaded locally. Database save failed — your JSON file is the backup."
                  : "Response saved. You can close this page or download again."}
              </div>
            )}
          </Card>
        </div>
      )}

      {/* Navigation */}
      <div style={{ display: "flex", justifyContent: "space-between", marginTop: 20, marginBottom: 40 }}>
        <button
          onClick={() => setStep(Math.max(0, step - 1))}
          disabled={step === 0}
          style={{
            background: step === 0 ? "transparent" : "rgba(255,255,255,0.05)",
            color: step === 0 ? "#333" : "#B0BEC5",
            border: "1px solid rgba(255,255,255,0.08)", borderRadius: 8,
            padding: "10px 24px", fontSize: 14, cursor: step === 0 ? "default" : "pointer",
          }}
        >
          Back
        </button>
        {step < SECTIONS.length - 1 && (
          <button
            onClick={() => setStep(Math.min(SECTIONS.length - 1, step + 1))}
            style={{
              background: "#06B6D4", color: "#0A0F0A",
              border: "none", borderRadius: 8,
              padding: "10px 24px", fontSize: 14, fontWeight: 700, cursor: "pointer",
            }}
          >
            Next
          </button>
        )}
      </div>
    </div>
  );
}

// Render
const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<AIReadinessInterview />);
