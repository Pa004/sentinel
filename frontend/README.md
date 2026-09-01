# Sentinel Frontend

React dashboard for the Sentinel architecture erosion detector.

## Stack

- **React 19** + **TypeScript 6.0**
- **Vite 8.2** with manual chunks (vendor, motion, index)
- **Tailwind CSS v4** (CSS-first, no config file)
- **Geist Sans + Mono** typography
- **lucide-react** icons
- **framer-motion** animations
- **Vitest 4.1** + **testing-library** for tests

## Setup

```bash
npm install
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_URL` | `""` (same origin) | Backend API URL for `/api/analyze` |

Create `.env` for local development:

```
VITE_API_URL=http://localhost:8000
```

## Commands

```bash
npm run dev      # Start dev server (http://localhost:5173)
npm run build    # Production build to dist/
npm run test     # Run Vitest tests
npm run lint     # Run oxlint
```

## Project Structure

```
frontend/src/
├── components/            # UI components
│   ├── AnalyzeForm.tsx    # Repo URL + branch input form
│   ├── ErrorBoundary.tsx  # React error boundary
│   ├── ExampleRepos.tsx   # Pre-filled example repos
│   ├── ExportButton.tsx   # Export to JSON/CSV
│   ├── FeatureCards.tsx   # Landing page feature cards
│   ├── HistoryPanel.tsx   # Past analysis history
│   ├── HowItWorks.tsx     # How-it-works explainer
│   ├── MetricsBar.tsx     # Metrics display bar
│   ├── RemediationTab.tsx # Remediation suggestions
│   ├── ShareButton.tsx    # Copy analysis URL
│   ├── SkeletonCards.tsx  # Loading skeleton
│   ├── SkeletonMetrics.tsx
│   ├── SkeletonTable.tsx
│   ├── SummaryCards.tsx   # Summary stat cards
│   ├── Toast.tsx          # Toast notification system
│   └── ViolationsTab.tsx  # Violations table/display
├── hooks/
│   ├── useAnalytics.ts          # localStorage event tracking
│   ├── useHistory.ts            # Analysis history (max 10)
│   ├── useKeyboardShortcuts.ts  # 1/2 tabs, Escape dismiss
│   ├── usePerformance.ts        # Analysis time tracking
│   └── usePrefersReducedMotion.ts
├── __tests__/             # Vitest + testing-library
├── api.ts                 # Backend client + 5min cache
├── App.tsx                # Root component
└── index.css              # Tailwind v4 theme
```

## Testing

Tests run in jsdom. React 18+ StrictMode renders twice, so:
- Use `getAllBy` with `.at(-1)` for queries matching multiple elements
- Animations (framer-motion) don't resolve in jsdom — avoid `AnimatePresence` in tested paths

```bash
npm run test
```

## Build

Production build outputs to `dist/` with manual chunks:
- `vendor` (~182KB): React, ReactDOM, react-dom
- `motion` (~133KB): framer-motion
- `index` (~42KB): app code
