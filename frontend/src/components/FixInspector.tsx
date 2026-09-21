import { useState } from "react"
import { Copy, Check } from "lucide-react"
import type { Violation } from "../api"

interface FixInspectorProps {
  violation: Violation | null
  branch: string
}

const severityBadge: Record<string, string> = {
  error: "bg-error/15 text-error",
  warning: "bg-warning/15 text-warning",
  info: "bg-info/15 text-info",
}

function FixBlock({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-md border border-border bg-surface-2 p-2.5">
      <h3 className="mb-1 text-[10px] uppercase tracking-wider text-muted">{title}</h3>
      <div className="text-xs text-content">{children}</div>
    </div>
  )
}

export default function FixInspector({ violation, branch }: FixInspectorProps) {
  const [copied, setCopied] = useState(false)

  if (!violation) {
    return (
      <aside aria-label="Remediation detail" className="inspector-col flex min-h-0 flex-col overflow-hidden border-l border-border bg-surface-1">
        <h2 className="px-3 pb-1.5 pt-2.5 text-[10px] uppercase tracking-wider text-muted">
          Fix detail
        </h2>
        <p className="px-3 text-xs text-muted">Select a row to see the fix.</p>
      </aside>
    )
  }

  const handleCopy = async () => {
    const text = `${violation.rule} [${violation.severity}/${violation.kind}]\nEvidence: ${violation.evidence}\nFix: ${violation.recommendation}`
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      // clipboard unavailable: do nothing
    }
  }

  return (
    <aside aria-label="Remediation detail" className="inspector-col flex min-h-0 flex-col overflow-hidden border-l border-border bg-surface-1">
      <h2 className="px-3 pb-1.5 pt-2.5 text-[10px] uppercase tracking-wider text-muted">
        Fix detail
      </h2>
      <div className="flex flex-col gap-2.5 overflow-y-auto px-3 pb-4">
        <div className="flex items-center gap-2">
          <span className={`inline-block rounded px-1.5 py-0.5 text-xs font-semibold ${severityBadge[violation.severity] ?? "text-content"}`}>
            {violation.severity}
          </span>
          <span className="font-mono text-[11px] text-muted">{violation.kind}</span>
        </div>
        <h3 className="font-mono text-sm font-semibold tracking-tight text-content">{violation.rule}</h3>
        <FixBlock title="Evidence">
          <span className="font-mono text-[11px]">{violation.evidence}</span>
        </FixBlock>
        <FixBlock title="Impact">{violation.impact}</FixBlock>
        <FixBlock title="Recommended fix">
          {violation.recommendation}
          <ol className="mt-1.5 list-decimal space-y-0.5 pl-4 text-muted">
            <li>Cut the direct import at the seam.</li>
            <li>Route through the public entry point.</li>
            <li>Pin with <code className="rounded bg-surface-3 px-1 font-mono text-[11px]">no-restricted-imports</code> in CI.</li>
          </ol>
        </FixBlock>
        <FixBlock title="Commit">
          {violation.commit_sha ? (
            <>First seen in <code className="rounded bg-surface-3 px-1 font-mono text-[11px]">{violation.commit_sha}</code> on {branch}.</>
          ) : (
            "Working-tree finding — commit to trace origin."
          )}
        </FixBlock>
        <button
          onClick={handleCopy}
          className="inline-flex items-center justify-center gap-1.5 rounded-md bg-brand px-3 py-1.5 text-xs font-semibold text-white transition-colors hover:bg-brand-hover"
        >
          {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
          {copied ? "Copied" : "Copy fix summary"}
        </button>
      </div>
    </aside>
  )
}
