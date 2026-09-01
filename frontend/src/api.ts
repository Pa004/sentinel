/* API client for Sentinel stateless backend. */

const API_URL = import.meta.env.VITE_API_URL || "";

const TIMEOUT_MS = 120_000;

export interface Violation {
  rule: string;
  kind: string;
  severity: string;
  evidence: string;
  components: string[];
  impact: string;
  recommendation: string;
  commit_sha: string | null;
}

export interface Metrics {
  nodes: number | null;
  edges: number | null;
  cycles: number | null;
  avg_coupling: number | null;
}

export interface AnalysisResult {
  repo_owner: string;
  repo_name: string;
  branch: string;
  status: string;
  total_violations: number;
  total_errors: number;
  total_warnings: number;
  total_info: number;
  drift_score: number;
  violations: Violation[];
  metrics: Metrics;
}

export async function analyze(repoUrl: string, branch: string): Promise<AnalysisResult> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), TIMEOUT_MS);

  try {
    const resp = await fetch(`${API_URL}/api/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ repo_url: repoUrl, branch }),
      signal: controller.signal,
    });
    if (!resp.ok) {
      const error = await resp.json().catch(() => ({ detail: resp.statusText }));
      throw new Error(error.detail || `HTTP ${resp.status}`);
    }
    return resp.json();
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new Error(`Request timed out after ${TIMEOUT_MS / 1000}s — the repository may be too large or unreachable`);
    }
    throw err;
  } finally {
    clearTimeout(timeout);
  }
}
