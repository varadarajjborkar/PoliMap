import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { isTranslated, loadStrings, translator } from '../lib/i18n'

// The interface language, read wherever something is rendered.
//
// A context rather than a prop because the strings are everywhere and threading
// one through every component is how half of them end up untranslated. What it
// carries is the translator itself rather than the language code: the table
// behind it is fetched, so a component asking what a button says cannot be the
// thing that waits for it.

export const LanguageContext = createContext(translator(null))

export function useT() {
  return useContext(LanguageContext)
}

// Fetches the chosen language and hands back the translator for it.
//
// `ready` is false only until the first table arrives, and only when the first
// language asked for is not English. Someone who has chosen Kannada should not
// watch the page render in English and then correct itself, and someone
// reading English waits for nothing, because there is nothing to fetch.
//
// A later change keeps the table already in hand until the next one lands, so
// switching languages never falls back through English on the way.
export function useLanguage(code) {
  // A box around the table rather than the table itself: a null table means
  // English, which has no table and needs none, while no box at all means the
  // first one has not arrived. Those are different states, and telling them
  // apart is the whole of what `ready` is for.
  const [held, setHeld] = useState(() => (isTranslated(code) ? null : { table: null }))

  useEffect(() => {
    if (!isTranslated(code)) {
      setHeld({ table: null })
      return
    }
    let live = true
    loadStrings(code).then((table) => {
      if (live) setHeld({ table })
    })
    return () => { live = false }
  }, [code])

  const t = useMemo(() => translator(held?.table ?? null), [held])
  return { t, ready: held !== null }
}
