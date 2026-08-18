import { useRef, useState } from 'react'
import { useT } from '../hooks/useLanguage'
import { Badge, Button, Card, CardHeader, Spinner } from './Primitives'

// The final bill, read and checked.
//
// Discharge is the worst moment to read a bill for the first time, and it is
// the only moment most people get. This screen is built to be used standing at
// a counter with the paper still in the other hand: the thing to say comes
// first, the arithmetic behind it second, and nothing here accuses anybody of
// anything. Billing is done at speed by people with several hundred lines to
// enter, and "could you check this line" gets a bill corrected where an
// accusation gets a supervisor.

const MAX_BILL_MB = 25

const SEVERITY = {
  urgent: { tone: 'bad', border: 'border-danger/25', bg: 'bg-danger-soft', text: 'text-danger' },
  attention: { tone: 'warn', border: 'border-warn/25', bg: 'bg-warn-soft', text: 'text-warn' },
  info: { tone: 'neutral', border: 'border-line', bg: 'bg-canvas', text: 'text-ink' },
}

export function BillCheck({ bill, busy, progress, onCheck, onDrop }) {
  const t = useT()
  return (
    <Card>
      <CardHeader
        title={t('bill.title', 'Check the final bill')}
        subtitle={t(
          'bill.subtitle',
          'Against the IRDAI list of items no policy pays, and against your ' +
            'own cover.'
        )}
        aside={
          bill && !busy && (
            <Badge tone={bill.worth_asking > 0 ? 'warn' : 'good'}>
              {bill.worth_asking > 0
                ? `${bill.worth_asking} ${t('bill.to_ask', 'to ask about')}`
                : t('bill.nothing_to_raise', 'Nothing to raise')}
            </Badge>
          )
        }
      />
      {bill && !busy ? (
        <Checked bill={bill} busy={busy} onDrop={onDrop} />
      ) : (
        <Upload busy={busy} progress={progress} onCheck={onCheck} />
      )}
    </Card>
  )
}

function Upload({ busy, progress, onCheck }) {
  const t = useT()
  const [tooLarge, setTooLarge] = useState('')
  const fileRef = useRef(null)

  function choose(file) {
    if (!file) return
    if (file.size > MAX_BILL_MB * 1024 * 1024) {
      setTooLarge(
        `That file is ${(file.size / 1024 / 1024).toFixed(0)} MB. ` +
          `The largest we can take is ${MAX_BILL_MB} MB.`
      )
      if (fileRef.current) fileRef.current.value = ''
      return
    }
    setTooLarge('')
    onCheck(file)
    if (fileRef.current) fileRef.current.value = ''
  }

  if (busy) {
    return (
      <div className="p-5">
        {progress ?? <Spinner label={t('bill.reading', 'Reading the bill\u2026')} />}
      </div>
    )
  }

  return (
    <div className="p-5">
      <p className="text-[0.875rem] leading-relaxed text-muted">
        Ask for the itemised bill, not the one-line total, and photograph it.
        We read it line by line and tell you what is worth raising before you
        sign: items the regulator says are already inside another charge, lines
        entered twice, figures that do not multiply out, and the deduction your
        insurer will make that the billing desk will not mention.
      </p>

      <input
        ref={fileRef}
        type="file"
        accept=".pdf,.jpg,.jpeg,.png,.webp,.heic,.tif,.tiff"
        className="hidden"
        onChange={(event) => choose(event.target.files?.[0])}
      />
      <Button className="mt-4 w-full" onClick={() => fileRef.current?.click()}>
        {t('bill.upload', 'Photograph or upload the bill')}
      </Button>

      {tooLarge && (
        <p className="mt-2 text-[0.75rem] leading-relaxed text-warn">{tooLarge}</p>
      )}
      <p className="mt-2 text-[0.75rem] leading-relaxed text-muted">
        Square-on, in good light. A PDF from the billing desk reads exactly.
      </p>
    </div>
  )
}

