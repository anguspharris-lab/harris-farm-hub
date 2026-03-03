/**
 * Harris Farm Markets — Supply Chain Analysis Dashboard
 * Version 5.0 — March 2026
 *
 * Self-contained React artifact for Claude.ai AND Hub embedding.
 * Accepts JSON interview responses, builds cumulative analysis:
 * - ADKAR Heatmap (5 dimensions x respondents)
 * - Capability Gap Bar Chart (8 scores averaged)
 * - AI Insights panel (injected from Claude API via parent)
 * - Individual profile drill-down
 * - Export combined dataset
 */

const { useState, useEffect, useCallback } = React;

const STORAGE_KEY = "hfm_sc_analysis_v5";

const ADKAR_DIMS = [
  { key: "awareness", label: "Awareness", scoreKey: "urgency", desc: "Understanding why change is needed" },
  { key: "desire", label: "Desire", scoreKey: "desire", desc: "Willingness to participate" },
  { key: "knowledge", label: "Knowledge", scoreKey: "clarity", desc: "Understanding what good looks like" },
  { key: "ability", label: "Ability", scoreKey: "readiness", desc: "Capability to execute now" },
  { key: "reinforcement", label: "Reinforcement", scoreKey: "sustain", desc: "Ability to sustain change" },
];

const CAPABILITIES = [
  { key: "visibility", label: "Visibility" },
  { key: "disruption_response", label: "Disruption" },
  { key: "data_quality", label: "Data Quality" },
  { key: "technology", label: "Technology" },
  { key: "suppliers", label: "Suppliers" },
  { key: "transport", label: "Transport" },
  { key: "demand_planning", label: "Demand Plan" },
  { key: "sustainability", label: "Sustainability" },
];

function scoreColor(score) {
  if (score >= 8) return "#2ECC71";
  if (score >= 6) return "#F1C40F";
  if (score >= 4) return "#F97316";
  return "#EF4444";
}

function scoreLabel(score) {
  if (score >= 8) return "Strong";
  if (score >= 6) return "Adequate";
  if (score >= 4) return "Gap";
  return "Critical";
}

function HeatmapCell({ score }) {
  return (
    <td style={{
      background: scoreColor(score) + "22",
      color: scoreColor(score),
      fontWeight: 700, fontSize: 16, textAlign: "center",
      padding: "8px 12px", border: "1px solid rgba(255,255,255,0.06)",
    }}>
      {score}
    </td>
  );
}

