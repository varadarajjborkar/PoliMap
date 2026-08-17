import { useCallback, useEffect, useRef, useState } from 'react'
import { api, subscribeToEvents } from './api'
import { ActivityLog } from './components/ActivityLog'
import { Journey } from './components/Journey'
import { PolicySummary } from './components/PolicySummary'
import { Results, SearchPanel } from './components/Results'
import { Button, ErrorNote } from './components/Primitives'
import { UploadStep } from './components/UploadStep'

const STEPS = [
  ['policy', 'Your cover'],
  ['search', 'Hospitals'],
  ['journey', 'Your stay'],
]

export default function App() {
  const [reference, setReference] = useState(null)
  const [session, setSession] = useState(null)
  const [policy, setPolicy] = useState(null)
  const [results, setResults] = useState(null)
  const [journey, setJourney] = useState(null)

  const [step, setStep] = useState('upload')
  const [busy, setBusy] = useState(null)
  const [error, setError] = useState(null)

  const [events, setEvents] = useState([])
  const [connected, setConnected] = useState(false)
  const [logOpen, setLogOpen] = useState(false)

  const [search, setSearch] = useState({
    procedure_code: '',
    city: 'Bengaluru',
    max_distance_km: 15,
    preference: 'balanced',
    urgency: 'planned',
  })

  const unsubscribe = useRef(null)

  useEffect(() => {
    api.reference().then(setReference).catch((e) => setError(e.message))
    return () => unsubscribe.current?.()
  }, [])

  // One event stream per session, opened as soon as a session exists so the
  // very first pipeline steps are captured rather than missed.
  const connect = useCallback((sessionId) => {
    unsubscribe.current?.()
    setEvents([])
    unsubscribe.current = subscribeToEvents(sessionId, (event) => {
      setConnected(true)
      setEvents((current) =>
        current.some((e) => e.id === event.id) ? current : [...current, event]
      )
    })
  }, [])

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

  async function handleUpload(file, insurerId) {
    const result = await run('upload', () => api.uploadPolicy(file, insurerId))
    if (result) {
      setSession(result.session_id)
      connect(result.session_id)
      setPolicy(result)
      setStep('policy')
      setLogOpen(true)
    }
  }

  async function handleManual(payload) {
    const result = await run('upload', () => api.manualPolicy(payload))
    if (result) {
      setSession(result.session_id)
      connect(result.session_id)
      setPolicy(result)
      setStep('policy')
    }
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
      setStep('journey')
    }
  }

  const journeyAction = (work) => async (...args) => {
    const result = await run('journey', () => work(...args))
    if (result) setJourney(result)
  }

  if (step === 'upload') {
    return (
      <Shell
        events={events}
        connected={connected}
        logOpen={logOpen}
        setLogOpen={setLogOpen}
        step={step}
        hasPolicy={false}
      >
        <UploadStep
          reference={reference}
          onUploaded={handleUpload}
          onManual={handleManual}
          busy={busy === 'upload'}
          error={error}
          onClearError={() => setError(null)}
        />
      </Shell>
    )
  }

  return (
    <Shell
      events={events}
      connected={connected}
      logOpen={logOpen}
      setLogOpen={setLogOpen}
      step={step}
      setStep={setStep}
      hasPolicy={Boolean(policy)}
      hasResults={Boolean(results)}
      hasJourney={Boolean(journey)}
    >
      <div className="mx-auto max-w-3xl space-y-5 py-6">
        <ErrorNote onDismiss={() => setError(null)}>{error}</ErrorNote>

        {step === 'policy' && policy && (
          <PolicySummary
            policy={policy}
            onAnswer={handleAnswer}
            onContinue={() => setStep('search')}
            answering={busy === 'answer'}
          />
        )}

        {step === 'search' && (
          <>
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
          <Journey
            journey={journey}
            busy={busy === 'journey'}
            onAdvance={journeyAction((stage) => api.advance(session, stage))}
            onRecordCost={journeyAction((payload) => api.recordCost(session, payload))}
            onFilePreauth={journeyAction(() => api.filePreauth(session))}
          />
        )}
      </div>
    </Shell>
  )
}

function Shell({
  children, events, connected, logOpen, setLogOpen,
  step, setStep, hasPolicy, hasResults, hasJourney,
}) {
  const available = { policy: hasPolicy, search: hasPolicy, journey: hasJourney }

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-20 border-b border-line bg-surface/95 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3">
          <div className="flex items-baseline gap-2.5">
            <span className="text-[15px] font-semibold tracking-tight">CoverPath</span>
            <span className="hidden text-[12px] text-muted sm:inline">
              Know what your hospital stay will cost
            </span>
          </div>

          <div className="flex items-center gap-2">
            {setStep && (
              <nav className="hidden items-center gap-1 sm:flex">
                {STEPS.map(([value, label]) => (
                  <button
                    key={value}
                    disabled={!available[value]}
                    onClick={() => setStep(value)}
                    className={`rounded-lg px-3 py-1.5 text-[12px] font-medium transition disabled:opacity-35 ${
                      step === value ? 'bg-brand-soft text-brand' : 'text-muted hover:text-ink'
                    }`}
                  >
                    {label}
                  </button>
                ))}
              </nav>
            )}
            <Button variant="secondary" onClick={() => setLogOpen(!logOpen)}>
              {logOpen ? 'Hide activity' : 'Show activity'}
              {events.length > 0 && (
                <span className="ml-1 rounded-full bg-canvas px-1.5 text-[11px] tabular-nums">
                  {events.length}
                </span>
              )}
            </Button>
          </div>
        </div>
      </header>

      <div className="mx-auto flex max-w-6xl gap-5 px-4">
        <main className="min-w-0 flex-1">{children}</main>

        {logOpen && (
          <aside className="sticky top-[57px] hidden h-[calc(100vh-57px)] w-80 shrink-0 border-l border-line bg-surface lg:block">
            <ActivityLog events={events} connected={connected} />
          </aside>
        )}
      </div>

      {logOpen && (
        <div className="border-t border-line bg-surface lg:hidden">
          <div className="h-72">
            <ActivityLog events={events} connected={connected} />
          </div>
        </div>
      )}
    </div>
  )
}
