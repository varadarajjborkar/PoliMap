import { useEffect, useState } from 'react'
import { useT } from '../hooks/useLanguage'
import { capped, date, said } from '../lib/i18n'
import { Badge, Button, Card, CardHeader, Field, Input, Select } from './Primitives'

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
  const t = useT()
  return (
    <>
      <div className="grid gap-px bg-line sm:grid-cols-2">
        <Fact
          label={t('scheme.cover', 'Cover this year')}
          value={policy.sum_insured_display}
          note={t('scheme.cover.note', 'Shared across your family for the year.')}
          emphasis
        />
        <Fact
          label={t('scheme.you_pay', 'What you pay at an empanelled hospital')}
          value={t('scheme.you_pay.value', 'Nothing')}
          note={t(
            'scheme.you_pay.note',
            'Treatment is bought at a fixed package rate. No bill to settle, ' +
              'nothing to claim back.')}
        />
        <Fact
          label={t('scheme.room', 'Room included')}
          value={capped(t, policy.room_limit)}
          note={t(
            'scheme.room.note',
            'A higher room is yours to pay for, but it reduces nothing else the ' +
              'scheme covers.')}
        />
        <Fact
          label={t('scheme.consumables', 'Consumables, implants, medicines, tests')}
          value={t('scheme.consumables.value', 'Included in the package')}
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
          {t(
            'scheme.empanelled_only',
            'Only at a hospital empanelled for {scheme}. Anywhere else it pays ' +
              'nothing, and there is no claim afterwards. The hospitals below are ' +
              'filtered on this.',
            { scheme: policy.scheme_label }
          )}
        </p>
      </div>
    </>
  )
}


