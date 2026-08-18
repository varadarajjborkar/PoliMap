import { useCallback, useEffect, useRef, useState } from 'react'

// Letting a screen finish leaving before the next one replaces it.
//
// React swaps a screen out the instant state changes, so an exit animation has
// nowhere to run: the element is already gone. This holds the outgoing screen
// for exactly as long as its animation lasts, then hands over.
//
// Somebody who has asked for less motion is handed over to immediately rather
// than made to wait out an animation they will not see. The delay is the
// animation; without one there is nothing to wait for.

export function useScreenExit(ms = 240) {
  const [leaving, setLeaving] = useState(false)
  const timer = useRef(null)

  useEffect(() => () => window.clearTimeout(timer.current), [])

  const leave = useCallback((then) => {
    if (window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) {
      then()
      return
    }
    setLeaving(true)
    timer.current = window.setTimeout(then, ms)
  }, [ms])

  return { leaving, leave }
}
