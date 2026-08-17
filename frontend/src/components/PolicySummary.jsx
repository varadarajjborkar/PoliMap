import { useEffect, useState } from 'react'
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

export function PolicySummary({ policy, onAnswer, onSkip, onContinue, answering }) {
  const question = policy.questions?.[0]

  return (
    <div className="space-y-5">
      {question && (
        <ClarificationCard
          question={question}
          remaining={policy.questions.length - 1}
          onAnswer={onAnswer}
          onSkip={onSkip}
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

// One question at a time, with a way out of it.
//
// The old card offered fixed choices or a box that took digits. Both assume the
// user's situation is one the form anticipated. Often it is not: their document
// says something none of the options covers, or they know the answer in words
// rather than figures. So every set of choices carries an "Other" that opens a
// box, the box accepts prose, and every question can be skipped.
//
// What the box does not do is let the answer steer the system. Text is read
// into the field that was asked about and no other, and anything the server had
// to interpret comes back as a confirmation before it is used.
function ClarificationCard({ question, remaining, onAnswer, onSkip, busy }) {
  const [typed, setTyped] = useState(
    question.suggested != null ? String(question.suggested) : ''
  )
  const [other, setOther] = useState(false)

  // A fresh question resets the box, otherwise an answer to the last one is
  // sitting in it as a default for this one.
  useEffect(() => {
    setTyped(question.suggested != null ? String(question.suggested) : '')
    setOther(false)
  }, [question.id, question.suggested])

  const placeholder =
    question.expects === 'percent'
      ? 'For example 10%, or ten percent'
      : 'For example 5 lakh, 5,00,000, or no limit'

  const showBox = other || !(question.options?.length > 0)

  return (
    <Card className="border-brand/30 ring-1 ring-brand/10 motion-safe:animate-rise">
      <div className="px-5 py-4">
        <div className="flex items-center justify-between gap-3">
          <h3 className="text-[0.875rem] font-semibold text-brand">
            {question.confirming ? 'Just checking' : 'We need one thing from you'}
          </h3>
          {remaining > 0 && (
            <span className="shrink-0 text-[0.75rem] text-muted">
              {remaining} more after this
            </span>
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
          {question.options?.length > 0 && !other &&
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
            ))}

          {question.options?.length > 0 && !other && question.allow_other && (
            <button
              disabled={busy}
              onClick={() => setOther(true)}
              className="flex w-full items-center justify-between rounded-lg border border-dashed border-line px-4 py-3 text-left transition hover:border-brand hover:bg-brand-soft disabled:opacity-50"
            >
              <span className="text-[0.9375rem] font-medium">
                None of these, let me explain
              </span>
            </button>
          )}

          {showBox && (
            <div className="motion-safe:animate-fade">
              <div className="flex gap-2">
                <Input
                  autoFocus
                  value={typed}
                  onChange={(event) => setTyped(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter' && typed) onAnswer(question.id, typed)
                  }}
                  placeholder={placeholder}
                />
                <Button
                  disabled={busy || !typed}
                  onClick={() => onAnswer(question.id, typed)}
                >
                  {busy ? 'Reading…' : 'Confirm'}
                </Button>
              </div>
              <p className="mt-1.5 text-[0.75rem] leading-relaxed text-muted">
                Write it however it appears on your document, in words or
                figures. We will read it back to you before using it.
              </p>
            </div>
          )}
        </div>

        {question.skippable && !question.confirming && (
          <div className="mt-3 flex items-center gap-3 border-t border-line pt-3">
            <button
              disabled={busy}
              onClick={() => onSkip(question.id)}
              className="text-[0.8125rem] text-muted underline-offset-2 transition hover:text-ink hover:underline disabled:opacity-50"
            >
              I do not know this
            </button>
            <span className="text-[0.75rem] text-muted">
              We will carry on and say where we are unsure.
            </span>
          </div>
        )}
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
