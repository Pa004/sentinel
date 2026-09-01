import { describe, it, expect } from "vitest"
import { render, screen } from "@testing-library/react"
import SummaryCards from "../components/SummaryCards"

describe("SummaryCards", () => {
  it("renders all 5 cards with correct values", () => {
    render(
      <SummaryCards total={10} errors={2} warnings={5} info={3} drift={0.45} />
    )

    expect(screen.getByText("Total")).toBeInTheDocument()
    expect(screen.getByText("10")).toBeInTheDocument()
    expect(screen.getByText("Errors")).toBeInTheDocument()
    expect(screen.getByText("2")).toBeInTheDocument()
    expect(screen.getByText("Warnings")).toBeInTheDocument()
    expect(screen.getByText("5")).toBeInTheDocument()
    expect(screen.getByText("Info")).toBeInTheDocument()
    expect(screen.getByText("3")).toBeInTheDocument()
    expect(screen.getByText("Drift")).toBeInTheDocument()
    expect(screen.getByText("0.45")).toBeInTheDocument()
  })
})
