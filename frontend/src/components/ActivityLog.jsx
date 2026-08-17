import { useEffect, useRef, useState } from 'react'
import { Badge } from './Primitives'

// Live view of what the server is doing, fed by the same PipelineEvent objects
// written to the server log. Nothing here is reconstructed or narrated on the
// client, so the panel cannot drift from what actually happened.

const STATUS_TONE = {
  started: 'neutral',
  ok: 'good',
  warn: 'warn',
  failed: 'bad',
  skipped: 'neutral',
}

const STATUS_MARK = {
  started: '·',
  ok: '✓',
  warn: '!',
  failed: '✕',
  skipped: '–',
}

function formatDetail(detail) {
  return Object.entries(detail || {})
    .filter(([, value]) => value !== null && value !== undefined && value !== '')
    .slice(0, 6)
    .map(([key, value]) => {
      const shown = Array.isArray(value)
        ? value.slice(0, 3).join(', ')
        : typeof value === 'number'
          ? Number.isInteger(value) ? value : value.toFixed(2)
          : String(value)
      return `${key.replace(/_/g, ' ')}: ${shown}`
    })
}

export function ActivityLog({ events, connected }) {
  const [expanded, setExpanded] = useState(null)
  const scrollRef = useRef(null)
  const pinnedToBottom = useRef(true)

  // Follow new events only while the user is already at the bottom; yanking the
  // view while they are reading an earlier step would be hostile.
  useEffect(() => {
    const node = scrollRef.current
    if (node && pinnedToBottom.current) node.scrollTop = node.scrollHeight
  }, [events])

  function handleScroll(event) {
    const { scrollTop, scrollHeight, clientHeight } = event.currentTarget
    pinnedToBottom.current = scrollHeight - scrollTop - clientHeight < 40
  }

  return (
    <div className="flex h-full flex-col">
      <header className="flex items-center justify-between border-b border-line px-4 py-3">
        <div>
          <h2 className="text-[13px] font-semibold">Activity</h2>
          <p className="text-[11px] text-muted">Every step the system takes</p>
        </div>
        <span className="flex items-center gap-1.5 text-[11px] text-muted">
          <span
            className={`h-1.5 w-1.5 rounded-full ${connected ? 'bg-brand' : 'bg-line'}`}
          />
          {connected ? 'live' : 'idle'}
        </span>
      </header>

      <div
        ref={scrollRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto px-2 py-2"
      >
        {events.length === 0 && (
          <p className="px-2 py-6 text-center text-[12px] text-muted">
            Steps will appear here as your policy is read.
          </p>
        )}

        <ol className="space-y-0.5">
          {events.map((event) => {
            const details = formatDetail(event.detail)
            const isOpen = expanded === event.id
            return (
              <li key={event.id}>
                <button
                  onClick={() => setExpanded(isOpen ? null : event.id)}
                  className="w-full rounded-md px-2 py-1.5 text-left hover:bg-canvas"
                >
                  <div className="flex items-baseline gap-2">
                    <span
                      className={`w-3 shrink-0 text-center text-[11px] ${
                        event.status === 'failed'
                          ? 'text-danger'
                          : event.status === 'warn'
                            ? 'text-warn'
                            : event.status === 'ok'
                              ? 'text-brand'
                              : 'text-muted'
                      }`}
                    >
                      {STATUS_MARK[event.status] ?? '·'}
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className="block truncate text-[12px] leading-snug">
                        {event.summary || event.step.replace(/_/g, ' ')}
                      </span>
                      <span className="mt-0.5 block text-[10px] uppercase tracking-wide text-muted">
                        {event.stage_label}
                        {event.duration_ms != null &&
                          ` · ${event.duration_ms < 1000
                            ? `${Math.round(event.duration_ms)}ms`
                            : `${(event.duration_ms / 1000).toFixed(1)}s`}`}
                      </span>
                    </span>
                  </div>
                </button>

                {isOpen && details.length > 0 && (
                  <dl className="mb-1 ml-7 rounded-md bg-canvas px-2.5 py-2 text-[11px] text-muted">
                    {details.map((line) => (
                      <div key={line} className="truncate">{line}</div>
                    ))}
                  </dl>
                )}
              </li>
            )
          })}
        </ol>
      </div>

      {events.length > 0 && (
        <footer className="border-t border-line px-4 py-2 text-[11px] text-muted">
          {events.length} step{events.length === 1 ? '' : 's'}
          {events.some((e) => e.status === 'warn') && (
            <Badge tone="warn">
              {events.filter((e) => e.status === 'warn').length} need attention
            </Badge>
          )}
        </footer>
      )}
    </div>
  )
}
