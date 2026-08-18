// Turning the pipeline's own event stream into something a person waiting on it
// can read.
//
// Nothing here invents progress. Every line shown comes from an event the
// server actually emitted, which is why a phase can sit still for half a
// minute: that is what is happening, and saying so is better than a bar that
// creeps along on a timer and lies. What this adds is grouping, so a hundred
// steps read as five, and counting, so a phase that will take a while can say
// how far through it is.

export const READING_PHASES = [
  { key: 'read', label: 'Reading the pages', stage: 'S0_INTAKE' },
  { key: 'sort', label: 'Working out what each page holds', stage: 'S1_TRIAGE' },
  { key: 'terms', label: 'Picking out the terms', stage: 'S2_ATOMIZE' },
  { key: 'check', label: 'Checking each term against the document', stage: 'S3_CHALLENGE' },
  { key: 'build', label: 'Building your cover', stage: 'S4_COMPILE' },
]

export const SEARCH_PHASES = [
  { key: 'find', label: 'Finding hospitals that can treat this', steps: ['find_options'] },
  { key: 'cost', label: 'Working out what each would cost you', steps: ['estimate_costs'] },
  { key: 'rank', label: 'Putting them in order', steps: ['rank_options'] },
]

// The step that means the whole run is over, whatever phase it stopped in.
const TERMINAL = 'pipeline_complete'

const belongsTo = (phase, event) =>
  phase.stage ? event.stage === phase.stage : phase.steps.includes(event.step)

// Only counters where the total is known from an event, so a fraction shown is
// a fraction that exists. Anything else gets no bar rather than a made-up one.
function tally(counts, event) {
  const detail = event.detail ?? {}
  switch (event.step) {
    case 'document_started':
      counts.file = detail.file ?? null
      counts.documents = detail.documents ?? 0
      counts.documentIndex = (detail.index ?? 0) + 1
      counts.pages = 0
      counts.pageTotal = 0
      break
    case 'open_pdf':
      counts.pageTotal = detail.pages ?? 0
      counts.pages = 0
      break
    case 'native_text':
    case 'ocr_page':
      counts.pages += 1
      break
    case 'chunk_document':
      // `read` is present when the document was too long to read whole, and is
      // then the honest denominator: the rest are not going to be read.
      counts.chunkTotal = detail.read ?? detail.chunks ?? 0
      counts.chunks = 0
      break
    case 'model_extract':
      counts.chunks += 1
      break
    default:
      break
  }
}

function fractionFor(key, counts) {
  if (key === 'read' && counts.pageTotal > 1) {
    return { done: Math.min(counts.pages, counts.pageTotal), total: counts.pageTotal, noun: 'page' }
  }
  if (key === 'terms' && counts.chunkTotal > 1) {
    return { done: Math.min(counts.chunks, counts.chunkTotal), total: counts.chunkTotal, noun: 'section' }
  }
  return null
}

export function progressOf(events, phases) {
  let furthest = -1
  let finished = false
  let failed = null
  // Which phase the current "document 2 of 3" marker belongs to. Reading and
  // term extraction happen per file; checking and compiling happen once over
  // all of them, and carrying the marker into those would say the work is
  // still on one file when it is not.
  let documentPhase = -1
  const notes = phases.map(() => '')
  // When each phase first said anything, and when anything last did. A phase
  // ran from its own first event until the next phase's, which is wall clock
  // and therefore comparable across phases. Summing the steps' own durations
  // was not: some steps are timed and some are one-shot notices, so a phase
  // built out of notices reported nothing at all.
  const startedAt = phases.map(() => null)
  let lastAt = null
  const counts = {
    pages: 0, pageTotal: 0, chunks: 0, chunkTotal: 0,
    file: null, documents: 0, documentIndex: 0,
  }

  for (const event of events) {
    if (event.step === TERMINAL) {
      // A completion arriving before any step of these phases belongs to
      // earlier work still sitting in the browser's buffer, not to this. The
      // activity panel keeps the log of a policy being read, and a search run
      // afterwards would otherwise open with all three steps already ticked.
      if (furthest >= 0) finished = true
      continue
    }

    tally(counts, event)

    const index = phases.findIndex((phase) => belongsTo(phase, event))
    if (index === -1) continue
    if (event.status === 'failed') failed = event.summary
    if (index > furthest) furthest = index
    if (event.step === 'document_started') documentPhase = index
    if (event.summary) notes[index] = event.summary

    const at = Date.parse(event.ts)
    if (!Number.isNaN(at)) {
      if (startedAt[index] === null) startedAt[index] = at
      lastAt = at
    }
  }

  const ranFor = (index) => {
    if (startedAt[index] === null) return 0
    for (let next = index + 1; next < startedAt.length; next += 1) {
      if (startedAt[next] !== null) return Math.max(0, startedAt[next] - startedAt[index])
    }
    return Math.max(0, (lastAt ?? startedAt[index]) - startedAt[index])
  }

  return {
    started: furthest >= 0,
    finished,
    failed,
    document:
      counts.documents > 1 && documentPhase === furthest && !finished
        ? { name: counts.file, index: counts.documentIndex, total: counts.documents }
        : null,
    phases: phases.map((phase, index) => {
      const state =
        finished || index < furthest ? 'done' : index === furthest ? 'active' : 'pending'
      return {
        key: phase.key,
        label: phase.label,
        state,
        note: state === 'active' ? notes[index] : '',
        ms: ranFor(index),
        fraction: state === 'active' ? fractionFor(phase.key, counts) : null,
      }
    }),
  }
}

export function humanDuration(ms) {
  if (!ms) return ''
  return ms < 950 ? `${Math.round(ms)}ms` : `${(ms / 1000).toFixed(1)}s`
}

export function clock(seconds) {
  const mins = Math.floor(seconds / 60)
  return `${mins}:${String(seconds % 60).padStart(2, '0')}`
}
