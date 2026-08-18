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

export function PolicySummary({ policy, onAnswer, onSkip, onEditField, onContinue, answering }) {
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
              field="sum_insured"
              current={policy.sum_insured}
              hint="However it appears on your policy, e.g. 5 lakh or 500000"
              onEdit={onEditField}
              emphasis
            />
            <Fact
              label="Cover left this year"
              value={policy.available_cover_display}
              field="sum_insured_remaining"
              current={policy.sum_insured_remaining ?? policy.sum_insured}
              hint="What is left after any claim made earlier this policy year."
              onEdit={onEditField}
              note={
                policy.sum_insured_remaining == null
                  ? 'We have assumed no claims yet this year. If you have already claimed, correct this: it changes every estimate.'
                  : policy.restore_benefit
                    ? 'Your policy restores the cover once per year if it runs out.'
                    : null
              }
            />
            <Fact
              label="Room you are covered for"
              value={policy.room_limit.description}
              field="room_limit"
              current={policy.room_limit.daily_cap ?? ''}
              hint="A daily amount, a percentage like 1%, a room type, or 'no limit'"
              onEdit={onEditField}
              note={
                policy.room_limit.daily_cap
                  ? 'A costlier room also reduces what your insurer pays on surgeon, theatre and nursing charges.'
                  : null
              }
            />
            <Fact
              label="Your share of every claim"
              value={policy.copay_pct > 0 ? `${policy.copay_pct}%` : 'None'}
              field="copay_pct"
              current={policy.copay_pct}
              hint="A percentage, e.g. 10. Enter 0 if you have none."
              onEdit={onEditField}
              note={
                policy.copay_pct > 0 && policy.copay_above_age
                  ? `Only on members aged ${policy.copay_above_age} and above. ` +
                    `A younger member's claim has no co-payment.`
                  : null
              }
            />
            <Fact label="ICU cover" value={policy.icu_limit} />
            <Fact
              label="You pay first"
              value={
                policy.deductible > 0
                  ? `₹${policy.deductible.toLocaleString('en-IN')}`
                  : 'Nothing'
              }
              field="deductible"
              current={policy.deductible}
              hint="Only top-up policies have this. Enter 0 if yours does not."
              onEdit={onEditField}
              note={
                policy.deductible > 0
                  ? 'This is a top-up policy. It pays only above this amount.'
                  : null
              }
            />
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

        <WhoIsCovered policy={policy} />
        <WaitingPeriods policy={policy} />

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

// Everyone on the schedule, with their ages.
//
// Not decoration. A family floater is conditioned on its eldest member, and
// whether a pre-existing waiting period is a formality or the whole question
// depends on who is being admitted. It is also the fastest way for someone to
// see that we read their document correctly.
function WhoIsCovered({ policy }) {
  if (!policy.insured?.length) return null

  return (
    <div className="border-t border-line px-5 py-4">
      <div className="flex items-baseline justify-between gap-4">
        <h3 className="text-[0.8125rem] font-medium text-muted">Who is covered</h3>
        {policy.period?.start && (
          <span className="text-[0.75rem] text-muted">
            Cover from {shortDate(policy.period.start)}
            {policy.period.end ? ` to ${shortDate(policy.period.end)}` : ''}
          </span>
        )}
      </div>

      <ul className="mt-2 space-y-1.5">
        {policy.insured.map((person, index) => (
          <li key={`${person.name}-${index}`} className="flex justify-between gap-4 text-[0.875rem]">
            <span className="min-w-0 truncate">
              {person.name}
              {person.relationship && (
                <span className="text-muted"> · {person.relationship}</span>
              )}
            </span>
            {person.age != null && (
              <span className="shrink-0 tabular-nums text-muted">{person.age}</span>
            )}
          </li>
        ))}
      </ul>

      {policy.period?.days_left != null && policy.period.days_left <= 45 && (
        <p className="mt-2.5 text-[0.8125rem] leading-relaxed text-warn">
          {policy.period.days_left > 0
            ? `This policy year ends in ${policy.period.days_left} days. Your ` +
              `cover starts again on renewal, so an admission either side of ` +
              `that date draws on a different year's cover.`
            : 'This policy year has ended. Check that it was renewed before ' +
              'relying on these figures.'}
        </p>
      )}
    </div>
  )
}

// What is not covered yet, and the date each one changes.
//
// These were listed and then ignored everywhere else in the app. A duration on
// its own is not usable: "two years" from a start date nobody stated does not
// answer "can I have this operation". The date does.
function WaitingPeriods({ policy }) {
  if (!policy.waiting_periods?.length) return null

  const pending = policy.waiting_periods.filter((w) => w.cleared === false)

  return (
    <div className="border-t border-line px-5 py-4">
      <h3 className="text-[0.8125rem] font-medium text-muted">Waiting periods</h3>
      <ul className="mt-2 space-y-2">
        {policy.waiting_periods.map((wait, index) => (
          <li key={index} className="text-[0.875rem]">
            <div className="flex justify-between gap-4">
              <span className={wait.cleared ? 'text-muted line-through' : ''}>
                {wait.applies_to === 'unspecified' ? wait.kind_label : wait.applies_to}
              </span>
              <span className="shrink-0 font-medium tabular-nums">{wait.duration}</span>
            </div>
            {wait.clears_on && (
              <p className="mt-0.5 text-[0.75rem] text-muted">
                {wait.cleared
                  ? `Served. Covered since ${shortDate(wait.clears_on)}.`
                  : `Covered from ${shortDate(wait.clears_on)}.`}
              </p>
            )}
          </li>
        ))}
      </ul>

      {!policy.period?.start && (
        <p className="mt-2.5 text-[0.8125rem] leading-relaxed text-warn">
          We could not read when this policy started, so we cannot tell you
          whether these still apply. You will be asked once you pick a treatment.
        </p>
      )}
      {policy.period?.start && pending.length > 0 && (
        <p className="mt-2.5 text-[0.8125rem] leading-relaxed text-muted">
          A claim made before the date shown would be declined. We check this
          against the treatment you choose.
        </p>
      )}
    </div>
  )
}

const shortDate = (iso) =>
  new Date(`${iso}T00:00:00`).toLocaleDateString('en-IN', {
    day: 'numeric', month: 'short', year: 'numeric',
  })


function ConfidenceBadge({ policy }) {
  if (policy.questions?.length) {
    return <Badge tone="warn">{policy.questions.length} to confirm</Badge>
  }
  if (policy.needed_ocr && policy.read_quality < 0.85) {
    return <Badge tone="warn">Read from a scan</Badge>
  }
  return <Badge tone="good">Read cleanly</Badge>
}

// One read figure, with a way to correct it.
//
// Machines misread documents, and when they do the user is looking straight at
// the mistake, next to the figure they know to be right. Everything downstream
// is computed from these few numbers, so a misread digit poisons every estimate
// after it while the user watches and cannot do anything.
//
// The control sits at the right edge of the box it changes, and the box accepts
// what the document says rather than only digits: "5 lakh" and "1% of my cover"
// both work, through the same reader the questions use.
function Fact({ label, value, note, emphasis, field, current, onEdit, hint }) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState('')
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  const editable = Boolean(field && onEdit)

  function open() {
    setDraft(current != null ? String(current) : '')
    setError('')
    setEditing(true)
  }

  async function save() {
    setSaving(true)
    setError('')
    try {
      await onEdit(field, draft)
      setEditing(false)
    } catch (e) {
      setError(e.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="bg-surface px-5 py-4">
      <div className="flex items-start justify-between gap-2">
        <div className="text-[0.8125rem] text-muted">{label}</div>
        {editable && !editing && (
          <button
            onClick={open}
            aria-label={`Correct ${label.toLowerCase()}`}
            title="Correct this"
            className="-mr-1 -mt-1 shrink-0 rounded-lg p-1.5 text-muted transition hover:bg-canvas hover:text-brand"
          >
            <PencilIcon />
          </button>
        )}
      </div>

      {editing ? (
        <div className="mt-2 motion-safe:animate-fade">
          <Input
            autoFocus
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') save()
              if (e.key === 'Escape') setEditing(false)
            }}
            placeholder={hint}
          />
          {hint && (
            <p className="mt-1 text-[0.75rem] leading-relaxed text-muted">{hint}</p>
          )}
          {error && <p className="mt-1 text-[0.75rem] text-danger">{error}</p>}
          <div className="mt-2 flex gap-2">
            <Button disabled={saving} onClick={save} className="px-3 py-1.5">
              {saving ? 'Saving…' : 'Save'}
            </Button>
            <Button
              variant="secondary"
              disabled={saving}
              onClick={() => setEditing(false)}
              className="px-3 py-1.5"
            >
              Cancel
            </Button>
          </div>
        </div>
      ) : (
        <>
          <div className={`mt-1 font-semibold ${emphasis ? 'text-[1.375rem]' : 'text-[0.9375rem]'}`}>
            {value}
          </div>
          {note && <p className="mt-1.5 text-[0.75rem] leading-relaxed text-muted">{note}</p>}
        </>
      )}
    </div>
  )
}

function PencilIcon() {
  return (
    <svg
      width="14" height="14" viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="2" strokeLinecap="round"
      strokeLinejoin="round" aria-hidden="true"
    >
      <path d="M12 20h9" />
      <path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z" />
    </svg>
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
