import { useEffect, useRef } from 'react'

// Shared behaviour for the two things that cover the page: the settings panel
// and the skip notice.
//
// Escape closes it, the page behind stops scrolling, and focus moves into it
// and back out again on close. The scrolling part matters most on a phone,
// where a panel over a scrollable page otherwise moves the page instead of
// itself under a thumb.
//
// `onClose` is held in a ref rather than listed as a dependency, because
// callers pass an inline arrow: as a dependency it would tear the listener
// down and rebuild it on every render, and the saved scroll style would be
// re-saved as the hidden one it had just been set to.

export function useDialog(open, onClose) {
  const ref = useRef(null)
  const close = useRef(onClose)
  close.current = onClose

  useEffect(() => {
    if (!open) return

    const onKey = (event) => {
      if (event.key === 'Escape') close.current()
    }
    window.addEventListener('keydown', onKey)

    const previous = document.body.style.overflow
    const returnTo = document.activeElement
    document.body.style.overflow = 'hidden'
    ref.current?.focus()

    return () => {
      window.removeEventListener('keydown', onKey)
      document.body.style.overflow = previous
      if (returnTo instanceof HTMLElement) returnTo.focus()
    }
  }, [open])

  return ref
}