import { useState, useCallback } from "react"

export interface HistoryEntry {
  url: string
  branch: string
  timestamp: number
  violations: number
  drift: number
}

const STORAGE_KEY = "sentinel-history"
const MAX_ENTRIES = 10

function loadHistory(): HistoryEntry[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

function saveHistory(entries: HistoryEntry[]): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(entries))
}

export function useHistory() {
  const [history, setHistory] = useState<HistoryEntry[]>(loadHistory)

  const addEntry = useCallback((entry: Omit<HistoryEntry, "timestamp">) => {
    setHistory((prev) => {
      const filtered = prev.filter(
        (e) => !(e.url === entry.url && e.branch === entry.branch)
      )
      const updated = [
        { ...entry, timestamp: Date.now() },
        ...filtered,
      ].slice(0, MAX_ENTRIES)
      saveHistory(updated)
      return updated
    })
  }, [])

  const clearHistory = useCallback(() => {
    setHistory([])
    localStorage.removeItem(STORAGE_KEY)
  }, [])

  return { history, addEntry, clearHistory }
}