function Checked({ bill, busy, onDrop }) {
  const t = useT()
  const [showLines, setShowLines] = useState(false)

  return (
    <div className="divide-y divide-line">
      <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1 px-5 py-4">
        <span className="text-[0.875rem] text-muted">
          {bill.items.length} lines read from {bill.document_name || 'the bill'}
        </span>
        <span className="text-[1.0625rem] font-semibold tabular-nums">
          {bill.gross_total_display || bill.line_total_display}
        </span>
      </div>

      {bill.questionable > 0 && (
        <div className="px-5 py-4">
          <p className="text-[0.875rem] leading-relaxed">
            <span className="font-semibold tabular-nums">
              {bill.questionable_display}
            </span>{' '}
            of this bill sits on lines worth asking about. That is not money you
            are owed; it is money whose reason is worth hearing before you pay it.
          </p>
        </div>
      )}

      {bill.findings.length === 0 ? (
        <p className="px-5 py-6 text-center text-[0.875rem] text-muted">
          {t(
            'bill.nothing',
            'Nothing on this bill stood out against the IRDAI list or your policy.'
          )}
        </p>
      ) : (
        <ul className="divide-y divide-line">
          {bill.findings.map((finding, index) => (
            <Finding key={index} finding={finding} />
          ))}
        </ul>
      )}

      {bill.notes.length > 0 && (
        <ul className="space-y-1 px-5 py-3">
          {bill.notes.map((note, index) => (
            <li key={index} className="text-[0.75rem] leading-relaxed text-muted">
              {note}
            </li>
          ))}
        </ul>
      )}

      {bill.settlement && <Settlement settlement={bill.settlement} />}

      <div className="px-5 py-3">
        <button
          onClick={() => setShowLines(!showLines)}
          className="text-[0.8125rem] text-brand underline"
        >
          {showLines
            ? t('bill.hide_lines', 'Hide the lines we read')
            : t('bill.show_lines', 'Show the lines we read')}
        </button>
      </div>

      {showLines && <Lines items={bill.items} />}

      <div className="px-5 py-3">
        <Button variant="secondary" disabled={busy} onClick={onDrop}>
          {t('bill.another', 'Check a different bill')}
        </Button>
      </div>
    </div>
  )
}

function Finding({ finding }) {
  const style = SEVERITY[finding.severity] ?? SEVERITY.info
  return (
    <li className={`px-5 py-4 ${style.bg}`}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <span className={`text-[0.75rem] font-medium ${style.text}`}>
            {finding.label}
          </span>
          <p className="mt-0.5 text-[0.875rem] font-medium leading-relaxed">
            {finding.headline}
          </p>
        </div>
        {finding.amount_display && (
          <span className={`shrink-0 text-[0.9375rem] font-semibold tabular-nums ${style.text}`}>
            {finding.amount_display}
          </span>
        )}
      </div>

      {finding.detail && (
        <p className="mt-1.5 text-[0.8125rem] leading-relaxed text-muted">
          {finding.detail}
        </p>
      )}

      {/* The sentence to say. It is the point of the whole screen, so it is
          set apart from the explanation rather than buried under it. */}
      {finding.ask && (
        <p className="mt-2 border-l-2 border-current/30 pl-3 text-[0.8125rem] leading-relaxed">
          {finding.ask}
        </p>
      )}

      {finding.lines.length > 0 && (
        <p className="mt-2 text-[0.75rem] text-muted">
          Line{finding.lines.length > 1 ? 's' : ''} {finding.lines.join(', ')}
        </p>
      )}
    </li>
  )
}

function Settlement({ settlement }) {
  const t = useT()
  return (
    <div className="px-5 py-4">
      <h3 className="text-[0.875rem] font-semibold">
        {t('bill.settles_to', 'What this bill settles to')}
      </h3>
      <p className="mt-0.5 text-[0.75rem] leading-relaxed text-muted">
        The same calculation as the estimate, run on the real bill.
      </p>

      <dl className="mt-3 grid grid-cols-2 gap-3">
        <div className="rounded-lg border border-line bg-canvas px-3 py-2">
          <dt className="text-[0.75rem] text-muted">
            {t('results.insurer_pays', 'Your insurer pays')}
          </dt>
          <dd className="mt-0.5 text-[1.0625rem] font-semibold tabular-nums">
            {settlement.payable_display}
          </dd>
        </div>
        <div className="rounded-lg border border-line bg-canvas px-3 py-2">
          <dt className="text-[0.75rem] text-muted">
            {t('results.you_pay', 'You pay')}
          </dt>
          <dd className="mt-0.5 text-[1.0625rem] font-semibold tabular-nums">
            {settlement.out_of_pocket_display}
          </dd>
        </div>
      </dl>

      {settlement.waterfall.length > 0 && (
        <ul className="mt-3 space-y-2">
          {settlement.waterfall.map((step, index) => (
            <li key={index} className="flex items-baseline justify-between gap-3">
              <span className="text-[0.8125rem]">{step.label}</span>
              <span className="shrink-0 text-[0.8125rem] tabular-nums text-muted">
                {step.deducted_display}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

function Lines({ items }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-[0.8125rem]">
        <thead className="bg-canvas text-left text-[0.75rem] text-muted">
          <tr>
            <th className="px-5 py-2 font-medium">Line</th>
            <th className="py-2 font-medium">Item</th>
            <th className="py-2 font-medium">Head</th>
            <th className="px-5 py-2 text-right font-medium">Amount</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-line">
          {items.map((item) => (
            <tr key={item.line} className={item.flagged ? 'bg-warn-soft' : ''}>
              <td className="px-5 py-2 tabular-nums text-muted">{item.line}</td>
              <td className="py-2">{item.description}</td>
              <td className="py-2 text-muted">{item.head_label}</td>
              <td className="px-5 py-2 text-right tabular-nums">
                {item.amount_display}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
