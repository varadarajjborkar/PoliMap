import { useCallback, useEffect, useState } from 'react'

// Preferences, kept on the device.
//
// Three of them, and every one is about reading: which language the app speaks,
// which theme it wears, how large it sets its type. Nothing that belongs to a
// developer is offered here, which is why the activity panel is not.
//
// Nothing about a policy is stored here. A reload starts over, which is the
// honest behaviour while there are no accounts: the alternative is leaving
// someone's insurance document on a device they may have borrowed.

// Also read by the boot script in index.html, which applies the theme before
// the first paint. Change one and change the other.
const KEY = 'polimap.settings'

export const DEFAULTS = {
  // "system" follows the operating system and changes with it.
  theme: 'system',
  // The interface's own language. English until somebody chooses otherwise,
  // because that is the one language every one of these documents is written
  // in, and a wrong guess from the browser's locale would put a person who
  // reads English into a script they may not.
  language: 'en',
  // The comfortable size is the default. "large" goes further.
  textSize: 'default',
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
      // Keep the phone's address bar on the same colour as the page. Read back
      // from the stylesheet rather than restated here, so the palette has one
      // home and this cannot drift from it.
      const canvas = getComputedStyle(root).getPropertyValue('--color-canvas').trim()
      document
        .querySelector('meta[name="theme-color"]')
        ?.setAttribute('content', canvas)
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

  // Screen readers and the browser's own font choice both key off this.
  useEffect(() => {
    document.documentElement.lang = settings.language
  }, [settings.language])

  const set = useCallback((key, value) => {
    setSettings((current) => ({ ...current, [key]: value }))
  }, [])

  const reset = useCallback(() => setSettings({ ...DEFAULTS }), [])

  return { settings, set, reset }
}
