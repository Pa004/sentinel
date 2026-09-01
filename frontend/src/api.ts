/* API client for Sentinel SaaS backend. */

import { getToken } from "./auth";

const API_URL = import.meta.env.VITE_API_URL || "";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  const resp = await fetch(`${API_URL}${path}`, { ...options, headers });
  if (!resp.ok) {
    const error = await resp.json().catch(() => ({ detail: resp.statusText }));
    throw new Error(error.detail || `HTTP ${resp.status}`);
  }
  return resp.json();
}

export interface Repo {
  name: string;
  full_name: string;
  owner: string;
  description: string;
  language: string | null;
  default_branch: string;
}

export interface Analysis {
  id: number;
  repo_owner: string;
  repo_name: string;
  branch: string;
  status: string;
  total_violations: number;
  total_errors: number;
  total_warnings: number;
  total_info: number;
  drift_score: number;
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
  violations?: Violation[];
  metrics?: Metrics | null;
}

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

export async function fetchRepos(): Promise<Repo[]> {
  return request<Repo[]>("/api/v1/repos/github");
}

export async function createAnalysis(owner: string, name: string, branch: string): Promise<Analysis> {
  return request<Analysis>("/api/v1/analyses", {
    method: "POST",
    body: JSON.stringify({ repo_owner: owner, repo_name: name, branch }),
  });
}

export async function fetchAnalyses(): Promise<Analysis[]> {
  return request<Analysis[]>("/api/v1/analyses");
}

export async function fetchAnalysis(id: number): Promise<Analysis> {
  return request<Analysis>(`/api/v1/analyses/${id}`);
}
