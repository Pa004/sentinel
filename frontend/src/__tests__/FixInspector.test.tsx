import { describe, it, expect } from "vitest"
import { render, screen } from "@testing-library/react"
import FixInspector from "../components/FixInspector"
import type { Violation } from "../api"

const violation: Violation = {
  rule: "god_module",
  kind: "god_module",
  severity: "warning",
  evidence: "Module A has 15 dependencies",
  components: ["src/a.ts"],
  impact: "High coupling",
  recommendation: "Split module",
  commit_sha: "abc123def",
}

describe("FixInspector", () => {
  it("shows placeholder when nothing is selected", () => {
    render(<FixInspector violation={null} branch="main" />)
    expect(screen.getByText(/Select a row to see the fix/)).toBeInTheDocument()
  })

  it("renders violation detail with commit", () => {
    render(<FixInspector violation={violation} branch="main" />)
    expect(screen.getAllByText("god_module").length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText("High coupling")).toBeInTheDocument()
    expect(screen.getByText("Split module")).toBeInTheDocument()
    expect(screen.getByText("abc123def")).toBeInTheDocument()
    expect(screen.getByRole("button", { name: /Copy fix summary/ })).toBeInTheDocument()
  })
})
