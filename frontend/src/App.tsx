import { useState, useEffect, useCallback } from "react";
import { isAuthenticated, getUser, login, logout, handleCallback } from "./auth";
import { fetchRepos, createAnalysis, fetchAnalyses, fetchAnalysis } from "./api";
import type { Repo, Analysis, Violation } from "./api";

interface RunMetrics {
  total_violations: number;
  error_count: number;
  warning_count: number;
  info_count: number;
  cycle_count: number;
  layer_violation_count: number;
  god_module_count: number;
  high_coupling_count: number;
  low_cohesion_count: number;
  boundary_crossing_count: number;
  database_leakage_count: number;
  drift_score: number;
  node_count: number;
  edge_count: number;
  avg_coupling: number;
}

interface Run {
  id: number;
  commit_sha: string;
  created_at: string;
  violation_count: number;
  drift: number;
  metrics: RunMetrics;
}

interface TrendPoint {
  commit: string;
  counts: Record<string, number>;
  introduced: string[];
  drift: number;
}

interface Summary {
  runs: number;
  total_violations: number;
  by_kind: Record<string, number>;
  by_severity: Record<string, number>;
}

const API = "";

// Landing page for non-authenticated users
function Landing() {
  return (
    <div style={{ maxWidth: 800, margin: "0 auto", padding: 60, fontFamily: "system-ui, sans-serif", background: "#0d1117", color: "#c9d1d9", minHeight: "100vh", textAlign: "center" }}>
      <div style={{ marginBottom: 40 }}>
        <h1 style={{ fontSize: "2.5rem", fontWeight: 700, marginBottom: 8 }}>Sentinel</h1>
        <p style={{ fontSize: "1.1rem", color: "#8b949e", marginBottom: 8 }}>Architecture erosion detection for GitHub repositories</p>
        <p style={{ fontSize: ".9rem", color: "#8b949e" }}>Connect your repo, get instant analysis of architectural violations, dependency health, and remediation guidance.</p>
      </div>
      <button
        onClick={login}
        style={{
          background: "#238636",
          color: "#fff",
          border: "none",
          borderRadius: 8,
          padding: "14px 32px",
          fontSize: "1rem",
          fontWeight: 600,
          cursor: "pointer",
          display: "inline-flex",
          alignItems: "center",
          gap: 8,
        }}
      >
        <svg width="20" height="20" viewBox="0 0 16 16" fill="currentColor"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"></path></svg>
        Analyze with GitHub
      </button>
      <div style={{ marginTop: 60, display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 24, textAlign: "left" }}>
        {[
          { title: "6 Detection Rules", desc: "Circular deps, god modules, high coupling, low cohesion, DB leakage, React components" },
          { title: "Instant Results", desc: "Shallow clone, parse, analyze — results in under a minute" },
          { title: "Remediation Guide", desc: "Prioritized violations with impact and actionable recommendations" },
        ].map((f) => (
          <div key={f.title} style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 8, padding: 20 }}>
            <h3 style={{ fontSize: ".95rem", marginBottom: 8 }}>{f.title}</h3>
            <p style={{ fontSize: ".8rem", color: "#8b949e", margin: 0 }}>{f.desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

// Dashboard for authenticated users
function Dashboard() {
  const user = getUser();
  const [repos, setRepos] = useState<Repo[]>([]);
  const [analyses, setAnalyses] = useState<Analysis[]>([]);
  const [selectedAnalysis, setSelectedAnalysis] = useState<Analysis | null>(null);
  const [selectedRepo, setSelectedRepo] = useState<Repo | null>(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [activeTab, setActiveTab] = useState<"violations" | "remediation">("violations");
  const [severityFilter, setSeverityFilter] = useState("");
  const [kindFilter, setKindFilter] = useState("");
  const [search, setSearch] = useState("");

  useEffect(() => {
    Promise.all([
      fetchRepos().catch(() => []),
      fetchAnalyses().catch(() => []),
    ]).then(([r, a]) => {
      setRepos(r);
      setAnalyses(a);
      setLoading(false);
    });
  }, []);

  const startAnalysis = async () => {
    if (!selectedRepo) return;
    setAnalyzing(true);
    try {
      const analysis = await createAnalysis(selectedRepo.owner, selectedRepo.name, selectedRepo.default_branch);
      setAnalyses((prev) => [analysis, ...prev]);
      pollAnalysis(analysis.id);
    } catch {
      setAnalyzing(false);
    }
  };

  const pollAnalysis = async (id: number) => {
    const poll = async () => {
      try {
        const result = await fetchAnalysis(id);
        if (result.status === "pending" || result.status === "running") {
          setTimeout(poll, 3000);
        } else {
          setAnalyses((prev) => prev.map((a) => (a.id === id ? result : a)));
          setSelectedAnalysis(result);
          setAnalyzing(false);
        }
      } catch {
        setAnalyzing(false);
      }
    };
    poll();
  };

  const loadAnalysis = async (id: number) => {
    const result = await fetchAnalysis(id);
    setSelectedAnalysis(result);
  };

  const violations: Violation[] = (selectedAnalysis?.violations ?? []) as Violation[];
  const metrics = selectedAnalysis?.metrics ?? null;

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

  if (loading) return <div style={{ padding: 24, color: "#8b949e" }}>Loading...</div>;

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto", padding: 24, fontFamily: "system-ui, sans-serif", background: "#0d1117", color: "#c9d1d9", minHeight: "100vh" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
        <h1 style={{ fontSize: "1.4rem", margin: 0 }}>Sentinel</h1>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          {user?.username && <span style={{ fontSize: ".85rem", color: "#8b949e" }}>{user.username}</span>}
          <button onClick={logout} style={{ background: "transparent", color: "#8b949e", border: "1px solid #30363d", borderRadius: 6, padding: "6px 12px", cursor: "pointer", fontSize: ".8rem" }}>
            Logout
          </button>
        </div>
      </div>

      {/* Repo selector + analyze button */}
      <div style={{ display: "flex", gap: 12, marginBottom: 24, alignItems: "center" }}>
        <select
          value={selectedRepo ? selectedRepo.full_name : ""}
          onChange={(e) => {
            const repo = repos.find((r) => r.full_name === e.target.value);
            setSelectedRepo(repo ?? null);
          }}
          style={{ flex: 1, background: "#161b22", color: "#c9d1d9", border: "1px solid #30363d", borderRadius: 6, padding: "8px 12px", fontSize: ".9rem" }}
        >
          <option value="">Select a repository...</option>
          {repos.map((r) => (
            <option key={r.full_name} value={r.full_name}>
              {r.full_name} {r.language ? `(${r.language})` : ""}
            </option>
          ))}
        </select>
        <button
          onClick={startAnalysis}
          disabled={!selectedRepo || analyzing}
          style={{
            background: selectedRepo && !analyzing ? "#238636" : "#21262d",
            color: selectedRepo && !analyzing ? "#fff" : "#8b949e",
            border: "none",
            borderRadius: 6,
            padding: "8px 20px",
            cursor: selectedRepo && !analyzing ? "pointer" : "not-allowed",
            fontSize: ".9rem",
            fontWeight: 600,
          }}
        >
          {analyzing ? "Analyzing..." : "Analyze"}
        </button>
      </div>

      {/* Analysis list */}
      {analyses.length > 0 && (
        <div style={{ marginBottom: 24 }}>
          <h3 style={{ fontSize: ".9rem", color: "#8b949e", marginBottom: 8 }}>Recent Analyses</h3>
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {analyses.map((a) => (
              <div
                key={a.id}
                onClick={() => loadAnalysis(a.id)}
                style={{
                  background: selectedAnalysis?.id === a.id ? "#21262d" : "#161b22",
                  border: `1px solid ${selectedAnalysis?.id === a.id ? "#30363d" : "#21262d"}`,
                  borderRadius: 6,
                  padding: "10px 16px",
                  cursor: "pointer",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                }}
              >
                <div>
                  <span style={{ fontWeight: 600 }}>{a.repo_owner}/{a.repo_name}</span>
                  <span style={{ fontSize: ".8rem", color: "#8b949e", marginLeft: 8 }}>{a.branch}</span>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                  <span style={{
                    fontSize: ".75rem",
                    padding: "2px 8px",
                    borderRadius: 4,
                    background: a.status === "done" ? "#23863622" : a.status === "error" ? "#f8514922" : "#d2992222",
                    color: a.status === "done" ? "#3fb950" : a.status === "error" ? "#f85149" : "#d29922",
                  }}>
                    {a.status}
                  </span>
                  {a.status === "done" && (
                    <span style={{ fontSize: ".8rem", color: a.total_errors > 0 ? "#f85149" : "#3fb950" }}>
                      {a.total_violations} violations
                    </span>
                  )}
                  <span style={{ fontSize: ".75rem", color: "#8b949e" }}>
                    {new Date(a.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Selected analysis results */}
      {selectedAnalysis && selectedAnalysis.status === "done" && (
        <>
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

          {/* Summary cards */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: 12, marginBottom: 20 }}>
            {[
              { label: "Total", value: counts.total, color: "#c9d1d9" },
              { label: "Errors", value: counts.error, color: "#f85149" },
              { label: "Warnings", value: counts.warning, color: "#d29922" },
              { label: "Info", value: counts.info, color: "#58a6ff" },
              { label: "Drift", value: selectedAnalysis.drift_score.toFixed(2), color: "#f85149" },
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

          {/* Violations tab */}
          {activeTab === "violations" && (
            <>
              {/* Filters */}
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

              {/* Violations table */}
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

      {selectedAnalysis && selectedAnalysis.status === "running" && (
        <div style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 8, padding: 40, textAlign: "center", color: "#d29922" }}>
          <div style={{ fontSize: "1.2rem", marginBottom: 8 }}>Analyzing repository...</div>
          <div style={{ fontSize: ".85rem", color: "#8b949e" }}>Cloning, parsing, and running detection rules. This usually takes 30-60 seconds.</div>
        </div>
      )}

      {selectedAnalysis && selectedAnalysis.status === "error" && (
        <div style={{ background: "#161b22", border: "1px solid #f8514933", borderRadius: 8, padding: 20, color: "#f85149" }}>
          <div style={{ fontWeight: 600, marginBottom: 4 }}>Analysis failed</div>
          <div style={{ fontSize: ".85rem", color: "#8b949e" }}>{selectedAnalysis.error_message}</div>
        </div>
      )}
    </div>
  );
}

export default function App() {
  // Check for OAuth callback token
  useEffect(() => {
    handleCallback();
  }, []);

  // Check for SaaS mode (API URL configured)
  const isSaaS = !!import.meta.env.VITE_API_URL;

  if (isSaaS && !isAuthenticated()) {
    return <Landing />;
  }

  if (isSaaS) {
    return <Dashboard />;
  }

  // Local mode — existing dashboard
  return <LocalDashboard />;
}

// Local dashboard (existing behavior for sentinel serve)
function LocalDashboard() {
  const [runs, setRuns] = useState<Run[]>([]);
  const [selectedRun, setSelectedRun] = useState<number | null>(null);
  const [violations, setViolations] = useState<Violation[]>([]);
  const [metrics, setMetrics] = useState<RunMetrics | null>(null);
  const [trend, setTrend] = useState<TrendPoint[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [severityFilter, setSeverityFilter] = useState("");
  const [kindFilter, setKindFilter] = useState("");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"violations" | "trend" | "summary" | "remediation">("violations");

  useEffect(() => {
    fetch(`${API}/api/runs`)
      .then((r) => r.json())
      .then((data: Run[]) => {
        setRuns(data);
        if (data.length > 0) {
          setSelectedRun(data[0].id);
          if (data[0].metrics) setMetrics(data[0].metrics);
        } else {
          fetch(`${API}/api/report.json`)
            .then((r) => r.json())
            .then((report: { violations: Violation[] }) => {
              setViolations(report.violations);
              setLoading(false);
            })
            .catch(() => setLoading(false));
        }
      })
      .catch(() => setLoading(false));

    fetch(`${API}/api/trend`)
      .then((r) => r.json())
      .then((data: TrendPoint[]) => setTrend(data))
      .catch(() => {});

    fetch(`${API}/api/summary`)
      .then((r) => r.json())
      .then((data: Summary) => setSummary(data))
      .catch(() => {});
  }, []);

  const loadRun = useCallback((id: number) => {
    setSelectedRun(id);
    fetch(`${API}/api/runs/${id}`)
      .then((r) => r.json())
      .then((data: { violations: Violation[]; metrics?: RunMetrics }) => {
        setViolations(data.violations);
        if (data.metrics) setMetrics(data.metrics);
      });
  }, []);

  useEffect(() => {
    if (selectedRun !== null) loadRun(selectedRun);
  }, [selectedRun, loadRun]);

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

  if (loading) return <div style={{ padding: 24, color: "#8b949e" }}>Loading...</div>;

  const liveMode = runs.length === 0 && violations.length > 0;

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto", padding: 24, fontFamily: "system-ui, sans-serif", background: "#0d1117", color: "#c9d1d9", minHeight: "100vh" }}>
      <h1 style={{ fontSize: "1.4rem", marginBottom: 8 }}>Sentinel Dashboard{liveMode ? " — Live Analysis" : ""}</h1>

      <div style={{ marginBottom: 16 }}>
        <select
          value={selectedRun ?? ""}
          onChange={(e) => setSelectedRun(Number(e.target.value))}
          style={{ background: "#161b22", color: "#c9d1d9", border: "1px solid #30363d", borderRadius: 6, padding: "6px 12px", fontSize: ".9rem" }}
        >
          {runs.map((r) => (
            <option key={r.id} value={r.id}>
              Run #{r.id} — {r.commit_sha?.slice(0, 8) ?? "n/a"} — {new Date(r.created_at).toLocaleDateString()}
            </option>
          ))}
        </select>
      </div>

      <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
        {(["violations", "trend", "summary", "remediation"] as const).map((tab) => (
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

      {activeTab === "violations" && (
        <>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: 12, marginBottom: 20 }}>
            {[
              { label: "Total", value: counts.total, color: "#c9d1d9" },
              { label: "Errors", value: counts.error, color: "#f85149" },
              { label: "Warnings", value: counts.warning, color: "#d29922" },
              { label: "Info", value: counts.info, color: "#58a6ff" },
              { label: "Drift", value: metrics?.drift_score?.toFixed(2) ?? "-", color: "#f85149" },
            ].map((c) => (
              <div key={c.label} style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 8, padding: "12px 16px", textAlign: "center" }}>
                <div style={{ fontSize: "1.8rem", fontWeight: 700, color: c.color }}>{c.value}</div>
                <div style={{ fontSize: ".75rem", color: "#8b949e" }}>{c.label}</div>
              </div>
            ))}
          </div>

          {metrics && (
            <div style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 8, padding: "16px 20px", marginBottom: 20 }}>
              <h3 style={{ fontSize: ".9rem", marginBottom: 12, color: "#8b949e" }}>Architecture Metrics</h3>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 12 }}>
                {[
                  { label: "Nodes", value: metrics.node_count },
                  { label: "Edges", value: metrics.edge_count },
                  { label: "Avg Coupling", value: metrics.avg_coupling.toFixed(1) },
                  { label: "Cycles", value: metrics.cycle_count, color: metrics.cycle_count > 0 ? "#f85149" : "#3fb950" },
                  { label: "Layer Violations", value: metrics.layer_violation_count, color: metrics.layer_violation_count > 0 ? "#f85149" : "#3fb950" },
                  { label: "God Modules", value: metrics.god_module_count, color: metrics.god_module_count > 0 ? "#d29922" : "#3fb950" },
                  { label: "High Coupling", value: metrics.high_coupling_count, color: metrics.high_coupling_count > 0 ? "#d29922" : "#3fb950" },
                  { label: "Low Cohesion", value: metrics.low_cohesion_count, color: metrics.low_cohesion_count > 0 ? "#d29922" : "#3fb950" },
                  { label: "Boundary Cross", value: metrics.boundary_crossing_count, color: metrics.boundary_crossing_count > 0 ? "#d29922" : "#3fb950" },
                  { label: "DB Leakage", value: metrics.database_leakage_count, color: metrics.database_leakage_count > 0 ? "#f85149" : "#3fb950" },
                ].map((m) => (
                  <div key={m.label} style={{ textAlign: "center" }}>
                    <div style={{ fontSize: "1.3rem", fontWeight: 700, color: (m as { color?: string }).color ?? "#c9d1d9" }}>{m.value}</div>
                    <div style={{ fontSize: ".7rem", color: "#8b949e" }}>{m.label}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

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
                <th style={{ padding: "8px 12px", color: "#8b949e", fontSize: ".8rem", textTransform: "uppercase" }}>Commit</th>
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 ? (
                <tr><td colSpan={5} style={{ padding: 24, textAlign: "center", color: "#8b949e" }}>No violations found</td></tr>
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
                    <td style={{ padding: "8px 12px", fontSize: ".85rem", maxWidth: 350, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{v.evidence}</td>
                    <td style={{ padding: "8px 12px", fontSize: ".85rem" }}>{v.components.join(" → ")}</td>
                    <td style={{ padding: "8px 12px", fontFamily: "monospace", fontSize: ".8rem", color: "#8b949e" }}>{v.commit_sha?.slice(0, 8) ?? "n/a"}</td>
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

      {activeTab === "trend" && (
        <div>
          {trend.length === 0 ? (
            <div style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 8, padding: 40, textAlign: "center", color: "#8b949e" }}>
              No trend data available.
            </div>
          ) : (
            <>
              <div style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 8, padding: "16px 20px", marginBottom: 20 }}>
                <h3 style={{ fontSize: ".9rem", marginBottom: 12, color: "#8b949e" }}>Violation Trend Over Time</h3>
                <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                  {trend.map((point, i) => {
                    const total = Object.values(point.counts).reduce((a, b) => a + b, 0);
                    const maxTotal = Math.max(...trend.map((p) => Object.values(p.counts).reduce((a, b) => a + b, 0)), 1);
                    const height = Math.max(4, (total / maxTotal) * 120);
                    return (
                      <div key={i} style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 4 }}>
                        <div style={{ fontSize: ".65rem", color: "#8b949e" }}>{total}</div>
                        <div
                          style={{
                            width: 24,
                            height,
                            background: point.drift > 0.5 ? "#f85149" : point.drift > 0.3 ? "#d29922" : "#3fb950",
                            borderRadius: 3,
                          }}
                          title={`${point.commit.slice(0, 8)}: ${total} violations, drift ${point.drift.toFixed(2)}`}
                        />
                        <div style={{ fontSize: ".6rem", color: "#8b949e", fontFamily: "monospace" }}>{point.commit.slice(0, 6)}</div>
                      </div>
                    );
                  })}
                </div>
              </div>

              <table style={{ width: "100%", borderCollapse: "collapse" }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid #30363d", textAlign: "left" }}>
                    <th style={{ padding: "8px 12px", color: "#8b949e", fontSize: ".8rem", textTransform: "uppercase" }}>Commit</th>
                    <th style={{ padding: "8px 12px", color: "#8b949e", fontSize: ".8rem", textTransform: "uppercase" }}>Total</th>
                    <th style={{ padding: "8px 12px", color: "#8b949e", fontSize: ".8rem", textTransform: "uppercase" }}>Drift</th>
                    <th style={{ padding: "8px 12px", color: "#8b949e", fontSize: ".8rem", textTransform: "uppercase" }}>Breakdown</th>
                    <th style={{ padding: "8px 12px", color: "#8b949e", fontSize: ".8rem", textTransform: "uppercase" }}>Introduced</th>
                  </tr>
                </thead>
                <tbody>
                  {trend.map((point, i) => {
                    const total = Object.values(point.counts).reduce((a, b) => a + b, 0);
                    const driftColor = point.drift > 0.5 ? "#f85149" : point.drift > 0.3 ? "#d29922" : "#3fb950";
                    return (
                      <tr key={i} style={{ borderBottom: "1px solid #21262d" }}>
                        <td style={{ padding: "8px 12px", fontFamily: "monospace", fontSize: ".8rem" }}>{point.commit.slice(0, 8)}</td>
                        <td style={{ padding: "8px 12px", fontWeight: 600 }}>{total}</td>
                        <td style={{ padding: "8px 12px" }}>
                          <span style={{ color: driftColor }}>{point.drift.toFixed(2)}</span>
                        </td>
                        <td style={{ padding: "8px 12px", fontSize: ".8rem" }}>
                          {Object.entries(point.counts).map(([kind, count]) => (
                            <span key={kind} style={{ marginRight: 8 }}>
                              <span style={{ color: "#8b949e" }}>{kind}:</span> {count}
                            </span>
                          ))}
                        </td>
                        <td style={{ padding: "8px 12px", fontSize: ".75rem", color: "#d29922" }}>
                          {point.introduced.length > 0 ? point.introduced.join(", ") : "-"}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </>
          )}
        </div>
      )}

      {activeTab === "summary" && (
        <div>
          {summary === null ? (
            <div style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 8, padding: 40, textAlign: "center", color: "#8b949e" }}>
              Loading summary...
            </div>
          ) : summary.runs === 0 ? (
            <div style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 8, padding: 40, textAlign: "center", color: "#8b949e" }}>
              No runs saved yet.
            </div>
          ) : (
            <>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 12, marginBottom: 20 }}>
                {[
                  { label: "Total Runs", value: summary.runs, color: "#58a6ff" },
                  { label: "Total Violations", value: summary.total_violations, color: "#c9d1d9" },
                  { label: "Errors", value: summary.by_severity["error"] ?? 0, color: "#f85149" },
                  { label: "Warnings", value: summary.by_severity["warning"] ?? 0, color: "#d29922" },
                  { label: "Info", value: summary.by_severity["info"] ?? 0, color: "#58a6ff" },
                ].map((c) => (
                  <div key={c.label} style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 8, padding: "16px 20px", textAlign: "center" }}>
                    <div style={{ fontSize: "2rem", fontWeight: 700, color: c.color }}>{c.value}</div>
                    <div style={{ fontSize: ".8rem", color: "#8b949e" }}>{c.label}</div>
                  </div>
                ))}
              </div>

              <div style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 8, padding: "16px 20px", marginBottom: 20 }}>
                <h3 style={{ fontSize: ".9rem", marginBottom: 12, color: "#8b949e" }}>Violations by Kind (All Runs)</h3>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: 12 }}>
                  {Object.entries(summary.by_kind)
                    .sort(([, a], [, b]) => b - a)
                    .map(([kind, count]) => (
                      <div key={kind} style={{ textAlign: "center" }}>
                        <div style={{ fontSize: "1.5rem", fontWeight: 700, color: count > 0 ? "#d29922" : "#3fb950" }}>{count}</div>
                        <div style={{ fontSize: ".7rem", color: "#8b949e" }}>{kind.replace(/_/g, " ")}</div>
                      </div>
                    ))}
                </div>
              </div>
            </>
          )}
        </div>
      )}

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
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                          <span style={{ fontWeight: 600, fontSize: ".9rem" }}>{v.rule}</span>
                          <span style={{ fontFamily: "monospace", fontSize: ".75rem", color: "#8b949e" }}>
                            {v.commit_sha?.slice(0, 8) ?? "n/a"}
                          </span>
                        </div>
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
    </div>
  );
}
