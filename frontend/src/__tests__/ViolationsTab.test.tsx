import { describe, it, expect, vi } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import ViolationsTab from "../components/ViolationsTab"
import type { Violation } from "../api"

const mockViolations: Violation[] = [
  {
    rule: "god_module",
    kind: "god_module",
    severity: "warning",
    evidence: "Module A has 15 dependencies",
    components: ["src/a.ts"],
    impact: "High coupling",
    recommendation: "Split module",
    commit_sha: null,
  },
  {
    rule: "circular_dependency",
    kind: "circular_dependency",
    severity: "error",
    evidence: "Cycle between A and B",
    components: ["src/a.ts", "src/b.ts"],
    impact: "Circular reference",
    recommendation: "Extract interface",
    commit_sha: "abc123def",
  },
]

describe("ViolationsTab", () => {
  it("renders violations table", () => {
    render(
      <ViolationsTab
        violations={mockViolations}
        filtered={mockViolations}
        severityFilter=""
        kindFilter=""
        search=""
        onSeverityChange={vi.fn()}
        onKindChange={vi.fn()}
        onSearchChange={vi.fn()}
      />
    )
    expect(screen.getAllByText("god_module").length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText("circular_dependency").length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText(/Showing 2 of 2 violations/)).toBeInTheDocument()
  })

  it("shows empty state when no violations", () => {
    render(
      <ViolationsTab
        violations={[]}
        filtered={[]}
        severityFilter=""
        kindFilter=""
        search=""
        onSeverityChange={vi.fn()}
        onKindChange={vi.fn()}
        onSearchChange={vi.fn()}
      />
    )
    expect(screen.getByText(/No violations found/)).toBeInTheDocument()
  })

  it("calls onSeverityChange on select change", () => {
    const onSeverityChange = vi.fn()
    render(
      <ViolationsTab
        violations={mockViolations}
        filtered={mockViolations}
        severityFilter=""
        kindFilter=""
        search=""
        onSeverityChange={onSeverityChange}
        onKindChange={vi.fn()}
        onSearchChange={vi.fn()}
      />
    )
    const selects = screen.getAllByDisplayValue("Severity: all")
    fireEvent.change(selects.at(-1)!, { target: { value: "error" } })
    expect(onSeverityChange).toHaveBeenCalledWith("error")
  })

  it("shows expanded details when clicking a desktop table row", () => {
    render(
      <ViolationsTab
        violations={mockViolations}
        filtered={mockViolations}
        severityFilter=""
        kindFilter=""
        search=""
        onSeverityChange={vi.fn()}
        onKindChange={vi.fn()}
        onSearchChange={vi.fn()}
      />
    )

    expect(screen.queryAllByText("High coupling")).toHaveLength(0)

    const rows = screen.getAllByRole("row", { hidden: true })
    const dataRows = rows.filter((r) => r.querySelector("td"))
    fireEvent.click(dataRows[0]!)

    expect(screen.getAllByText("High coupling").length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText("Split module").length).toBeGreaterThanOrEqual(1)
  })

  it("toggles expanded details on row click", () => {
    render(
      <ViolationsTab
        violations={mockViolations}
        filtered={mockViolations}
        severityFilter=""
        kindFilter=""
        search=""
        onSeverityChange={vi.fn()}
        onKindChange={vi.fn()}
        onSearchChange={vi.fn()}
      />
    )

    expect(screen.queryAllByText("High coupling")).toHaveLength(0)

    const rows = screen.getAllByRole("row", { hidden: true })
    const dataRows = rows.filter((r) => r.querySelector("td"))
    fireEvent.click(dataRows[0]!)
    expect(screen.getAllByText("High coupling").length).toBeGreaterThanOrEqual(1)

    const rows2 = screen.getAllByRole("row", { hidden: true })
    const dataRows2 = rows2.filter((r) => r.querySelector("td"))
    fireEvent.click(dataRows2[0]!)
    expect(screen.queryAllByText("High coupling")).toHaveLength(0)
  })

  it("mobile card expand button works", () => {
    render(
      <ViolationsTab
        violations={mockViolations}
        filtered={mockViolations}
        severityFilter=""
        kindFilter=""
        search=""
        onSeverityChange={vi.fn()}
        onKindChange={vi.fn()}
        onSearchChange={vi.fn()}
      />
    )

    expect(screen.queryAllByText("High coupling")).toHaveLength(0)

    const expandBtn = screen.getAllByRole("button", { expanded: false })[0]
    fireEvent.click(expandBtn)

    expect(screen.getAllByText("High coupling").length).toBeGreaterThanOrEqual(1)
  })
})
