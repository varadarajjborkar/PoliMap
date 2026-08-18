import { useCallback, useEffect, useState } from 'react'
import { api, subscribeToEvents } from './api'
import { ActivityLog } from './components/ActivityLog'
import { SignIn, StayList } from './components/HomeScreen'
import { Journey } from './components/Journey'
import { PolicySummary } from './components/PolicySummary'
import { ReadingProgress } from './components/ReadingProgress'
import { EligibilityNotice, Results, SearchPanel } from './components/Results'
import { Locked, SettledRail, SetupFlow } from './components/SetupFlow'
import { Button, ErrorNote, Spinner } from './components/Primitives'
import { SettingsPanel } from './components/Settings'
import { UploadStep } from './components/UploadStep'
import {
  SETUP_STEPS, TRACK_STEP, stayPath, useRoute,
} from './hooks/useRoute'
import { READING_PHASES, SEARCH_PHASES } from './lib/progress'
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
  patient_index: null,
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

  // The two things no document holds: whether the condition was there before
  // the policy, and whether this follows an accident. Kept beside the search
  // rather than inside it, because they are facts about the patient rather
  // than about what they are looking for.
  const [claimFacts, setClaimFacts] = useState({ pre_existing: null, accident: false })

  // A move within the setup flow, asked for by something inside it. Carries a
  // nonce so asking twice for the same section still moves the page.
  const [jump, setJump] = useState(null)
  const goToSection = useCallback(
    (id) => setJump({ id, n: Date.now() }), [],
  )

  const [busy, setBusy] = useState(null)
  const [error, setError] = useState(null)
  const [settingsOpen, setSettingsOpen] = useState(false)

  const [events, setEvents] = useState([])
  const [connected, setConnected] = useState(false)

  // The session whose work is being watched right now. Set before an upload,
  // so the stream is open before the reading starts rather than after it ends,
  // and cleared when the work finishes.
  const [watching, setWatching] = useState(null)

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

  // The stream is open while something is running, and otherwise only when the
  // activity panel is showing it.
  //
  // It used to run always, so a hidden developer panel cost an open connection
  // and a re-render of the whole page per pipeline step. It then ran only with
  // the panel on, which meant the one moment worth watching, a document being
  // read, was the one moment nothing was watching. Both are covered now, and
  // nothing is lost either way: the server keeps a replay buffer, so switching
  // the panel on mid-session still shows every step from the beginning.
  //
  // `watching` and `sessionId` hold the same string once an upload succeeds,
  // so finishing does not tear the connection down and lose the log with it.
  const streamId = watching ?? sessionId
  const streaming = Boolean(streamId) && (Boolean(watching) || settings.showActivity)

  useEffect(() => {
    if (!streaming || !streamId) return

    setEvents([])
    const stop = subscribeToEvents(streamId, (event) => {
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
  }, [streamId, streaming])

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

  // Keep the address bar on the section being read, so a link copied halfway
  // through the flow reopens where the reader was. `replace`, because scrolling
  // is not navigation: filling the history with a dozen entries would make the
  // back button useless for leaving.
  const markStepInView = useCallback((id) => {
    if (!stayId || id === step) return
    navigate(stayPath(stayId, id), { replace: true })
  }, [stayId, step, navigate])

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

  async function handleUpload(files, insurerId) {
    const id = stayId ?? newStayId()

    // The session is claimed before the files are sent, so the stream carrying
    // the reading is already open when the reading begins. If that call fails
    // there is nothing to watch, but there is still a policy to read, so the
    // upload goes ahead and the server issues its own id.
    const watchId = await api.newSession()
      .then((s) => s.session_id)
      .catch(() => null)
    setWatching(watchId)

    const result = await run('upload', () => api.uploadPolicy(files, insurerId, watchId))
    if (!result) {
      setWatching(null)
      return
    }

    saveStay(user, { id, createdAt: Date.now(), insurer: result.insurer_name })
    // Adopted first, so the stay takes over the same id in the same render and
    // the log of what just happened survives into the activity panel.
    adoptPolicy(result, id)
    setWatching(null)
  }

  async function handleManual(payload) {
    const id = stayId ?? newStayId()
    const result = await run('upload', () => api.manualPolicy(payload))
    if (!result) return
    saveStay(user, { id, createdAt: Date.now() })
    adoptPolicy(result, id)
  }

  // Not wrapped in `run`: ticking a box should not grey out the page, and a
  // failure here is worth a banner rather than an interruption.
  async function handleToggleChecklist(itemId, done) {
    try {
      setJourney(await api.toggleChecklist(sessionId, itemId, done))
    } catch (e) {
      setError(e.message)
    }
  }

  // The final bill. Kept on the journey object rather than in its own state,
  // because it belongs to this stay and has to travel with it when the browser
  // saves and restores one.
  async function handleCheckBill(file) {
    const result = await run('bill', () => api.checkBill(sessionId, file))
    if (result) setJourney((current) => (current ? { ...current, bill: result } : current))
  }

  async function handleDropBill() {
    const result = await run('bill', () => api.dropBill(sessionId))
    if (result) setJourney((current) => (current ? { ...current, bill: null } : current))
  }

  // A second cover on the same admission, typed rather than uploaded: most
  // people holding two have their own document and not their employer's. The
  // results are dropped because they were costed against one policy.
  async function handleAddSecondPolicy(entered) {
    const result = await run('answer', () =>
      api.manualPolicy({ ...entered, session_id: sessionId, attach: true }))
    if (result) {
      setPolicy(result)
      setResults(null)
    }
  }

  async function handleDropSecondPolicy() {
    const result = await run('answer', () => api.dropSecondPolicy(sessionId))
    if (result) {
      setPolicy(result)
      setResults(null)
    }
  }

  async function handleAnswer(questionId, answer) {
    const result = await run('answer', () =>
      api.answer(sessionId, questionId, answer))
    if (result) setPolicy(result)
  }

  // Deliberately not wrapped in `run`: the field reports its own error inline,
  // next to the value being corrected, rather than in the page-level banner
  // where it would be far from what it refers to.
  async function handleEditField(field, value) {
    const result = await api.editField(sessionId, field, value)
    setPolicy(result)
    return result
  }

  async function handleSkip(questionId) {
    const result = await run('answer', () =>
      api.skipQuestion(sessionId, questionId))
    if (result) setPolicy(result)
  }

  async function handleSearch(facts = claimFacts) {
    const city = reference?.cities?.find((c) => c.city === search.city)
    // Same id as the session, so this opens the stream without disturbing it
    // when the activity panel already has it open.
    setWatching(sessionId)
    const result = await run('search', () =>
      api.search(sessionId, {
        procedure_code: search.procedure_code,
        lat: city?.lat ?? 12.9716,
        lon: city?.lon ?? 77.5946,
        city: search.city,
        max_distance_km: Number(search.max_distance_km),
        preference: search.preference,
        urgency: search.urgency,
        pre_existing: facts.pre_existing,
        accident: facts.accident,
        patient_index: search.patient_index ?? null,
      })
    )
    setWatching(null)
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

  // What the setup flow may scroll to. The same map, minus the stay, which is
  // a separate screen rather than a section of this one.
  const reached = {
    upload: true, policy: reachable.policy, search: reachable.search,
  }

  const chosenTreatment = reference?.procedures
    ?.find((p) => p.code === search.procedure_code)?.name

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
        ) : step !== 'journey' ? (
          <>
            <ErrorNote onDismiss={() => setError(null)}>{error}</ErrorNote>
            {/* Clears the sticky sub-step bar, which is fixed on small
                screens because it has to sit under a header that is itself
                sticky. */}
            <div aria-hidden="true" className="h-9 lg:hidden" />
            <SetupFlow
              step={step}
              reached={reached}
              jump={jump}
              onStepInView={markStepInView}
              rail={
                <SettledRail
                  items={[
                    policy && {
                      label: 'Your cover',
                      value: policy.sum_insured_display,
                      onChange: () => goToSection('policy'),
                      changeLabel: 'Check what we read',
                    },
                    policy && {
                      label: 'Room you are covered for',
                      value: policy.room_limit?.description,
                    },
                    chosenTreatment && {
                      label: 'Treatment',
                      value: chosenTreatment,
                    },
                    results?.options?.length && {
                      label: 'Cheapest for you',
                      value: `${results.options[0].hospital.name} · ${results.options[0].you_pay_display}`,
                    },
                  ]}
                />
              }
              sections={{
                upload: (
                  <UploadStep
                    reference={reference}
                    onUploaded={handleUpload}
                    onManual={handleManual}
                    busy={busy === 'upload'}
                    error={null}
                    onClearError={() => setError(null)}
                    done={Boolean(policy)}
                    progress={
                      busy === 'upload' && (
                        <ReadingProgress
                          events={events}
                          phases={READING_PHASES}
                          title="Reading your policy"
                          waiting="Sending your files. Keep this page open."
                          hint="Long documents and phone photos take longer. You can leave this open in the background."
                        />
                      )
                    }
                  />
                ),
                policy: policy ? (
                  <PolicySummary
                    policy={policy}
                    onAddSecondPolicy={handleAddSecondPolicy}
                    onDropSecondPolicy={handleDropSecondPolicy}
                    onAnswer={handleAnswer}
                    onSkip={handleSkip}
                    onEditField={handleEditField}
                    onContinue={() => goToSection('search')}
                    answering={busy === 'answer'}
                  />
                ) : (
                  <Locked title="Your cover">
                    Once your policy is read, everything it says about what you
                    are covered for appears here, and you can correct anything we
                    got wrong.
                  </Locked>
                ),
                search: policy ? (
                  <div className="space-y-5">
                    <SearchPanel
                      reference={reference}
                      policy={policy}
                      value={search}
                      onChange={setSearch}
                      onSearch={() => handleSearch()}
                      busy={busy === 'search'}
                    />
                    {busy === 'search' && (
                      <ReadingProgress
                        events={events}
                        phases={SEARCH_PHASES}
                        title="Looking for your options"
                        hint="Every hospital in range is costed against your policy, one at a time."
                      />
                    )}
                    <EligibilityNotice
                      eligibility={results?.eligibility}
                      busy={busy === 'search'}
                      onAnswer={(answer) => {
                        const facts = { ...claimFacts, ...answer }
                        setClaimFacts(facts)
                        handleSearch(facts)
                      }}
                    />
                    <Results
                      results={results}
                      onStartJourney={handleStartJourney}
                      starting={busy === 'journey'}
                    />
                  </div>
                ) : (
                  <Locked title="Hospitals">
                    We cost every hospital in range against your own policy, so
                    this needs your cover first.
                  </Locked>
                ),
              }}
            />
          </>
        ) : (
          <div className="mx-auto max-w-3xl space-y-5 py-6 motion-safe:animate-fade">
            <ErrorNote onDismiss={() => setError(null)}>{error}</ErrorNote>

            {step === 'journey' && (
              <>
                <BackLink onClick={() => navigate(stayPath(stayId, 'search'))}>
                  Back to hospitals
                </BackLink>
                <Journey
                  journey={journey}
                  onToggleChecklist={handleToggleChecklist}
                  onCheckBill={handleCheckBill}
                  onDropBill={handleDropBill}
                  billBusy={busy === 'bill'}
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

// Two, not four.
//
// Setting up and tracking the stay are different kinds of work: the first is
// answered once, at the start, while the second is returned to daily for as
// long as the admission lasts. Putting the three setup steps in this bar as
// well meant the same three things were named twice on the same screen, once
// here and once on the thread beside the flow they belong to, and the bar was
// the copy with no sense of where in the page you were.
//
// The three live on the thread now. This says which of the two halves of the
// application you are in, which is the only thing it was ever good at.
function StepNav({ step, onGo, reachable }) {
  const inSetup = step !== TRACK_STEP.id

  const item = (id, label, enabled, isCurrent) => (
    <li key={id} className="min-w-0 flex-1">
      <button
        disabled={!enabled}
        aria-current={isCurrent ? 'page' : undefined}
        onClick={() => onGo(id)}
        className={`flex w-full items-center justify-center gap-2 border-b-2 px-2 py-2 text-[0.875rem] font-medium transition ${
          isCurrent
            ? 'border-brand text-brand'
            : enabled
              ? 'border-transparent text-muted hover:text-ink'
              : 'cursor-not-allowed border-transparent text-muted/40'
        }`}
      >
        {label}
      </button>
    </li>
  )

  return (
    <nav aria-label="Sections" className="border-t border-line">
      <ol className="mx-auto flex max-w-6xl items-stretch px-2">
        {item(
          SETUP_STEPS[0].id, 'Setting up', true, inSetup,
        )}
        {item(
          TRACK_STEP.id, TRACK_STEP.label, reachable[TRACK_STEP.id], !inSetup,
        )}
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
