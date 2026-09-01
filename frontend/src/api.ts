/* API client for Sentinel stateless backend. */

const API_URL = import.meta.env.VITE_API_URL || "";

const CACHE_TTL_MS = 5 * 60 * 1000;
const cache = new Map<string, { data: AnalysisResult; timestamp: number }>();

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

function cacheKey(repoUrl: string, branch: string): string {
  return `${repoUrl.trim().toLowerCase()}@${branch.trim()}`
}

function getCached(repoUrl: string, branch: string): AnalysisResult | null {
  const key = cacheKey(repoUrl, branch)
  const entry = cache.get(key)
  if (entry && Date.now() - entry.timestamp < CACHE_TTL_MS) {
    return entry.data
  }
  cache.delete(key)
  return null
}

function setCache(repoUrl: string, branch: string, data: AnalysisResult): void {
  const key = cacheKey(repoUrl, branch)
  cache.set(key, { data, timestamp: Date.now() })
}

export async function analyze(repoUrl: string, branch: string): Promise<AnalysisResult> {
  const cached = getCached(repoUrl, branch)
  if (cached) return cached

  const resp = await fetch(`${API_URL}/api/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ repo_url: repoUrl, branch }),
  });
  if (!resp.ok) {
    const error = await resp.json().catch(() => ({ detail: resp.statusText }));
    throw new Error(error.detail || `HTTP ${resp.status}`);
  }
  const data: AnalysisResult = await resp.json()
  setCache(repoUrl, branch, data)
  return data
}
