import { useCallback, useEffect, useState } from 'react'

// Preferences, kept on the device.
//
// Defaults are chosen for the person the app is actually for: someone dealing
// with a hospital admission, not someone inspecting a pipeline. So the activity
// panel starts hidden. It is a developer tool, and a live feed of extraction
// steps is noise to a user and reassurance only to us.

const KEY = 'coverpath.settings'

export const DEFAULTS = {
  // Developer
  showActivity: false,
  // Reading comfort
  largeText: false,
  // Privacy. Off means the session id is dropped when the tab closes, so a
  // shared or borrowed device does not hand the next person a policy.
  rememberSession: true,
}

function load() {
  try {
    const raw = window.localStorage.getItem(KEY)
    if (!raw) return { ...DEFAULTS }
    // Spread over the defaults so a setting added later is not undefined for
    // someone who already has a stored object.
    return { ...DEFAULTS, ...JSON.parse(raw) }
  } catch {
    return { ...DEFAULTS }
  }
}

export function useSettings() {
  const [settings, setSettings] = useState(load)

  useEffect(() => {
    try {
      window.localStorage.setItem(KEY, JSON.stringify(settings))
    } catch {
      // Private browsing can refuse storage. The settings still apply for the
      // life of the tab, which is the part that matters.
    }
  }, [settings])

  // Larger type is applied at the root so every rem-based size follows it.
  useEffect(() => {
    document.documentElement.style.fontSize = settings.largeText ? '18px' : ''
  }, [settings.largeText])

  const set = useCallback((key, value) => {
    setSettings((current) => ({ ...current, [key]: value }))
  }, [])

  const reset = useCallback(() => setSettings({ ...DEFAULTS }), [])

  return { settings, set, reset }
}

// The session id lives separately from the settings: it is state, not
// preference, and it must be clearable on its own.
const SESSION_KEY = 'coverpath.session'

export const rememberedSession = () => {
  try {
    return window.localStorage.getItem(SESSION_KEY)
  } catch {
    return null
  }
}

export const rememberSession = (id) => {
  try {
    if (id) window.localStorage.setItem(SESSION_KEY, id)
    else window.localStorage.removeItem(SESSION_KEY)
  } catch {
    // Nothing to do; the session simply will not survive a reload.
  }
}
