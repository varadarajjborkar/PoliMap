import { useCallback, useEffect, useState } from 'react'

// Routing on the URL hash.
//
// The hash is used rather than the History API for one practical reason: it
// needs no server rewrite rule, so the same build works behind the Vite dev
// server and behind a static host without either being configured for it.
//
// Putting the step in the URL is what makes the browser's own back and forward
// buttons work. People reach for those before they reach for anything we draw,
// and a hospital cost estimate is exactly the kind of page someone backs out of
// to compare against the previous one.

export const STEPS = [
  { id: 'upload', path: '/', label: 'Your policy', short: 'Policy' },
  { id: 'policy', path: '/cover', label: 'Your cover', short: 'Cover' },
  { id: 'search', path: '/hospitals', label: 'Hospitals', short: 'Hospitals' },
  { id: 'journey', path: '/stay', label: 'Your stay', short: 'Stay' },
]

const BY_ID = Object.fromEntries(STEPS.map((s) => [s.id, s]))
const BY_PATH = Object.fromEntries(STEPS.map((s) => [s.path, s]))

function currentId() {
  const path = window.location.hash.replace(/^#/, '') || '/'
  return (BY_PATH[path] ?? STEPS[0]).id
}

export function useRoute() {
  const [route, setRoute] = useState(currentId)

  useEffect(() => {
    const onChange = () => setRoute(currentId())
    window.addEventListener('hashchange', onChange)
    return () => window.removeEventListener('hashchange', onChange)
  }, [])

  // Adds a history entry, so back returns to where the user was.
  const go = useCallback((id) => {
    const step = BY_ID[id] ?? STEPS[0]
    if (window.location.hash.replace(/^#/, '') === step.path) {
      setRoute(step.id)
      return
    }
    window.location.hash = step.path
  }, [])

  // Replaces the current entry. Used when the app corrects the URL itself, so
  // that pressing back does not land on a step that was never reachable.
  const replace = useCallback((id) => {
    const step = BY_ID[id] ?? STEPS[0]
    window.history.replaceState(null, '', `#${step.path}`)
    setRoute(step.id)
  }, [])

  return { route, go, replace }
}

export const stepIndex = (id) => STEPS.findIndex((s) => s.id === id)
export const stepAt = (index) => STEPS[index] ?? null
