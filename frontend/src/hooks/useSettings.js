import { useCallback, useEffect, useState } from 'react'

// Preferences, kept on the device.
//
// Defaults are chosen for the person the app is actually for: someone dealing
// with a hospital admission, not someone inspecting a pipeline. So the activity
// panel starts hidden. It is a developer tool, and a live feed of extraction
// steps is noise to a user and reassurance only to us.
//
// Nothing about a policy is stored here. A reload starts over, which is the
// honest behaviour while there are no accounts: the alternative is leaving
// someone's insurance document on a device they may have borrowed.

const KEY = 'coverpath.settings'

export const DEFAULTS = {
  // "system" follows the operating system and changes with it.
  theme: 'system',
  // The comfortable size is the default. "large" goes further.
  textSize: 'default',
  // Developer
  showActivity: false,
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

const prefersDark = () =>
  window.matchMedia?.('(prefers-color-scheme: dark)').matches ?? false

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

  useEffect(() => {
    const root = document.documentElement

    const apply = () => {
      const dark =
        settings.theme === 'dark' ||
        (settings.theme === 'system' && prefersDark())
      root.classList.toggle('theme-dark', dark)
    }
    apply()

    if (settings.theme !== 'system') return
    // Only while following the system: someone who has chosen a theme should
    // not have it changed under them at sunset.
    const query = window.matchMedia('(prefers-color-scheme: dark)')
    query.addEventListener('change', apply)
    return () => query.removeEventListener('change', apply)
  }, [settings.theme])

  useEffect(() => {
    document.documentElement.dataset.text = settings.textSize
  }, [settings.textSize])

  const set = useCallback((key, value) => {
    setSettings((current) => ({ ...current, [key]: value }))
  }, [])

  const reset = useCallback(() => setSettings({ ...DEFAULTS }), [])

  return { settings, set, reset }
}
