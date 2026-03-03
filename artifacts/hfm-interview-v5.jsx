/**
 * Harris Farm Markets — Supply Chain Transformation Interview
 * Version 5.0 — March 2026
 *
 * Self-contained React artifact for Claude.ai AND Hub embedding.
 * 5-section stepper: Welcome -> What's Working -> ADKAR -> Vision -> Quick Ratings
 * Auto-saves to localStorage. Download JSON on submit.
 * HFM dark theme (navy #0A0F0A, green #2ECC71).
 */

const { useState, useEffect, useCallback } = React;

const STORAGE_KEY = "hfm_sc_interview_v5";

const CAPABILITIES = [
  { key: "visibility", label: "Supply Chain Visibility", help: "End-to-end view of inventory, orders, and flow" },
  { key: "disruption_response", label: "Disruption Response", help: "Speed and effectiveness when things go wrong" },
  { key: "data_quality", label: "Data & Insights", help: "Quality and timeliness of supply chain data" },
  { key: "technology", label: "Technology & Tools", help: "Systems supporting supply chain operations" },
  { key: "suppliers", label: "Supplier Relationships", help: "Partnership quality, reliability, communication" },
  { key: "transport", label: "Transport & Logistics", help: "Delivery efficiency, route optimisation, costs" },
  { key: "demand_planning", label: "Demand Planning", help: "Forecasting accuracy, seasonal readiness" },
  { key: "sustainability", label: "Sustainability & Waste", help: "Waste reduction, packaging, environmental impact" },
];

const SECTIONS = [
  { key: "welcome", label: "Welcome", num: 1 },
  { key: "working", label: "What's Working", num: 2 },
  { key: "adkar", label: "Change Readiness", num: 3 },
  { key: "vision", label: "The Vision", num: 4 },
  { key: "ratings", label: "Quick Ratings", num: 5 },
];

const defaultData = () => ({
  meta: { version: "5.0", tool: "hfm-sc-interview", timestamp: "" },
  respondent: { name: "", role: "", department: "", sc_touchpoint: "" },
  whats_working: { protect: "", pain_points: "", external_pressures: "" },
  scores: {
    confidence: 5, leverage: 5, urgency: 5,
    desire: 5, clarity: 5, readiness: 5, sustain: 5,
  },
  capabilities: Object.fromEntries(CAPABILITIES.map(c => [c.key, 5])),
  qualitative: {
    excites: "", worries: "",
    ideal_5yr: "", one_big_thing: "", impact_if_successful: "",
    additional_comments: "",
  },
});

