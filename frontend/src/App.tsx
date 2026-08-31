import { useState, useEffect, useCallback } from "react";

interface Violation {
  rule: string;
  kind: string;
  severity: string;
  evidence: string;
  components: string[];
  impact: string;
  recommendation: string;
  commit: string | null;
}

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

const API = "";

export default function App() {
  const [runs, setRuns] = useState<Run[]>([]);
  const [selectedRun, setSelectedRun] = useState<number | null>(null);
  const [violations, setViolations] = useState<Violation[]>([]);
  const [metrics, setMetrics] = useState<RunMetrics | null>(null);
  const [severityFilter, setSeverityFilter] = useState("");
  const [kindFilter, setKindFilter] = useState("");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

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

      {/* Run selector */}
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

      {/* Summary cards */}
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

      {/* Aggregated metrics */}
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
                <div style={{ fontSize: "1.3rem", fontWeight: 700, color: m.color ?? "#c9d1d9" }}>{m.value}</div>
                <div style={{ fontSize: ".7rem", color: "#8b949e" }}>{m.label}</div>
              </div>
            ))}
          </div>
        </div>
      )}

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
                <td style={{ padding: "8px 12px", fontFamily: "monospace", fontSize: ".8rem", color: "#8b949e" }}>{v.commit?.slice(0, 8) ?? "n/a"}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>

      <div style={{ marginTop: 16, fontSize: ".8rem", color: "#8b949e" }}>
        Showing {filtered.length} of {violations.length} violations
      </div>
    </div>
  );
}
