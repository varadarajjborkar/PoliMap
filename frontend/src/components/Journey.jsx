import { useEffect, useRef, useState } from 'react'
import { api } from '../api'
import { Badge, Button, Card, CardHeader, Field, Input, Select } from './Primitives'

// The care journey: where the paperwork stands, what has been billed, and what
// that means for the cover still available.
//
// Stages are administrative, never clinical. Nothing here records or reasons
// about a diagnosis, and no prompt suggests a course of treatment.

const STAGES = [
  ['pre_admission', 'Choosing a hospital'],
  ['admitted', 'Admitted'],
  ['investigation', 'Tests and scans'],
  ['pre_auth', 'Insurance approval'],
  ['procedure', 'Treatment'],
  ['recovery', 'Recovery'],
  ['discharge_planning', 'Planning discharge'],
  ['settled', 'Claim settled'],
]

const SEVERITY = {
  urgent: { tone: 'bad', border: 'border-danger/25', bg: 'bg-danger-soft', text: 'text-danger' },
  attention: { tone: 'warn', border: 'border-warn/25', bg: 'bg-warn-soft', text: 'text-warn' },
  info: { tone: 'neutral', border: 'border-line', bg: 'bg-canvas', text: 'text-ink' },
}

export function Journey({
  journey, sessionId, busy,
  onAdvance, onRecordCost, onUpdateCost, onDeleteCost, onFilePreauth,
}) {
  if (!journey) return null

  const currentIndex = STAGES.findIndex(([value]) => value === journey.stage)

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader
          title={journey.hospital_name || 'Your stay'}
          subtitle={
            [journey.room, journey.room_rate && `₹${journey.room_rate.toLocaleString('en-IN')} a day`]
              .filter(Boolean)
              .join(' · ')
          }
          aside={<Badge tone="good">{journey.stage_label}</Badge>}
        />

        <div className="px-5 py-4">
          <ol className="flex flex-wrap gap-1">
            {STAGES.map(([value, label], index) => {
              const done = index < currentIndex
              const current = index === currentIndex
              return (
                <li key={value} className="flex items-center gap-1">
                  <span
                    className={`rounded-full px-2.5 py-1 text-[0.6875rem] ${
                      current
                        ? 'bg-brand text-on-brand font-medium'
                        : done
                          ? 'bg-brand-soft text-brand'
                          : 'bg-canvas text-muted'
                    }`}
                  >
                    {label}
                  </span>
                  {index < STAGES.length - 1 && (
                    <span className="text-[0.625rem] text-line">→</span>
                  )}
                </li>
              )
            })}
          </ol>
        </div>

        <BurnDown burn={journey.burn_down} accrued={journey.accrued_display} />
      </Card>

      {journey.alerts.length > 0 && (
        <div className="space-y-3">
          {journey.alerts.map((alert, index) => {
            const style = SEVERITY[alert.severity] ?? SEVERITY.info
            return (
              <Card key={index} className={`${style.border} ${style.bg}`}>
                <div className="px-5 py-4">
                  <div className="flex items-start justify-between gap-3">
                    <h3 className={`text-[0.875rem] font-semibold ${style.text}`}>
                      {alert.title}
                    </h3>
                    {alert.amount_display && (
                      <span className={`shrink-0 text-[0.9375rem] font-semibold tabular-nums ${style.text}`}>
                        {alert.amount_display}
                      </span>
                    )}
                  </div>
                  <p className="mt-1.5 text-[0.8125rem] leading-relaxed">{alert.message}</p>
                  {alert.action && (
                    <p className="mt-2 text-[0.8125rem] font-medium leading-relaxed">
                      → {alert.action}
                    </p>
                  )}
                  {alert.kind === 'pre_auth_due' && !journey.pre_auth_filed && (
                    <Button
                      variant="secondary"
                      className="mt-3"
                      disabled={busy}
                      onClick={onFilePreauth}
                    >
                      Mark pre-authorisation as filed
                    </Button>
                  )}
                </div>
              </Card>
            )
          })}
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-2">
        <AdvanceCard journey={journey} onAdvance={onAdvance} busy={busy} />
        <CostCard onRecordCost={onRecordCost} busy={busy} />
      </div>

      <ChargesCard
        journey={journey}
        sessionId={sessionId}
        busy={busy}
        onUpdateCost={onUpdateCost}
        onDeleteCost={onDeleteCost}
      />

      <Card>
        <CardHeader title="What has happened so far" />
        <ol className="divide-y divide-line">
          {[...journey.timeline].reverse().map((event) => (
            <li key={event.id} className="px-5 py-3">
              <div className="flex items-baseline justify-between gap-3">
                <span className="text-[0.8125rem] font-medium">{event.title}</span>
                <span className="shrink-0 text-[0.6875rem] text-muted">
                  {new Date(event.at).toLocaleString('en-IN', {
                    day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit',
                  })}
                </span>
              </div>
              {event.description && (
                <p className="mt-0.5 text-[0.75rem] leading-relaxed text-muted">
                  {event.description}
                </p>
              )}
              {event.skipped?.length > 0 && (
                <p className="mt-1 text-[0.6875rem] text-muted">
                  Skipped {listOf(event.skipped)}.
                </p>
              )}
              {event.reason && (
                <p className="mt-1 border-l-2 border-line pl-2 text-[0.6875rem] italic leading-relaxed text-muted">
                  {event.reason}
                </p>
              )}
            </li>
          ))}
        </ol>
      </Card>
    </div>
  )
}

// Charges recorded so far, each correctable.
//
// Money entered in a hurry is money entered wrong, so every row can be edited
// or removed. Editing happens inline, next to the row it changes, rather than
// in a modal that hides the list you are checking it against.
function ChargesCard({ journey, sessionId, busy, onUpdateCost, onDeleteCost }) {
  const [editing, setEditing] = useState(null)
  const [menuFor, setMenuFor] = useState(null)

  if (!journey.costs?.length) return null

  return (
    <Card>
      <CardHeader
        title="Charges so far"
        subtitle={`${journey.costs.length} recorded, ${journey.accrued_display} in total`}
      />
      <ul className="divide-y divide-line">
        {[...journey.costs].reverse().map((cost) => (
          <li key={cost.id} className="px-5 py-3">
            {editing === cost.id ? (
              <EditCharge
                cost={cost}
                busy={busy}
                onClose={() => setEditing(null)}
                onSave={(patch) => {
                  setEditing(null)
                  onUpdateCost(cost.id, patch)
                }}
              />
            ) : (
              <div className="flex items-start gap-3">
                <div className="min-w-0 flex-1">
                  <div className="flex items-baseline gap-2">
                    <span className="text-[0.8125rem] font-medium">{cost.head}</span>
                    <span className="text-[0.6875rem] text-muted">
                      {new Date(cost.at).toLocaleString('en-IN', {
                        day: 'numeric', month: 'short',
                        hour: '2-digit', minute: '2-digit',
                      })}
                    </span>
                  </div>
                  {cost.description && (
                    <p className="mt-0.5 text-[0.75rem] text-muted">{cost.description}</p>
                  )}
                  {cost.receipt_name && (
                    <a
                      href={api.receiptUrl(sessionId, cost.id)}
                      target="_blank"
                      rel="noreferrer"
                      className="mt-0.5 inline-block max-w-full truncate text-[0.6875rem] text-brand underline"
                    >
                      {cost.receipt_name}
                    </a>
                  )}
                </div>

                <span className="shrink-0 text-[0.8125rem] font-medium tabular-nums">
                  {cost.amount_display}
                </span>

                <div className="relative shrink-0">
                  <button
                    aria-label={`Options for ${cost.head}`}
                    aria-haspopup="menu"
                    aria-expanded={menuFor === cost.id}
                    onClick={() => setMenuFor(menuFor === cost.id ? null : cost.id)}
                    className="rounded-md px-1.5 py-0.5 text-muted transition hover:bg-canvas hover:text-ink"
                  >
                    &#8942;
                  </button>

                  {menuFor === cost.id && (
                    <>
                      <button
                        aria-label="Close menu"
                        onClick={() => setMenuFor(null)}
                        className="fixed inset-0 z-10 cursor-default"
                      />
                      <div
                        role="menu"
                        className="absolute right-0 z-20 mt-1 w-32 overflow-hidden rounded-lg border border-line bg-surface shadow-lg"
                      >
                        <button
                          role="menuitem"
                          onClick={() => {
                            setMenuFor(null)
                            setEditing(cost.id)
                          }}
                          className="block w-full px-3 py-2 text-left text-[0.75rem] hover:bg-canvas"
                        >
                          Edit
                        </button>
                        <button
                          role="menuitem"
                          disabled={busy}
                          onClick={() => {
                            setMenuFor(null)
                            onDeleteCost(cost.id)
                          }}
                          className="block w-full px-3 py-2 text-left text-[0.75rem] text-danger hover:bg-danger-soft"
                        >
                          Delete
                        </button>
                      </div>
                    </>
                  )}
                </div>
              </div>
            )}
          </li>
        ))}
      </ul>
    </Card>
  )
}

// `datetime-local` wants a naive local string, not an ISO instant.
function toLocalInput(iso) {
  const d = new Date(iso)
  const pad = (n) => String(n).padStart(2, '0')
  return (
    `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}` +
    `T${pad(d.getHours())}:${pad(d.getMinutes())}`
  )
}

function EditCharge({ cost, onSave, onClose, busy }) {
  const [head, setHead] = useState(cost.head_value)
  const [amount, setAmount] = useState(String(cost.amount))
  const [at, setAt] = useState(toLocalInput(cost.at))

  return (
    <div className="rounded-lg border border-brand/30 bg-canvas p-3">
      <div className="grid gap-3 sm:grid-cols-2">
        <Field label="What is it for?">
          <Select value={head} onChange={(event) => setHead(event.target.value)}>
            {HEADS.map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </Select>
        </Field>

        <Field label="Amount">
          <Input
            type="number"
            value={amount}
            onChange={(event) => setAmount(event.target.value)}
          />
        </Field>

        <div className="sm:col-span-2">
          <Field label="When">
            <Input
              type="datetime-local"
              value={at}
              onChange={(event) => setAt(event.target.value)}
            />
          </Field>
        </div>
      </div>

      <div className="mt-3 flex flex-wrap gap-2">
        <Button
          disabled={busy || !amount || Number(amount) <= 0}
          onClick={() =>
            onSave({
              head,
              amount: Number(amount),
              at: new Date(at).toISOString(),
            })
          }
        >
          Save
        </Button>
        <Button variant="secondary" onClick={onClose}>
          Close
        </Button>
      </div>
    </div>
  )
}

function BurnDown({ burn, accrued }) {
  const used = Math.min(100, burn.consumed_fraction * 100)
  const projected = Math.min(
    100,
    burn.sum_insured > 0 ? (burn.projected / burn.sum_insured) * 100 : 0
  )

  return (
    <div className="border-t border-line px-5 py-4">
      <div className="flex items-baseline justify-between">
        <span className="text-[0.75rem] text-muted">Cover used so far</span>
        <span className="text-[0.8125rem] font-medium tabular-nums">
          {accrued} of ₹{burn.sum_insured.toLocaleString('en-IN')}
        </span>
      </div>

      <div className="relative mt-2 h-2.5 overflow-hidden rounded-full bg-line">
        {burn.will_exceed && (
          <div
            className="absolute inset-y-0 left-0 bg-warn/25"
            style={{ width: `${projected}%` }}
          />
        )}
        <div
          className={`absolute inset-y-0 left-0 rounded-full ${
            used > 90 ? 'bg-danger' : used > 70 ? 'bg-warn' : 'bg-brand'
          }`}
          style={{ width: `${used}%` }}
        />
      </div>

      <div className="mt-1.5 flex justify-between text-[0.6875rem] text-muted">
        <span>{burn.remaining_display} left</span>
        {burn.will_exceed && (
          <span className="text-warn">
            On track to pass your cover
          </span>
        )}
      </div>
    </div>
  )
}

function AdvanceCard({ journey, onAdvance, busy }) {
  // Keyed on the current stage, so the selection resets to the next step in
  // sequence every time the journey moves. Holding it in state across a move
  // is what left the control offering a stage that had already passed.
  const [stage, setStage] = useState(journey.next_stage ?? journey.stage)
  const [pending, setPending] = useState(null)

  useEffect(() => {
    setStage(journey.next_stage ?? journey.stage)
  }, [journey.stage, journey.next_stage])

  const stages = journey.stages ?? []
  const chosen = stages.find((s) => s.value === stage)
  const done = !journey.next_stage

  function submit() {
    if (!chosen || chosen.kind === 'current') return
    // A skip is the only move worth interrupting for. Going back is a
    // correction, and correcting something should never need a permission slip.
    if (chosen.kind === 'skip') {
      setPending(chosen)
      return
    }
    onAdvance(stage, {})
  }

  return (
    <Card>
      <CardHeader
        title={done ? 'Your claim is settled' : 'Where are you now?'}
        subtitle={
          done
            ? 'You can still go back to an earlier stage if something changes.'
            : 'Update this as things move. You can go back at any point.'
        }
      />
      <div className="space-y-3 p-5">
        <Field label="Stage">
          <Select value={stage} onChange={(event) => setStage(event.target.value)}>
            {stages.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
                {s.kind === 'current' ? '  (you are here)' : ''}
                {s.kind === 'back' ? '  (go back)' : ''}
              </option>
            ))}
          </Select>
        </Field>

        {chosen?.kind === 'back' && (
          <p className="text-[0.75rem] leading-relaxed text-muted">
            This moves your stay back to {chosen.label.toLowerCase()}. Nothing
            you have recorded is lost.
          </p>
        )}

        <Button
          className="w-full"
          disabled={busy || !chosen || chosen.kind === 'current'}
          onClick={submit}
        >
          {chosen?.kind === 'back' ? 'Go back to this stage' : 'Update'}
        </Button>
      </div>

      {pending && (
        <SkipDialog
          target={pending}
          busy={busy}
          onCancel={() => setPending(null)}
          onConfirm={(reason) => {
            setPending(null)
            onAdvance(pending.value, { confirmSkip: true, reason })
          }}
        />
      )}
    </Card>
  )
}

