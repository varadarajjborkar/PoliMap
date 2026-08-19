import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '../api'
import { useT } from '../hooks/useLanguage'
import { saveTicket } from '../lib/tickets'
import { Button, Spinner } from './Primitives'

// The help desk, in the corner of whatever you are already doing.
//
// It opens in place rather than taking the screen, because the question is
// nearly always about what is on the screen: "whose name goes here", "which of
// these rooms", "what is this deduction". Sending somebody to a help page to
// ask about the page they were on is how help stops being used.
//
// It answers and it files. It cannot change anything, and that is structural
// rather than a matter of asking it nicely: there is no path from here into a
// session. Everything in this app is what somebody's claim gets estimated
// from, so it stays in their hands.
//
// Nothing is kept. Closing, starting a new chat or changing name loses the
// conversation, which is the honest behaviour when there is nowhere private to
// put a transcript that may name a hospital and a treatment.
//
// It answers in the language it was asked in, which in this country is often
// one language written in another one's letters. Everything this app wrote
// itself is looked up here by the key the server sends beside it; a model's
// answer is not, because it came back already written in the right language and
// looking it up would swap it for an answer to a different question.

// Below this the panel is a sheet at the bottom of the screen. Dragging a
// window around a phone is a way to lose it behind your own thumb.
const DRAG_FROM = 640

const KINDS = [
  ['feedback', 'Feedback'],
  ['problem', 'Something is not working'],
  ['data', 'Something I cannot change myself'],
]

// What the server sends beside anything it wrote down: an opening, a refusal,
// an answer out of the knowledge base. `said` is empty for a model's answer.
const said = (t, key, text) => (key ? t(`helpsay.${key}`, text) : text)

export function HelpDesk({ screen, user, language }) {
  const t = useT()
  const [open, setOpen] = useState(false)
  const [turns, setTurns] = useState([])
  const [opening, setOpening] = useState(null)
  const [asking, setAsking] = useState(false)
  const [draft, setDraft] = useState('')
  const [ticketing, setTicketing] = useState(false)
  const endRef = useRef(null)

  // Asked for once per screen, so the chips offered are about what is on it.
  useEffect(() => {
    if (!open) return
    api.helpOpening(screen).then(setOpening).catch(() => setOpening(null))
  }, [open, screen])

  useEffect(() => {
    endRef.current?.scrollIntoView({ block: 'end', behavior: 'smooth' })
  }, [turns, asking])

  // The answer is put on screen while it is still being written, and replaced
  // by the finished one when it arrives. The two differ only when the server
  // stopped a draft part way, and then replacing it is the whole point.
  const ask = useCallback(async (message) => {
    const question = message.trim()
    if (!question || asking) return
    setDraft('')
    setTurns((current) => [
      ...current,
      { role: 'you', text: question },
      { role: 'desk', text: '', writing: true },
    ])
    setAsking(true)

    const onDelta = (piece) => {
      setTurns((current) => current.map((turn, index) =>
        index === current.length - 1 && turn.writing
          ? { ...turn, text: turn.text + piece }
          : turn
      ))
    }
    const settle = (turn) => {
      setTurns((current) => [...current.slice(0, -1), { role: 'desk', ...turn }])
    }

    try {
      settle(await api.helpAsk({ message: question, screen, language }, onDelta))
    } catch {
      settle({
        text: t(
          'help.unreachable',
          'I could not reach the help desk just now. Your work is not affected, '
            + 'and the app itself is still working.'),
      })
    } finally {
      setAsking(false)
    }
  }, [asking, screen, language, t])

  function startOver() {
    setTurns([])
    setTicketing(false)
  }

  async function file(kind, subject, detail) {
    const ticket = await api.raiseTicket({ kind, subject, detail, screen })
    saveTicket(user, ticket)
    setTicketing(false)
    setTurns((current) => [...current, {
      role: 'desk',
      text: t(
        'help.logged',
        'Logged as {id}. You can see it under Settings, Your tickets.',
        { id: ticket.ticket_id }
      ) + ' ' + t('help.logged.note', ticket.note),
      ticket: ticket.ticket_id,
    }])
    return ticket
  }

  return (
    <>
      <Launcher open={open} onToggle={() => setOpen(!open)} t={t} />
      {open && (
        <Panel
          t={t}
          turns={turns}
          opening={opening}
          asking={asking}
          draft={draft}
          setDraft={setDraft}
          onAsk={ask}
          onClose={() => setOpen(false)}
          onStartOver={startOver}
          ticketing={ticketing}
          setTicketing={setTicketing}
          onFile={file}
          endRef={endRef}
        />
      )}
    </>
  )
}

