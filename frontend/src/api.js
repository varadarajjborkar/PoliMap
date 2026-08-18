// Thin API client. Errors are surfaced with the server's own message where it
// gave one, because those messages are written for the person reading them.
//
// In development the Vite proxy puts the API on this same origin, so the base
// is empty. A deployed frontend is served from somewhere the API is not, so it
// sets VITE_API_BASE to the API's origin at build time.

const BASE = (import.meta.env.VITE_API_BASE ?? '').replace(/\/$/, '')

export const apiUrl = (path) => `${BASE}${path}`

async function request(path, options = {}) {
  const response = await fetch(apiUrl(path), options)
  if (!response.ok) {
    let message = `Something went wrong (${response.status}).`
    let detail = null
    try {
      const body = await response.json()
      if (typeof body.detail === 'string') {
        message = body.detail
      } else if (body.detail?.message) {
        // A structured refusal, e.g. two documents that name different
        // policies. The reasons matter as much as the headline.
        message = body.detail.message
        detail = body.detail
      }
    } catch {
      // Non-JSON error body; the generic message stands.
    }
    const error = new Error(message)
    error.status = response.status
    error.detail = detail
    throw error
  }
  return response.json()
}

const json = (body) => ({
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(body),
})

export const api = {
  health: () => request('/api/health'),
  providers: () => request('/api/health/providers'),
  reference: () => request('/api/reference'),

  clear: (sessionId) => request(`/api/session/${sessionId}`, { method: 'DELETE' }),

  // An empty session, asked for before there is anything to put in it. The
  // activity stream is keyed by session, so having the id up front is what
  // lets the browser watch a document being read instead of waiting blind.
  newSession: () => request('/api/session', { method: 'POST' }),

  // The session as the server holds it, for the browser to keep. Sessions
  // expire here and a restart drops them, so the device is the durable copy.
  session: (sessionId) => request(`/api/session/${sessionId}`),
  exportSession: (sessionId) => request(`/api/session/${sessionId}/export`),
  importSession: (snapshot) => request('/api/session/import', json({ snapshot })),

  // One policy usually arrives in pieces: the schedule, the wording, a
  // photograph of an endorsement. They are read together, and the server
  // refuses to merge them if they turn out to name two different policies.
  uploadPolicy(files, insurerId, sessionId = '') {
    const chosen = Array.isArray(files) ? files : [files]
    const form = new FormData()
    for (const file of chosen) form.append('files', file)
    form.append('insurer_id', insurerId || '')
    form.append('session_id', sessionId || '')
    return request('/api/policy/upload-many', { method: 'POST', body: form })
  },
  manualPolicy: (payload) => request('/api/policy/manual', json(payload)),
  answer: (sessionId, questionId, answer) =>
    request(`/api/policy/${sessionId}/answer`, json({ question_id: questionId, answer })),
  // Skipping is not answering: the clause stays unconfirmed and the estimate
  // still says where it is unsure. What stops is the asking.
  skipQuestion: (sessionId, questionId) =>
    request(`/api/policy/${sessionId}/skip`, json({ question_id: questionId })),
  // Correcting a figure the system read wrong. Everything downstream is
  // computed from these few numbers, so one misread digit poisons the lot.
  editField: (sessionId, field, value) =>
    request(`/api/policy/${sessionId}/field`, {
      ...json({ field, value }),
      method: 'PATCH',
    }),

  search: (sessionId, payload) => request(`/api/search/${sessionId}`, json(payload)),

  startJourney: (sessionId, payload) =>
    request(`/api/journey/${sessionId}/start`, json(payload)),

  // `confirmSkip` is set once the user has been shown which stages are being
  // passed over. `reason` is theirs to give or leave blank.
  advance: (sessionId, stage, { note = '', confirmSkip = false, reason = '' } = {}) =>
    request(
      `/api/journey/${sessionId}/advance`,
      json({ stage, note, confirm_skip: confirmSkip, reason })
    ),

  // Multipart, because a charge can carry a photograph of the bill.
  recordCost(sessionId, { head, amount, description = '', advanceDay = false, receipt }) {
    const form = new FormData()
    form.append('head', head)
    form.append('amount', String(amount))
    form.append('description', description)
    form.append('advance_day', String(advanceDay))
    if (receipt) form.append('receipt', receipt)
    return request(`/api/journey/${sessionId}/cost`, { method: 'POST', body: form })
  },
  updateCost: (sessionId, entryId, patch) =>
    request(`/api/journey/${sessionId}/cost/${entryId}`, {
      ...json(patch),
      method: 'PATCH',
    }),
  deleteCost: (sessionId, entryId) =>
    request(`/api/journey/${sessionId}/cost/${entryId}`, { method: 'DELETE' }),
  receiptUrl: (sessionId, entryId) =>
    apiUrl(`/api/journey/${sessionId}/cost/${entryId}/receipt`),

  // Ticking off something on the stage checklist. Kept server-side so the list
  // is a record of what was done rather than a poster that resets on reload.
  toggleChecklist: (sessionId, itemId, done) =>
    request(`/api/journey/${sessionId}/checklist`, json({ item_id: itemId, done })),

  filePreauth: (sessionId) =>
    request(`/api/journey/${sessionId}/preauth`, { method: 'POST' }),
}

// Subscribes to the pipeline's activity stream. Returns an unsubscribe function.
export function subscribeToEvents(sessionId, onEvent) {
  const source = new EventSource(apiUrl(`/api/events/${sessionId}`))
  source.onmessage = (message) => {
    try {
      onEvent(JSON.parse(message.data))
    } catch {
      // Keep-alive comment frames arrive here; ignoring them is correct.
    }
  }
  // The browser reconnects automatically, so an error is not necessarily fatal.
  source.onerror = () => {}
  return () => source.close()
}