function Slider({ label, help, value, onChange, color = "#2ECC71" }) {
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

function Card({ title, children, color = "#2ECC71" }) {
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

function SupplyChainInterview() {
  const [step, setStep] = useState(0);
  const [data, setData] = useState(defaultData);
  const [saved, setSaved] = useState(false);

  // Load from localStorage
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) setData(JSON.parse(stored));
    } catch (e) { /* ignore */ }
  }, []);

  // Auto-save
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
    const CF_URL = "https://australia-southeast1-oval-blend-488902-p2.cloudfunctions.net/hfm-scr-insert";
    const API_KEY = "hfm-scr-2026";
    const payload = {
      name: output.respondent?.name || "",
      role: output.respondent?.role || "",
      sc_touch: output.respondent?.sc_touchpoint || "",
      five_year_confidence: output.scores?.confidence,
      leverage_strengths: output.scores?.leverage,
      urgency: output.scores?.urgency,
      desire_score: output.scores?.desire,
      clarity_score: output.scores?.clarity,
      readiness_score: output.scores?.readiness,
      sustain_score: output.scores?.sustain,
      rf_visibility: output.capabilities?.visibility,
      rf_disruption: output.capabilities?.disruption_response,
      rf_data: output.capabilities?.data_quality,
      rf_technology: output.capabilities?.technology,
      rf_suppliers: output.capabilities?.suppliers,
      rf_transport: output.capabilities?.transport,
      rf_demand: output.capabilities?.demand_planning,
      rf_sustainability: output.capabilities?.sustainability,
      protect_processes: output.whats_working?.protect || "",
      external_pressures: output.whats_working?.external_pressures || "",
      worries: output.qualitative?.worries || "",
      ideal_5yr: output.qualitative?.ideal_5yr || "",
      one_big_thing: output.qualitative?.one_big_thing || "",
      customer_impact: output.qualitative?.impact_if_successful || "",
      concepts_investigate: "",
      additional: output.qualitative?.additional_comments || "",
    };
    const resp = await fetch(CF_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-API-Key": API_KEY },
      body: JSON.stringify(payload),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return resp.json();
  };

  const handleDownload = async () => {
    const output = { ...data, meta: { ...data.meta, timestamp: new Date().toISOString() } };

    // Download JSON file
    const blob = new Blob([JSON.stringify(output, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `sc-interview-${(data.respondent.name || "unknown").toLowerCase().replace(/\s+/g, "-")}-${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);

    // Submit to BigQuery via Cloud Function
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

  // Check completeness
  const isComplete = data.respondent.name && data.respondent.role;

  return (
    <div style={{
      maxWidth: 720, margin: "0 auto", fontFamily: "'Trebuchet MS', 'Segoe UI', sans-serif",
      color: "#F1F8E9", padding: "0 12px",
    }}>
      {/* Header */}
      <div style={{ textAlign: "center", marginBottom: 24 }}>
        <h1 style={{ fontFamily: "Georgia, serif", color: "#2ECC71", fontSize: 28, fontWeight: 700, marginBottom: 4 }}>
          Supply Chain Transformation
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
                background: i === step ? "#2ECC71" : i < step ? "rgba(46,204,113,0.3)" : "rgba(255,255,255,0.05)",
                color: i === step ? "#0A0F0A" : i < step ? "#2ECC71" : "#6B7B8D",
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
          <div style={{ width: `${progress}%`, background: "#2ECC71", height: "100%", transition: "width 0.3s", borderRadius: 4 }} />
        </div>
      </div>

      {/* Section 1: Welcome */}
      {step === 0 && (
        <div>
          <Card title="About You" color="#2ECC71">
            <div style={{ background: "rgba(46,204,113,0.08)", borderRadius: 8, padding: 14, marginBottom: 18, fontSize: 13, color: "#B0BEC5", lineHeight: 1.5 }}>
              This interview takes 10-15 minutes. Your responses will help shape our supply chain transformation program.
              All answers are confidential and used for diagnostic purposes only.
            </div>
            <TextInput label="Your Name" value={data.respondent.name} onChange={v => update("respondent.name", v)} placeholder="Full name" />
            <TextInput label="Your Role" value={data.respondent.role} onChange={v => update("respondent.role", v)} placeholder="e.g. Head of Logistics, Store Manager" />
            <TextInput label="Department" value={data.respondent.department} onChange={v => update("respondent.department", v)} placeholder="e.g. Supply Chain, Operations, Buying" />
          </Card>
          <Card title="Supply Chain Connection" color="#3B82F6">
            <TextArea
              label="How does supply chain touch your day-to-day?"
              help="What parts of the supply chain do you interact with most?"
              value={data.respondent.sc_touchpoint}
              onChange={v => update("respondent.sc_touchpoint", v)}
            />
            <Slider
              label="5-Year Confidence" value={data.scores.confidence}
              help="How confident are you that our current supply chain can support HFM's growth over the next 5 years?"
              onChange={v => update("scores.confidence", v)}
            />
          </Card>
        </div>
      )}

      {/* Section 2: What's Working */}
      {step === 1 && (
        <div>
          <Card title="What to Protect" color="#2ECC71">
            <TextArea
              label="What's working well that we should protect?"
              help="What parts of our supply chain work well today? What would you NOT want to change?"
              value={data.whats_working.protect}
              onChange={v => update("whats_working.protect", v)}
              rows={4}
            />
          </Card>
          <Card title="Pressures & Challenges" color="#F97316">
            <TextArea
              label="What are the biggest pain points?"
              help="Where does the supply chain create friction, delays, or waste?"
              value={data.whats_working.pain_points}
              onChange={v => update("whats_working.pain_points", v)}
              rows={4}
            />
            <TextArea
              label="What external pressures concern you?"
              help="Market changes, competitor moves, regulatory shifts, supplier risks..."
              value={data.whats_working.external_pressures}
              onChange={v => update("whats_working.external_pressures", v)}
              rows={3}
            />
          </Card>
          <Card title="Scores" color="#F1C40F">
            <Slider
              label="Leverage" value={data.scores.leverage}
              help="How well do we leverage our existing supply chain strengths?"
              onChange={v => update("scores.leverage", v)} color="#F1C40F"
            />
            <Slider
              label="Urgency" value={data.scores.urgency}
              help="How urgent is supply chain transformation for HFM right now?"
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
              ADKAR measures five dimensions of change readiness: Awareness, Desire, Knowledge, Ability, and Reinforcement.
              Rate each on a 1-10 scale for our supply chain transformation.
            </div>
            <TextArea
              label="What excites you about transforming our supply chain?"
              value={data.qualitative.excites}
              onChange={v => update("qualitative.excites", v)}
              rows={3}
            />
            <TextArea
              label="What worries you about it?"
              value={data.qualitative.worries}
              onChange={v => update("qualitative.worries", v)}
              rows={3}
            />
          </Card>
          <Card title="ADKAR Dimensions" color="#8B5CF6">
            <Slider
              label="Awareness" value={data.scores.urgency}
              help="Does the team understand WHY supply chain change is needed?"
              onChange={v => update("scores.urgency", v)} color="#EF4444"
            />
            <Slider
              label="Desire" value={data.scores.desire}
              help="Does the team WANT this transformation to happen?"
              onChange={v => update("scores.desire", v)} color="#F97316"
            />
            <Slider
              label="Knowledge" value={data.scores.clarity}
              help="Does the team know WHAT good looks like and HOW to get there?"
              onChange={v => update("scores.clarity", v)} color="#F1C40F"
            />
            <Slider
              label="Ability" value={data.scores.readiness}
              help="Can the organisation EXECUTE the transformation right now?"
              onChange={v => update("scores.readiness", v)} color="#3B82F6"
            />
            <Slider
              label="Reinforcement" value={data.scores.sustain}
              help="Will changes STICK? Can we sustain new ways of working?"
              onChange={v => update("scores.sustain", v)} color="#8B5CF6"
            />
          </Card>
        </div>
      )}

      {/* Section 4: Vision */}
      {step === 3 && (
        <div>
          <Card title="The Vision" color="#06B6D4">
            <TextArea
              label="What does a world-class supply chain look like for HFM in 5 years?"
              help="Paint the picture. What would be different? What would it feel like?"
              value={data.qualitative.ideal_5yr}
              onChange={v => update("qualitative.ideal_5yr", v)}
              rows={5}
            />
            <TextArea
              label="If you could change ONE big thing, what would it be?"
              help="The single highest-impact change you'd make"
              value={data.qualitative.one_big_thing}
              onChange={v => update("qualitative.one_big_thing", v)}
              rows={3}
            />
            <TextArea
              label="If we get this right, what's the impact on customers and the team?"
              help="What does success look like for the people who matter most?"
              value={data.qualitative.impact_if_successful}
              onChange={v => update("qualitative.impact_if_successful", v)}
              rows={3}
            />
          </Card>
        </div>
      )}

      {/* Section 5: Quick Ratings + Submit */}
      {step === 4 && (
        <div>
          <Card title="Capability Assessment" color="#F1C40F">
            <div style={{ fontSize: 13, color: "#B0BEC5", marginBottom: 16 }}>
              Rate each supply chain capability from 1 (critical gap) to 10 (world-class).
            </div>
            {CAPABILITIES.map(cap => (
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
          <Card title="Anything Else?" color="#8899AA">
            <TextArea
              label="Additional comments or thoughts"
              help="Anything we haven't covered that you think is important"
              value={data.qualitative.additional_comments}
              onChange={v => update("qualitative.additional_comments", v)}
              rows={3}
            />
          </Card>

          {/* Summary */}
          <Card title="Response Summary" color="#2ECC71">
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
                <div style={{ fontSize: 12, color: "#8899AA", marginBottom: 4 }}>Top Capability Gaps</div>
                {Object.entries(data.capabilities)
                  .sort((a, b) => a[1] - b[1])
                  .slice(0, 4)
                  .map(([key, score]) => (
                    <div key={key} style={{ display: "flex", justifyContent: "space-between", padding: "3px 0", fontSize: 13, color: "#B0BEC5" }}>
                      <span>{CAPABILITIES.find(c => c.key === key)?.label}</span>
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
                  flex: 1, background: isComplete ? "#2ECC71" : "#333",
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
                Please enter your name and role in Section 1 before downloading.
              </div>
            )}
            {submitting && (
              <div style={{ fontSize: 13, color: "#3B82F6", marginTop: 8, textAlign: "center" }}>
                Saving to database...
              </div>
            )}
            {saved && (
              <div style={{ fontSize: 13, color: "#2ECC71", marginTop: 8, textAlign: "center" }}>
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

      {/* Navigation buttons */}
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
              background: "#2ECC71", color: "#0A0F0A",
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
root.render(<SupplyChainInterview />);
