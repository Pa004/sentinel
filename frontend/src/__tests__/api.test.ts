import { describe, it, expect, vi, beforeEach } from "vitest"
import { analyze } from "../api"

beforeEach(() => {
  vi.restoreAllMocks()
})

describe("analyze", () => {
  it("sends correct request and returns data", async () => {
    const mockData = {
      repo_owner: "owner",
      repo_name: "repo",
      branch: "main",
      status: "done",
      total_violations: 2,
      total_errors: 0,
      total_warnings: 2,
      total_info: 0,
      drift_score: 0.0,
      violations: [],
      metrics: { nodes: 5, edges: 10, cycles: 0, avg_coupling: 1.5 },
    }

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockData),
      })
    )

    const result = await analyze("owner/repo", "main")

    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/analyze"),
      expect.objectContaining({
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo_url: "owner/repo", branch: "main" }),
      })
    )
    expect(result).toEqual(mockData)
  })

  it("throws on HTTP error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        json: () => Promise.resolve({ detail: "Internal error" }),
      })
    )

    await expect(analyze("owner/repo", "main")).rejects.toThrow("Internal error")
  })

  it("throws on network error", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("Network fail")))

    await expect(analyze("owner/repo", "main")).rejects.toThrow("Network fail")
  })
})
