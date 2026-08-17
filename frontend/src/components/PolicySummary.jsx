import { useState } from 'react'
import { Badge, Button, Card, CardHeader, Input } from './Primitives'

// What we read from the policy, and the things we could not settle.
//
// Open questions are shown before the summary and one at a time. A person who
// has just uploaded a document under stress can answer one clear question; a
// form of six is abandoned.

// A scheme has none of the things the indemnity grid asks about. Rendering it
// through that grid put a room rent limit and a co-payment in front of a PM-JAY
// beneficiary and told them consumables were theirs to pay, which is false and
// false in the frightening direction. It is described in its own terms instead.
function SchemeFacts({ policy }) {
  return (
    <>
      <div className="grid gap-px bg-line sm:grid-cols-2">
        <Fact
          label="Cover this year"
          value={policy.sum_insured_display}
          note="Shared across your family for the year."
          emphasis
        />
        <Fact
          label="What you pay at an empanelled hospital"
          value="Nothing"
          note="Treatment is bought at a fixed package rate. There is no bill to settle and nothing to claim back."
        />
        <Fact
          label="Room included"
          value={policy.room_limit.description}
          note="A higher room is yours to pay for, but it does not reduce what the scheme covers on anything else."
        />
        <Fact
          label="Consumables, implants, medicines, tests"
          value="Included in the package"
        />
      </div>
      {policy.scheme_note && (
        <div className="border-t border-line px-5 py-3.5">
          <p className="text-[0.875rem] leading-relaxed text-muted">
            {policy.scheme_note}
          </p>
        </div>
      )}
      <div className="border-t border-line bg-warn-soft px-5 py-3.5">
        <p className="text-[0.875rem] leading-relaxed text-warn">
          This only works at a hospital empanelled for {policy.scheme_label}.
          Anywhere else the scheme pays nothing, and there is no claim to make
          afterwards. The hospitals we show you are filtered on this.
        </p>
      </div>
    </>
  )
}

