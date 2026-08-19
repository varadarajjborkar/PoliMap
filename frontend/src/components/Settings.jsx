import { useCallback, useEffect, useState } from 'react'
import { useDialog } from '../hooks/useDialog'
import { useScreenExit } from '../hooks/useScreenExit'
import { useT } from '../hooks/useLanguage'
import { LANGUAGES } from '../lib/i18n'
import { listTickets } from '../lib/tickets'
import { Button } from './Primitives'

// Settings, in a panel over the page.
//
// Everything here is the reader's own: how the app speaks to them, and what it
// is holding for them. There is no diagnostics section, because a live feed of
// pipeline steps is a thing we want to watch and not a thing anybody using this
// needs offered.
//
// `brief` is the panel before a stay exists. On the sign-in and home screens
// there is no session and no ticket worth listing, so it carries the two
// settings that apply everywhere and stops. Reaching them from the very first
// screen is the point: somebody who cannot read English has to be able to
// change the language before they are asked to type anything.

export function SettingsPanel({
  open, onClose, settings, set, reset, sessionId, onForget, user, brief = false,
}) {
  const [confirmForget, setConfirmForget] = useState(false)
  const [tickets, setTickets] = useState([])
  const t = useT()

  // The drawer has to still be on screen to animate off it, so closing is held
  // for exactly as long as the slide lasts and it unmounts after. Every way out
  // goes through `close`: the backdrop, the header, and the escape key.
  const { leaving, leave, reset: resetExit } = useScreenExit(200)
  const close = useCallback(() => leave(onClose), [leave, onClose])
  const panel = useDialog(open, close)

  useEffect(() => {
    if (!open) {
      setConfirmForget(false)
      return
    }
    // A drawer closed once is still holding the state that closed it, and
    // would open part-way through its own exit.
    resetExit()
    setTickets(listTickets(user))
  }, [open, resetExit, user])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-40">
      <button
        aria-label={t('settings.close', 'Close settings')}
        onClick={close}
        className={`absolute inset-0 bg-ink/25 ${
          leaving ? 'motion-safe:animate-dim-out' : 'motion-safe:animate-fade'
        }`}
      />

      <aside
        ref={panel}
        tabIndex={-1}
        role="dialog"
        aria-modal="true"
        aria-label={t('nav.settings', 'Settings')}
        className={`absolute right-0 top-0 flex h-full w-full max-w-sm flex-col border-l border-line bg-surface shadow-xl outline-none ${
          leaving ? 'motion-safe:animate-slide-out' : 'motion-safe:animate-slide-in'
        }`}
      >
        <header className="flex items-center justify-between border-b border-line px-5 py-4">
          <h2 className="text-[0.9375rem] font-semibold tracking-tight">
            {t('nav.settings', 'Settings')}
          </h2>
          <button
            onClick={close}
            aria-label={t('settings.close', 'Close settings')}
            className="rounded-lg px-2 py-1 text-[0.875rem] text-muted hover:bg-canvas hover:text-ink"
          >
            {t('settings.close.short', 'Close')}
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
                'This changes the app’s own words. Anything read out of your policy ' +
                  'stays as the document wrote it.')}
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
              label={t('settings.theme.label', 'Theme')}
              hint={t('settings.theme.hint', 'System follows your phone or computer.')}
              value={settings.theme}
              onChange={(v) => set('theme', v)}
              options={[
                { value: 'light', label: t('settings.theme.light', 'Light') },
                { value: 'dark', label: t('settings.theme.dark', 'Dark') },
                { value: 'system', label: t('settings.theme.system', 'System') },
              ]}
            />
            <Choice
              label={t('settings.text_size', 'Text size')}
              hint={t(
                'settings.text_size.hint',
                'Larger type throughout, for reading on a phone in a hurry.'
              )}
              value={settings.textSize}
              onChange={(v) => set('textSize', v)}
              options={[
                { value: 'default', label: t('settings.text_size.default', 'Default') },
                { value: 'large', label: t('settings.text_size.large', 'Large') },
              ]}
            />
          </Section>

          {!brief && (
            <Section title={t('settings.tickets', 'Your tickets')}>
              {tickets.length === 0 ? (
                <p className="pt-1 text-[0.8125rem] leading-relaxed text-muted">
                  {t(
                    'settings.tickets.none',
                    'Nothing raised yet. Anything you send from the help desk appears here.')}
                </p>
              ) : (
                <ul className="space-y-2 pt-1">
                  {tickets.map((ticket) => (
                    <TicketRow key={ticket.ticket_id} ticket={ticket} t={t} />
                  ))}
                </ul>
              )}
            </Section>
          )}

          {!brief && sessionId && (
            <Section title={t('settings.session', 'This session')}>
              <p className="pt-1 text-[0.8125rem] leading-relaxed text-muted">
                {t(
                  'settings.session.hint',
                  'Your policy and the hospitals found for you are held only while this ' +
                    'tab is open. Reloading starts over.')}
              </p>
              {confirmForget ? (
                <div className="mt-3 flex flex-wrap gap-2">
                  <Button
                    onClick={() => {
                      setConfirmForget(false)
                      onForget()
                    }}
                  >
                    {t('settings.clear.yes', 'Yes, clear it')}
                  </Button>
                  <Button variant="secondary" onClick={() => setConfirmForget(false)}>
                    {t('settings.clear.no', 'Keep it')}
                  </Button>
                </div>
              ) : (
                <Button
                  variant="secondary"
                  className="mt-3"
                  onClick={() => setConfirmForget(true)}
                >
                  {t('settings.clear', 'Clear and start over')}
                </Button>
              )}
            </Section>
          )}

          {!brief && (
            <div className="border-t border-line py-4">
              <Button variant="secondary" onClick={reset}>
                {t('settings.reset', 'Reset settings to defaults')}
              </Button>
            </div>
          )}
        </div>
      </aside>
    </div>
  )
}

// One ticket, and how far it has got, which is never far.
//
// The stages after the first are drawn as what they are: not started. There is
// no support desk behind this app, and a tracker that crept along on its own
// would be the one dishonest thing in it.
const STAGES = ['received', 'triaged', 'in_progress', 'resolved']

function TicketRow({ ticket, t }) {
  const reached = STAGES.indexOf(ticket.stage)
  return (
    <li className="rounded-lg border border-line bg-canvas px-3 py-2.5">
      <div className="flex items-baseline justify-between gap-2">
        <span className="min-w-0 truncate text-[0.8125rem] font-medium">
          {ticket.subject}
        </span>
        <span className="shrink-0 font-mono text-[0.6875rem] text-muted">
          {ticket.ticket_id}
        </span>
      </div>

      <div className="mt-2 flex items-center gap-1">
        {STAGES.map((stage, index) => (
          <span
            key={stage}
            title={stage.replace(/_/g, ' ')}
            className={`h-1 flex-1 rounded-full ${
              index <= reached ? 'bg-brand' : 'bg-line'
            }`}
          />
        ))}
      </div>

      <p className="mt-1.5 text-[0.6875rem] leading-relaxed text-muted">
        {t('settings.tickets.stage', 'Received')}
        {' · '}
        {new Date(ticket.raised_at).toLocaleDateString('en-IN', {
          day: 'numeric', month: 'short',
        })}
        {' · '}
        {t(
          'settings.tickets.note',
          'nothing is working on it yet, and saying so beats a status that pretends otherwise'
        )}
      </p>
    </li>
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

