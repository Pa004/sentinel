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

interface Run {
  id: number;
  commit_sha: string;
  created_at: string;
  violation_count: number;
  drift: number;
}

const API = "";

export default function App() {
  const [runs, setRuns] = useState<Run[]>([]);
  const [selectedRun, setSelectedRun] = useState<number | null>(null);
  const [violations, setViolations] = useState<Violation[]>([]);
  const [severityFilter, setSeverityFilter] = useState("");
  const [kindFilter, setKindFilter] = useState("");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API}/api/runs`)
      .then((r) => r.json())
      .then((data: Run[]) => {
        setRuns(data);
        if (data.length > 0) setSelectedRun(data[0].id);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const loadRun = useCallback((id: number) => {
    setSelectedRun(id);
    fetch(`${API}/api/runs/${id}`)
      .then((r) => r.json())
      .then((data: { violations: Violation[] }) => setViolations(data.violations));
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

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto", padding: 24, fontFamily: "system-ui, sans-serif", background: "#0d1117", color: "#c9d1d9", minHeight: "100vh" }}>
      <h1 style={{ fontSize: "1.4rem", marginBottom: 8 }}>Sentinel Dashboard</h1>

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
        ].map((c) => (
          <div key={c.label} style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 8, padding: "12px 16px", textAlign: "center" }}>
            <div style={{ fontSize: "1.8rem", fontWeight: 700, color: c.color }}>{c.value}</div>
            <div style={{ fontSize: ".75rem", color: "#8b949e" }}>{c.label}</div>
          </div>
        ))}
      </div>

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