export function PolicySummary({ policy, onAnswer, onContinue, answering }) {
  const question = policy.questions?.[0]

  return (
    <div className="space-y-5">
      {question && (
        <ClarificationCard
          question={question}
          remaining={policy.questions.length - 1}
          onAnswer={onAnswer}
          busy={answering}
        />
      )}

      {policy.warnings?.length > 0 && (
        <Card className="border-warn/30 bg-warn-soft">
          <div className="px-5 py-4">
            <h3 className="text-[0.875rem] font-semibold text-warn">
              About the document you uploaded
            </h3>
            <ul className="mt-2 space-y-1 text-[0.875rem] leading-relaxed text-warn">
              {policy.warnings.map((warning) => (
                <li key={warning}>{warning}</li>
              ))}
            </ul>
          </div>
        </Card>
      )}

      <Card>
        <CardHeader
          title="Your cover"
          subtitle={
            [policy.insurer_name, policy.plan_name].filter(Boolean).join(' · ') ||
            policy.document
          }
          aside={<ConfidenceBadge policy={policy} />}
        />

        {policy.government_scheme ? (
          <SchemeFacts policy={policy} />
        ) : (
          <div className="grid gap-px bg-line sm:grid-cols-2 [&>*:last-child:nth-child(odd)]:sm:col-span-2">
            <Fact
              label="Total cover this year"
              value={policy.sum_insured_display}
              emphasis
            />
            <Fact
              label="Room you are covered for"
              value={policy.room_limit.description}
              note={
                policy.room_limit.daily_cap
                  ? 'A costlier room also reduces what your insurer pays on surgeon, theatre and nursing charges.'
                  : null
              }
            />
            <Fact
              label="Your share of every claim"
              value={policy.copay_pct > 0 ? `${policy.copay_pct}%` : 'None'}
            />
            <Fact label="ICU cover" value={policy.icu_limit} />
            {policy.deductible > 0 && (
              <Fact
                label="You pay first"
                value={`₹${policy.deductible.toLocaleString('en-IN')}`}
                note="This is a top-up policy. It pays only above this amount."
              />
            )}
            <Fact
              label="Consumables"
              value={policy.covers_consumables ? 'Covered' : 'Not covered'}
              note={
                policy.covers_consumables
                  ? null
                  : 'Gloves, syringes and similar items are yours to pay.'
              }
            />
          </div>
        )}

        {policy.sublimits?.length > 0 && (
          <div className="border-t border-line px-5 py-4">
            <h3 className="text-[0.8125rem] font-medium text-muted">Separate limits</h3>
            <ul className="mt-2 space-y-1.5">
              {policy.sublimits.map((limit) => (
                <li key={limit.label} className="flex justify-between text-[0.875rem]">
                  <span>{limit.label}</span>
                  <span className="tabular-nums font-medium">{limit.amount_display}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {policy.waiting_periods?.length > 0 && (
          <div className="border-t border-line px-5 py-4">
            <h3 className="text-[0.8125rem] font-medium text-muted">Waiting periods</h3>
            <ul className="mt-2 space-y-1.5">
              {policy.waiting_periods.map((wait, index) => (
                <li key={index} className="flex justify-between gap-4 text-[0.875rem]">
                  <span className="text-muted">{wait.applies_to}</span>
                  <span className="shrink-0 font-medium">
                    {wait.months === 1 ? '30 days' : `${wait.months} months`}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}

        <div className="border-t border-line px-5 py-4">
          <Button onClick={onContinue} className="w-full sm:w-auto">
            Find hospitals I am covered at
          </Button>
        </div>
      </Card>

      <EvidenceTable clauses={policy.clauses} />
    </div>
  )
}

function ConfidenceBadge({ policy }) {
  if (policy.questions?.length) {
    return <Badge tone="warn">{policy.questions.length} to confirm</Badge>
  }
  if (policy.needed_ocr && policy.read_quality < 0.85) {
    return <Badge tone="warn">Read from a scan</Badge>
  }
  return <Badge tone="good">Read cleanly</Badge>
}

function Fact({ label, value, note, emphasis }) {
  return (
    <div className="bg-surface px-5 py-4">
      <div className="text-[0.8125rem] text-muted">{label}</div>
      <div className={`mt-1 font-semibold ${emphasis ? 'text-[1.375rem]' : 'text-[0.9375rem]'}`}>
        {value}
      </div>
      {note && <p className="mt-1.5 text-[0.75rem] leading-relaxed text-muted">{note}</p>}
    </div>
  )
}

function ClarificationCard({ question, remaining, onAnswer, busy }) {
  const [typed, setTyped] = useState(
    question.suggested != null ? String(question.suggested) : ''
  )

  return (
    <Card className="border-brand/30 ring-1 ring-brand/10">
      <div className="px-5 py-4">
        <div className="flex items-center justify-between">
          <h3 className="text-[0.875rem] font-semibold text-brand">We need one thing from you</h3>
          {remaining > 0 && (
            <span className="text-[0.75rem] text-muted">{remaining} more after this</span>
          )}
        </div>

        <p className="mt-2.5 text-[0.9375rem] font-medium">{question.question}</p>
        {question.help && (
          <p className="mt-1.5 text-[0.8125rem] leading-relaxed text-muted">{question.help}</p>
        )}
        {question.page && (
          <p className="mt-1 text-[0.75rem] text-muted">
            We were looking at page {question.page} of your document.
          </p>
        )}

        <div className="mt-4 space-y-2">
          {question.options?.length > 0 ? (
            question.options.map((option) => (
              <button
                key={option.value}
                disabled={busy}
                onClick={() => onAnswer(question.id, option.value)}
                className="flex w-full items-center justify-between rounded-lg border border-line px-4 py-3 text-left transition hover:border-brand hover:bg-brand-soft disabled:opacity-50"
              >
                <span className="text-[0.9375rem] font-medium">{option.label}</span>
                {option.source && (
                  <span className="text-[0.75rem] text-muted">
                    from the {option.source}
                    {option.page ? `, page ${option.page}` : ''}
                  </span>
                )}
              </button>
            ))
          ) : (
            <div className="flex gap-2">
              <Input
                autoFocus
                value={typed}
                onChange={(event) => setTyped(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter' && typed) onAnswer(question.id, typed)
                }}
                placeholder="Enter the amount"
              />
              <Button disabled={busy || !typed} onClick={() => onAnswer(question.id, typed)}>
                Confirm
              </Button>
            </div>
          )}
        </div>
      </div>
    </Card>
  )
}

function EvidenceTable({ clauses }) {
  const [open, setOpen] = useState(false)
  const shown = (clauses ?? []).filter((c) => c.status !== 'rejected')

  if (shown.length === 0) return null

  return (
    <Card>
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between px-5 py-4 text-left"
      >
        <div>
          <h2 className="text-[0.9375rem] font-semibold tracking-tight">
            Where these figures came from
          </h2>
          <p className="mt-0.5 text-[0.875rem] text-muted">
            {shown.length} passages read from your document
          </p>
        </div>
        <span className="text-[0.8125rem] text-brand">{open ? 'Hide' : 'Show'}</span>
      </button>

      {open && (
        <div className="border-t border-line">
          <ul className="divide-y divide-line">
            {shown.map((clause, index) => (
              <li key={index} className="px-5 py-3">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-[0.8125rem] font-medium">
                    {clause.kind.replace(/_/g, ' ')}
                  </span>
                  <span className="text-[0.75rem] text-muted">
                    page {clause.page} · {clause.section}
                  </span>
                  {clause.confidence < 0.55 && <Badge tone="warn">uncertain</Badge>}
                </div>
                <blockquote className="mt-1.5 border-l-2 border-line pl-3 text-[0.8125rem] leading-relaxed text-muted">
                  {clause.quote}
                </blockquote>
                {clause.notes?.map((note) => (
                  <p key={note} className="mt-1 text-[0.75rem] text-warn">{note}</p>
                ))}
              </li>
            ))}
          </ul>
        </div>
      )}
    </Card>
  )
}
