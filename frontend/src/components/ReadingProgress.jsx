import { useEffect, useState } from 'react'
import { useT } from '../hooks/useLanguage'
import { clock, humanDuration, progressOf } from '../lib/progress'

// What the system is doing, while it does it.
//
// Reading a policy is the slowest thing here and the one moment the user is
// certainly waiting on us, and until now the only thing on screen was a
// spinner and a sentence guessing at how long it would take. A phone photo of
// a forty-page wording is a minute of work; a spinner for a minute reads as a
// hang.
//
// So the same events that fill the activity log fill this, grouped into the
// five things that actually happen, one after another. Every line is an event
// the server sent. Nothing advances on a timer, which is the point: when a
// step is slow, this shows a slow step rather than a bar that keeps moving.

export function ReadingProgress({ events, phases, title, hint, waiting }) {
  const t = useT()
  const elapsed = useElapsed()
  const { phases: rows, document, started, failed } = progressOf(events, phases)

  return (
    <div className="rounded-xl border border-line bg-canvas motion-safe:animate-rise">
      <div className="h-0.5 overflow-hidden rounded-t-xl bg-brand-soft">
        <div className="h-full w-2/5 rounded-full bg-brand/70 motion-safe:animate-sweep" />
      </div>

      <div className="flex items-baseline justify-between gap-3 px-4 pt-3">
        <h3 className="text-[0.875rem] font-semibold">{title}</h3>
        <span className="shrink-0 font-mono text-[0.75rem] tabular-nums text-muted">
          {clock(elapsed)}
        </span>
      </div>

      {document && (
        <p className="px-4 pt-1 text-[0.75rem] text-muted">
          {t('reading.document', 'Document {index} of {total}', {
            index: document.index, total: document.total,
          })}
          {document.name ? ` · ${document.name}` : ''}
        </p>
      )}

      <ol className="space-y-0 px-4 py-3">
        {rows.map((row, index) => (
          <Row key={row.key} row={row} last={index === rows.length - 1} t={t} />
        ))}
      </ol>

      <p className="border-t border-line px-4 py-2.5 text-[0.75rem] leading-relaxed text-muted">
        {failed
          ? failed
          : started
            ? hint
            : waiting || t('reading.starting', 'Starting.')}
      </p>
    </div>
  )
}

// The thread down the left with a knot on each step. The knot is the state:
// filled and ticked once done, ringed and breathing while it is the one being
// worked on, hollow until then.
function Row({ row, last, t }) {
  const done = row.state === 'done'
  const active = row.state === 'active'
  const note = row.note ? t(row.note.key, row.note.english, row.note.values) : ''

  return (
    <li className="flex gap-3">
      <div className="flex flex-col items-center">
        <span className="relative flex h-4 w-4 shrink-0 items-center justify-center">
          {active && (
            <span className="absolute inset-0 rounded-full bg-brand/25 motion-safe:animate-breathe" />
          )}
          <span
            className={`relative flex h-3.5 w-3.5 items-center justify-center rounded-full border text-[0.5rem] leading-none transition ${
              done
                ? 'border-brand bg-brand text-on-brand'
                : active
                  ? 'border-brand bg-surface'
                  : 'border-line bg-surface'
            }`}
          >
            {done ? '✓' : ''}
          </span>
        </span>
        {!last && (
          <span
            className={`w-px flex-1 transition-colors ${done ? 'bg-brand/40' : 'bg-line'}`}
          />
        )}
      </div>

      <div className={`min-w-0 flex-1 ${last ? 'pb-0' : 'pb-3'}`}>
        <div className="flex items-baseline justify-between gap-3">
          <span
            className={`text-[0.8125rem] leading-snug ${
              active ? 'font-medium text-ink' : done ? 'text-muted' : 'text-muted/60'
            }`}
          >
            {t(row.name, row.label)}
          </span>
          {done && row.ms > 0 && (
            <span className="shrink-0 font-mono text-[0.6875rem] tabular-nums text-muted/70">
              {humanDuration(row.ms)}
            </span>
          )}
        </div>

        {active && row.fraction && (
          <div className="mt-1.5 flex items-center gap-2">
            <div className="h-1 flex-1 overflow-hidden rounded-full bg-line">
              <div
                className="h-full rounded-full bg-brand transition-[width] duration-500 ease-out"
                style={{ width: `${(row.fraction.done / row.fraction.total) * 100}%` }}
              />
            </div>
            <span className="shrink-0 text-[0.6875rem] tabular-nums text-muted">
              {t(row.fraction.name, row.fraction.label, {
                done: row.fraction.done, total: row.fraction.total,
              })}
            </span>
          </div>
        )}

        {active && note && (
          // Keyed on the text so each new line fades in rather than swapping.
          <p
            key={note}
            className="mt-1 truncate text-[0.75rem] text-muted motion-safe:animate-fade"
          >
            {note}
          </p>
        )}
      </div>
    </li>
  )
}

// Seconds since this appeared. Worth showing: someone who knows it has been
// forty seconds waits differently from someone who does not.
function useElapsed() {
  const [seconds, setSeconds] = useState(0)
  useEffect(() => {
    const id = setInterval(() => setSeconds((n) => n + 1), 1000)
    return () => clearInterval(id)
  }, [])
  return seconds
}