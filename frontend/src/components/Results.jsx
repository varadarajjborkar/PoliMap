import { useMemo, useState } from 'react'
import { Badge, Button, Card, CardHeader, Disclaimer, Field, Select } from './Primitives'

// Search controls and ranked results.
//
// The headline on every card is what the user pays, not what the hospital
// charges. Everything else on the card exists to justify or qualify that one
// number.

export function SearchPanel({ reference, value, onChange, onSearch, busy }) {
  const grouped = useMemo(() => {
    const map = new Map()
    for (const procedure of reference?.procedures ?? []) {
      if (!map.has(procedure.specialty_label)) map.set(procedure.specialty_label, [])
      map.get(procedure.specialty_label).push(procedure)
    }
    return [...map.entries()].sort(([a], [b]) => a.localeCompare(b))
  }, [reference])

  const set = (key) => (event) => onChange({ ...value, [key]: event.target.value })

  return (
    <Card>
      <CardHeader
        title="What treatment do you need?"
        subtitle="We will find hospitals that do it and show what each would cost you."
      />
      <div className="grid gap-4 p-5 sm:grid-cols-2">
        <div className="sm:col-span-2">
          <Field label="Treatment">
            <Select value={value.procedure_code} onChange={set('procedure_code')}>
              <option value="">Choose a treatment</option>
              {grouped.map(([specialty, procedures]) => (
                <optgroup key={specialty} label={specialty}>
                  {procedures.map((procedure) => (
                    <option key={procedure.code} value={procedure.code}>
                      {procedure.name}
                    </option>
                  ))}
                </optgroup>
              ))}
            </Select>
          </Field>
        </div>

        <Field label="City">
          <Select value={value.city} onChange={set('city')}>
            {(reference?.cities ?? []).map((city) => (
              <option key={city.city} value={city.city}>
                {city.city} ({city.count} hospitals)
              </option>
            ))}
          </Select>
        </Field>

        <Field label="How far can you travel?">
          <Select value={value.max_distance_km} onChange={set('max_distance_km')}>
            {[5, 10, 15, 25, 40].map((km) => (
              <option key={km} value={km}>Up to {km} km</option>
            ))}
          </Select>
        </Field>

        <Field label="What matters most to you?">
          <Select value={value.preference} onChange={set('preference')}>
            {(reference?.preferences ?? []).map((preference) => (
              <option key={preference.value} value={preference.value}>
                {preference.label}
              </option>
            ))}
          </Select>
        </Field>

        <Field label="How soon?">
          <Select value={value.urgency} onChange={set('urgency')}>
            <option value="planned">Planned</option>
            <option value="urgent">Within a few days</option>
            <option value="emergency">Emergency</option>
          </Select>
        </Field>

        <div className="sm:col-span-2">
          <Button
            className="w-full"
            disabled={busy || !value.procedure_code}
            onClick={onSearch}
          >
            {busy ? 'Searching…' : 'Show me my options'}
          </Button>
        </div>
      </div>
    </Card>
  )
}

export function Results({ results, onStartJourney, starting }) {
  if (!results) return null

  const allOnFrontier = results.options.every((o) => o.on_frontier)

  return (
    <div className="space-y-4">
      <Card>
        <div className="px-5 py-4">
          <p className="text-[14px] font-medium">{results.message}</p>
          <p className="mt-1 text-[12px] text-muted">
            We looked at {results.considered.toLocaleString('en-IN')} hospitals.
          </p>

          {results.relaxations?.length > 0 && (
            <div className="mt-3 space-y-2 rounded-lg border border-warn/25 bg-warn-soft p-3">
              <p className="text-[12px] font-semibold text-warn">
                To find these, we had to relax what you asked for
              </p>
              {results.relaxations.map((relaxation) => (
                <div key={relaxation.kind} className="text-[12px] leading-relaxed text-warn">
                  <span className="font-medium">{relaxation.description}</span>{' '}
                  {relaxation.consequence}
                </div>
              ))}
            </div>
          )}

          {results.exclusions?.length > 0 && (
            <details className="mt-3">
              <summary className="cursor-pointer text-[12px] text-muted">
                Why other hospitals were left out
              </summary>
              <ul className="mt-2 space-y-1 text-[12px] text-muted">
                {results.exclusions.map((exclusion) => (
                  <li key={exclusion.reason} className="flex justify-between">
                    <span>{exclusion.reason.replace(/_/g, ' ')}</span>
                    <span className="tabular-nums">{exclusion.count}</span>
                  </li>
                ))}
              </ul>
            </details>
          )}
        </div>
      </Card>

      {results.options.map((option) => (
        <OptionCard
          key={option.hospital.id}
          option={option}
          // A badge every card carries tells the user nothing; it is only worth
          // showing when it actually separates some options from others.
          showFrontierBadge={!allOnFrontier}
          onStart={() => onStartJourney(option)}
          starting={starting}
        />
      ))}

      <Disclaimer />
    </div>
  )
}

