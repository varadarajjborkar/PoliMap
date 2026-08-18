import { useMemo, useState } from 'react'
import { Badge, Button, Card, CardHeader, Disclaimer, Field, Input, Select } from './Primitives'
import { TreatmentPicker } from './TreatmentPicker'

// Search controls and ranked results.
//
// The headline on every card is what the user pays, not what the hospital
// charges. Everything else on the card exists to justify or qualify that one
// number.

export function SearchPanel({ reference, value, onChange, onSearch, busy }) {
  const set = (key) => (event) => onChange({ ...value, [key]: event.target.value })

  return (
    <Card>
      <CardHeader
        title="What treatment do you need?"
        subtitle="We will find hospitals that do it and show what each would cost you."
      />
      <div className="grid gap-4 p-5 sm:grid-cols-2">
        <div className="sm:col-span-2">
          <Field
            label="Treatment"
            hint="Type what you were told. We will match it to the closest treatment we can cost."
          >
            <TreatmentPicker
              procedures={reference?.procedures ?? []}
              value={value.procedure_code}
              onChange={(code) => onChange({ ...value, procedure_code: code })}
            />
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

// Whether the policy pays at all, which every rupee below it assumes.
//
// Placed above the options rather than instead of them. Someone whose waiting
// period has not run still wants to know what the treatment costs, because
// they are now the one paying for it. What changes is who the figure is for.
export function EligibilityNotice({ eligibility, onAnswer, busy }) {
  if (!eligibility || eligibility.verdict === 'covered') return null

  const blocking = eligibility.blocks
  const question = eligibility.findings.find((f) => f.question)

  return (
    <Card
      className={`motion-safe:animate-rise ${
        blocking ? 'border-danger/40 bg-danger-soft' : 'border-warn/40 bg-warn-soft'
      }`}
    >
      <div className="space-y-3 px-5 py-4">
        <div>
          <p className={`text-[0.9375rem] font-semibold ${blocking ? 'text-danger' : 'text-warn'}`}>
            {blocking
              ? 'Your insurer would decline this claim'
              : eligibility.headline}
          </p>
          <p className="mt-1 text-[0.875rem] leading-relaxed">
            {blocking
              ? 'The costs below are what you would pay yourself.'
              : 'One answer settles this.'}
          </p>
        </div>

        <ul className="space-y-2">
          {eligibility.findings
            .filter((finding) => finding.verdict !== 'covered')
            .map((finding, index) => (
              <li key={index} className="rounded-lg bg-surface/70 px-3 py-2">
                <p className="text-[0.8125rem] font-medium">{finding.headline}</p>
                <p className="mt-0.5 text-[0.8125rem] leading-relaxed text-muted">
                  {finding.detail}
                </p>
              </li>
            ))}
        </ul>

        {question && (
          <div className="rounded-lg border border-line bg-surface px-3 py-3">
            <p className="text-[0.875rem] font-medium">{question.question}</p>
            <p className="mt-0.5 text-[0.8125rem] leading-relaxed text-muted">
              Nothing in your document says this, and it changes the answer, so
              we have to ask. Your answer stays on this device.
            </p>
            <div className="mt-2.5 flex flex-wrap gap-2">
              <Button
                variant="secondary"
                disabled={busy}
                onClick={() => onAnswer({ pre_existing: true })}
              >
                Yes, I had it before
              </Button>
              <Button
                variant="secondary"
                disabled={busy}
                onClick={() => onAnswer({ pre_existing: false })}
              >
                No, it came up after
              </Button>
              <Button
                variant="ghost"
                disabled={busy}
                onClick={() => onAnswer({ accident: true })}
              >
                It was an accident
              </Button>
            </div>
          </div>
        )}
      </div>
    </Card>
  )
}

export function Results({ results, onStartJourney, starting }) {
  const [query, setQuery] = useState('')

  const shown = useMemo(() => {
    if (!results) return []
    const needle = query.trim().toLowerCase()
    if (!needle) return results.options
    // Name and locality, which is how people actually look: either they know
    // the hospital or they know the part of town they can get to.
    return results.options.filter((option) =>
      `${option.hospital.name} ${option.hospital.locality} ${option.hospital.city}`
        .toLowerCase()
        .includes(needle)
    )
  }, [results, query])

  if (!results) return null

  // Judged across every result, not the filtered view: a badge that appeared
  // and disappeared as someone typed in the search box would be saying
  // something about the search rather than about the hospital.
  const allOnFrontier = results.options.every((o) => o.on_frontier)

  return (
    <div className="space-y-4">
      <Card>
        <div className="px-5 py-4">
          <p className="text-[0.9375rem] font-medium">{results.message}</p>
          <p className="mt-1 text-[0.875rem] text-muted">
            We looked at{' '}
            {(results.considered_in_city || results.considered).toLocaleString('en-IN')}
            {' '}hospitals{results.city ? ` in ${results.city}` : ''}.
          </p>
          {results.one_thing_to_change && (
            <p className="mt-1 text-[0.875rem] text-muted">
              {results.one_thing_to_change}
            </p>
          )}

          {results.relaxations?.length > 0 && (
            <div className="mt-3 space-y-2 rounded-lg border border-warn/25 bg-warn-soft p-3">
              <p className="text-[0.8125rem] font-semibold text-warn">
                To find these, we had to relax what you asked for
              </p>
              {results.relaxations.map((relaxation) => (
                <div key={relaxation.kind} className="text-[0.8125rem] leading-relaxed text-warn">
                  <span className="font-medium">{relaxation.description}</span>{' '}
                  {relaxation.consequence}
                </div>
              ))}
            </div>
          )}

          {/* Kept, but folded away. The counts are how the system explains
              itself when challenged, not something to put in front of someone
              who only wants to know where to go. */}
          {results.exclusions?.length > 0 && (
            <details className="mt-3">
              <summary className="cursor-pointer text-[0.8125rem] text-muted">
                Why other hospitals were left out
              </summary>
              <ul className="mt-2 space-y-1 text-[0.8125rem] text-muted">
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

      {results.options.length > 1 && (
        <div className="relative">
          <Input
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Find a hospital by name or area"
            aria-label="Filter these results by hospital name or area"
            className="pl-9"
          />
          <span
            aria-hidden="true"
            className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[0.875rem] text-muted"
          >
            &#9906;
          </span>
        </div>
      )}

      {query && (
        <p className="text-[0.8125rem] text-muted">
          {shown.length === 0
            ? `No hospital here matches "${query}".`
            : `${shown.length} of ${results.options.length} match "${query}".`}
        </p>
      )}

      {shown.map((option) => (
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
            <span className="text-[0.75rem] font-semibold text-muted">#{option.rank}</span>
            <h3 className="text-[1rem] font-semibold tracking-tight">
              {option.hospital.name}
            </h3>
            {option.on_frontier && showFrontierBadge && (
              <Badge tone="good">Strong option</Badge>
            )}
          </div>
          <p className="mt-1 text-[0.8125rem] text-muted">
            {option.hospital.locality} · {option.distance_km} km ·{' '}
            about {option.travel_minutes} min · {option.hospital.accreditation}
          </p>
        </div>

        <div className="text-right">
          <div className="text-[0.8125rem] text-muted">You would pay</div>
          <div className="text-[1.5rem] font-semibold tabular-nums">
            {option.you_pay_display}
          </div>
          {/* Stated as a worst case with its cause rather than a symmetrical
              range. A family braces against a specific thing going wrong, and
              a bare pair of numbers invites the reader to average them. */}
          {option.band && option.band.high > option.band.expected && (
            <div className="mt-0.5 text-[0.8125rem] leading-snug text-muted">
              up to{' '}
              <span className="tabular-nums font-medium">
                {option.band.high_display}
              </span>
              {option.band.high_driver && (
                <span className="block max-w-[13rem] text-[0.75rem] leading-snug">
                  with {option.band.high_driver}
                </span>
              )}
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
        <div className="text-[0.8125rem]">
          <span className="text-muted">Room: </span>
          <span className="font-medium">
            {option.room.label} at {option.room.per_day_display} a day
          </span>
        </div>

        {option.reasons.map((reason) => (
          <p key={reason} className="text-[0.875rem] leading-relaxed">
            <span className="text-brand">✓</span> {reason}
          </p>
        ))}
        {option.tradeoffs.map((tradeoff) => (
          <p key={tradeoff} className="text-[0.875rem] leading-relaxed text-muted">
            <span>−</span> {tradeoff}
          </p>
        ))}

        {option.counterfactual && (
          <p className="rounded-lg bg-brand-soft px-3 py-2 text-[0.875rem] leading-relaxed text-brand">
            {option.counterfactual}
          </p>
        )}

        {option.warnings?.map((warning) => (
          <p
            key={warning}
            className="rounded-lg bg-warn-soft px-3 py-2 text-[0.8125rem] leading-relaxed text-warn"
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
      <div className="text-[0.75rem] text-muted">{label}</div>
      <div
        className={`mt-0.5 text-[0.9375rem] font-semibold tabular-nums ${
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
      <h4 className="text-[0.8125rem] font-semibold">
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
            <p className="mt-1 pl-1 text-[0.75rem] leading-relaxed text-muted">
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
        <summary className="cursor-pointer text-[0.8125rem] text-muted">
          The hospital bill, item by item
        </summary>
        <ul className="mt-2 space-y-1">
          {option.bill_lines.map((line, index) => (
            <li key={index} className="flex justify-between gap-4 text-[0.8125rem]">
              <span className="text-muted">
                {line.label}
                {line.note && <span className="text-[0.6875rem]"> ({line.note})</span>}
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
      <div className="flex items-baseline justify-between gap-4 text-[0.8125rem]">
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
