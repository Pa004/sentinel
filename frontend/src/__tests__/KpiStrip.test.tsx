import { describe, it, expect } from "vitest"
import { render, screen } from "@testing-library/react"
import KpiStrip from "../components/KpiStrip"

const metrics = { nodes: 148, edges: 312, cycles: 4, avg_coupling: 2.11 }

describe("KpiStrip", () => {
  it("renders counts, drift and graph metrics in one strip", () => {
    render(
      <KpiStrip
        total={10}
        errors={3}
        warnings={5}
        info={2}
        drift={0.42}
        metrics={metrics}
        elapsedMs={1800}
      />
    )
    expect(screen.getByText("Total")).toBeInTheDocument()
    expect(screen.getByText("10")).toBeInTheDocument()
    expect(screen.getByText("0.42")).toBeInTheDocument()
    expect(screen.getByText("148")).toBeInTheDocument()
    expect(screen.getByText("2.11")).toBeInTheDocument()
    expect(screen.getByText("analyzed in 1.8s")).toBeInTheDocument()
  })

  it("renders dash for missing metrics", () => {
    render(
      <KpiStrip
        total={0}
        errors={0}
        warnings={0}
        info={0}
        drift={0}
        metrics={{ nodes: null, edges: null, cycles: null, avg_coupling: null }}
        elapsedMs={null}
      />
    )
    expect(screen.getAllByText("-").length).toBeGreaterThanOrEqual(4)
  })
})
