import { useEffect } from "react"

interface Shortcuts {
  [key: string]: () => void
}

export function useKeyboardShortcuts(shortcuts: Shortcuts) {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement
      if (target.tagName === "INPUT" || target.tagName === "TEXTAREA" || target.isContentEditable) {
        return
      }

      const parts: string[] = []
      if (e.ctrlKey || e.metaKey) parts.push("ctrl")
      if (e.shiftKey) parts.push("shift")
      if (e.altKey) parts.push("alt")
      parts.push(e.key.toLowerCase())
      const combo = parts.join("+")

      if (combo in shortcuts) {
        e.preventDefault()
        shortcuts[combo]()
      }
    }

    window.addEventListener("keydown", handler)
    return () => window.removeEventListener("keydown", handler)
  }, [shortcuts])
}
