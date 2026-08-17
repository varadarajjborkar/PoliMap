import { useCallback, useEffect, useState } from 'react'
import { api, subscribeToEvents } from './api'
import { ActivityLog } from './components/ActivityLog'
import { SignIn, StayList } from './components/HomeScreen'
import { Journey } from './components/Journey'
import { PolicySummary } from './components/PolicySummary'
import { Results, SearchPanel } from './components/Results'
import { Button, ErrorNote, Spinner } from './components/Primitives'
import { SettingsPanel } from './components/Settings'
import { UploadStep } from './components/UploadStep'
import {
  SETUP_STEPS, TRACK_STEP, stayPath, stepIndex, useRoute,
} from './hooks/useRoute'
import { useSettings } from './hooks/useSettings'
import { useStay } from './hooks/useStay'
import {
  clearUser, deleteAllStays, deleteStay, listStays, newStayId,
  readUser, saveStay, writeUser,
} from './lib/stays'

// The server replays at most 500 events to a new subscriber, so holding more
// than this only grows an array nobody scrolls back through.
const MAX_EVENTS = 400

const DEFAULT_SEARCH = {
  procedure_code: '',
  city: 'Bengaluru',
  max_distance_km: 15,
  preference: 'balanced',
  urgency: 'planned',
}

export default function App() {
  const { settings, set, reset } = useSettings()
  const { view, stayId, step, navigate } = useRoute()

  const [user, setUser] = useState(readUser)
  const [stays, setStays] = useState([])

  const [reference, setReference] = useState(null)
  const [policy, setPolicy] = useState(null)
  const [results, setResults] = useState(null)
  const [journey, setJourney] = useState(null)
  const [search, setSearch] = useState(DEFAULT_SEARCH)

  const [busy, setBusy] = useState(null)
  const [error, setError] = useState(null)
  const [settingsOpen, setSettingsOpen] = useState(false)

  const [events, setEvents] = useState([])
  const [connected, setConnected] = useState(false)

  // Destructured rather than held as an object: the hook returns a fresh one
  // every render, and an effect depending on the object would re-run forever.
  // The functions inside it are memoised, so these are stable.
  const {
    sessionId, adopt, scheduleSave, open: openSavedStay, restoring, gone,
  } = useStay({ user, stayId })

  const refreshStays = useCallback(() => setStays(listStays(user)), [user])
  useEffect(refreshStays, [refreshStays])

  useEffect(() => {
    api.reference().then(setReference).catch((e) => setError(e.message))
  }, [])

  // The stream is opened only when the panel that displays it is on.
  //
  // It used to run always, so a hidden developer panel cost an open connection
  // and a re-render of the whole page per pipeline step, during the upload,
  // which is the one moment the user is waiting on us. Nothing is lost by
  // waiting: the server keeps a replay buffer, so switching the panel on
  // mid-session still shows every step from the beginning.
  useEffect(() => {
    if (!sessionId || !settings.showActivity) return

    setEvents([])
    const stop = subscribeToEvents(sessionId, (event) => {
      setConnected(true)
      setEvents((current) =>
        current.some((e) => e.id === event.id)
          ? current
          : [...current, event].slice(-MAX_EVENTS)
      )
    })
    return () => {
      stop()
      setConnected(false)
    }
  }, [sessionId, settings.showActivity])

  // Put a restored session back on screen. The server returns every part of it
  // in one payload, so a reload lands on the step the user left rather than
  // sending them back to the upload screen with their document already read.
  const hydrate = useCallback((restored) => {
    if (!restored) return
    setPolicy(restored.policy ?? null)
    setResults(restored.search ?? null)
    setJourney(restored.journey ?? null)
    if (restored.search_context?.procedure_code) {
      setSearch((current) => ({
        ...current,
        procedure_code: restored.search_context.procedure_code,
        city: restored.search_context.city || current.city,
        max_distance_km:
          restored.search_context.max_distance_km ?? current.max_distance_km,
        preference: restored.search_context.preference ?? current.preference,
        urgency: restored.search_context.urgency ?? current.urgency,
      }))
    }
  }, [])

  // Opening a stay from a link, a reload, or the home screen all arrive here.
  useEffect(() => {
    if (view !== 'stay' || !stayId || !user) return
    if (sessionId) return

    let cancelled = false
    setBusy('restore')
    openSavedStay()
      .then((restored) => { if (!cancelled) hydrate(restored) })
      .catch((e) => { if (!cancelled) setError(e.message) })
      .finally(() => { if (!cancelled) setBusy(null) })
    return () => { cancelled = true }
  }, [view, stayId, user, sessionId, openSavedStay, hydrate])

  // Anything the server now holds is worth writing to the device.
  //
  // Deliberately an effect rather than a call at each site that changes state.
  // A step added later cannot forget to save, and it solves a timing problem
  // besides: the first policy is read at `/new`, before this stay has an id,
  // so the save has to happen after the navigation that gives it one.
  useEffect(() => {
    if (!sessionId || !stayId) return
    scheduleSave()
  }, [sessionId, stayId, policy, results, journey, scheduleSave])

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

  // What this stay is, so the home screen lists it recognisably a day later.
  // The hospital and the treatment are what someone recognises; the id is not.
  const remember = useCallback((patch) => {
    if (!user || !stayId) return
    saveStay(user, { id: stayId, createdAt: Date.now(), ...patch })
    setStays(listStays(user))
  }, [user, stayId])

  // Take a freshly read policy as this stay's starting point.
  function adoptPolicy(result, id) {
    adopt(result.session_id)
    setPolicy(result)
    setResults(null)
    setJourney(null)
    navigate(stayPath(id, 'policy'), { replace: true })
  }

  async function handleUpload(file, insurerId) {
    const id = stayId ?? newStayId()
    const result = await run('upload', () => api.uploadPolicy(file, insurerId))
    if (!result) return
    saveStay(user, { id, createdAt: Date.now(), insurer: result.insurer_name })
    adoptPolicy(result, id)
  }

  async function handleManual(payload) {
    const id = stayId ?? newStayId()
    const result = await run('upload', () => api.manualPolicy(payload))
    if (!result) return
    saveStay(user, { id, createdAt: Date.now() })
    adoptPolicy(result, id)
  }

  async function handleAnswer(questionId, answer) {
    const result = await run('answer', () =>
      api.answer(sessionId, questionId, answer))
    if (result) setPolicy(result)
  }

  async function handleSearch() {
    const city = reference?.cities?.find((c) => c.city === search.city)
    const result = await run('search', () =>
      api.search(sessionId, {
        procedure_code: search.procedure_code,
        lat: city?.lat ?? 12.9716,
        lon: city?.lon ?? 77.5946,
        city: search.city,
        max_distance_km: Number(search.max_distance_km),
        preference: search.preference,
        urgency: search.urgency,
      })
    )
    if (result) {
      setResults(result)
      const name = reference?.procedures
        ?.find((p) => p.code === search.procedure_code)?.name
      remember({ procedure: name })
    }
  }

  async function handleStartJourney(option) {
    const result = await run('journey', () =>
      api.startJourney(sessionId, {
        hospital_id: option.hospital.id,
        procedure_code: search.procedure_code,
        room_category: option.room.category,
      })
    )
    if (result) {
      setJourney(result)
      remember({
        hospital: option.hospital.name,
        stageLabel: result.stage_label,
      })
      navigate(stayPath(stayId, 'journey'))
    }
  }

  const journeyAction = (work) => async (...args) => {
    const result = await run('journey', () => work(...args))
    if (result) {
      setJourney(result)
      remember({ stageLabel: result.stage_label })
    }
  }

  // --- identity and stays ---------------------------------------------------

  function signIn(name) {
    writeUser(name)
    setUser(name)
    setStays(listStays(name))
    navigate('/')
  }

  function switchUser() {
    clearUser()
    setUser('')
    resetWorkingState()
    navigate('/')
  }

  function resetWorkingState() {
    setPolicy(null)
    setResults(null)
    setJourney(null)
    setSearch(DEFAULT_SEARCH)
    setEvents([])
    setConnected(false)
    setError(null)
    setSettingsOpen(false)
    adopt(null)
  }

  function startNewStay() {
    resetWorkingState()
    navigate('/new')
  }

  function openStay(target) {
    resetWorkingState()
    navigate(stayPath(target.id, target.stageLabel ? 'journey' : 'policy'))
  }

  function goHome() {
    resetWorkingState()
    navigate('/')
    setStays(listStays(user))
  }

  // "Start over" throws away this stay, and only this stay. Another name on
  // the same device keeps everything, which is the point of having names.
  async function discardStay() {
    if (sessionId) await api.clear(sessionId).catch(() => {})
    if (stayId) deleteStay(user, stayId)
    goHome()
  }

  function removeStay(target) {
    deleteStay(user, target.id)
    setStays(listStays(user))
  }

  function forgetEverything() {
    if (sessionId) api.clear(sessionId).catch(() => {})
    deleteAllStays(user)
    goHome()
  }

  // --- render ---------------------------------------------------------------

  if (!user) return <SignIn onSignIn={signIn} />

  if (view === 'home') {
    return (
      <>
        <StayList
          user={user}
          stays={stays}
          onOpen={openStay}
          onNew={startNewStay}
          onDelete={removeStay}
          onSwitchUser={switchUser}
        />
        <SettingsPanel
          open={settingsOpen}
          onClose={() => setSettingsOpen(false)}
          settings={settings} set={set} reset={reset}
          sessionId={null}
          onForget={forgetEverything}
        />
      </>
    )
  }

  const reachable = {
    upload: true,
    policy: Boolean(policy),
    search: Boolean(policy),
    journey: Boolean(journey),
  }

  const shell = {
    events, connected, settings,
    onOpenSettings: () => setSettingsOpen(true),
    step, reachable,
    onGo: (id) => navigate(stayPath(stayId, id)),
    onHome: goHome,
    onStartOver: discardStay,
    hasSession: Boolean(sessionId),
    user,
    onToggleText: () =>
      set('textSize', settings.textSize === 'large' ? 'default' : 'large'),
  }


  return (
    <>
      <Shell {...shell}>
        {busy === 'restore' || restoring ? (
          <div className="mx-auto max-w-2xl px-4 py-20 text-center motion-safe:animate-fade">
            <Spinner label="Opening your stay. The server may take a moment to wake." />
          </div>
        ) : gone && !policy ? (
          <StayGone onHome={goHome} onNew={startNewStay} />
        ) : step === 'upload' ? (
          <UploadStep
            reference={reference}
            onUploaded={handleUpload}
            onManual={handleManual}
            busy={busy === 'upload'}
            error={error}
            onClearError={() => setError(null)}
          />
        ) : (
          <div className="mx-auto max-w-3xl space-y-5 py-6 motion-safe:animate-fade">
            <ErrorNote onDismiss={() => setError(null)}>{error}</ErrorNote>

            {step === 'policy' && policy && (
              <>
                <BackLink onClick={goHome}>All your stays</BackLink>
                <PolicySummary
                  policy={policy}
                  onAnswer={handleAnswer}
                  onContinue={() => navigate(stayPath(stayId, 'search'))}
                  answering={busy === 'answer'}
                />
              </>
            )}

            {step === 'search' && (
              <>
                <BackLink onClick={() => navigate(stayPath(stayId, 'policy'))}>
                  Back to your cover
                </BackLink>
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

            {step === 'journey' && (
              <>
                <BackLink onClick={() => navigate(stayPath(stayId, 'search'))}>
                  Back to hospitals
                </BackLink>
                <Journey
                  journey={journey}
                  busy={busy === 'journey'}
                  sessionId={sessionId}
                  onAdvance={journeyAction((stage, opts) =>
                    api.advance(sessionId, stage, opts)
                  )}
                  onRecordCost={journeyAction((payload) =>
                    api.recordCost(sessionId, payload)
                  )}
                  onUpdateCost={journeyAction((entryId, patch) =>
                    api.updateCost(sessionId, entryId, patch)
                  )}
                  onDeleteCost={journeyAction((entryId) =>
                    api.deleteCost(sessionId, entryId)
                  )}
                  onFilePreauth={journeyAction(() => api.filePreauth(sessionId))}
                />
              </>
            )}
          </div>
        )}
      </Shell>

      <SettingsPanel
        open={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        settings={settings} set={set} reset={reset}
        sessionId={sessionId}
        onForget={forgetEverything}
      />
    </>
  )
}

function StayGone({ onHome, onNew }) {
  return (
    <div className="mx-auto max-w-md px-4 py-20 text-center motion-safe:animate-rise">
      <h2 className="text-lg font-semibold">This stay is not on this device</h2>
      <p className="mt-2 text-[0.9375rem] leading-relaxed text-muted">
        Stays are saved on the device they were created on. If this link came
        from another phone or another browser, the admission it points to is
        still there, not here.
      </p>
      <div className="mt-5 flex justify-center gap-2.5">
        <Button variant="secondary" onClick={onHome}>Your stays</Button>
        <Button onClick={onNew}>Start a new stay</Button>
      </div>
    </div>
  )
}

function BackLink({ onClick, children }) {
  return (
    <button
      onClick={onClick}
      className="group inline-flex items-center gap-1.5 text-[0.875rem] text-muted transition hover:text-brand"
    >
      <span
        aria-hidden="true"
        className="transition-transform group-hover:-translate-x-0.5"
      >
        &larr;
      </span>
      {children}
    </button>
  )
}

function Shell({
  children, events, connected, settings, onOpenSettings,
  step, reachable, onGo, onHome, onStartOver, hasSession, user, onToggleText,
}) {
  const showActivity = settings.showActivity

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-20 border-b border-line bg-surface/95 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-2 px-4 py-2">
          <button
            onClick={onHome}
            className="group flex items-center gap-2.5 text-left"
            title="Your stays"
          >
            {/* The mark has no background of its own, so it sits on the header
                in either theme without a pale tile around it. */}
            {/* 64px for a 28px slot: enough for a high-density screen, and a
                twelfth the weight of the 192px icon the manifest needs. */}
            <img
              src="/logo-64.png"
              alt=""
              width="28"
              height="28"
              className="h-7 w-7 shrink-0 transition-transform group-hover:scale-105"
            />
            <span className="text-[0.9375rem] font-semibold tracking-tight">PoliMap</span>
          </button>

          <div className="flex items-center gap-2">
            {showActivity && events.length > 0 && (
              <span className="hidden text-[0.75rem] text-muted sm:inline">
                {events.length} steps
              </span>
            )}
            <span className="hidden text-[0.875rem] text-muted sm:inline">{user}</span>
            {hasSession && (
              <Button variant="secondary" onClick={onStartOver} className="px-3 py-1.5">
                Start over
              </Button>
            )}
            <button
              onClick={onToggleText}
              aria-label={
                settings.textSize === 'large'
                  ? 'Use the normal text size'
                  : 'Make the text larger'
              }
              title="Text size"
              aria-pressed={settings.textSize === 'large'}
              className={`rounded-lg border px-2.5 py-1.5 text-[0.9375rem] font-semibold leading-none transition ${
                settings.textSize === 'large'
                  ? 'border-brand bg-brand-soft text-brand'
                  : 'border-line text-muted hover:bg-canvas hover:text-ink'
              }`}
            >
              A<span className="text-[0.75rem]">A</span>
            </button>
            <button
              onClick={onOpenSettings}
              aria-label="Settings"
              title="Settings"
              className="rounded-lg border border-line px-2.5 py-2 text-[0.875rem] text-muted transition hover:bg-canvas hover:text-ink"
            >
              <GearIcon />
            </button>
          </div>
        </div>

        <StepNav step={step} onGo={onGo} reachable={reachable} />
      </header>

      <div className="mx-auto flex max-w-6xl gap-5 px-4">
        <main className="min-w-0 flex-1">{children}</main>

        {showActivity && (
          <aside className="sticky top-[var(--header-h)] hidden h-[calc(100vh-var(--header-h))] w-80 shrink-0 border-l border-line bg-surface lg:block">
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
//
// The three setup steps are grouped apart from the stay itself. They are
// different kinds of work: the first three are answered once, at the start,
// while the stay is returned to daily for as long as the admission lasts.
function StepNav({ step, onGo, reachable }) {
  const current = stepIndex(step)

  const item = (entry, index) => {
    const isCurrent = entry.id === step
    const isDone = index < current && reachable[entry.id]
    const enabled = reachable[entry.id]

    return (
      <li key={entry.id} className="min-w-0 flex-1">
        <button
          disabled={!enabled}
          aria-current={isCurrent ? 'step' : undefined}
          onClick={() => onGo(entry.id)}
          className={`flex w-full items-center justify-center gap-1.5 border-b-2 px-1.5 py-2 text-[0.8125rem] font-medium transition sm:px-2 sm:text-[0.875rem] ${
            isCurrent
              ? 'border-brand text-brand'
              : enabled
                ? 'border-transparent text-muted hover:text-ink'
                : 'cursor-not-allowed border-transparent text-muted/40'
          }`}
        >
          <span
            className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[0.75rem] transition ${
              isCurrent
                ? 'bg-brand text-on-brand'
                : isDone
                  ? 'bg-brand-soft text-brand'
                  : 'bg-canvas text-muted'
            }`}
          >
            {isDone ? '✓' : index + 1}
          </span>
          <span className="truncate sm:hidden">{entry.short}</span>
          <span className="hidden truncate sm:inline">{entry.label}</span>
        </button>
      </li>
    )
  }

  return (
    <nav aria-label="Progress" className="border-t border-line">
      <div className="mx-auto flex max-w-6xl items-stretch px-2">
        <ol className="flex min-w-0 flex-[3] items-stretch gap-1">
          {SETUP_STEPS.map(item)}
        </ol>
        <div className="mx-1.5 my-2 w-px shrink-0 bg-line" aria-hidden="true" />
        <ol className="flex min-w-0 flex-1 items-stretch">
          {item(TRACK_STEP, SETUP_STEPS.length)}
        </ol>
      </div>
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
