import { useEffect, useState } from 'react'
import { api } from '../api'
import { Badge, Button, Toggle } from './Primitives'

// Settings, in a panel over the page.
//
// Grouped by whose problem each setting solves. Reading and privacy belong to
// the user. The activity stream belongs to whoever is building or judging this,
// so it sits under its own heading, off by default, and says what it is.

export function SettingsPanel({ open, onClose, settings, set, reset, sessionId, onForget }) {
  const [health, setHealth] = useState(null)
  const [providers, setProviders] = useState(null)
  const [confirmForget, setConfirmForget] = useState(false)

  // Probed when the panel opens rather than on load, so the page does not pay
  // for diagnostics nobody asked to see.
  useEffect(() => {
    if (!open) {
      setConfirmForget(false)
      return
    }
    api.health().then(setHealth).catch(() => setHealth(null))
    api.providers().then(setProviders).catch(() => setProviders(null))
  }, [open])

  useEffect(() => {
    if (!open) return
    const onKey = (event) => event.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-40">
      <button
        aria-label="Close settings"
        onClick={onClose}
        className="absolute inset-0 bg-ink/25"
      />

      <aside
        role="dialog"
        aria-modal="true"
        aria-label="Settings"
        className="absolute right-0 top-0 flex h-full w-full max-w-sm flex-col border-l border-line bg-surface shadow-xl"
      >
        <header className="flex items-center justify-between border-b border-line px-5 py-4">
          <h2 className="text-[15px] font-semibold tracking-tight">Settings</h2>
          <button
            onClick={onClose}
            aria-label="Close settings"
            className="rounded-lg px-2 py-1 text-[13px] text-muted hover:bg-canvas hover:text-ink"
          >
            Close
          </button>
        </header>

        <div className="flex-1 overflow-y-auto px-5 py-2">
          <Section title="Reading">
            <Toggle
              label="Larger text"
              hint="Increases the type size across the whole app."
              checked={settings.largeText}
              onChange={(v) => set('largeText', v)}
            />
          </Section>

          <Section title="Privacy">
            <Toggle
              label="Stay signed in to this session"
              hint="Keeps your policy on this device so a reload does not lose it. Turn off on a shared or borrowed phone."
              checked={settings.rememberSession}
              onChange={(v) => set('rememberSession', v)}
            />

            {sessionId && (
              <div className="border-t border-line pt-3">
                <p className="text-[12px] leading-relaxed text-muted">
                  Your policy, the hospitals found for you and any pages read
                  from your document are held against this session and removed
                  when you forget it.
                </p>
                <p className="mt-1.5 font-mono text-[11px] text-muted">
                  {sessionId}
                </p>
                {confirmForget ? (
                  <div className="mt-3 flex flex-wrap gap-2">
                    <Button
                      onClick={() => {
                        setConfirmForget(false)
                        onForget()
                      }}
                    >
                      Yes, forget everything
                    </Button>
                    <Button variant="secondary" onClick={() => setConfirmForget(false)}>
                      Keep it
                    </Button>
                  </div>
                ) : (
                  <Button
                    variant="secondary"
                    className="mt-3"
                    onClick={() => setConfirmForget(true)}
                  >
                    Forget this session and start over
                  </Button>
                )}
              </div>
            )}
          </Section>

          <Section
            title="Developer"
            note="Diagnostics. Nothing here changes what the app calculates."
          >
            <Toggle
              label="Show the activity panel"
              hint="A live feed of every pipeline step as it runs, with timings. The same events the server writes to its log."
              checked={settings.showActivity}
              onChange={(v) => set('showActivity', v)}
            />

            <div className="border-t border-line pt-3 text-[12px]">
              <Row label="API">
                {health ? (
                  <Badge tone="good">reachable</Badge>
                ) : (
                  <Badge tone="bad">unreachable</Badge>
                )}
              </Row>
              {health && (
                <>
                  <Row label="Hospital data">
                    {health.dataset_built ? (
                      <Badge tone="good">built</Badge>
                    ) : (
                      <Badge tone="warn">not built</Badge>
                    )}
                  </Row>
                  <Row label="Session storage">
                    <span className="text-muted">{health.session_store}</span>
                  </Row>
                  <Row label="Sessions held">
                    <span className="tabular-nums text-muted">
                      {health.active_sessions}
                    </span>
                  </Row>
                  {health.page_image_bytes > 0 && (
                    <Row label="Page images on disk">
                      <span className="tabular-nums text-muted">
                        {(health.page_image_bytes / 1024 / 1024).toFixed(1)} MB
                      </span>
                    </Row>
                  )}
                </>
              )}
            </div>

            {providers && (
              <div className="border-t border-line pt-3">
                <p className="text-[12px] font-medium text-muted">Models in use</p>
                {providers.llm_available ? (
                  <div className="mt-1.5 space-y-1">
                    {Object.entries(providers.roles ?? {}).map(([role, model]) => (
                      <Row key={role} label={role.replace(/_/g, ' ')}>
                        <span className="font-mono text-[11px] text-muted">
                          {model || 'unavailable'}
                        </span>
                      </Row>
                    ))}
                  </div>
                ) : (
                  <p className="mt-1.5 text-[12px] leading-relaxed text-muted">
                    No language model is reachable. The app is running on its
                    rule-based extractor alone, which is a supported mode and
                    not an error.
                  </p>
                )}
              </div>
            )}
          </Section>

          <div className="border-t border-line py-4">
            <Button variant="secondary" onClick={reset}>
              Reset settings to defaults
            </Button>
          </div>
        </div>
      </aside>
    </div>
  )
}

function Section({ title, note, children }) {
  return (
    <section className="border-b border-line py-3 last:border-0">
      <h3 className="text-[12px] font-semibold uppercase tracking-wide text-muted">
        {title}
      </h3>
      {note && <p className="mt-1 text-[12px] leading-relaxed text-muted">{note}</p>}
      <div className="mt-1">{children}</div>
    </section>
  )
}

function Row({ label, children }) {
  return (
    <div className="flex items-center justify-between gap-3 py-1">
      <span className="capitalize text-muted">{label}</span>
      {children}
    </div>
  )
}
