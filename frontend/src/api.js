// Thin API client. Errors are surfaced with the server's own message where it
// gave one, because those messages are written for the person reading them.

async function request(path, options = {}) {
  const response = await fetch(path, options)
  if (!response.ok) {
    let message = `Something went wrong (${response.status}).`
    try {
      const body = await response.json()
      if (body.detail) message = typeof body.detail === 'string' ? body.detail : message
    } catch {
      // Non-JSON error body; the generic message stands.
    }
    throw new Error(message)
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

  uploadPolicy(file, insurerId) {
    const form = new FormData()
    form.append('file', file)
    form.append('insurer_id', insurerId || '')
    return request('/api/policy/upload', { method: 'POST', body: form })
  },
  manualPolicy: (payload) => request('/api/policy/manual', json(payload)),
  answer: (sessionId, questionId, answer) =>
    request(`/api/policy/${sessionId}/answer`, json({ question_id: questionId, answer })),

  search: (sessionId, payload) => request(`/api/search/${sessionId}`, json(payload)),

  startJourney: (sessionId, payload) =>
    request(`/api/journey/${sessionId}/start`, json(payload)),
  advance: (sessionId, stage, note = '') =>
    request(`/api/journey/${sessionId}/advance`, json({ stage, note })),
  recordCost: (sessionId, payload) =>
    request(`/api/journey/${sessionId}/cost`, json(payload)),
  filePreauth: (sessionId) =>
    request(`/api/journey/${sessionId}/preauth`, { method: 'POST' }),
}

// Subscribes to the pipeline's activity stream. Returns an unsubscribe function.
export function subscribeToEvents(sessionId, onEvent) {
  const source = new EventSource(`/api/events/${sessionId}`)
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