function OptionCard({ option, onStart, starting, showFrontierBadge }) {
  const [showDetail, setShowDetail] = useState(false)
  const reimbursement = option.settlement === 'reimbursement'

  return (
    <Card>
      <div className="flex flex-wrap items-start justify-between gap-4 px-5 py-4">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-[11px] font-semibold text-muted">#{option.rank}</span>
            <h3 className="text-[16px] font-semibold tracking-tight">
              {option.hospital.name}
            </h3>
            {option.on_frontier && showFrontierBadge && (
              <Badge tone="good">Strong option</Badge>
            )}
          </div>
          <p className="mt-1 text-[12px] text-muted">
            {option.hospital.locality} · {option.distance_km} km ·{' '}
            about {option.travel_minutes} min · {option.hospital.accreditation}
          </p>
        </div>

        <div className="text-right">
          <div className="text-[11px] text-muted">You would pay</div>
          <div className="text-[24px] font-semibold tabular-nums">
            {option.you_pay_display}
          </div>
          {option.band && (
            <div className="text-[11px] text-muted tabular-nums">
              {option.band.low_display} – {option.band.high_display}
            </div>
          )}
        </div>
      </div>

      <div className="grid gap-px border-y border-line bg-line sm:grid-cols-3">
        <Stat label="Hospital bill" value={option.estimated_bill_display} />
        <Stat label="Insurer pays" value={option.insurer_pays_display} />
        <Stat
          label={reimbursement ? 'You pay upfront' : 'Settlement'}
          value={reimbursement ? option.cash_upfront_display : option.settlement_label}
          tone={reimbursement ? 'warn' : 'neutral'}
        />
      </div>

      <div className="space-y-2.5 px-5 py-4">
        <div className="text-[12px]">
          <span className="text-muted">Room: </span>
          <span className="font-medium">
            {option.room.label} at {option.room.per_day_display} a day
          </span>
        </div>

        {option.reasons.map((reason) => (
          <p key={reason} className="text-[13px] leading-relaxed">
            <span className="text-brand">✓</span> {reason}
          </p>
        ))}
        {option.tradeoffs.map((tradeoff) => (
          <p key={tradeoff} className="text-[13px] leading-relaxed text-muted">
            <span>−</span> {tradeoff}
          </p>
        ))}

        {option.counterfactual && (
          <p className="rounded-lg bg-brand-soft px-3 py-2 text-[13px] leading-relaxed text-brand">
            {option.counterfactual}
          </p>
        )}

        {option.warnings?.map((warning) => (
          <p
            key={warning}
            className="rounded-lg bg-warn-soft px-3 py-2 text-[12px] leading-relaxed text-warn"
          >
            {warning}
          </p>
        ))}
      </div>

      <div className="flex flex-wrap gap-2 border-t border-line px-5 py-3">
        <Button variant="secondary" onClick={() => setShowDetail(!showDetail)}>
          {showDetail ? 'Hide the breakdown' : 'Where does my money go?'}
        </Button>
        <Button onClick={onStart} disabled={starting}>
          Track my stay here
        </Button>
      </div>

      {showDetail && <Waterfall option={option} />}
    </Card>
  )
}

function Stat({ label, value, tone = 'neutral' }) {
  return (
    <div className="bg-surface px-5 py-3">
      <div className="text-[11px] text-muted">{label}</div>
      <div
        className={`mt-0.5 text-[15px] font-semibold tabular-nums ${
          tone === 'warn' ? 'text-warn' : ''
        }`}
      >
        {value}
      </div>
    </div>
  )
}

// The deduction chain. Every step names its cause and explains itself, so the
// final figure is an argument the user can follow rather than an assertion.
function Waterfall({ option }) {
  const bill = option.estimated_bill

  return (
    <div className="border-t border-line bg-canvas px-5 py-4">
      <h4 className="text-[12px] font-semibold">
        From the hospital bill to what you pay
      </h4>

      <div className="mt-3 space-y-2">
        <Row
          label="Hospital bill"
          amount={option.estimated_bill_display}
          width={100}
          tone="base"
        />

        {option.waterfall.map((step, index) => (
          <div key={index}>
            <Row
              label={step.label}
              amount={`− ${step.amount_display}`}
              width={bill > 0 ? (step.payable_after / bill) * 100 : 0}
              tone="deduct"
            />
            <p className="mt-1 pl-1 text-[11px] leading-relaxed text-muted">
              {step.explanation}
              {step.heads?.length > 0 && (
                <span className="text-muted"> ({step.heads.join(', ')})</span>
              )}
            </p>
          </div>
        ))}

        <Row
          label="Your insurer pays"
          amount={option.insurer_pays_display}
          width={bill > 0 ? (option.insurer_pays / bill) * 100 : 0}
          tone="final"
        />
      </div>

      <details className="mt-4">
        <summary className="cursor-pointer text-[12px] text-muted">
          The hospital bill, item by item
        </summary>
        <ul className="mt-2 space-y-1">
          {option.bill_lines.map((line, index) => (
            <li key={index} className="flex justify-between gap-4 text-[12px]">
              <span className="text-muted">
                {line.label}
                {line.note && <span className="text-[10px]"> — {line.note}</span>}
              </span>
              <span className="shrink-0 tabular-nums">{line.amount_display}</span>
            </li>
          ))}
        </ul>
      </details>
    </div>
  )
}

function Row({ label, amount, width, tone }) {
  const colour = {
    base: 'bg-ink/15',
    deduct: 'bg-warn/30',
    final: 'bg-brand/25',
  }[tone]

  return (
    <div>
      <div className="flex items-baseline justify-between gap-4 text-[12px]">
        <span className={tone === 'base' || tone === 'final' ? 'font-medium' : ''}>
          {label}
        </span>
        <span className="shrink-0 tabular-nums">{amount}</span>
      </div>
      <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-line">
        <div
          className={`h-full rounded-full ${colour}`}
          style={{ width: `${Math.max(0, Math.min(100, width))}%` }}
        />
      </div>
    </div>
  )
}
