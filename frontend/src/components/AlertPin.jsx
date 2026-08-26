import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { useT } from '../hooks/useLanguage'
import { readable } from '../lib/i18n'

// An alert, pinned to the thing it is about.
//
// Alerts used to be a stack of cards down the middle of the page, which put
// "your room costs more than your cover" a long way from the figure it was
// explaining and made the column they sat in the loudest part of a screen
// somebody reads when they are already worried. A mark beside the number
// instead: it is the same colour it always was, it is next to the thing that
// is wrong, and it says nothing until it is asked.
//
// The panel is rendered into the body rather than beside the mark. Both
// columns it can be pinned inside scroll within themselves, and anything
// positioned inside a scrolling box is cut off at its edge.

const TONE = {
  urgent: {
    mark: 'border-danger/40 bg-danger-soft text-danger ring-2 ring-danger/15',
    edge: 'border-danger/25 bg-danger-soft',
    text: 'text-danger',
  },
  attention: {
    mark: 'border-warn/40 bg-warn-soft text-warn',
    edge: 'border-warn/25 bg-warn-soft',
    text: 'text-warn',
  },
  info: {
    mark: 'border-line bg-canvas text-muted',
    edge: 'border-line bg-canvas',
    text: 'text-ink',
  },
}

const RANK = { urgent: 3, attention: 2, info: 1 }

// Wide enough for a sentence, narrow enough for a phone. Held here as a
// number because the placement has to know it before the panel exists.
const PANEL = 320
const EDGE = 8
// Below the mark unless there is less room than this, in which case above it.
// A height rather than the panel's own, which cannot be known until it has
// been laid out somewhere.
const ROOM_BELOW = 220

export function AlertPin({ alerts, action, className = '' }) {
  const t = useT()
  const [open, setOpen] = useState(false)
  const markRef = useRef(null)
  const panelRef = useRef(null)
  const at = useAnchored(open, markRef)

  useEffect(() => {
    if (!open) return
    const away = (event) => {
      if (markRef.current?.contains(event.target)) return
      if (panelRef.current?.contains(event.target)) return
      setOpen(false)
    }
    const key = (event) => { if (event.key === 'Escape') setOpen(false) }
    document.addEventListener('mousedown', away)
    document.addEventListener('keydown', key)
    return () => {
      document.removeEventListener('mousedown', away)
      document.removeEventListener('keydown', key)
    }
  }, [open])

  if (!alerts?.length) return null

  const worst = alerts
    .map((alert) => alert.severity)
    .sort((a, b) => (RANK[b] ?? 0) - (RANK[a] ?? 0))[0]
  const tone = TONE[worst] ?? TONE.info

  return (
    <>
      <button
        ref={markRef}
        type="button"
        aria-haspopup="dialog"
        aria-expanded={open}
        aria-label={t('journey.alert.open', 'Something needs your attention')}
        title={t('journey.alert.open', 'Something needs your attention')}
        onClick={() => setOpen((was) => !was)}
        className={`inline-flex h-[1.375rem] shrink-0 items-center justify-center gap-1 rounded-full border px-1.5 text-[0.6875rem] font-bold leading-none transition hover:brightness-95 ${tone.mark} ${className}`}
      >
        <span aria-hidden="true">!</span>
        {alerts.length > 1 && (
          <span className="tabular-nums">{alerts.length}</span>
        )}
      </button>

      {open && at && createPortal(
        <div
          ref={panelRef}
          role="dialog"
          aria-label={t('journey.alert.open', 'Something needs your attention')}
          style={{ ...at, width: at.width }}
          className="fixed z-50 overflow-y-auto overscroll-contain rounded-xl border border-line bg-surface shadow-xl motion-safe:animate-fade"
        >
          <div className="divide-y divide-line">
            {alerts.map((alert, index) => {
              const style = TONE[alert.severity] ?? TONE.info
              return (
                <div key={index} className={`px-4 py-3.5 ${style.edge}`}>
                  <div className="flex items-start justify-between gap-3">
                    <h3 className={`text-[0.875rem] font-semibold leading-snug ${style.text}`}>
                      {t(`alert.${alert.key}`, alert.title, readable(t, alert.values))}
                    </h3>
                    {alert.amount_display && (
                      <span className={`shrink-0 text-[0.875rem] font-semibold tabular-nums ${style.text}`}>
                        {alert.amount_display}
                      </span>
                    )}
                  </div>
                  <p className="mt-1.5 text-[0.8125rem] leading-relaxed">
                    {t(`alert.${alert.key}.msg`, alert.message, readable(t, alert.values))}
                  </p>
                  {alert.action && (
                    <p className="mt-2 text-[0.8125rem] font-medium leading-relaxed">
                      &rarr; {t(`alert.${alert.key}.do`, alert.action, readable(t, alert.values))}
                    </p>
                  )}
                  {action?.(alert)}
                </div>
              )
            })}
          </div>
        </div>,
        document.body
      )}
    </>
  )
}

// Where the panel goes, in viewport coordinates, kept in step with anything
// that scrolls underneath it. `capture` on the scroll listener because the
// column the mark sits in is itself a scrolling box, and a scroll inside it
// does not reach the window otherwise.
function useAnchored(open, markRef) {
  const [at, setAt] = useState(null)

  useLayoutEffect(() => {
    if (!open) {
      setAt(null)
      return
    }
    const place = () => {
      const mark = markRef.current?.getBoundingClientRect()
      if (!mark) return
      const width = Math.min(PANEL, window.innerWidth - EDGE * 2)
      const left = Math.min(
        Math.max(EDGE, mark.left + mark.width / 2 - width / 2),
        window.innerWidth - width - EDGE
      )
      const below = window.innerHeight - mark.bottom
      setAt(
        below >= ROOM_BELOW
          ? { left, top: mark.bottom + EDGE, maxHeight: below - EDGE * 2, width }
          : {
              left,
              bottom: window.innerHeight - mark.top + EDGE,
              maxHeight: mark.top - EDGE * 2,
              width,
            }
      )
    }
    place()
    window.addEventListener('scroll', place, true)
    window.addEventListener('resize', place)
    return () => {
      window.removeEventListener('scroll', place, true)
      window.removeEventListener('resize', place)
    }
  }, [open, markRef])

  return at
}