function Launcher({ open, onToggle, t }) {
  return (
    <button
      onClick={onToggle}
      aria-expanded={open}
      aria-label={t('help.open', 'Help')}
      className={`fixed bottom-safe right-4 z-30 flex h-14 w-14 items-center justify-center rounded-full border border-line bg-brand text-on-brand shadow-lg transition hover:scale-105 active:scale-95 sm:h-12 sm:w-12 ${
        open ? 'opacity-0 pointer-events-none' : 'opacity-100'
      }`}
    >
      <ChatIcon />
    </button>
  )
}

function Panel({
  t, turns, opening, asking, draft, setDraft, onAsk, onClose, onStartOver,
  ticketing, setTicketing, onFile, endRef,
}) {
  const { style, onGrab, dragging } = useDrag()

  return (
    <section
      role="dialog"
      aria-label={t('help.title', 'Help')}
      style={style}
      className={`fixed z-30 flex flex-col overflow-hidden rounded-2xl border border-line bg-surface shadow-2xl motion-safe:animate-rise
        inset-x-2 bottom-2 max-h-[72dvh]
        sm:inset-x-auto sm:bottom-4 sm:right-4 sm:h-[30rem] sm:max-h-[80dvh] sm:w-[22rem]
        ${dragging ? 'select-none' : ''}`}
    >
      {/* The handle is the header, which is where anybody would try first.
          Only a pointer device gets it: on a phone the panel is a sheet at the
          bottom and moving it is a way to lose it under your own thumb. */}
      <header
        onPointerDown={onGrab}
        className="flex items-center justify-between gap-2 border-b border-line bg-canvas px-3 py-2.5 sm:cursor-grab sm:active:cursor-grabbing"
      >
        <div className="flex min-w-0 items-center gap-2">
          <span className="grid h-6 w-6 shrink-0 place-items-center rounded-full bg-brand text-on-brand">
            <ChatIcon small />
          </span>
          <h2 className="truncate text-[0.875rem] font-semibold">
            {t('help.title', 'Help')}
          </h2>
        </div>
        <div className="flex shrink-0 items-center gap-1">
          <button
            onClick={onStartOver}
            className="rounded px-2.5 py-2 text-[0.75rem] text-muted hover:bg-surface hover:text-ink"
          >
            {t('help.new_chat', 'New chat')}
          </button>
          <button
            onClick={onClose}
            aria-label={t('help.close', 'Close help')}
            className="rounded px-2.5 py-2 text-[0.875rem] text-muted hover:bg-surface hover:text-ink"
          >
            ✕
          </button>
        </div>
      </header>

      <div className="flex-1 space-y-3 overflow-y-auto px-3 py-3">
        {turns.length === 0 && opening && (
          <Bubble>{said(t, opening.key, opening.text)}</Bubble>
        )}

        {turns.map((turn, index) => (
          turn.role === 'you' ? (
            <p
              key={index}
              className="ml-auto max-w-[85%] rounded-2xl rounded-br-sm bg-brand px-3 py-2 text-[0.8125rem] leading-relaxed text-on-brand"
            >
              {turn.text}
            </p>
          ) : (
            <div key={index} className="space-y-2">
              {(turn.text || !turn.writing) && (
                <Bubble writing={turn.writing}>
                  {said(t, turn.key, turn.text)}
                </Bubble>
              )}
              {turn.offer_ticket && !ticketing && (
                <button
                  onClick={() => setTicketing(true)}
                  className="text-[0.75rem] text-brand underline"
                >
                  {t('help.raise', 'Pass this to the team')}
                </button>
              )}
            </div>
          )
        ))}

        {/* Only until the first words arrive. After that the answer writing
            itself is a better sign of life than a spinner beside it. */}
        {asking && !turns[turns.length - 1]?.text && (
          <Spinner label={t('help.thinking', 'Looking that up')} />
        )}

        {ticketing && (
          <TicketForm t={t} onCancel={() => setTicketing(false)} onFile={onFile} />
        )}

        {!ticketing && !asking && (
          <Chips
            t={t}
            suggestions={
              (turns.length ? turns[turns.length - 1]?.suggestions : opening?.suggestions) ?? []
            }
            onPick={onAsk}
          />
        )}

        <div ref={endRef} />
      </div>

      <form
        onSubmit={(event) => { event.preventDefault(); onAsk(draft) }}
        className="flex items-center gap-2 border-t border-line px-3 py-2.5 pb-safe sm:pb-2.5"
      >
        <input
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          maxLength={2000}
          placeholder={t('help.placeholder', 'Ask about anything on this screen')}
          className="min-w-0 flex-1 rounded-lg border border-line bg-canvas px-3 py-2.5 text-base outline-none focus:border-brand sm:py-2 sm:text-[0.8125rem]"
        />
        <Button type="submit" disabled={!draft.trim() || asking} className="px-3 py-2">
          {t('help.send', 'Ask')}
        </Button>
      </form>

      <p className="hidden border-t border-line px-3 py-2 text-[0.6875rem] leading-relaxed text-muted sm:block">
        {t(
          'help.footer',
          'Guidance only, never medical advice, and it cannot change your stay. ' +
            'Nothing here is kept once you close it.')}
      </p>
    </section>
  )
}