export function PolicySummary({
  policy, onAnswer, onSkip, onEditField, onContinue, answering,
  onAddSecondPolicy, onDropSecondPolicy,
}) {
  const t = useT()
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
              {t('policy.warnings', 'About the document you uploaded')}
            </h3>
            <ul className="mt-2 space-y-1 text-[0.875rem] leading-relaxed text-warn">
              {policy.warnings.map((warning) => (
                <li key={warning.key}>{said(t, warning)}</li>
              ))}
            </ul>
          </div>
        </Card>
      )}

      <Card>
        <CardHeader
          title={t('policy.title', 'Your cover')}
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
              label={t('policy.sum_insured', 'Total cover this year')}
              value={policy.sum_insured_display}
              field="sum_insured"
              current={policy.sum_insured}
              hint={t(
                'policy.sum_insured.hint',
                'However it appears on your policy, e.g. 5 lakh or 500000'
              )}
              onEdit={onEditField}
              emphasis
            />
            <Fact
              label={t('policy.remaining', 'Cover left this year')}
              value={policy.available_cover_display}
              field="sum_insured_remaining"
              current={policy.sum_insured_remaining ?? policy.sum_insured}
              hint={t(
                'policy.remaining.hint',
                'What is left after any claim made earlier this policy year.'
              )}
              onEdit={onEditField}
              note={
                policy.sum_insured_remaining == null
                  ? t(
                      'policy.remaining.assumed',
                      'We assume no claims yet this year. If you have claimed, correct it: ' +
                        'it changes every estimate.')
                  : policy.restore_benefit
                    ? t(
                        'policy.remaining.restore',
                        'Your policy restores the cover once per year if it runs out.'
                      )
                    : null
              }
            />
            <Fact
              label={t('policy.room', 'Room you are covered for')}
              value={capped(t, policy.room_limit)}
              field="room_limit"
              current={policy.room_limit.daily_cap ?? ''}
              hint={t(
                'policy.room.hint',
                "A daily amount, a percentage like 1%, a room type, or 'no limit'"
              )}
              onEdit={onEditField}
              note={
                policy.room_limit.daily_cap
                  ? t(
                      'policy.room.note',
                      'A costlier room also cuts what is paid on surgeon, theatre and ' +
                        'nursing.')
                  : null
              }
            />
            <Fact
              label={t('policy.copay', 'Your share of every claim')}
              value={
                policy.copay_pct > 0
                  ? `${policy.copay_pct}%`
                  : t('policy.copay.none', 'None')
              }
              field="copay_pct"
              current={policy.copay_pct}
              hint={t(
                'policy.copay.hint',
                'A percentage, e.g. 10. Enter 0 if you have none.'
              )}
              onEdit={onEditField}
              note={
                policy.copay_pct > 0 && policy.copay_above_age
                  ? t(
                      'policy.copay.age',
                      'Only on members aged {age} and above. A younger ' +
                        "member's claim has no co-payment.",
                      { age: policy.copay_above_age }
                    )
                  : null
              }
            />
            <Fact label={t('policy.icu', 'ICU cover')} value={capped(t, policy.icu_limit)} />
            <Fact
              label={t('policy.deductible', 'You pay first')}
              value={
                policy.deductible > 0
                  ? `₹${policy.deductible.toLocaleString('en-IN')}`
                  : t('policy.deductible.none', 'Nothing')
              }
              field="deductible"
              current={policy.deductible}
              hint={t(
                'policy.deductible.hint',
                'Only top-up policies have this. Enter 0 if yours does not.'
              )}
              onEdit={onEditField}
              note={
                policy.deductible > 0
                  ? t(
                      'policy.deductible.note',
                      'This is a top-up policy. It pays only above this amount.'
                    )
                  : null
              }
            />
            <Fact
              label={t('policy.consumables', 'Consumables')}
              value={
                policy.covers_consumables
                  ? t('policy.covered', 'Covered')
                  : t('policy.not_covered', 'Not covered')
              }
              note={
                policy.covers_consumables
                  ? null
                  : t(
                      'policy.consumables.note',
                      'Gloves, syringes and similar items are yours to pay.'
                    )
              }
            />
            <Fact
              label={t('policy.daycare', 'Treatment under a day')}
              value={
                policy.covers_daycare == null
                  ? t('policy.not_stated', 'Not stated')
                  : policy.covers_daycare
                    ? t('policy.covered', 'Covered')
                    : t('policy.not_covered', 'Not covered')
              }
              note={
                policy.covers_daycare === false
                  ? t(
                      'policy.daycare.no',
                      'Cover needs a full day of admission. Cataract, dialysis and the like ' +
                        'would not be paid.')
                  : policy.covers_daycare == null
                    ? t(
                        'policy.daycare.unknown',
                        'Your document does not say. Worth asking: cover normally needs 24 ' +
                          'hours.')
                    : null
              }
            />
          </div>
        )}

        {policy.sublimits?.length > 0 && (
          <div className="border-t border-line px-5 py-4">
            <h3 className="text-[0.8125rem] font-medium text-muted">
              {t('policy.sublimits', 'Separate limits')}
            </h3>
            <ul className="mt-2 space-y-1.5">
              {policy.sublimits.map((sub) => (
                <li key={sub.label} className="flex justify-between text-[0.875rem]">
                  <span>{t(sub.label_key, sub.label)}</span>
                  <span className="tabular-nums font-medium">{sub.amount_display}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        <SecondPolicy
          policy={policy}
          onAdd={onAddSecondPolicy}
          onDrop={onDropSecondPolicy}
          busy={answering}
        />
        <WhoIsCovered policy={policy} />
        <WaitingPeriods policy={policy} />

        <div className="border-t border-line px-5 py-4">
          <Button onClick={onContinue} className="w-full sm:w-auto">
            {t('policy.continue', 'Find hospitals I am covered at')}
          </Button>
        </div>
      </Card>

      <EvidenceTable clauses={policy.clauses} />
    </div>
  )
}

// A second cover on the same admission.
//
// Very common in India and almost never used: an employer's group policy
// beside a personal one, or a base policy with a top-up above it. Every tool
// that reads a policy reads one policy, so the second sits in a drawer while
// the family pays a bill it would have covered.
//
// Held apart rather than merged, because they settle in sequence against their
// own terms; merged, they would be one policy that exists nowhere.
function SecondPolicy({ policy, onAdd, onDrop, busy }) {
  const t = useT()
  const [adding, setAdding] = useState(false)
  const second = policy.second_policy

  if (second) {
    return (
      <div className="border-t border-line px-5 py-4 motion-safe:animate-fade">
        <div className="flex items-baseline justify-between gap-3">
          <h3 className="text-[0.8125rem] font-medium text-muted">
            {t('second.title', 'Your second policy')}
          </h3>
          <button
            onClick={onDrop}
            disabled={busy}
            className="text-[0.75rem] text-muted underline-offset-2 transition hover:text-danger hover:underline disabled:opacity-50"
          >
            {t('second.remove', 'Remove')}
          </button>
        </div>

        <p className="mt-1.5 text-[0.9375rem] font-medium">{second.label}</p>
        <dl className="mt-1.5 space-y-1 text-[0.8125rem] text-muted">
          <div className="flex justify-between gap-4">
            <dt>{t('second.cover', 'Cover')}</dt>
            <dd className="tabular-nums">{second.sum_insured_display}</dd>
          </div>
          <div className="flex justify-between gap-4">
            <dt>{t('second.room', 'Room')}</dt>
            <dd>{capped(t, second.room_limit)}</dd>
          </div>
          {second.is_top_up && (
            <div className="flex justify-between gap-4">
              <dt>{t('second.above', 'Pays only above')}</dt>
              <dd className="tabular-nums">{second.deductible_display}</dd>
            </div>
          )}
        </dl>
        <p className="mt-2 text-[0.8125rem] leading-relaxed text-muted">
          {second.is_top_up
            ? t(
                'second.topup.how',
                'A top-up pays what is left once the band above it is covered. We ' +
                  'settle your first policy, then this one against the balance.')
            : t(
                'second.how',
                'We settle one policy, put the balance to the other, and say which ' +
                  'order costs less.')}
        </p>
      </div>
    )
  }

  if (!adding) {
    return (
      <div className="border-t border-line px-5 py-4">
        <button
          onClick={() => setAdding(true)}
          className="text-[0.875rem] font-medium text-brand transition hover:underline"
        >
          {t('second.add', '+ I have another policy')}
        </button>
        <p className="mt-1 text-[0.8125rem] leading-relaxed text-muted">
          {t(
            'second.add.why',
            "An employer's cover, or a top-up. A second policy pays what the " +
              'first one leaves, and most people never claim from it.'
          )}
        </p>
      </div>
    )
  }

  return (
    <div className="border-t border-line px-5 py-4 motion-safe:animate-fade">
      <div className="flex items-baseline justify-between gap-3">
        <h3 className="text-[0.8125rem] font-medium text-muted">
          {t('second.other', 'Your other policy')}
        </h3>
        <button
          onClick={() => setAdding(false)}
          className="text-[0.75rem] text-muted transition hover:text-ink"
        >
          {t('second.cancel', 'Cancel')}
        </button>
      </div>
      <SecondPolicyForm onSubmit={onAdd} busy={busy} />
    </div>
  )
}

// Typed rather than uploaded, because most people holding two policies have the
// personal document and not the employer's.
function SecondPolicyForm({ onSubmit, busy }) {
  const t = useT()
  const [values, setValues] = useState({
    insurer_name: '',
    sum_insured: '500000',
    room_limit_type: 'none',
    room_limit_amount: '5000',
    copay_pct: '0',
    deductible: '0',
  })
  const set = (key) => (e) => setValues((v) => ({ ...v, [key]: e.target.value }))

  return (
    <div className="mt-3 space-y-3">
      <Field
        label={t('second.form.insurer', 'Who is it with?')}
        hint={t('second.form.insurer.hint', "The insurer's name, or your employer's.")}
      >
        <Input
          value={values.insurer_name}
          onChange={set('insurer_name')}
          placeholder={t(
            'second.form.insurer.placeholder',
            "e.g. my employer's group cover"
          )}
        />
      </Field>
      <Field label={t('second.form.cover', 'How much cover?')}>
        <Input type="number" value={values.sum_insured} onChange={set('sum_insured')} />
      </Field>
      <Field label={t('second.form.room', 'Room rent limit')}>
        <Select value={values.room_limit_type} onChange={set('room_limit_type')}>
          <option value="none">{t('second.form.room.none', 'No limit')}</option>
          <option value="flat">
            {t('second.form.room.flat', 'A fixed amount per day')}
          </option>
        </Select>
      </Field>
      {values.room_limit_type === 'flat' && (
        <Field label={t('second.form.room.amount', 'Amount per day')}>
          <Input
            type="number"
            value={values.room_limit_amount}
            onChange={set('room_limit_amount')}
          />
        </Field>
      )}
      <Field
        label={t('second.form.deductible', 'Does it only pay above an amount?')}
        hint={t(
          'second.form.deductible.hint',
          'Top-up policies do. Leave it at 0 if yours does not.'
        )}
      >
        <Input type="number" value={values.deductible} onChange={set('deductible')} />
      </Field>

      <Button
        disabled={busy || !values.sum_insured}
        onClick={() =>
          onSubmit({
            insurer_name: values.insurer_name.trim(),
            sum_insured: Number(values.sum_insured),
            room_limit_type: values.room_limit_type,
            room_limit_amount: Number(values.room_limit_amount) || null,
            copay_pct: Number(values.copay_pct) || 0,
            deductible: Number(values.deductible) || 0,
          })
        }
      >
        {busy
          ? t('second.form.adding', 'Adding\u2026')
          : t('second.form.submit', 'Add this policy')}
      </Button>
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
  const t = useT()
  if (!policy.insured?.length) return null

  return (
    <div className="border-t border-line px-5 py-4">
      <div className="flex items-baseline justify-between gap-4">
        <h3 className="text-[0.8125rem] font-medium text-muted">
          {t('insured.title', 'Who is covered')}
        </h3>
        {policy.period?.start && (
          <span className="text-[0.75rem] text-muted">
            {policy.period.end
              ? t('insured.period', 'Cover from {from} to {to}', {
                  from: shortDate(policy.period.start),
                  to: shortDate(policy.period.end),
                })
              : t('insured.period.open', 'Cover from {from}', {
                  from: shortDate(policy.period.start),
                })}
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
            ? t(
                'insured.ending',
                'This policy year ends in {days} days. Your cover starts again ' +
                  'on renewal, so an admission either side of that date draws ' +
                  "on a different year's cover.",
                { days: policy.period.days_left }
              )
            : t(
                'insured.ended',
                'This policy year has ended. Check it was renewed before relying on ' +
                  'these figures.')}
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
  const t = useT()
  if (!policy.waiting_periods?.length) return null

  const pending = policy.waiting_periods.filter((w) => w.cleared === false)

  return (
    <div className="border-t border-line px-5 py-4">
      <h3 className="text-[0.8125rem] font-medium text-muted">
        {t('waiting.title', 'Waiting periods')}
      </h3>
      <ul className="mt-2 space-y-2">
        {policy.waiting_periods.map((wait, index) => (
          <li key={index} className="text-[0.875rem]">
            <div className="flex justify-between gap-4">
              <span className={wait.cleared ? 'text-muted line-through' : ''}>
                {wait.applies_to === 'unspecified'
                  ? t(`waitkind.${wait.kind}`, wait.kind_label)
                  : wait.applies_to}
              </span>
              {/* The span arrives as a unit and its numbers as well as written
                  out, because "24 months" is a phrase no table reaches into. */}
              <span className="shrink-0 font-medium tabular-nums">
                {t(`dur.${wait.duration_unit}`, wait.duration, wait.duration_parts)}
              </span>
            </div>
            {wait.clears_on && (
              <p className="mt-0.5 text-[0.75rem] text-muted">
                {wait.cleared
                  ? t('waiting.served', 'Served. Covered since {date}.', {
                      date: shortDate(wait.clears_on),
                    })
                  : t('waiting.from', 'Covered from {date}.', {
                      date: shortDate(wait.clears_on),
                    })}
              </p>
            )}
          </li>
        ))}
      </ul>

      {!policy.period?.start && (
        <p className="mt-2.5 text-[0.8125rem] leading-relaxed text-warn">
          {t(
            'waiting.no_start',
            'We could not read the start date, so we cannot say if these still ' +
              'apply. You will be asked once you pick a treatment.')}
        </p>
      )}
      {policy.period?.start && pending.length > 0 && (
        <p className="mt-2.5 text-[0.8125rem] leading-relaxed text-muted">
          {t(
            'waiting.pending',
            'A claim before the date shown would be declined. We check this ' +
              'against your treatment.')}
        </p>
      )}
    </div>
  )
}

const shortDate = (iso) =>
  date(`${iso}T00:00:00`, { month: 'short', year: 'numeric' })


function ConfidenceBadge({ policy }) {
  const t = useT()
  if (policy.questions?.length) {
    return (
      <Badge tone="warn">
        {t('policy.to_confirm', '{count} to confirm', {
          count: policy.questions.length,
        })}
      </Badge>
    )
  }
  if (policy.needed_ocr && policy.read_quality < 0.85) {
    return <Badge tone="warn">{t('policy.from_scan', 'Read from a scan')}</Badge>
  }
  return <Badge tone="good">{t('policy.read_cleanly', 'Read cleanly')}</Badge>
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
  const t = useT()
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
            aria-label={t('fact.correct.label', 'Correct {field}', {
              field: label.toLowerCase(),
            })}
            title={t('fact.correct', 'Correct this')}
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
              {saving ? t('fact.saving', 'Saving\u2026') : t('fact.save', 'Save')}
            </Button>
            <Button
              variant="secondary"
              disabled={saving}
              onClick={() => setEditing(false)}
              className="px-3 py-1.5"
            >
              {t('fact.cancel', 'Cancel')}
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
  const t = useT()
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
      ? t('ask.placeholder.percent', 'For example 10%, or ten percent')
      : t('ask.placeholder.amount', 'For example 5 lakh, 5,00,000, or no limit')

  const showBox = other || !(question.options?.length > 0)

  return (
    <Card className="border-brand/30 ring-1 ring-brand/10 motion-safe:animate-rise">
      <div className="px-5 py-4">
        <div className="flex items-center justify-between gap-3">
          <h3 className="text-[0.875rem] font-semibold text-brand">
            {question.confirming
              ? t('ask.confirming', 'Just checking')
              : t('ask.title', 'We need one thing from you')}
          </h3>
          {remaining > 0 && (
            <span className="shrink-0 text-[0.75rem] text-muted">
              {t('ask.remaining', '{count} more after this', { count: remaining })}
            </span>
          )}
        </div>

        <p className="mt-2.5 text-[0.9375rem] font-medium">{question.question}</p>
        {question.help && (
          <p className="mt-1.5 text-[0.8125rem] leading-relaxed text-muted">{question.help}</p>
        )}
        {question.page && (
          <p className="mt-1 text-[0.75rem] text-muted">
            {t('ask.page', 'We were looking at page {page} of your document.', {
              page: question.page,
            })}
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
                    {option.page
                      ? t('ask.source.page', 'from the {source}, page {page}', {
                          source: option.source, page: option.page,
                        })
                      : t('ask.source', 'from the {source}', {
                          source: option.source,
                        })}
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
                {t('ask.other', 'None of these, let me explain')}
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
                  {busy ? t('ask.reading', 'Reading\u2026') : t('ask.confirm', 'Confirm')}
                </Button>
              </div>
              <p className="mt-1.5 text-[0.75rem] leading-relaxed text-muted">
                {t(
                  'ask.free_text',
                  'Write it as it appears on your document, in words or figures. We ' +
                    'will read it back first.')}
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
              {t('ask.skip', 'I do not know this')}
            </button>
            <span className="text-[0.75rem] text-muted">
              {t('ask.skip.hint', 'We will carry on and say where we are unsure.')}
            </span>
          </div>
        )}
      </div>
    </Card>
  )
}

function EvidenceTable({ clauses }) {
  const t = useT()
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
            {t('evidence.title', 'Where these figures came from')}
          </h2>
          <p className="mt-0.5 text-[0.875rem] text-muted">
            {t('evidence.count', '{count} passages read from your document', {
              count: shown.length,
            })}
          </p>
        </div>
        <span className="text-[0.8125rem] text-brand">
          {open ? t('evidence.hide', 'Hide') : t('evidence.show', 'Show')}
        </span>
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
                    {t('evidence.page', 'page {page}', { page: clause.page })}
                    {' · '}
                    {clause.section}
                  </span>
                  {clause.confidence < 0.55 && (
                    <Badge tone="warn">{t('evidence.uncertain', 'uncertain')}</Badge>
                  )}
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
