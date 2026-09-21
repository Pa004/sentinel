import { useState, useEffect, useRef, useCallback } from "react"
import { Sun, Moon, X, RotateCcw, History } from "lucide-react"
import { motion } from "framer-motion"
import { analyze } from "./api"
import type { Violation, AnalysisResult } from "./api"
import AnalyzeForm from "./components/AnalyzeForm"
import KpiStrip from "./components/KpiStrip"
import ViolationsTab from "./components/ViolationsTab"
import RemediationTab from "./components/RemediationTab"
import ShareButton from "./components/ShareButton"
import ExportButton from "./components/ExportButton"
import SkeletonCards from "./components/SkeletonCards"
import SkeletonMetrics from "./components/SkeletonMetrics"
import SkeletonTable from "./components/SkeletonTable"
import FeatureCards from "./components/FeatureCards"
import HowItWorks from "./components/HowItWorks"
import ExampleRepos from "./components/ExampleRepos"
import HistoryRail from "./components/HistoryRail"
import FixInspector from "./components/FixInspector"
import { SampleOutput, MicroStats } from "./components/SampleOutput"
import { usePrefersReducedMotion } from "./hooks/usePrefersReducedMotion"
import { usePerformance } from "./hooks/usePerformance"
import { useAnalytics } from "./hooks/useAnalytics"
import { useToast } from "./components/Toast"
import { useKeyboardShortcuts } from "./hooks/useKeyboardShortcuts"
import { useHistory } from "./hooks/useHistory"

function useTheme() {
  const [dark, setDark] = useState(() => {
    const stored = localStorage.getItem("sentinel-theme")
    return stored ? stored === "dark" : true
  })

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark)
    document.documentElement.classList.toggle("light", !dark)
    localStorage.setItem("sentinel-theme", dark ? "dark" : "light")
  }, [dark])

  return { dark, toggle: () => setDark((d) => !d) }
}

const TABS = ["violations", "remediation"] as const
type TabKey = (typeof TABS)[number]

