import { createContext, useContext, useMemo } from 'react'
import { translator } from '../lib/i18n'

// The interface language, read wherever something is rendered.
//
// A context rather than a prop because the strings are everywhere and threading
// one through every component is how half of them end up untranslated. The
// value is the language code alone, so changing it re-renders the tree once and
// nothing has to be recomputed to find out what a button says.

export const LanguageContext = createContext('en')

export function useT() {
  const code = useContext(LanguageContext)
  return useMemo(() => translator(code), [code])
}