function BarChart({ data, maxVal = 10 }) {
  return (
    <div>
      {data.map(item => (
        <div key={item.key} style={{ display: "flex", alignItems: "center", marginBottom: 8 }}>
          <div style={{ width: 100, fontSize: 12, color: "#B0BEC5", textAlign: "right", paddingRight: 10, flexShrink: 0 }}>
            {item.label}
          </div>
          <div style={{ flex: 1, background: "rgba(255,255,255,0.06)", borderRadius: 4, height: 24, position: "relative", overflow: "hidden" }}>
            <div style={{
              width: `${(item.avg / maxVal) * 100}%`,
              background: scoreColor(item.avg),
              height: "100%", borderRadius: 4,
              transition: "width 0.5s ease",
            }} />
            <span style={{
              position: "absolute", right: 8, top: 3,
              fontSize: 12, fontWeight: 700, color: "#F1F8E9",
            }}>
              {item.avg.toFixed(1)}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}

function SupplyChainAnalysis() {
  const [responses, setResponses] = useState([]);
  const [pasteText, setPasteText] = useState("");
  const [selectedProfile, setSelectedProfile] = useState(null);
  const [aiInsights, setAiInsights] = useState(null);
  const [activeTab, setActiveTab] = useState("overview");
  const [error, setError] = useState("");

  // Load from localStorage
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        if (parsed.responses) setResponses(parsed.responses);
        if (parsed.aiInsights) setAiInsights(parsed.aiInsights);
      }
    } catch (e) { /* ignore */ }
  }, []);

  // Auto-save
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ responses, aiInsights }));
    } catch (e) { /* ignore */ }
  }, [responses, aiInsights]);

  // Listen for AI insights from parent (Streamlit)
  useEffect(() => {
    const handler = (event) => {
      if (event.data && event.data.type === "ai_insights") {
        setAiInsights(event.data.payload);
      }
    };
    window.addEventListener("message", handler);
    return () => window.removeEventListener("message", handler);
  }, []);

  const addResponse = useCallback(() => {
    setError("");
    try {
      const data = JSON.parse(pasteText);
      if (!data.respondent || !data.scores) {
        setError("Invalid format: missing respondent or scores fields");
        return;
      }
      // Check for duplicate
      const name = data.respondent.name || "Unknown";
      if (responses.some(r => r.respondent?.name === name)) {
        setError(`Response from "${name}" already added`);
        return;
      }
      setResponses(prev => [...prev, data]);
      setPasteText("");
    } catch (e) {
      setError("Invalid JSON. Paste the full interview response file.");
    }
  }, [pasteText, responses]);

  const removeResponse = (index) => {
    setResponses(prev => prev.filter((_, i) => i !== index));
    if (selectedProfile === index) setSelectedProfile(null);
  };

  const handleExport = () => {
    const output = {
      exported: new Date().toISOString(),
      response_count: responses.length,
      responses,
      ai_insights: aiInsights,
    };
    const blob = new Blob([JSON.stringify(output, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `sc-analysis-combined-${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleReset = () => {
    if (confirm("Clear all responses and analysis?")) {
      setResponses([]);
      setAiInsights(null);
      setSelectedProfile(null);
      localStorage.removeItem(STORAGE_KEY);
    }
  };

  // Computed stats
  const adkarAvgs = ADKAR_DIMS.map(dim => {
    const scores = responses.map(r => r.scores?.[dim.scoreKey] || 0).filter(s => s > 0);
    return { ...dim, avg: scores.length ? scores.reduce((a, b) => a + b, 0) / scores.length : 0 };
  });

  const capAvgs = CAPABILITIES.map(cap => {
    const scores = responses.map(r => r.capabilities?.[cap.key] || 0).filter(s => s > 0);
    return { ...cap, avg: scores.length ? scores.reduce((a, b) => a + b, 0) / scores.length : 0 };
  });

  const overallAdkar = adkarAvgs.reduce((sum, d) => sum + d.avg, 0) / (adkarAvgs.length || 1);
  const overallCap = capAvgs.reduce((sum, c) => sum + c.avg, 0) / (capAvgs.length || 1);

  const tabs = [
    { key: "overview", label: "Overview" },
    { key: "adkar", label: "ADKAR" },
    { key: "capabilities", label: "Capabilities" },
    { key: "insights", label: "AI Insights" },
    { key: "profiles", label: "Profiles" },
  ];

  return (
    <div style={{
      maxWidth: 900, margin: "0 auto", fontFamily: "'Trebuchet MS', 'Segoe UI', sans-serif",
      color: "#F1F8E9", padding: "0 12px",
    }}>
      {/* Header */}
      <div style={{ textAlign: "center", marginBottom: 20 }}>
        <h1 style={{ fontFamily: "Georgia, serif", color: "#2ECC71", fontSize: 26, fontWeight: 700, marginBottom: 4 }}>
          Supply Chain Analysis
        </h1>
        <p style={{ color: "#8899AA", fontSize: 14 }}>
          {responses.length} response{responses.length !== 1 ? "s" : ""} loaded
          {responses.length > 0 && ` | ADKAR avg: ${overallAdkar.toFixed(1)} | Capability avg: ${overallCap.toFixed(1)}`}
        </p>
      </div>

      {/* Data Input */}
      <div style={{
        background: "#0D150D", border: "1px solid rgba(255,255,255,0.08)",
        borderRadius: 12, padding: "16px 20px", marginBottom: 20,
      }}>
        <div style={{ fontWeight: 600, fontSize: 14, color: "#2ECC71", marginBottom: 8 }}>Add Response</div>
        <textarea
          value={pasteText} onChange={e => setPasteText(e.target.value)}
          placeholder="Paste interview JSON here..."
          rows={4}
          style={{
            width: "100%", background: "#111A11", border: "1px solid rgba(255,255,255,0.12)",
            borderRadius: 8, padding: "10px 12px", color: "#F1F8E9", fontSize: 13,
            fontFamily: "monospace", resize: "vertical", marginBottom: 8,
          }}
        />
        {error && <div style={{ color: "#EF4444", fontSize: 12, marginBottom: 8 }}>{error}</div>}
        <div style={{ display: "flex", gap: 8 }}>
          <button onClick={addResponse} disabled={!pasteText.trim()} style={{
            background: pasteText.trim() ? "#2ECC71" : "#333", color: pasteText.trim() ? "#0A0F0A" : "#666",
            border: "none", borderRadius: 6, padding: "8px 18px", fontSize: 13, fontWeight: 600, cursor: pasteText.trim() ? "pointer" : "default",
          }}>Add Response</button>
          {responses.length > 0 && (
            <>
              <button onClick={handleExport} style={{
                background: "rgba(255,255,255,0.05)", color: "#B0BEC5",
                border: "1px solid rgba(255,255,255,0.12)", borderRadius: 6, padding: "8px 14px", fontSize: 13, cursor: "pointer",
              }}>Export All</button>
              <button onClick={handleReset} style={{
                background: "transparent", color: "#EF4444",
                border: "1px solid rgba(239,68,68,0.3)", borderRadius: 6, padding: "8px 14px", fontSize: 13, cursor: "pointer",
              }}>Reset</button>
            </>
          )}
        </div>
      </div>

      {/* Respondent chips */}
      {responses.length > 0 && (
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 20 }}>
          {responses.map((r, i) => (
            <div key={i} style={{
              background: "rgba(46,204,113,0.1)", border: "1px solid rgba(46,204,113,0.25)",
              borderRadius: 20, padding: "6px 14px", fontSize: 13, display: "flex", alignItems: "center", gap: 8,
            }}>
              <span style={{ color: "#2ECC71", fontWeight: 600 }}>{r.respondent?.name || `Response ${i + 1}`}</span>
              <span style={{ color: "#8899AA" }}>{r.respondent?.role || ""}</span>
              <button onClick={() => removeResponse(i)} style={{
                background: "none", border: "none", color: "#EF4444", cursor: "pointer", fontSize: 14, padding: "0 2px",
              }}>x</button>
            </div>
          ))}
        </div>
      )}

      {/* Tabs */}
      {responses.length > 0 && (
        <>
          <div style={{ display: "flex", gap: 4, marginBottom: 20, borderBottom: "1px solid rgba(255,255,255,0.08)", paddingBottom: 4 }}>
            {tabs.map(tab => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                style={{
                  background: activeTab === tab.key ? "rgba(46,204,113,0.15)" : "transparent",
                  color: activeTab === tab.key ? "#2ECC71" : "#8899AA",
                  border: "none", borderRadius: "8px 8px 0 0", padding: "10px 18px",
                  fontSize: 14, fontWeight: activeTab === tab.key ? 700 : 400, cursor: "pointer",
                  borderBottom: activeTab === tab.key ? "2px solid #2ECC71" : "2px solid transparent",
                }}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Overview Tab */}
          {activeTab === "overview" && (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
              <div style={{ background: "#0D150D", borderRadius: 12, padding: 20, border: "1px solid rgba(255,255,255,0.08)" }}>
                <h3 style={{ fontFamily: "Georgia, serif", color: "#8B5CF6", fontSize: 16, marginBottom: 12 }}>ADKAR Summary</h3>
                {adkarAvgs.map(d => (
                  <div key={d.key} style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
                    <span style={{ color: "#B0BEC5", fontSize: 13 }}>{d.label}</span>
                    <span style={{ fontWeight: 700, color: scoreColor(d.avg) }}>{d.avg.toFixed(1)} <span style={{ fontSize: 11, fontWeight: 400 }}>{scoreLabel(d.avg)}</span></span>
                  </div>
                ))}
                <div style={{ marginTop: 10, padding: "8px 0", borderTop: "1px solid rgba(255,255,255,0.1)" }}>
                  <span style={{ color: "#8899AA", fontSize: 13 }}>Overall</span>
                  <span style={{ float: "right", fontWeight: 700, fontSize: 18, color: scoreColor(overallAdkar) }}>{overallAdkar.toFixed(1)}</span>
                </div>
              </div>
              <div style={{ background: "#0D150D", borderRadius: 12, padding: 20, border: "1px solid rgba(255,255,255,0.08)" }}>
                <h3 style={{ fontFamily: "Georgia, serif", color: "#F1C40F", fontSize: 16, marginBottom: 12 }}>Capability Gaps</h3>
                <BarChart data={capAvgs} />
                <div style={{ marginTop: 10, padding: "8px 0", borderTop: "1px solid rgba(255,255,255,0.1)" }}>
                  <span style={{ color: "#8899AA", fontSize: 13 }}>Overall</span>
                  <span style={{ float: "right", fontWeight: 700, fontSize: 18, color: scoreColor(overallCap) }}>{overallCap.toFixed(1)}</span>
                </div>
              </div>
            </div>
          )}

          {/* ADKAR Heatmap Tab */}
          {activeTab === "adkar" && (
            <div style={{ background: "#0D150D", borderRadius: 12, padding: 20, border: "1px solid rgba(255,255,255,0.08)", overflowX: "auto" }}>
              <h3 style={{ fontFamily: "Georgia, serif", color: "#8B5CF6", fontSize: 16, marginBottom: 16 }}>ADKAR Heatmap</h3>
              <table style={{ width: "100%", borderCollapse: "collapse" }}>
                <thead>
                  <tr>
                    <th style={{ textAlign: "left", padding: "8px 12px", color: "#8899AA", fontSize: 12, borderBottom: "1px solid rgba(255,255,255,0.1)" }}>Respondent</th>
                    {ADKAR_DIMS.map(d => (
                      <th key={d.key} style={{ textAlign: "center", padding: "8px 12px", color: "#8899AA", fontSize: 12, borderBottom: "1px solid rgba(255,255,255,0.1)" }}>
                        {d.label}
                      </th>
                    ))}
                    <th style={{ textAlign: "center", padding: "8px 12px", color: "#8899AA", fontSize: 12, borderBottom: "1px solid rgba(255,255,255,0.1)" }}>Avg</th>
                  </tr>
                </thead>
                <tbody>
                  {responses.map((r, i) => {
                    const scores = ADKAR_DIMS.map(d => r.scores?.[d.scoreKey] || 0);
                    const avg = scores.reduce((a, b) => a + b, 0) / scores.length;
                    return (
                      <tr key={i}>
                        <td style={{ padding: "8px 12px", color: "#F1F8E9", fontWeight: 600, fontSize: 13, border: "1px solid rgba(255,255,255,0.06)" }}>
                          {r.respondent?.name || `#${i + 1}`}
                          <div style={{ fontSize: 11, color: "#8899AA", fontWeight: 400 }}>{r.respondent?.role}</div>
                        </td>
                        {scores.map((s, j) => <HeatmapCell key={j} score={s} />)}
                        <HeatmapCell score={Math.round(avg * 10) / 10} />
                      </tr>
                    );
                  })}
                  {/* Averages row */}
                  <tr style={{ borderTop: "2px solid rgba(255,255,255,0.15)" }}>
                    <td style={{ padding: "8px 12px", fontWeight: 700, color: "#2ECC71", fontSize: 13, border: "1px solid rgba(255,255,255,0.06)" }}>Average</td>
                    {adkarAvgs.map(d => <HeatmapCell key={d.key} score={Math.round(d.avg * 10) / 10} />)}
                    <HeatmapCell score={Math.round(overallAdkar * 10) / 10} />
                  </tr>
                </tbody>
              </table>
              <div style={{ marginTop: 16, display: "flex", gap: 16, fontSize: 12 }}>
                <span><span style={{ background: "#2ECC7122", color: "#2ECC71", padding: "2px 8px", borderRadius: 4 }}>8-10 Strong</span></span>
                <span><span style={{ background: "#F1C40F22", color: "#F1C40F", padding: "2px 8px", borderRadius: 4 }}>6-7 Adequate</span></span>
                <span><span style={{ background: "#F9731622", color: "#F97316", padding: "2px 8px", borderRadius: 4 }}>4-5 Gap</span></span>
                <span><span style={{ background: "#EF444422", color: "#EF4444", padding: "2px 8px", borderRadius: 4 }}>1-3 Critical</span></span>
              </div>
            </div>
          )}

          {/* Capabilities Tab */}
          {activeTab === "capabilities" && (
            <div style={{ background: "#0D150D", borderRadius: 12, padding: 20, border: "1px solid rgba(255,255,255,0.08)" }}>
              <h3 style={{ fontFamily: "Georgia, serif", color: "#F1C40F", fontSize: 16, marginBottom: 16 }}>Capability Assessment</h3>
              <BarChart data={capAvgs} />
              <div style={{ marginTop: 24 }}>
                <h4 style={{ color: "#F97316", fontSize: 14, marginBottom: 10 }}>Priority Gaps (score &lt; 6)</h4>
                {capAvgs.filter(c => c.avg > 0 && c.avg < 6).sort((a, b) => a.avg - b.avg).map(c => (
                  <div key={c.key} style={{
                    background: "rgba(249,115,22,0.08)", border: "1px solid rgba(249,115,22,0.2)",
                    borderRadius: 8, padding: "10px 14px", marginBottom: 8,
                  }}>
                    <span style={{ fontWeight: 600, color: "#F97316" }}>{c.label}</span>
                    <span style={{ float: "right", fontWeight: 700, color: scoreColor(c.avg) }}>{c.avg.toFixed(1)}</span>
                  </div>
                ))}
                {capAvgs.filter(c => c.avg > 0 && c.avg < 6).length === 0 && (
                  <div style={{ color: "#8899AA", fontSize: 13 }}>No critical gaps identified.</div>
                )}
              </div>
            </div>
          )}

          {/* AI Insights Tab */}
          {activeTab === "insights" && (
            <div style={{ background: "#0D150D", borderRadius: 12, padding: 20, border: "1px solid rgba(255,255,255,0.08)" }}>
              <h3 style={{ fontFamily: "Georgia, serif", color: "#2ECC71", fontSize: 16, marginBottom: 16 }}>AI-Powered Analysis</h3>
              {aiInsights ? (
                <div>
                  {aiInsights.one_page_summary && (
                    <div style={{ background: "rgba(46,204,113,0.08)", borderRadius: 8, padding: 16, marginBottom: 16, fontSize: 14, color: "#B0BEC5", lineHeight: 1.6 }}>
                      {aiInsights.one_page_summary}
                    </div>
                  )}
                  {aiInsights.adkar_summary && (
                    <div style={{ marginBottom: 20 }}>
                      <h4 style={{ color: "#8B5CF6", fontSize: 14, marginBottom: 10 }}>ADKAR Insights</h4>
                      {Object.entries(aiInsights.adkar_summary).map(([key, val]) => (
                        <div key={key} style={{ marginBottom: 10, padding: "10px 14px", background: "rgba(255,255,255,0.03)", borderRadius: 8, borderLeft: `3px solid ${scoreColor(val?.score || 5)}` }}>
                          <div style={{ fontWeight: 600, color: "#F1F8E9", fontSize: 14 }}>{key}</div>
                          <div style={{ fontSize: 13, color: "#B0BEC5", marginTop: 4 }}>{typeof val === "string" ? val : val?.interpretation || JSON.stringify(val)}</div>
                        </div>
                      ))}
                    </div>
                  )}
                  {aiInsights.themes && (
                    <div style={{ marginBottom: 20 }}>
                      <h4 style={{ color: "#06B6D4", fontSize: 14, marginBottom: 10 }}>Key Themes</h4>
                      {(Array.isArray(aiInsights.themes) ? aiInsights.themes : Object.entries(aiInsights.themes)).map((theme, i) => (
                        <div key={i} style={{ marginBottom: 8, padding: "10px 14px", background: "rgba(255,255,255,0.03)", borderRadius: 8 }}>
                          <div style={{ fontWeight: 600, color: "#06B6D4", fontSize: 13 }}>{typeof theme === "string" ? theme : theme[0] || theme.theme || ""}</div>
                          {typeof theme !== "string" && <div style={{ fontSize: 12, color: "#8899AA", marginTop: 4 }}>{theme[1] || theme.detail || ""}</div>}
                        </div>
                      ))}
                    </div>
                  )}
                  {aiInsights.recommendations && (
                    <div>
                      <h4 style={{ color: "#2ECC71", fontSize: 14, marginBottom: 10 }}>Recommendations</h4>
                      {(Array.isArray(aiInsights.recommendations) ? aiInsights.recommendations : []).map((rec, i) => (
                        <div key={i} style={{ display: "flex", gap: 10, marginBottom: 8, alignItems: "flex-start" }}>
                          <span style={{ background: "#2ECC71", color: "#0A0F0A", borderRadius: "50%", width: 22, height: 22, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 12, fontWeight: 700, flexShrink: 0 }}>{i + 1}</span>
                          <span style={{ fontSize: 13, color: "#B0BEC5" }}>{typeof rec === "string" ? rec : rec.action || JSON.stringify(rec)}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ) : (
                <div style={{ textAlign: "center", padding: 40 }}>
                  <div style={{ fontSize: 40, marginBottom: 12 }}>🤖</div>
                  <div style={{ color: "#8899AA", fontSize: 14 }}>
                    Click <strong>"Analyse with Claude"</strong> above to generate AI-powered insights from all responses.
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Profiles Tab */}
          {activeTab === "profiles" && (
            <div style={{ display: "grid", gridTemplateColumns: "200px 1fr", gap: 16 }}>
              <div style={{ background: "#0D150D", borderRadius: 12, padding: 16, border: "1px solid rgba(255,255,255,0.08)" }}>
                <div style={{ fontSize: 12, color: "#8899AA", marginBottom: 8 }}>Select respondent</div>
                {responses.map((r, i) => (
                  <button
                    key={i}
                    onClick={() => setSelectedProfile(i)}
                    style={{
                      display: "block", width: "100%", textAlign: "left",
                      background: selectedProfile === i ? "rgba(46,204,113,0.15)" : "transparent",
                      color: selectedProfile === i ? "#2ECC71" : "#B0BEC5",
                      border: "none", borderRadius: 6, padding: "8px 10px",
                      fontSize: 13, cursor: "pointer", marginBottom: 4,
                    }}
                  >
                    <div style={{ fontWeight: 600 }}>{r.respondent?.name || `#${i + 1}`}</div>
                    <div style={{ fontSize: 11, color: "#8899AA" }}>{r.respondent?.role}</div>
                  </button>
                ))}
              </div>
              <div style={{ background: "#0D150D", borderRadius: 12, padding: 20, border: "1px solid rgba(255,255,255,0.08)" }}>
                {selectedProfile !== null && responses[selectedProfile] ? (() => {
                  const r = responses[selectedProfile];
                  return (
                    <div>
                      <h3 style={{ fontFamily: "Georgia, serif", color: "#2ECC71", fontSize: 18, marginBottom: 4 }}>
                        {r.respondent?.name}
                      </h3>
                      <div style={{ color: "#8899AA", fontSize: 13, marginBottom: 16 }}>
                        {r.respondent?.role} | {r.respondent?.department}
                      </div>
                      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 16 }}>
                        {ADKAR_DIMS.map(d => (
                          <div key={d.key} style={{ display: "flex", justifyContent: "space-between", padding: "6px 8px", background: "rgba(255,255,255,0.03)", borderRadius: 6 }}>
                            <span style={{ fontSize: 13, color: "#B0BEC5" }}>{d.label}</span>
                            <span style={{ fontWeight: 700, color: scoreColor(r.scores?.[d.scoreKey] || 0) }}>{r.scores?.[d.scoreKey] || "-"}</span>
                          </div>
                        ))}
                      </div>
                      {r.qualitative && Object.entries(r.qualitative).filter(([_, v]) => v).map(([key, val]) => (
                        <div key={key} style={{ marginBottom: 12 }}>
                          <div style={{ fontSize: 12, color: "#8899AA", textTransform: "capitalize", marginBottom: 4 }}>{key.replace(/_/g, " ")}</div>
                          <div style={{ fontSize: 13, color: "#B0BEC5", lineHeight: 1.5, padding: "8px 12px", background: "rgba(255,255,255,0.03)", borderRadius: 8 }}>{val}</div>
                        </div>
                      ))}
                      {r.whats_working && Object.entries(r.whats_working).filter(([_, v]) => v).map(([key, val]) => (
                        <div key={key} style={{ marginBottom: 12 }}>
                          <div style={{ fontSize: 12, color: "#8899AA", textTransform: "capitalize", marginBottom: 4 }}>{key.replace(/_/g, " ")}</div>
                          <div style={{ fontSize: 13, color: "#B0BEC5", lineHeight: 1.5, padding: "8px 12px", background: "rgba(255,255,255,0.03)", borderRadius: 8 }}>{val}</div>
                        </div>
                      ))}
                    </div>
                  );
                })() : (
                  <div style={{ textAlign: "center", padding: 40, color: "#8899AA" }}>
                    Select a respondent to view their full profile.
                  </div>
                )}
              </div>
            </div>
          )}
        </>
      )}

      {/* Empty state */}
      {responses.length === 0 && (
        <div style={{ textAlign: "center", padding: "60px 20px" }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>📋</div>
          <div style={{ color: "#8899AA", fontSize: 15 }}>
            Paste interview JSON responses above to begin analysis.
          </div>
        </div>
      )}
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<SupplyChainAnalysis />);
