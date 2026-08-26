import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '../api'
import { readSnapshot, writeSnapshot } from '../lib/stays'

// Keeping a stay alive across reloads, restarts and days.
//
// The server holds session state, but it expires on a timer and a container
// restart takes it with it. An admission is tracked over five days, so the
// server cannot be the durable copy. The browser holds a snapshot of the
// server's own session, and the two are reconciled on open:
//
//   the server still has it   -> use it, no upload needed
//   the server has forgotten  -> hand the snapshot back and take the new id
//   neither has it            -> the stay is genuinely gone, say so
//
// The snapshot is refreshed after anything that changes state. That write is
// debounced rather than immediate: recording four charges in a row should cost
// one save, not four, and the window is short enough that closing the tab
// straight after typing an amount still keeps it.
const SAVE_DEBOUNCE_MS = 600

export function useStay({ user, stayId }) {
  const [sessionId, setSessionId] = useState(null)
  const [restoring, setRestoring] = useState(false)
  const [gone, setGone] = useState(false)

  // Held in a ref as well as state: the save timer fires outside React's
  // render, and reading the id off state there would capture a stale one.
  const sessionRef = useRef(null)
  const timerRef = useRef(null)

  const adopt = useCallback((id) => {
    sessionRef.current = id
    setSessionId(id)
  }, [])

  // Pull the server's copy of the session and put it on the device.
  const persist = useCallback(async () => {
    const id = sessionRef.current
    if (!id || !user || !stayId) return
    try {
      const { snapshot } = await api.exportSession(id)
      writeSnapshot(user, stayId, { sessionId: id, snapshot })
    } catch {
      // A failed save is not worth interrupting anyone for. The next action
      // schedules another, and the in-memory session is still correct.
    }
  }, [user, stayId])

  const scheduleSave = useCallback(() => {
    if (timerRef.current) clearTimeout(timerRef.current)
    timerRef.current = setTimeout(persist, SAVE_DEBOUNCE_MS)
  }, [persist])

  // A tab closed or backgrounded mid-edit still saves. `visibilitychange` is
  // the event that actually fires on a phone; `beforeunload` does not.
  useEffect(() => {
    const flush = () => {
      if (document.visibilityState === 'hidden') persist()
    }
    document.addEventListener('visibilitychange', flush)
    return () => {
      document.removeEventListener('visibilitychange', flush)
      if (timerRef.current) clearTimeout(timerRef.current)
    }
  }, [persist])

  // Open a stay saved on this device, restoring it server-side if needed.
  const open = useCallback(async () => {
    if (!user || !stayId) return null
    const saved = readSnapshot(user, stayId)
    if (!saved?.snapshot) {
      setGone(true)
      return null
    }

    setRestoring(true)
    setGone(false)
    try {
      if (saved.sessionId) {
        try {
          const live = await api.session(saved.sessionId)
          adopt(saved.sessionId)
          return live
        } catch (error) {
          // Anything other than "the server forgot it" is a real failure and
          // should not be papered over by silently uploading a stale copy.
          if (error.status !== 404) throw error
        }
      }

      const restored = await api.importSession(saved.snapshot)
      adopt(restored.session_id)
      // The id changed, so the stored pairing has to change with it or the
      // next open would ask the server for a session that never existed.
      writeSnapshot(user, stayId, {
        sessionId: restored.session_id, snapshot: saved.snapshot,
      })
      return restored
    } finally {
      setRestoring(false)
    }
  }, [user, stayId, adopt])

  return { sessionId, adopt, scheduleSave, persist, open, restoring, gone }
}