export default function App() {
  const { dark, toggle } = useTheme()
  const reducedMotion = usePrefersReducedMotion()
  const { metrics: perfMetrics, startTimer, endTimer } = usePerformance()
  const { track } = useAnalytics()
  const { addToast } = useToast()
  const { history, addEntry, clearHistory } = useHistory()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [lastAnalyzed, setLastAnalyzed] = useState<{ url: string; branch: string } | null>(null)
  const [activeTab, setActiveTab] = useState<TabKey>("violations")
  const [severityFilter, setSeverityFilter] = useState("")
  const [kindFilter, setKindFilter] = useState("")
  const [search, setSearch] = useState("")
  const [selectedIdx, setSelectedIdx] = useState<number | null>(null)
  const [railOpen, setRailOpen] = useState(false)

  const resultsRef = useRef<HTMLDivElement>(null)
  const tabRefs = useRef<Record<TabKey, HTMLButtonElement | null>>({
    violations: null,
    remediation: null,
  })

  const handleAnalyze = async (url: string, br: string) => {
    setLoading(true)
    setError("")
    setResult(null)
    setSelectedIdx(null)
    setLastAnalyzed({ url, branch: br })
    startTimer()
    track("analysis_start", { repo: url, branch: br })
    try {
      const data = await analyze(url, br)
      const elapsed = endTimer()
      setResult(data)
      track("analysis_complete", {
        repo: url,
        branch: br,
        violations: data.total_violations,
        drift: data.drift_score,
        timeMs: Math.round(elapsed),
      })
      if (data.total_violations === 0) {
        addToast("No violations found — architecture looks clean!", "success")
      } else {
        addToast(`Found ${data.total_violations} violation(s)`, "info")
      }
      addEntry({
        url,
        branch: br,
        violations: data.total_violations,
        drift: data.drift_score,
      })
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Analysis failed"
      setError(msg)
      track("analysis_error", { repo: url, error: msg })
      addToast(msg, "error")
    } finally {
      setLoading(false)
    }
  }

  const handleRetry = () => {
    if (lastAnalyzed) {
      handleAnalyze(lastAnalyzed.url, lastAnalyzed.branch)
    }
  }

  // Keyboard shortcuts
  useKeyboardShortcuts({
    "1": () => setActiveTab("violations"),
    "2": () => setActiveTab("remediation"),
    "escape": () => setError(""),
  })

  // Focus management: move focus to results after analysis completes
  useEffect(() => {
    if (result && !loading && resultsRef.current) {
      resultsRef.current.focus()
    }
  }, [result, loading])

  // Keyboard navigation for tabs
  const handleTabKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      const currentIndex = TABS.indexOf(activeTab)
      let nextIndex: number | null = null

      if (e.key === "ArrowRight" || e.key === "ArrowDown") {
        e.preventDefault()
        nextIndex = (currentIndex + 1) % TABS.length
      } else if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
        e.preventDefault()
        nextIndex = (currentIndex - 1 + TABS.length) % TABS.length
      } else if (e.key === "Home") {
        e.preventDefault()
        nextIndex = 0
      } else if (e.key === "End") {
        e.preventDefault()
        nextIndex = TABS.length - 1
      }

      if (nextIndex !== null) {
        const nextTab = TABS[nextIndex]
        setActiveTab(nextTab)
        tabRefs.current[nextTab]?.focus()
      }
    },
    [activeTab]
  )

  const violations: Violation[] = result?.violations ?? []
  const metrics = result?.metrics ?? null

  const filtered = violations.filter((v) => {
    if (severityFilter && v.severity !== severityFilter) return false
    if (kindFilter && v.kind !== kindFilter) return false
    if (search) {
      const q = search.toLowerCase()
      return (
        v.evidence.toLowerCase().includes(q) ||
        v.impact.toLowerCase().includes(q) ||
        v.rule.toLowerCase().includes(q)
      )
    }
    return true
  })

  const showHero = !result && !loading && !error

  const counts = {
    total: violations.length,
    errors: violations.filter((v) => v.severity === "error").length,
    warnings: violations.filter((v) => v.severity === "warning").length,
    info: violations.filter((v) => v.severity === "info").length,
  }

  const ruleGroups = new Set(violations.map((v) => v.rule)).size
  const selectedViolation =
    selectedIdx !== null && selectedIdx >= 0 && selectedIdx < violations.length
      ? violations[selectedIdx]
      : null

  const MotionOrDiv = reducedMotion ? "div" : motion.div
  const animProps = reducedMotion
    ? {}
    : { initial: { opacity: 0 }, animate: { opacity: 1 } }

  return (
    <div className="app-shell bg-surface-0 text-content">
      <a
        href="#results-panel"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-brand focus:px-4 focus:py-2 focus:text-sm focus:text-white focus:outline-none"
      >
        Skip to results
      </a>

      <header className="flex min-w-0 items-center gap-2.5 border-b border-border bg-surface-1 px-3">
        <div className="flex shrink-0 items-center gap-1.5">
          <span className="grid h-[22px] w-[22px] place-items-center rounded-md bg-brand text-xs font-extrabold text-white">
            S
          </span>
          <h1 className="text-sm font-bold tracking-tight">Sentinel</h1>
          <span className="h-1.5 w-1.5 rounded-full bg-success" title="backend reachable" />
        </div>
        <div className="hidden min-w-0 items-center gap-1.5 font-mono text-xs text-muted sm:flex" aria-live="polite">
          {lastAnalyzed ? (
            <>
              <b className="truncate font-semibold text-content">{lastAnalyzed.url}</b>
              <span className="shrink-0 rounded-full border border-border bg-surface-2 px-2 py-px text-[11px]">
                {lastAnalyzed.branch}
              </span>
              {result && (
                <span className="shrink-0 rounded-full border border-warning/40 bg-warning/15 px-2 py-px text-[11px] font-bold text-warning">
                  drift {result.drift_score.toFixed(2)}
                </span>
              )}
            </>
          ) : (
            <span>no repo analyzed yet</span>
          )}
        </div>
        <AnalyzeForm onAnalyze={handleAnalyze} loading={loading} compact />
        <div className="flex shrink-0 items-center">
          <button
            onClick={() => setRailOpen((o) => !o)}
            className="grid h-7 w-7 place-items-center rounded-md text-muted transition-colors hover:bg-surface-2 hover:text-content md:hidden"
            aria-label="Toggle history"
            aria-pressed={railOpen}
          >
            <History className="h-4 w-4" />
          </button>
          <button
            onClick={toggle}
            className="grid h-7 w-7 place-items-center rounded-md text-muted transition-colors hover:bg-surface-2 hover:text-content"
            aria-label={dark ? "Switch to light mode" : "Switch to dark mode"}
          >
            {dark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </button>
          {result && (
            <>
              <ShareButton
                repoUrl={lastAnalyzed?.url ?? ""}
                branch={lastAnalyzed?.branch ?? "main"}
                iconOnly
              />
              <ExportButton result={result} iconOnly />
            </>
          )}
        </div>
      </header>

      {result && !loading && (
        <KpiStrip
          total={counts.total}
          errors={counts.errors}
          warnings={counts.warnings}
          info={counts.info}
          drift={result.drift_score}
          metrics={metrics}
          elapsedMs={perfMetrics.analysisTimeMs}
        />
      )}

      <main className="min-h-0">
        {showHero ? (
          <div className="col-span-full grid min-h-0 grid-cols-1 gap-0 overflow-y-auto bg-surface-0 lg:grid-cols-[1.1fr_.9fr]">
            <div className="flex min-h-0 flex-col justify-between gap-5 border-b border-border px-5 py-7 sm:px-8 lg:border-b-0 lg:border-r lg:py-9">
              <div>
                <div className="text-[10px] font-bold uppercase tracking-widest text-brand">
                  Architecture erosion detector
                </div>
                <h2 className="mt-2 max-w-xl text-3xl font-bold leading-tight tracking-tight sm:text-4xl lg:text-[44px] lg:leading-[1.05]">
                  Ship features without rotting the architecture.
                </h2>
                <p className="mt-3 max-w-lg text-sm text-muted">
                  Paste a GitHub repo. Sentinel maps the dependency graph, flags layering
                  violations and cycles, and scores drift — with a concrete fix for every finding.
                </p>
              </div>
              <div>
                <FeatureCards />
                <div className="mt-3">
                  <HowItWorks />
                </div>
              </div>
            </div>
            <div className="flex min-h-0 flex-col justify-between gap-4 bg-surface-1 px-5 py-7 sm:px-8 lg:py-9">
              <SampleOutput />
              <div className="rounded-xl border border-border bg-surface-0 p-4">
                <AnalyzeForm onAnalyze={handleAnalyze} loading={loading} />
                <ExampleRepos onSelect={(repo) => handleAnalyze(repo, "main")} loading={loading} />
              </div>
              <MicroStats />
            </div>
          </div>
        ) : (
          <>
            <HistoryRail
              history={history}
              onSelect={(url, branch) => handleAnalyze(url, branch)}
              onClear={clearHistory}
              loading={loading}
              open={railOpen}
            />
            <section
              ref={resultsRef}
              id="results-panel"
              tabIndex={-1}
              aria-label="Results"
              className="flex min-h-0 min-w-0 flex-col bg-surface-0 outline-none"
            >
              <div aria-live="polite" aria-atomic="true" className="sr-only">
                {result && !loading && (
                  <>Analysis complete. {counts.total} violations found: {counts.errors} errors, {counts.warnings} warnings, {counts.info} info.</>
                )}
              </div>

              {error && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  role="alert"
                  className="m-2 rounded-md border border-error/30 bg-error/10 p-3 text-sm text-error"
                >
                  <div className="flex items-start justify-between gap-3">
                    <span>{error}</span>
                    <div className="flex shrink-0 gap-2">
                      {lastAnalyzed && (
                        <button
                          onClick={handleRetry}
                          className="inline-flex items-center gap-1 rounded bg-error/15 px-2 py-1 text-xs font-medium transition-colors hover:bg-error/25"
                        >
                          <RotateCcw className="h-3 w-3" />
                          Retry
                        </button>
                      )}
                      <button
                        onClick={() => setError("")}
                        className="rounded p-1 transition-colors hover:bg-error/15"
                        aria-label="Dismiss error"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </motion.div>
              )}

              {loading && (
                <div className="space-y-4 overflow-y-auto p-3" aria-label="Loading analysis" role="status">
                  <SkeletonCards />
                  <SkeletonMetrics />
                  <SkeletonTable />
                </div>
              )}

              {result && !loading && (
                <>
                  <div
                    role="tablist"
                    aria-label="Analysis results"
                    className="flex gap-1 px-3 pt-1.5"
                    onKeyDown={handleTabKeyDown}
                  >
                    {TABS.map((tab) => {
                      const n = tab === "violations" ? violations.length : ruleGroups
                      return (
                        <button
                          key={tab}
                          ref={(el) => { tabRefs.current[tab] = el }}
                          role="tab"
                          id={`tab-${tab}`}
                          aria-selected={activeTab === tab}
                          aria-controls={`panel-${tab}`}
                          tabIndex={activeTab === tab ? 0 : -1}
                          onClick={() => setActiveTab(tab)}
                          className={`rounded-t-md px-3 py-1.5 text-xs font-semibold transition-colors ${
                            activeTab === tab
                              ? "border border-b-0 border-border bg-surface-1 text-content"
                              : "text-muted hover:text-content"
                          }`}
                        >
                          {tab.charAt(0).toUpperCase() + tab.slice(1)}
                          <span className="ml-1.5 rounded-full bg-surface-3 px-1.5 font-mono text-[10px]">
                            {n}
                          </span>
                        </button>
                      )
                    })}
                  </div>

                  <MotionOrDiv
                    {...animProps}
                    role="tabpanel"
                    id={`panel-${activeTab}`}
                    aria-labelledby={`tab-${activeTab}`}
                    className="flex min-h-0 flex-1 flex-col border-t border-border bg-surface-1 outline-none"
                  >
                    {activeTab === "violations" ? (
                      <div className="flex min-h-0 flex-1 flex-col overflow-y-auto">
                        <ViolationsTab
                          violations={violations}
                          filtered={filtered}
                          severityFilter={severityFilter}
                          kindFilter={kindFilter}
                          search={search}
                          onSeverityChange={setSeverityFilter}
                          onKindChange={setKindFilter}
                          onSearchChange={setSearch}
                          selectedIndex={selectedIdx}
                          onSelect={(idx) =>
                            setSelectedIdx((prev) => (idx === prev ? null : idx))
                          }
                        />
                      </div>
                    ) : (
                      <div className="min-h-0 flex-1 overflow-y-auto p-3">
                        <RemediationTab violations={violations} />
                      </div>
                    )}
                  </MotionOrDiv>
                </>
              )}
            </section>
            <FixInspector
              violation={selectedViolation}
              branch={lastAnalyzed?.branch ?? "main"}
            />
          </>
        )}
      </main>
    </div>
  )
}