function Bubble({ children, writing = false }) {
  return (
    <div className="max-w-[92%] whitespace-pre-line rounded-2xl rounded-bl-sm border border-line bg-canvas px-3 py-2 text-[0.8125rem] leading-relaxed">
      {children}
      {/* A cursor where the next word will land, so a pause reads as thinking
          rather than as a message that has stopped. */}
      {writing && (
        <span className="ml-0.5 inline-block h-3 w-1.5 translate-y-px bg-brand/70 motion-safe:animate-breathe" />
      )}
    </div>
  )
}

function Chips({ suggestions, onPick, t }) {
  if (!suggestions.length) return null
  return (
    <div className="flex flex-wrap gap-1.5 pt-1">
      {suggestions.map((suggestion) => (
        <button
          key={suggestion.key}
          onClick={() => onPick(t(`helpq.${suggestion.key}`, suggestion.question))}
          className="rounded-full border border-line px-2.5 py-1 text-left text-[0.75rem] text-muted transition hover:border-brand/40 hover:text-ink"
        >
          {t(`helpq.${suggestion.key}`, suggestion.question)}
        </button>
      ))}
    </div>
  )
}

function TicketForm({ t, onCancel, onFile }) {
  const [kind, setKind] = useState('feedback')
  const [subject, setSubject] = useState('')
  const [detail, setDetail] = useState('')
  const [busy, setBusy] = useState(false)

  return (
    <form
      onSubmit={async (event) => {
        event.preventDefault()
        if (!subject.trim() || busy) return
        setBusy(true)
        try {
          await onFile(kind, subject, detail)
        } finally {
          setBusy(false)
        }
      }}
      className="space-y-2 rounded-xl border border-line bg-canvas p-3"
    >
      <p className="text-[0.75rem] font-medium">
        {t('help.ticket_title', 'Pass it to the team')}
      </p>
      <select
        value={kind}
        onChange={(event) => setKind(event.target.value)}
        className="w-full rounded-lg border border-line bg-surface px-2 py-2 text-base sm:py-1.5 sm:text-[0.8125rem]"
      >
        {KINDS.map(([value, label]) => (
          <option key={value} value={value}>{t(`ticket.${value}`, label)}</option>
        ))}
      </select>
      <input
        value={subject}
        onChange={(event) => setSubject(event.target.value)}
        maxLength={200}
        placeholder={t('help.ticket_subject', 'In one line')}
        className="w-full rounded-lg border border-line bg-surface px-2 py-2 text-base sm:py-1.5 sm:text-[0.8125rem]"
      />
      <textarea
        value={detail}
        onChange={(event) => setDetail(event.target.value)}
        maxLength={4000}
        rows={3}
        placeholder={t('help.ticket_detail', 'Anything else worth knowing')}
        className="w-full rounded-lg border border-line bg-surface px-2 py-2 text-base sm:py-1.5 sm:text-[0.8125rem]"
      />
      <div className="flex gap-2">
        <Button type="submit" disabled={!subject.trim() || busy} className="px-3 py-1.5">
          {busy ? t('help.filing', 'Filing') : t('help.file', 'Send it')}
        </Button>
        <Button variant="secondary" onClick={onCancel} className="px-3 py-1.5">
          {t('help.cancel', 'Cancel')}
        </Button>
      </div>
    </form>
  )
}

