import { useCallback } from "react"

const STORAGE_KEY = "sentinel-analytics"

interface AnalyticsEvent {
  type: string
  timestamp: number
  data?: Record<string, string | number>
}

function loadEvents(): AnalyticsEvent[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

function saveEvents(events: AnalyticsEvent[]): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(events.slice(-50)))
}

export function useAnalytics() {
  const track = useCallback((type: string, data?: Record<string, string | number>) => {
    const events = loadEvents()
    events.push({ type, timestamp: Date.now(), data })
    saveEvents(events)
  }, [])

  const getEvents = useCallback(() => {
    return loadEvents()
  }, [])

  const clearEvents = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY)
  }, [])

  return { track, getEvents, clearEvents }
}