// Shown when a move passes over stages. Deliberately quiet: the person reading
// it may be standing in a hospital corridor, and nothing here is an error. It
// states what is being skipped, offers to go on, and offers a way back out.
function SkipDialog({ target, onConfirm, onCancel, busy }) {
  const [explain, setExplain] = useState(false)
  const [reason, setReason] = useState('')

  useEffect(() => {
    const onKey = (event) => event.key === 'Escape' && onCancel()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onCancel])

  const skipped = target.skips ?? []

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center p-4 sm:items-center">
      <button aria-label="Cancel" onClick={onCancel} className="absolute inset-0 bg-ink/30" />

      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="skip-title"
        className="relative w-full max-w-md rounded-xl border border-line bg-surface shadow-xl"
      >
        <div className="px-5 py-4">
          <h3 id="skip-title" className="text-[0.9375rem] font-semibold">
            Just so you know
          </h3>
          <p className="mt-2 text-[0.8125rem] leading-relaxed">
            Moving straight to <strong>{target.label.toLowerCase()}</strong> passes
            over {listOf(skipped)}.
          </p>
          <p className="mt-2 text-[0.75rem] leading-relaxed text-muted">
            That is often exactly right. Plenty of admissions never involve some
            of these. Your estimate stays accurate either way, and you can come
            back to any stage later.
          </p>

          <label className="mt-4 flex items-start gap-2 text-[0.75rem] text-muted">
            <input
              type="checkbox"
              checked={explain}
              onChange={(event) => setExplain(event.target.checked)}
              className="mt-0.5 rounded border-line"
            />
            I would like to note why (optional)
          </label>

          {explain && (
            <textarea
              autoFocus
              rows={3}
              value={reason}
              onChange={(event) => setReason(event.target.value)}
              maxLength={600}
              placeholder="For example: admitted through emergency, so there was no time for pre-approval."
              className="mt-2 w-full rounded-lg border border-line bg-surface px-3 py-2 text-[0.8125rem] outline-none focus:border-brand focus:ring-2 focus:ring-brand/15"
            />
          )}
        </div>

        <div className="flex flex-wrap gap-2 border-t border-line px-5 py-3">
          <Button disabled={busy} onClick={() => onConfirm(reason)}>
            Skip to {target.label.toLowerCase()}
          </Button>
          <Button variant="secondary" disabled={busy} onClick={onCancel}>
            Not yet
          </Button>
        </div>
      </div>
    </div>
  )
}

