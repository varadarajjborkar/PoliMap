import { useEffect, useState } from 'react'
import { api } from '../api'
import { useDialog } from '../hooks/useDialog'
import { useT } from '../hooks/useLanguage'
import { LANGUAGES } from '../lib/i18n'
import { Badge, Button, Toggle } from './Primitives'

// Settings, in a panel over the page.
//
// Grouped by whose problem each setting solves. Reading and privacy belong to
// the user. The activity stream belongs to whoever is building or judging this,
// so it sits under its own heading, off by default, and says what it is.

// Written out rather than derived from the role name, so that "vision_ocr"
// does not render as "Vision Ocr".
const ROLE_LABELS = {
  extract: 'Extract',
  challenge: 'Challenge',
  adjudicate: 'Adjudicate',
  vision_ocr: 'Vision OCR',
  narrate: 'Narrate',
}

export function SettingsPanel({ open, onClose, settings, set, reset, sessionId, onForget }) {
  const [health, setHealth] = useState(null)
  const [providers, setProviders] = useState(null)
  const [confirmForget, setConfirmForget] = useState(false)
  const t = useT()

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

  const panel = useDialog(open, onClose)

  if (!open) return null

  return (
    <div className="fixed inset-0 z-40">
      <button
        aria-label="Close settings"
        onClick={onClose}
        className="absolute inset-0 bg-ink/25"
      />

      <aside
        ref={panel}
        tabIndex={-1}
        role="dialog"
        aria-modal="true"
        aria-label="Settings"
        className="absolute right-0 top-0 flex h-full w-full max-w-sm flex-col border-l border-line bg-surface shadow-xl outline-none"
      >
        <header className="flex items-center justify-between border-b border-line px-5 py-4">
          <h2 className="text-[0.9375rem] font-semibold tracking-tight">Settings</h2>
          <button
            onClick={onClose}
            aria-label="Close settings"
            className="rounded-lg px-2 py-1 text-[0.875rem] text-muted hover:bg-canvas hover:text-ink"
          >
            Close
          </button>
        </header>

        <div className="flex-1 overflow-y-auto px-5 py-2">
          {/* First, because somebody who cannot read the rest of this panel
              cannot reach it if it is at the bottom. Each language is written
              in its own script rather than in English: a person looking for
              Kannada is looking for the word ಕನ್ನಡ. */}
          <Section title={t('settings.language', 'Language')}>
            <Choice
              label={t('settings.language', 'Language')}
              hint={t(
                'settings.language.hint',
                'This changes the app\u2019s own words. Anything read out of your ' +
                  'policy stays in the language the document is written in.'
              )}
              value={settings.language}
              onChange={(v) => set('language', v)}
              wrap
              options={LANGUAGES.map((language) => ({
                value: language.code,
                label: language.endonym,
              }))}
            />
          </Section>

          <Section title={t('settings.theme', 'Appearance')}>
            <Choice
              label="Theme"
              hint="System follows your phone or computer."
              value={settings.theme}
              onChange={(v) => set('theme', v)}
              options={[
                { value: 'light', label: 'Light' },
                { value: 'dark', label: 'Dark' },
                { value: 'system', label: 'System' },
              ]}
            />
            <Choice
              label={t('settings.text_size', 'Text size')}
              hint="Larger type throughout, for reading on a phone in a hurry."
              value={settings.textSize}
              onChange={(v) => set('textSize', v)}
              options={[
                { value: 'default', label: 'Default' },
                { value: 'large', label: 'Large' },
              ]}
            />
          </Section>

          {sessionId && (
            <Section title="This session">
              <p className="pt-1 text-[0.8125rem] leading-relaxed text-muted">
                Your policy and the hospitals found for you are held only while
                this tab is open. Reloading the page starts over.
              </p>
              {confirmForget ? (
                <div className="mt-3 flex flex-wrap gap-2">
                  <Button
                    onClick={() => {
                      setConfirmForget(false)
                      onForget()
                    }}
                  >
                    Yes, clear it
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
                  Clear and start over
                </Button>
              )}
            </Section>
          )}

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

            <div className="border-t border-line pt-3 text-[0.8125rem]">
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
                <p className="text-[0.8125rem] font-medium text-muted">Models in use</p>
                {providers.llm_available ? (
                  <div className="mt-1.5 space-y-1">
                    {Object.entries(providers.roles ?? {}).map(([role, model]) => (
                      <Row key={role} label={ROLE_LABELS[role] ?? role.replace(/_/g, ' ')}>
                        <span className="font-mono text-[0.75rem] text-muted">
                          {model || 'unavailable'}
                        </span>
                      </Row>
                    ))}
                  </div>
                ) : (
                  <p className="mt-1.5 text-[0.8125rem] leading-relaxed text-muted">
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

// A segmented control rather than a dropdown: the options are few, and seeing
// all of them at once beats opening a menu to find out what they are.
function Choice({ label, hint, value, onChange, options, wrap = false }) {
  return (
    <div className="py-3">
      <span className="block text-[0.875rem] font-medium">{label}</span>
      {hint && (
        <span className="mt-0.5 block text-[0.8125rem] leading-relaxed text-muted">
          {hint}
        </span>
      )}
      <div
        role="radiogroup"
        aria-label={label}
        className={`mt-2 flex gap-1 rounded-lg bg-canvas p-1 ${
          wrap ? 'flex-wrap' : ''
        }`}
      >
        {options.map((option) => (
          <button
            key={option.value}
            role="radio"
            aria-checked={value === option.value}
            onClick={() => onChange(option.value)}
            className={`rounded-md px-3 py-1.5 text-[0.8125rem] font-medium transition ${
              wrap ? '' : 'flex-1'
            } ${
              value === option.value
                ? 'bg-surface text-ink shadow-sm'
                : 'text-muted hover:text-ink'
            }`}
          >
            {option.label}
          </button>
        ))}
      </div>
    </div>
  )
}

function Section({ title, note, children }) {
  return (
    <section className="border-b border-line py-3 last:border-0">
      <h3 className="text-[0.8125rem] font-semibold uppercase tracking-wide text-muted">
        {title}
      </h3>
      {note && <p className="mt-1 text-[0.8125rem] leading-relaxed text-muted">{note}</p>}
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
