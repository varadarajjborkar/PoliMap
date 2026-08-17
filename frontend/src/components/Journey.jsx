import { useState } from 'react'
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

export function Journey({ journey, onAdvance, onRecordCost, onFilePreauth, busy }) {
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
                    className={`rounded-full px-2.5 py-1 text-[11px] ${
                      current
                        ? 'bg-brand text-white font-medium'
                        : done
                          ? 'bg-brand-soft text-brand'
                          : 'bg-canvas text-muted'
                    }`}
                  >
                    {label}
                  </span>
                  {index < STAGES.length - 1 && (
                    <span className="text-[10px] text-line">→</span>
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
                    <h3 className={`text-[14px] font-semibold ${style.text}`}>
                      {alert.title}
                    </h3>
                    {alert.amount_display && (
                      <span className={`shrink-0 text-[15px] font-semibold tabular-nums ${style.text}`}>
                        {alert.amount_display}
                      </span>
                    )}
                  </div>
                  <p className="mt-1.5 text-[13px] leading-relaxed">{alert.message}</p>
                  {alert.action && (
                    <p className="mt-2 text-[13px] font-medium leading-relaxed">
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
        <CostCard journey={journey} onRecordCost={onRecordCost} busy={busy} />
      </div>

      <Card>
        <CardHeader title="What has happened so far" />
        <ol className="divide-y divide-line">
          {[...journey.timeline].reverse().map((event, index) => (
            <li key={index} className="px-5 py-3">
              <div className="flex items-baseline justify-between gap-3">
                <span className="text-[13px] font-medium">{event.title}</span>
                <span className="shrink-0 text-[11px] text-muted">
                  {new Date(event.at).toLocaleString('en-IN', {
                    day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit',
                  })}
                </span>
              </div>
              {event.description && (
                <p className="mt-0.5 text-[12px] leading-relaxed text-muted">
                  {event.description}
                </p>
              )}
            </li>
          ))}
        </ol>
      </Card>
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
        <span className="text-[12px] text-muted">Cover used so far</span>
        <span className="text-[13px] font-medium tabular-nums">
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

      <div className="mt-1.5 flex justify-between text-[11px] text-muted">
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
  const [stage, setStage] = useState(journey.next_stages[0] ?? '')

  if (journey.next_stages.length === 0) {
    return (
      <Card>
        <CardHeader title="Your claim is settled" subtitle="Nothing further to track." />
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader title="Move to the next stage" />
      <div className="space-y-3 p-5">
        <Field label="Where are you now?">
          <Select value={stage} onChange={(event) => setStage(event.target.value)}>
            {journey.next_stages.map((value) => (
              <option key={value} value={value}>
                {STAGES.find(([s]) => s === value)?.[1] ?? value}
              </option>
            ))}
          </Select>
        </Field>
        <Button
          className="w-full"
          disabled={busy || !stage}
          onClick={() => onAdvance(stage)}
        >
          Update
        </Button>
      </div>
    </Card>
  )
}

function CostCard({ journey, onRecordCost, busy }) {
  const [head, setHead] = useState('room_rent')
  const [amount, setAmount] = useState('')
  const [advanceDay, setAdvanceDay] = useState(true)

  const heads = [
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

        <label className="flex items-center gap-2 text-[12px] text-muted">
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
              advance_day: advanceDay,
            })
            setAmount('')
          }}
        >
          Add charge
        </Button>

        {journey.costs.length > 0 && (
          <ul className="max-h-32 space-y-1 overflow-y-auto border-t border-line pt-2">
            {[...journey.costs].reverse().map((cost, index) => (
              <li key={index} className="flex justify-between text-[12px]">
                <span className="text-muted">{cost.head}</span>
                <span className="tabular-nums">{cost.amount_display}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </Card>
  )
}
