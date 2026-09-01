import { useState } from "react";
import { analyze } from "./api";
import type { Violation, Metrics, AnalysisResult } from "./api";

export default function App() {
  const [repoUrl, setRepoUrl] = useState("");
  const [branch, setBranch] = useState("main");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [activeTab, setActiveTab] = useState<"violations" | "remediation">("violations");
  const [severityFilter, setSeverityFilter] = useState("");
  const [kindFilter, setKindFilter] = useState("");
  const [search, setSearch] = useState("");

  const handleAnalyze = async () => {
    if (!repoUrl.trim()) return;
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const data = await analyze(repoUrl, branch);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  };

  const violations: Violation[] = result?.violations ?? [];
  const metrics: Metrics | null = result?.metrics ?? null;

  const kinds = [...new Set(violations.map((v) => v.kind))].sort();
  const severities = ["error", "warning", "info"];

  const filtered = violations.filter((v) => {
    if (severityFilter && v.severity !== severityFilter) return false;
    if (kindFilter && v.kind !== kindFilter) return false;
    if (search) {
      const q = search.toLowerCase();
      return (
        v.evidence.toLowerCase().includes(q) ||
        v.impact.toLowerCase().includes(q) ||
        v.rule.toLowerCase().includes(q)
      );
    }
    return true;
  });

  const counts = {
    error: violations.filter((v) => v.severity === "error").length,
    warning: violations.filter((v) => v.severity === "warning").length,
    info: violations.filter((v) => v.severity === "info").length,
    total: violations.length,
  };

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto", padding: 24, fontFamily: "system-ui, sans-serif", background: "#0d1117", color: "#c9d1d9", minHeight: "100vh" }}>
      <h1 style={{ fontSize: "1.4rem", marginBottom: 20 }}>Sentinel</h1>

      {/* Input form */}
      <div style={{ display: "flex", gap: 12, marginBottom: 24, alignItems: "center" }}>
        <input
          type="text"
          placeholder="GitHub repo URL or owner/name"
          value={repoUrl}
          onChange={(e) => setRepoUrl(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleAnalyze()}
          style={{ flex: 1, background: "#161b22", color: "#c9d1d9", border: "1px solid #30363d", borderRadius: 6, padding: "10px 14px", fontSize: ".9rem" }}
        />
        <input
          type="text"
          placeholder="Branch"
          value={branch}
          onChange={(e) => setBranch(e.target.value)}
          style={{ width: 120, background: "#161b22", color: "#c9d1d9", border: "1px solid #30363d", borderRadius: 6, padding: "10px 14px", fontSize: ".9rem" }}
        />
        <button
          onClick={handleAnalyze}
          disabled={!repoUrl.trim() || loading}
          style={{
            background: repoUrl.trim() && !loading ? "#238636" : "#21262d",
            color: repoUrl.trim() && !loading ? "#fff" : "#8b949e",
            border: "none",
            borderRadius: 6,
            padding: "10px 24px",
            cursor: repoUrl.trim() && !loading ? "pointer" : "not-allowed",
            fontSize: ".9rem",
            fontWeight: 600,
          }}
        >
          {loading ? "Analyzing..." : "Analyze"}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div style={{ background: "#161b22", border: "1px solid #f8514933", borderRadius: 8, padding: 16, color: "#f85149", marginBottom: 20 }}>
          {error}
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 8, padding: 40, textAlign: "center", color: "#d29922" }}>
          <div style={{ fontSize: "1.1rem", marginBottom: 8 }}>Analyzing repository...</div>
          <div style={{ fontSize: ".85rem", color: "#8b949e" }}>Cloning, parsing, and running detection rules.</div>
        </div>
      )}

      {/* Results */}
      {result && !loading && (
        <>
          {/* Summary cards */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: 12, marginBottom: 20 }}>
            {[
              { label: "Total", value: counts.total, color: "#c9d1d9" },
              { label: "Errors", value: counts.error, color: "#f85149" },
              { label: "Warnings", value: counts.warning, color: "#d29922" },
              { label: "Info", value: counts.info, color: "#58a6ff" },
              { label: "Drift", value: result.drift_score.toFixed(2), color: "#f85149" },
            ].map((c) => (
              <div key={c.label} style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 8, padding: "12px 16px", textAlign: "center" }}>
                <div style={{ fontSize: "1.8rem", fontWeight: 700, color: c.color }}>{c.value}</div>
                <div style={{ fontSize: ".75rem", color: "#8b949e" }}>{c.label}</div>
              </div>
            ))}
          </div>

          {/* Metrics */}
          {metrics && (
            <div style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 8, padding: "16px 20px", marginBottom: 20 }}>
              <h3 style={{ fontSize: ".9rem", marginBottom: 12, color: "#8b949e" }}>Architecture Metrics</h3>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: 12 }}>
                {[
                  { label: "Nodes", value: metrics.nodes ?? "-" },
                  { label: "Edges", value: metrics.edges ?? "-" },
                  { label: "Cycles", value: metrics.cycles ?? 0, color: (metrics.cycles ?? 0) > 0 ? "#f85149" : "#3fb950" },
                  { label: "Avg Coupling", value: metrics.avg_coupling?.toFixed(1) ?? "-" },
                ].map((m) => (
                  <div key={m.label} style={{ textAlign: "center" }}>
                    <div style={{ fontSize: "1.3rem", fontWeight: 700, color: (m as { color?: string }).color ?? "#c9d1d9" }}>{m.value}</div>
                    <div style={{ fontSize: ".7rem", color: "#8b949e" }}>{m.label}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Tab navigation */}
          <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
            {(["violations", "remediation"] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                style={{
                  background: activeTab === tab ? "#21262d" : "transparent",
                  color: activeTab === tab ? "#c9d1d9" : "#8b949e",
                  border: `1px solid ${activeTab === tab ? "#30363d" : "transparent"}`,
                  borderRadius: 6,
                  padding: "6px 16px",
                  cursor: "pointer",
                  fontSize: ".85rem",
                  textTransform: "capitalize",
                }}
              >
                {tab}
              </button>
            ))}
          </div>

          {/* Violations tab */}
          {activeTab === "violations" && (
            <>
              <div style={{ display: "flex", gap: 12, marginBottom: 12, flexWrap: "wrap" }}>
                <select value={severityFilter} onChange={(e) => setSeverityFilter(e.target.value)}
                  style={{ background: "#161b22", color: "#c9d1d9", border: "1px solid #30363d", borderRadius: 6, padding: "6px 10px" }}>
                  <option value="">Severity: all</option>
                  {severities.map((s) => <option key={s} value={s}>{s}</option>)}
                </select>
                <select value={kindFilter} onChange={(e) => setKindFilter(e.target.value)}
                  style={{ background: "#161b22", color: "#c9d1d9", border: "1px solid #30363d", borderRadius: 6, padding: "6px 10px" }}>
                  <option value="">Kind: all</option>
                  {kinds.map((k) => <option key={k} value={k}>{k}</option>)}
                </select>
                <input
                  type="text"
                  placeholder="Search..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  style={{ background: "#161b22", color: "#c9d1d9", border: "1px solid #30363d", borderRadius: 6, padding: "6px 10px", minWidth: 200 }}
                />
              </div>

              <table style={{ width: "100%", borderCollapse: "collapse" }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid #30363d", textAlign: "left" }}>
                    <th style={{ padding: "8px 12px", color: "#8b949e", fontSize: ".8rem", textTransform: "uppercase" }}>Severity</th>
                    <th style={{ padding: "8px 12px", color: "#8b949e", fontSize: ".8rem", textTransform: "uppercase" }}>Rule</th>
                    <th style={{ padding: "8px 12px", color: "#8b949e", fontSize: ".8rem", textTransform: "uppercase" }}>Evidence</th>
                    <th style={{ padding: "8px 12px", color: "#8b949e", fontSize: ".8rem", textTransform: "uppercase" }}>Components</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.length === 0 ? (
                    <tr><td colSpan={4} style={{ padding: 24, textAlign: "center", color: "#3fb950" }}>No violations found — architecture is clean.</td></tr>
                  ) : (
                    filtered.map((v, i) => (
                      <tr key={i} style={{ borderBottom: "1px solid #21262d" }}>
                        <td style={{ padding: "8px 12px" }}>
                          <span style={{
                            color: v.severity === "error" ? "#f85149" : v.severity === "warning" ? "#d29922" : "#58a6ff",
                            fontWeight: 600,
                          }}>{v.severity}</span>
                        </td>
                        <td style={{ padding: "8px 12px" }}>{v.rule}</td>
                        <td style={{ padding: "8px 12px", fontSize: ".85rem", maxWidth: 400, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{v.evidence}</td>
                        <td style={{ padding: "8px 12px", fontSize: ".85rem" }}>{v.components.join(" → ")}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
              <div style={{ marginTop: 16, fontSize: ".8rem", color: "#8b949e" }}>
                Showing {filtered.length} of {violations.length} violations
              </div>
            </>
          )}

          {/* Remediation tab */}
          {activeTab === "remediation" && (
            <div>
              {violations.length === 0 ? (
                <div style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 8, padding: 40, textAlign: "center", color: "#3fb950" }}>
                  No violations to remediate — architecture is clean.
                </div>
              ) : (
                <>
                  {(["error", "warning", "info"] as const).map((sev) => {
                    const sevViolations = violations
                      .filter((v) => v.severity === sev)
                      .sort((a, b) => a.rule.localeCompare(b.rule));
                    if (sevViolations.length === 0) return null;
                    const color = sev === "error" ? "#f85149" : sev === "warning" ? "#d29922" : "#58a6ff";
                    return (
                      <div key={sev} style={{ marginBottom: 24 }}>
                        <h3 style={{ fontSize: ".9rem", marginBottom: 12, color, display: "flex", alignItems: "center", gap: 8 }}>
                          <span style={{ display: "inline-block", width: 8, height: 8, borderRadius: "50%", background: color }} />
                          {sev.charAt(0).toUpperCase() + sev.slice(1)}s — {sevViolations.length}
                        </h3>
                        {sevViolations.map((v, i) => (
                          <div
                            key={i}
                            style={{
                              background: "#161b22",
                              border: "1px solid #30363d",
                              borderLeft: `3px solid ${color}`,
                              borderRadius: 8,
                              padding: "16px 20px",
                              marginBottom: 10,
                            }}
                          >
                            <div style={{ fontWeight: 600, fontSize: ".9rem", marginBottom: 8 }}>{v.rule}</div>
                            <div style={{ fontSize: ".8rem", color: "#8b949e", marginBottom: 6 }}>{v.evidence}</div>
                            <div style={{ fontSize: ".85rem", marginBottom: 6 }}>
                              <span style={{ color: "#8b949e" }}>Impact: </span>{v.impact}
                            </div>
                            <div style={{ fontSize: ".85rem", background: "#21262d", borderRadius: 6, padding: "8px 12px", borderLeft: "2px solid #3fb950" }}>
                              <span style={{ color: "#3fb950", fontWeight: 600 }}>Recommendation: </span>{v.recommendation}
                            </div>
                          </div>
                        ))}
                      </div>
                    );
                  })}
                </>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}
