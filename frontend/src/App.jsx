import { useCallback, useEffect, useRef, useState } from 'react'
import { api, subscribeToEvents } from './api'
import { ActivityLog } from './components/ActivityLog'
import { Journey } from './components/Journey'
import { PolicySummary } from './components/PolicySummary'
import { Results, SearchPanel } from './components/Results'
import { Button, ErrorNote, Spinner } from './components/Primitives'
import { SettingsPanel } from './components/Settings'
import { UploadStep } from './components/UploadStep'
import { STEPS, stepIndex, useRoute } from './hooks/useRoute'
import { rememberSession, rememberedSession, useSettings } from './hooks/useSettings'

const DEFAULT_SEARCH = {
  procedure_code: '',
  city: 'Bengaluru',
  max_distance_km: 15,
  preference: 'balanced',
  urgency: 'planned',
}

export default function App() {
  const { settings, set, reset } = useSettings()
  const { route, go, replace } = useRoute()

  const [reference, setReference] = useState(null)
  const [session, setSession] = useState(null)
  const [policy, setPolicy] = useState(null)
  const [results, setResults] = useState(null)
  const [journey, setJourney] = useState(null)
  const [search, setSearch] = useState(DEFAULT_SEARCH)

  const [busy, setBusy] = useState(null)
  const [error, setError] = useState(null)
  const [restoring, setRestoring] = useState(Boolean(rememberedSession()))
  const [settingsOpen, setSettingsOpen] = useState(false)

  const [events, setEvents] = useState([])
  const [connected, setConnected] = useState(false)

  const unsubscribe = useRef(null)

  // One event stream per session, opened as soon as a session exists so the
  // very first pipeline steps are captured rather than missed.
  const connect = useCallback((sessionId, { fresh = true } = {}) => {
    unsubscribe.current?.()
    if (fresh) setEvents([])
    unsubscribe.current = subscribeToEvents(sessionId, (event) => {
      setConnected(true)
      setEvents((current) =>
        current.some((e) => e.id === event.id) ? current : [...current, event]
      )
    })
  }, [])

  useEffect(() => () => unsubscribe.current?.(), [])

  useEffect(() => {
    api.reference().then(setReference).catch((e) => setError(e.message))
  }, [])

  // Put the interface back the way it was left. The browser only ever holds a
  // session id; everything else is re-read from the server, so a stale tab
  // cannot show figures that no longer exist behind it.
  useEffect(() => {
    const stored = rememberedSession()
    if (!stored) return
    if (!settings.rememberSession) {
      rememberSession(null)
      setRestoring(false)
      return
    }

    let cancelled = false
    api
      .restore(stored)
      .then((state) => {
        if (cancelled) return
        setSession(stored)
        if (state.policy) setPolicy(state.policy)
        if (state.search) setResults(state.search)
        if (state.journey) setJourney(state.journey)
        if (state.search_context) {
          setSearch((current) => ({
            ...current,
            procedure_code: state.search_context.procedure_code ?? current.procedure_code,
            city: state.search_context.city || current.city,
            max_distance_km: state.search_context.max_distance_km ?? current.max_distance_km,
            preference: state.search_context.preference ?? current.preference,
            urgency: state.search_context.urgency ?? current.urgency,
          }))
        }
        connect(stored)
      })
      .catch(() => {
        // The session expired or the server was rebuilt. Nothing to recover,
        // and saying so would only alarm someone who just opened the page.
        if (!cancelled) rememberSession(null)
      })
      .finally(() => !cancelled && setRestoring(false))

    return () => {
      cancelled = true
    }
    // Runs once: this is a restore, not a subscription to settings changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const reachable = {
    upload: true,
    policy: Boolean(policy),
    search: Boolean(policy),
    journey: Boolean(journey),
  }

  // Keep the URL honest. Someone can type or bookmark any step, and landing on
  // one that has nothing behind it should send them where the work starts.
  useEffect(() => {
    if (restoring) return
    if (!reachable[route]) replace(policy ? 'policy' : 'upload')
  }, [route, restoring, policy, journey, replace]) // eslint-disable-line react-hooks/exhaustive-deps

  async function run(name, work) {
    setBusy(name)
    setError(null)
    try {
      return await work()
    } catch (e) {
      setError(e.message)
      return null
    } finally {
      setBusy(null)
    }
  }

  function adopt(result) {
    setSession(result.session_id)
    if (settings.rememberSession) rememberSession(result.session_id)
    connect(result.session_id)
    setPolicy(result)
    setResults(null)
    setJourney(null)
    go('policy')
  }

  async function handleUpload(file, insurerId) {
    const result = await run('upload', () => api.uploadPolicy(file, insurerId))
    if (result) adopt(result)
  }

  async function handleManual(payload) {
    const result = await run('upload', () => api.manualPolicy(payload))
    if (result) adopt(result)
  }

  async function handleAnswer(questionId, answer) {
    const result = await run('answer', () => api.answer(session, questionId, answer))
    if (result) setPolicy(result)
  }

  async function handleSearch() {
    const city = reference?.cities?.find((c) => c.city === search.city)
    const result = await run('search', () =>
      api.search(session, {
        procedure_code: search.procedure_code,
        lat: city?.lat ?? 12.9716,
        lon: city?.lon ?? 77.5946,
        city: search.city,
        max_distance_km: Number(search.max_distance_km),
        preference: search.preference,
        urgency: search.urgency,
      })
    )
    if (result) setResults(result)
  }

  async function handleStartJourney(option) {
    const result = await run('journey', () =>
      api.startJourney(session, {
        hospital_id: option.hospital.id,
        procedure_code: search.procedure_code,
        room_category: option.room.category,
      })
    )
    if (result) {
      setJourney(result)
      go('journey')
    }
  }

  const journeyAction = (work) => async (...args) => {
    const result = await run('journey', () => work(...args))
    if (result) setJourney(result)
  }

  async function startOver({ forget = false } = {}) {
    if (forget && session) {
      // Best effort: the interface resets either way, and a failed delete
      // should not strand someone on a screen they asked to leave.
      await api.clear(session).catch(() => {})
    }
    unsubscribe.current?.()
    unsubscribe.current = null
    rememberSession(null)
    setSession(null)
    setPolicy(null)
    setResults(null)
    setJourney(null)
    setSearch(DEFAULT_SEARCH)
    setEvents([])
    setConnected(false)
    setError(null)
    setSettingsOpen(false)
    go('upload')
  }

  const shell = {
    events,
    connected,
    settings,
    onOpenSettings: () => setSettingsOpen(true),
    route,
    go,
    reachable,
    onStartOver: () => startOver(),
    hasSession: Boolean(session),
  }

  if (restoring) {
    return (
      <Shell {...shell}>
        <div className="flex justify-center py-24">
          <Spinner label="Picking up where you left off" />
        </div>
      </Shell>
    )
  }

  return (
    <>
      <Shell {...shell}>
        {route === 'upload' ? (
          <UploadStep
            reference={reference}
            onUploaded={handleUpload}
            onManual={handleManual}
            busy={busy === 'upload'}
            error={error}
            onClearError={() => setError(null)}
          />
        ) : (
          <div className="mx-auto max-w-3xl space-y-5 py-6">
            <ErrorNote onDismiss={() => setError(null)}>{error}</ErrorNote>

            {route === 'policy' && policy && (
              <>
                <BackLink onClick={() => go('upload')}>
                  Use a different policy
                </BackLink>
                <PolicySummary
                  policy={policy}
                  onAnswer={handleAnswer}
                  onContinue={() => go('search')}
                  answering={busy === 'answer'}
                />
              </>
            )}

            {route === 'search' && (
              <>
                <BackLink onClick={() => go('policy')}>Back to your cover</BackLink>
                <SearchPanel
                  reference={reference}
                  value={search}
                  onChange={setSearch}
                  onSearch={handleSearch}
                  busy={busy === 'search'}
                />
                <Results
                  results={results}
                  onStartJourney={handleStartJourney}
                  starting={busy === 'journey'}
                />
              </>
            )}

            {route === 'journey' && (
              <>
                <BackLink onClick={() => go('search')}>Back to hospitals</BackLink>
                <Journey
                  journey={journey}
                  busy={busy === 'journey'}
                  onAdvance={journeyAction((stage) => api.advance(session, stage))}
                  onRecordCost={journeyAction((payload) => api.recordCost(session, payload))}
                  onFilePreauth={journeyAction(() => api.filePreauth(session))}
                />
              </>
            )}
          </div>
        )}
      </Shell>

      <SettingsPanel
        open={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        settings={settings}
        set={set}
        reset={reset}
        sessionId={session}
        onForget={() => startOver({ forget: true })}
      />
    </>
  )
}

function BackLink({ onClick, children }) {
  return (
    <button
      onClick={onClick}
      className="inline-flex items-center gap-1.5 text-[13px] text-muted transition hover:text-brand"
    >
      <span aria-hidden="true">&larr;</span>
      {children}
    </button>
  )
}

function Shell({
  children, events, connected, settings, onOpenSettings,
  route, go, reachable, onStartOver, hasSession,
}) {
  const showActivity = settings.showActivity

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-20 border-b border-line bg-surface/95 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-3 px-4 py-3">
          <button
            onClick={onStartOver}
            className="flex items-baseline gap-2.5 text-left"
            title="Start again"
          >
            <span className="text-[15px] font-semibold tracking-tight">CoverPath</span>
            <span className="hidden text-[12px] text-muted lg:inline">
              Know what your hospital stay will cost
            </span>
          </button>

          <div className="flex items-center gap-2">
            {showActivity && events.length > 0 && (
              <span className="hidden text-[11px] text-muted sm:inline">
                {events.length} steps
              </span>
            )}
            {hasSession && (
              <Button variant="secondary" onClick={onStartOver}>
                Start over
              </Button>
            )}
            <button
              onClick={onOpenSettings}
              aria-label="Settings"
              title="Settings"
              className="rounded-lg border border-line px-3 py-2 text-[13px] text-muted transition hover:bg-canvas hover:text-ink"
            >
              <GearIcon />
            </button>
          </div>
        </div>

        <StepNav route={route} go={go} reachable={reachable} />
      </header>

      <div className="mx-auto flex max-w-6xl gap-5 px-4">
        <main className="min-w-0 flex-1">{children}</main>

        {showActivity && (
          <aside className="sticky top-[104px] hidden h-[calc(100vh-104px)] w-80 shrink-0 border-l border-line bg-surface lg:block">
            <ActivityLog events={events} connected={connected} />
          </aside>
        )}
      </div>

      {showActivity && (
        <div className="border-t border-line bg-surface lg:hidden">
          <div className="h-72">
            <ActivityLog events={events} connected={connected} />
          </div>
        </div>
      )}
    </div>
  )
}

// The step bar doubles as navigation and as a sense of place. A step already
// visited stays clickable, because comparing what you were shown at one step
// against another is the whole reason someone would move backwards here.
function StepNav({ route, go, reachable }) {
  const current = stepIndex(route)

  return (
    <nav aria-label="Progress" className="border-t border-line">
      <ol className="mx-auto flex max-w-6xl items-stretch gap-1 px-2">
        {STEPS.map((step, index) => {
          const isCurrent = step.id === route
          const isDone = index < current && reachable[step.id]
          const enabled = reachable[step.id]

          return (
            <li key={step.id} className="min-w-0 flex-1">
              <button
                disabled={!enabled}
                aria-current={isCurrent ? 'step' : undefined}
                onClick={() => go(step.id)}
                className={`flex w-full items-center justify-center gap-1.5 border-b-2 px-2 py-2.5 text-[12px] font-medium transition ${
                  isCurrent
                    ? 'border-brand text-brand'
                    : enabled
                      ? 'border-transparent text-muted hover:text-ink'
                      : 'cursor-not-allowed border-transparent text-muted/40'
                }`}
              >
                <span
                  className={`flex h-4.5 w-4.5 shrink-0 items-center justify-center rounded-full text-[10px] ${
                    isCurrent
                      ? 'bg-brand text-white'
                      : isDone
                        ? 'bg-brand-soft text-brand'
                        : 'bg-canvas text-muted'
                  }`}
                >
                  {isDone ? '✓' : index + 1}
                </span>
                <span className="truncate sm:hidden">{step.short}</span>
                <span className="hidden truncate sm:inline">{step.label}</span>
              </button>
            </li>
          )
        })}
      </ol>
    </nav>
  )
}

function GearIcon() {
  return (
    <svg
      width="16" height="16" viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="2" strokeLinecap="round"
      strokeLinejoin="round" aria-hidden="true"
    >
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
    </svg>
  )
}