function listOf(items) {
  const names = items.map((s) => s.toLowerCase())
  if (names.length === 0) return 'a stage'
  if (names.length === 1) return names[0]
  return `${names.slice(0, -1).join(', ')} and ${names[names.length - 1]}`
}

const HEADS = [
  ['room_rent', 'Room rent'],
  ['icu_charges', 'ICU charges'],
  ['investigations', 'Tests and scans'],
  ['pharmacy', 'Medicines'],
  ['consumables', 'Consumables'],
  ['surgeon_fee', "Surgeon's fee"],
  ['ot_charges', 'Operation theatre'],
  ['nursing', 'Nursing'],
  ['implants', 'Implants'],
  ['non_medical', 'Non-medical items'],
]

function CostCard({ onRecordCost, busy }) {
  const [head, setHead] = useState('room_rent')
  const [amount, setAmount] = useState('')
  const [advanceDay, setAdvanceDay] = useState(true)
  const [receipt, setReceipt] = useState(null)
  const fileRef = useRef(null)

  const heads = HEADS

  return (
    <Card>
      <CardHeader
        title="Add a charge"
        subtitle="Enter bills as they arrive to keep the estimate current."
      />
      <div className="space-y-3 p-5">
        <Field label="What is it for?">
          <Select value={head} onChange={(event) => setHead(event.target.value)}>
            {heads.map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </Select>
        </Field>

        <Field label="Amount">
          <Input
            type="number"
            placeholder="0"
            value={amount}
            onChange={(event) => setAmount(event.target.value)}
          />
        </Field>

        {/* Attaching the bill now saves hunting for it at claim time, which is
            the part of this people actually dread. Entirely optional. */}
        <div>
          <input
            ref={fileRef}
            type="file"
            accept=".pdf,.jpg,.jpeg,.png,.webp,.heic,.tif,.tiff"
            className="hidden"
            onChange={(event) => setReceipt(event.target.files?.[0] ?? null)}
          />
          {receipt ? (
            <div className="flex items-center justify-between gap-2 rounded-lg border border-line bg-canvas px-3 py-2">
              <span className="min-w-0 flex-1 truncate text-[0.75rem]">
                {receipt.name}
              </span>
              <button
                onClick={() => {
                  setReceipt(null)
                  if (fileRef.current) fileRef.current.value = ''
                }}
                className="shrink-0 text-[0.6875rem] text-muted underline"
              >
                remove
              </button>
            </div>
          ) : (
            <button
              onClick={() => fileRef.current?.click()}
              className="w-full rounded-lg border border-dashed border-line px-3 py-2 text-[0.75rem] text-muted transition hover:border-brand/40 hover:text-ink"
            >
              Attach the bill or receipt (optional)
            </button>
          )}
        </div>

        <label className="flex items-center gap-2 text-[0.75rem] text-muted">
          <input
            type="checkbox"
            checked={advanceDay}
            onChange={(event) => setAdvanceDay(event.target.checked)}
            className="rounded border-line"
          />
          This is a new day of the stay
        </label>

        <Button
          className="w-full"
          disabled={busy || !amount}
          onClick={() => {
            onRecordCost({
              head,
              amount: Number(amount),
              advanceDay,
              receipt,
            })
            setAmount('')
            setReceipt(null)
            if (fileRef.current) fileRef.current.value = ''
          }}
        >
          Add charge
        </Button>
      </div>
    </Card>
  )
}
