import { useState } from "react"
import { Share2, Check } from "lucide-react"

interface ShareButtonProps {
  repoUrl: string
  branch: string
}

export default function ShareButton({ repoUrl, branch }: ShareButtonProps) {
  const [copied, setCopied] = useState(false)

  const handleShare = async () => {
    const url = new URL(window.location.href)
    url.searchParams.set("repo", repoUrl)
    url.searchParams.set("branch", branch)

    try {
      await navigator.clipboard.writeText(url.toString())
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // Fallback: open in new tab
      window.open(url.toString(), "_blank")
    }
  }

  return (
    <button
      onClick={handleShare}
      className="inline-flex items-center gap-1.5 rounded-md border border-border px-3 py-1.5 text-sm font-medium text-muted transition-colors hover:bg-surface-2 hover:text-content"
      aria-label="Share analysis"
    >
      {copied ? (
        <>
          <Check className="h-3.5 w-3.5" />
          Copied
        </>
      ) : (
        <>
          <Share2 className="h-3.5 w-3.5" />
          Share
        </>
      )}
    </button>
  )
}
