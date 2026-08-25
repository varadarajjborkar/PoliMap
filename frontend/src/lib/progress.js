// Turning the pipeline's own event stream into something a person waiting on it
// can read.
//
// Nothing here invents progress. Every line shown comes from an event the
// server actually emitted, which is why a phase can sit still for half a
// minute: that is what is happening, and saying so is better than a bar that
// creeps along on a timer and lies. What this adds is grouping, so a hundred
// steps read as five, and counting, so a phase that will take a while can say
// how far through it is.

// Every phase carries the key its name is read under as well as the name. The
// counter keys (`read`, `terms`) say which phase this is to the code and are
// not unique across the three sets, so they cannot double as the string's name:
// the first phase of a policy and the first of a bill count pages the same way
// and are called different things.
export const READING_PHASES = [
  { key: 'read', name: 'phase.pages', label: 'Reading the pages', stage: 'S0_INTAKE' },
  {
    key: 'sort', name: 'phase.sort', label: 'Working out what each page holds',
    stage: 'S1_TRIAGE',
  },
  { key: 'terms', name: 'phase.terms', label: 'Picking out the terms', stage: 'S2_ATOMIZE' },
  {
    key: 'check', name: 'phase.check', label: 'Checking each term against the document',
    stage: 'S3_CHALLENGE',
  },
  { key: 'build', name: 'phase.build', label: 'Building your cover', stage: 'S4_COMPILE' },
]

export const SEARCH_PHASES = [
  {
    key: 'find', name: 'phase.find', label: 'Finding hospitals that can treat this',
    steps: ['find_options'],
  },
  {
    key: 'cost', name: 'phase.cost', label: 'Working out what each would cost you',
    steps: ['estimate_costs'],
  },
  { key: 'rank', name: 'phase.rank', label: 'Putting them in order', steps: ['rank_options'] },
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

// The line under the phase being worked on, said in the reader's language.
//
// The server writes every event a one-line English summary. That summary is
// what the console prints and what the activity panel shows, and both of those
// are ours to read. The person waiting on their policy gets the same thing
// composed here instead, out of the figures on the very same event, because a
// sentence already assembled in Python around a number cannot be translated
// afterwards without taking it apart again.
//
// A step with nothing to say here shows no line rather than an English one.
// The phase's own name is above it and already says what is happening; the
// line is for the number beside it, and a step that has not produced its
// number yet has not got to the interesting part.
const NOTES = {
  document_started: (d) => say('note.reading', 'Reading {file}', { file: d.file }),
  read_image: (d) => say('note.reading', 'Reading {file}', { file: d.file }),
  open_pdf: (d) =>
    say('note.opened', 'Opened {file}, {pages} pages', {
      file: d.file, pages: d.pages,
    }),
  native_text: (d) =>
    say('note.page_text', 'Page {page}: read from the file itself', {
      page: pageNumber(d),
    }),
  ocr_page: (d) =>
    say('note.page_ocr', 'Page {page}: {chars} characters, {sure}% sure', {
      page: pageNumber(d), chars: d.chars, sure: percent(d.confidence),
    }),
  vision_escalation: (d) =>
    say('note.page_vision', 'Page {page}: hard to read, asking a model to look', {
      page: pageNumber(d),
    }),
  intake_complete: (d) =>
    say('note.pages_read', '{pages} pages read', { pages: d.pages }),
  classify_pages: (d) =>
    say('note.insurer', 'Looks like a {insurer} policy', { insurer: d.insurer }),
  chunk_document: (d) =>
    say('note.sections', 'Split into {chunks} sections', { chunks: d.chunks }),
  grammar_extract: (d) =>
    say('note.rules_found', 'The rules found {clauses} terms', { clauses: d.clauses }),
  model_extract: (d) =>
    say('note.model_kept', '{admitted} more terms, each one found in the document', {
      admitted: d.admitted,
    }),
  merge_clauses: (d) =>
    say('note.ledger', '{total} terms in all', { total: d.total }),
  challenge_round: (d) =>
    say('note.questions', 'Round {round}: {challenges} things worth questioning', {
      round: d.round, challenges: d.challenges,
    }),
  compile_policy: (d) =>
    say('note.compiled', '{sublimits} limits found in your cover', {
      sublimits: d.sublimits,
    }),
  find_options: (d) =>
    say('note.matched', '{matched} of {considered} hospitals fit', {
      matched: d.matched, considered: d.considered,
    }),
  estimate_costs: (d) =>
    say('note.costed', 'Costed {costed} of them', { costed: d.costed }),
  rank_options: (d) =>
    say('note.shortlisted', '{shortlisted} shortlisted', {
      shortlisted: d.shortlisted,
    }),
}

// A note needs every figure it names. Anything missing means the step has
// started and not finished, so there is nothing to say yet.
function say(key, english, values) {
  for (const value of Object.values(values)) {
    if (value === undefined || value === null || value === '') return null
  }
  return { key, english, values }
}

const pageNumber = (detail) =>
  typeof detail.page === 'number' ? detail.page + 1 : null

const percent = (value) =>
  typeof value === 'number' ? Math.round(value * 100) : null

function noteFor(event) {
  const compose = NOTES[event.step]
  return compose ? compose(event.detail ?? {}) : null
}

function fractionFor(key, counts) {
  if (key === 'read' && counts.pageTotal > 1) {
    return {
      done: Math.min(counts.pages, counts.pageTotal),
      total: counts.pageTotal,
      name: 'count.pages',
      label: '{done}/{total} pages',
    }
  }
  if (key === 'terms' && counts.chunkTotal > 1) {
    return {
      done: Math.min(counts.chunks, counts.chunkTotal),
      total: counts.chunkTotal,
      name: 'count.sections',
      label: '{done}/{total} sections',
    }
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
  const notes = phases.map(() => null)
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
    const note = noteFor(event)
    if (note) notes[index] = note

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
        name: phase.name,
        label: phase.label,
        state,
        note: state === 'active' ? notes[index] : null,
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
