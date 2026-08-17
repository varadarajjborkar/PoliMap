import { useCallback, useEffect, useState } from 'react'

// Routing on real paths.
//
// This used to route on the hash, which needs no server rewrite. The cost was a
// URL that read as `#/` on the home screen and `#/hospitals` deeper in, neither
// of which survived being pasted to anyone. Real paths are served by the SPA
// rewrite already in `vercel.json`, and Vite's dev server falls back to
// index.html on its own, so nothing extra is configured for either.
//
// A stay's id is in the path. That is what makes a link to an admission mean
// the same thing tomorrow as it does now, and it is why the browser's own back
// button lands where the user expects instead of on a step that no longer has
// anything behind it.

export const SETUP_STEPS = [
  { id: 'upload', segment: '', label: 'Your policy', short: 'Policy' },
  { id: 'policy', segment: 'cover', label: 'Your cover', short: 'Cover' },
  { id: 'search', segment: 'hospitals', label: 'Hospitals', short: 'Hospitals' },
]

export const TRACK_STEP = {
  id: 'journey', segment: 'track', label: 'Your stay', short: 'Stay',
}

export const STEPS = [...SETUP_STEPS, TRACK_STEP]

const BY_ID = Object.fromEntries(STEPS.map((s) => [s.id, s]))
const BY_SEGMENT = Object.fromEntries(STEPS.map((s) => [s.segment, s]))

export function stayPath(stayId, stepId) {
  const step = BY_ID[stepId] ?? SETUP_STEPS[0]
  return `/stay/${stayId}${step.segment ? `/${step.segment}` : ''}`
}

// The path is the only source of truth for where the user is. Parsing it in one
// place means a typed URL, a restored tab and a click all arrive as the same
// shape, and none of them can disagree with the address bar.
export function parse(pathname) {
  const parts = pathname.split('/').filter(Boolean)

  if (parts[0] === 'stay' && parts[1]) {
    const step = BY_SEGMENT[parts[2] ?? ''] ?? SETUP_STEPS[0]
    return { view: 'stay', stayId: parts[1], step: step.id }
  }
  if (parts[0] === 'new') return { view: 'stay', stayId: null, step: 'upload' }
  return { view: 'home', stayId: null, step: null }
}

export function useRoute() {
  const [location, setLocation] = useState(() => parse(window.location.pathname))

  useEffect(() => {
    const onPop = () => setLocation(parse(window.location.pathname))
    window.addEventListener('popstate', onPop)
    return () => window.removeEventListener('popstate', onPop)
  }, [])

  // Adds a history entry, so back returns to where the user was.
  const navigate = useCallback((path, { replace = false } = {}) => {
    if (window.location.pathname === path) {
      setLocation(parse(path))
      return
    }
    // `replace` is for corrections the app makes to itself. Pressing back
    // should not return to a step the app has just decided was unreachable.
    window.history[replace ? 'replaceState' : 'pushState'](null, '', path)
    setLocation(parse(path))
    window.scrollTo({ top: 0, behavior: 'instant' })
  }, [])

  return { ...location, navigate }
}

export const stepIndex = (id) => STEPS.findIndex((s) => s.id === id)