// Moving the panel out of the way of what it is covering.
//
// Pointer events rather than mouse events, so a stylus and a trackpad behave
// the same. The position is clamped to the viewport on every move: a window
// dragged off the edge of the screen is a window somebody has lost.
function useDrag() {
  const [at, setAt] = useState(null)
  const [dragging, setDragging] = useState(false)
  const from = useRef(null)

  const onGrab = useCallback((event) => {
    if (window.innerWidth < DRAG_FROM) return
    // The handle is the whole header, and the buttons sit inside it. Capturing
    // the pointer here sent the release to the header as well, so "New chat"
    // and the close button never completed a click: they were pressed, the
    // header took the pointer, and no click ever landed on them. A press that
    // starts on a control is that control's, not the handle's.
    if (event.target.closest('button')) return
    const panel = event.currentTarget.parentElement
    const box = panel.getBoundingClientRect()
    from.current = {
      dx: event.clientX - box.left, dy: event.clientY - box.top,
      w: box.width, h: box.height,
    }
    setDragging(true)
    event.currentTarget.setPointerCapture?.(event.pointerId)
  }, [])

  useEffect(() => {
    if (!dragging) return

    const move = (event) => {
      const grab = from.current
      if (!grab) return
      const margin = 8
      setAt({
        left: Math.min(
          Math.max(event.clientX - grab.dx, margin),
          window.innerWidth - grab.w - margin
        ),
        top: Math.min(
          Math.max(event.clientY - grab.dy, margin),
          window.innerHeight - grab.h - margin
        ),
      })
    }
    const drop = () => setDragging(false)

    window.addEventListener('pointermove', move)
    window.addEventListener('pointerup', drop)
    window.addEventListener('pointercancel', drop)
    return () => {
      window.removeEventListener('pointermove', move)
      window.removeEventListener('pointerup', drop)
      window.removeEventListener('pointercancel', drop)
    }
  }, [dragging])

  // A panel dragged on a wide screen and then met on a narrow one has to give
  // its position back, or it sits pinned somewhere off the side of a phone.
  useEffect(() => {
    const onResize = () => {
      if (window.innerWidth < DRAG_FROM) setAt(null)
    }
    window.addEventListener('resize', onResize)
    return () => window.removeEventListener('resize', onResize)
  }, [])

  const style = at
    ? { left: at.left, top: at.top, right: 'auto', bottom: 'auto' }
    : undefined

  return { style, onGrab, dragging }
}

function ChatIcon({ small = false }) {
  const size = small ? 13 : 20
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
         stroke="currentColor" strokeWidth="2" strokeLinecap="round"
         strokeLinejoin="round" aria-hidden="true">
      <path d="M21 11.5a8.4 8.4 0 0 1-9 8.4 8.9 8.9 0 0 1-4-.9L3 21l1.9-4.6a8.4 8.4 0 0 1-.9-4A8.4 8.4 0 0 1 12.5 4h.5a8.4 8.4 0 0 1 8 7.5z" />
    </svg>
  )
}
