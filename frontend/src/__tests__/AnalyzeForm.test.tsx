import { describe, it, expect, vi } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import AnalyzeForm from "../components/AnalyzeForm"

describe("AnalyzeForm", () => {
  it("renders inputs and button", () => {
    render(<AnalyzeForm onAnalyze={vi.fn()} loading={false} />)
    expect(screen.getByPlaceholderText(/GitHub repo URL/)).toBeInTheDocument()
    expect(screen.getByPlaceholderText("Branch")).toBeInTheDocument()
    expect(screen.getAllByRole("button", { name: /Analyze/i }).pop()).toBeInTheDocument()
  })

  it("calls onAnalyze with URL and branch on button click", () => {
    const onAnalyze = vi.fn()
    render(<AnalyzeForm onAnalyze={onAnalyze} loading={false} />)
    const inputs = screen.getAllByPlaceholderText(/GitHub repo URL/)
    fireEvent.change(inputs.at(-1)!, { target: { value: "owner/repo" } })
    const buttons = screen.getAllByRole("button", { name: /Analyze/i })
    fireEvent.click(buttons.at(-1)!)
    expect(onAnalyze).toHaveBeenCalledWith("owner/repo", "main")
  })

  it("calls onAnalyze on Enter key", () => {
    const onAnalyze = vi.fn()
    render(<AnalyzeForm onAnalyze={onAnalyze} loading={false} />)
    const inputs = screen.getAllByPlaceholderText(/GitHub repo URL/)
    const input = inputs.at(-1)!
    fireEvent.change(input, { target: { value: "test/repo" } })
    fireEvent.keyDown(input, { key: "Enter" })
    expect(onAnalyze).toHaveBeenCalledWith("test/repo", "main")
  })

  it("does not call onAnalyze when URL is empty", () => {
    const onAnalyze = vi.fn()
    render(<AnalyzeForm onAnalyze={onAnalyze} loading={false} />)
    const buttons = screen.getAllByRole("button", { name: /Analyze/i })
    fireEvent.click(buttons.at(-1)!)
    expect(onAnalyze).not.toHaveBeenCalled()
  })

  it("disables button when loading", () => {
    render(<AnalyzeForm onAnalyze={vi.fn()} loading={true} />)
    const buttons = screen.getAllByRole("button", { name: /Analyzing/ })
    expect(buttons.at(-1)).toBeDisabled()
  })
})
