import { useEffect, useMemo, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { api } from '../api'
import { useDialog } from '../hooks/useDialog'
import { useT } from '../hooks/useLanguage'
import { pinAlerts } from '../lib/alerts'
import { packStay } from '../lib/bundle'
import { moment, readable } from '../lib/i18n'
import { ACCEPT, listReceipts, shrinkImage, typeOf } from '../lib/receipts'
import { save } from '../lib/zip'
import { AlertPin } from './AlertPin'
import { Papers } from './Receipts'
import { Badge, Button, Card, CardHeader, Field, Input, Select } from './Primitives'

// The care journey: where the paperwork stands, what has been billed, and what
// that means for the cover still available.
//
// Stages are administrative, never clinical. Nothing here records or reasons
// about a diagnosis, and no prompt suggests a course of treatment.

// Four, and the server agrees: `journey.stages` carries the same list. Written
// out here so the bar renders before the first response arrives.
//
// It was eight. Tests, the operation and recovery are clinically distinct and
// insurance-identical, so moving the marker three times told the system nothing
// and told the user less, and eight chips do not fit across a phone.
const STAGES = [
  ['pre_admission', 'Before admission'],
  ['admitted', 'In hospital'],
  ['discharge_planning', 'Going home'],
  ['settled', 'Claim settled'],
]

// The server names stages too, in English, and sends those names back inside
// labels, alerts and the list of what a skip passes over. The same four are
// named here, so a label can be turned back into its key and read in the
// reader's language rather than the server's.
const STAGE_KEY = Object.fromEntries(STAGES.map(([value, label]) => [label, value]))

function stageName(t, label) {
  const value = STAGE_KEY[label]
  return value ? t(`journey.stage.${value}`, label) : label
}

export function Journey({
  journey, sessionId, user, stayId, busy,
  onAdvance, onRecordCost, onUpdateCost, onDeleteCost, onFilePreauth,
  onToggleChecklist,
}) {
  const t = useT()

  // Which of the three faces of the record is showing. Held here rather than
  // in the card, because the figure on the right opens one of them: pressing
  // "show where the difference comes from" beside the money turns the record
  // to the page that answers it.
  const [tab, setTab] = useState('charges')
  const record = useRef(null)

  // The bills attached to this stay, read back off this device.
  //
  // Reloaded whenever the ledger changes, keyed on the charges and the names
  // filed against them: adding a charge with a bill, or deleting one, is
  // exactly when the shelf is out of date, and nothing else is.
  const [papers, setPapers] = useState([])
  const [papersBusy, setPapersBusy] = useState(true)
  const ledger = (journey?.costs ?? [])
    .map((cost) => `${cost.id}:${cost.receipt_name}`)
    .join('|')

  useEffect(() => {
    let live = true
    setPapersBusy(true)
    listReceipts(user, stayId).then((found) => {
      if (!live) return
      setPapers(found)
      setPapersBusy(false)
    })
    return () => { live = false }
  }, [user, stayId, ledger])

  // What each file is for, in the reader's language and at today's figures.
  // The store keeps the file and which charge it belongs to; everything said
  // about it here is read off that charge, so a charge corrected after the
  // fact does not leave its bill labelled with the old amount.
  const costs = journey?.costs
  const filed = useMemo(() => {
    const byId = new Map((costs ?? []).map((cost) => [cost.id, cost]))
    return papers
      .filter((paper) => byId.has(paper.entry))
      .map((paper) => {
        const cost = byId.get(paper.entry)
        return {
          ...paper,
          head: cost.head_value,
          headLabel: t(`head.${cost.head_value}`, cost.head),
          amount: cost.amount_display,
        }
      })
  }, [papers, costs, t])

  if (!journey) return null

  function showSplit() {
    setTab('split')
    record.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
  }

  // Three columns rather than one long scroll.
  //
  // A stay is read by holding two things against each other: what is left of
  // the cover against what has just been billed, what is still outstanding
  // against where the paperwork has got to. Stacked one under another, every
  // one of those comparisons was a scroll, and on a laptop the page spent two
  // thirds of the screen on empty margin while it happened.
  //
  // So the figures sit on the right, what needs doing sits on the left, both
  // stay where they are, and the middle column is the only part that moves.
  // Below a wide screen it all comes back into one column, in the order
  // somebody standing in a corridor needs it: where they are, what it costs,
  // what to do.
  //
  // The widths below are arithmetic rather than the usual breakpoints. Two
  // 17rem columns and the gaps between them take 640px before the middle gets
  // anything, so splitting at Tailwind's 1024px left the column everything is
  // read in about 250px wide. Each of these is the width at which the thing it
  // turns on has room to be worth turning on.
  const aside =
    'space-y-4 min-[1180px]:sticky min-[1180px]:top-[calc(var(--header-h)+1rem)] ' +
    'min-[1180px]:max-h-[calc(100vh-var(--header-h)-2rem)] ' +
    'min-[1180px]:overflow-y-auto min-[1180px]:overscroll-contain min-[1180px]:pb-1'

  // The middle column is three things: which stay this is, what it costs to
  // add to, and what is on record. Nothing is paired, because paired cards are never
  // the same height and every pair left a hole beside the shorter one.
  //
  // Folded into one column, the order is not the order of the columns. It is
  // where you are, what you owe, the charge you are holding, what is on
  // record, and last the list of what to do before this stage ends. See the
  // `order-` classes below.
  //
  // What is missing from it is the alerts, which were a stack of cards here
  // and are now marks beside the figures they are about. See AlertPin.
  const middle = 'min-w-0 min-[1180px]:col-start-2'

  const pinned = pinAlerts(journey.alerts)

  // The one alert that carries a control rather than a sentence. It travels
  // with the alert into whichever panel that alert ends up in.
  const alertAction = (alert) =>
    alert.kind === 'pre_auth_due' && !journey.pre_auth_filed ? (
      <Button
        variant="secondary"
        className="mt-3"
        disabled={busy}
        onClick={onFilePreauth}
      >
        {t('journey.preauth.file', 'Mark pre-authorisation as filed')}
      </Button>
    ) : null

  return (
    <div className="mx-auto grid max-w-3xl items-start gap-4 min-[1180px]:max-w-none min-[1180px]:grid-cols-[17rem_minmax(0,1fr)_17rem] min-[1440px]:grid-cols-[19rem_minmax(0,1fr)_19rem]">
      <StayHead
        journey={journey}
        pins={pinned.room}
        alertAction={alertAction}
        className={`order-1 ${middle} min-[1180px]:row-start-1`}
      />

      <div className={`order-2 min-[1180px]:col-start-3 min-[1180px]:row-start-1 min-[1180px]:row-span-3 ${aside}`}>
        <Standing
          journey={journey}
          sessionId={sessionId}
          busy={busy}
          onAdvance={onAdvance}
          pinned={pinned}
          alertAction={alertAction}
          papers={filed}
          onShowSplit={showSplit}
        />
      </div>

      <CostCard
        onRecordCost={onRecordCost}
        busy={busy}
        className={`order-3 ${middle} min-[1180px]:row-start-2`}
      />

      <ChargesCard
        ref={record}
        journey={journey}
        busy={busy}
        tab={tab}
        onTab={setTab}
        papers={filed}
        papersBusy={papersBusy}
        onUpdateCost={onUpdateCost}
        onDeleteCost={onDeleteCost}
        className={`order-4 ${middle} min-[1180px]:row-start-3`}
      />

      {/* Last, once the columns fold into one, and only there: the grid places
          it by row and column above that width, so nothing on a desk moves.
          It is the tallest card on the page and it is read once a stage, while
          the charge in somebody's hand is entered several times a day. Third
          in the column, it put the thing they came to do two and a half
          screens down a phone. */}
      <div className={`order-5 min-[1180px]:col-start-1 min-[1180px]:row-start-1 min-[1180px]:row-span-3 ${aside}`}>
        <Checklist
          checklist={journey.checklist}
          stageLabel={journey.stage_label}
          onToggle={onToggleChecklist}
          busy={busy}
        />
      </div>
    </div>
  )
}

// Who, where, and how far along.
//
// The stage control used to live under this as a strip with a dropdown in it.
// It has gone to the marker on the right, which was already drawing the four
// stages and is the natural place to move between them: you press the step you
// want, or the button under it for the next one.
function StayHead({ journey, pins, alertAction, className = '' }) {
  const t = useT()
  const room = [
    journey.room_category
      ? t(`room.${journey.room_category}`, journey.room)
      : journey.room,
    journey.room_rate &&
      t('journey.per_day', '\u20b9{amount} a day', {
        amount: journey.room_rate.toLocaleString('en-IN'),
      }),
  ]
    .filter(Boolean)
    .join(' \u00b7 ')

  return (
    <Card className={className}>
      <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-1.5 px-5 py-3.5">
        <div className="min-w-0">
          <h2 className="truncate text-[1.0625rem] font-semibold tracking-tight">
            {journey.hospital_name || t('journey.title', 'Your stay')}
          </h2>
          {room && (
            // Beside the rate, because what the mark has to say is that this
            // rate and the one being billed are not the same number.
            <p className="mt-0.5 flex items-center gap-2 text-[0.8125rem] text-muted">
              <span className="truncate">{room}</span>
              <AlertPin alerts={pins} action={alertAction} />
            </p>
          )}
        </div>
        <Badge tone="good">{stageName(t, journey.stage_label)}</Badge>
      </div>
    </Card>
  )
}

// Where the stay stands and what it has cost, in one block.
//
// These were four cards spread down the page, which meant the figure somebody
// came to this screen for was underneath the tracker, the tracker was above
// the cover bar, and reading the three together took two scrolls. They answer
// the same question and belong in the same place.
function Standing({
  journey, sessionId, busy, onAdvance, pinned, alertAction, papers, onShowSplit,
}) {
  return (
    <Card className="motion-safe:animate-rise">
      <StageTrack
        journey={journey}
        busy={busy}
        onAdvance={onAdvance}
        pins={pinned.stage}
        alertAction={alertAction}
      />
      <Position
        position={journey.position}
        accrued={journey.accrued_display}
        pins={pinned.money}
        alertAction={alertAction}
        onShowSplit={onShowSplit}
      />
      <BurnDown
        burn={journey.burn_down}
        accrued={journey.accrued_display}
        pins={pinned.cover}
        alertAction={alertAction}
      />
      <TakeAway journey={journey} sessionId={sessionId} papers={papers} />
    </Card>
  )
}

// The four stages, stood on end, and the way to move between them.
//
// Laid across the page, four labels shared the width of a column and every one
// of them wrapped, so the marker was the tallest thing on the screen and said
// the least. Standing them up reads at a glance, which is the whole job of a
// marker on a wall.
//
// It is the control as well now. Moving a stay on used to be a dropdown and a
// button in a card of their own, which asked somebody to find the stage they
// were already looking at in a list and pick it again. The step you want is on
// the screen: press it. The button underneath is the next one along, which is
// what nearly every move is, and it says where it goes.
function StageTrack({ journey, busy, onAdvance, pins, alertAction }) {
  const t = useT()
  const [pending, setPending] = useState(null)

  const stages = journey.stages ?? []
  const byValue = Object.fromEntries(stages.map((one) => [one.value, one]))
  const next = byValue[journey.next_stage]
  const currentIndex = STAGES.findIndex(([value]) => value === journey.stage)

  function go(target) {
    if (!target || target.kind === 'current' || busy) return
    // A skip is the only move worth interrupting for. Going back is a
    // correction, and correcting something should never need a permission slip.
    if (target.kind === 'skip') {
      setPending(target)
      return
    }
    onAdvance(target.value, {})
  }

  return (
    <div className="px-5 py-4">
      <div className="flex items-center justify-between gap-2">
        <h3 className="text-[0.8125rem] font-medium">
          {t('journey.advance.title', 'Where are you now?')}
        </h3>
        <AlertPin alerts={pins} action={alertAction} />
      </div>

      <ol className="mt-3">
        {STAGES.map(([value, label], index) => {
          const done = index < currentIndex
          const current = index === currentIndex
          const last = index === STAGES.length - 1
          const target = byValue[value]
          const movable = Boolean(target) && target.kind !== 'current' && !busy

          return (
            <li key={value} className="flex gap-2.5">
              <div className="flex flex-col items-center">
                <span
                  className={`flex h-4 w-4 shrink-0 items-center justify-center rounded-full border text-[0.5rem] leading-none transition ${
                    done
                      ? 'border-brand bg-brand text-on-brand'
                      : current
                        ? 'border-brand bg-surface ring-4 ring-brand/15'
                        : 'border-line bg-surface'
                  }`}
                >
                  {done ? '\u2713' : ''}
                </span>
                {!last && (
                  <span
                    className={`w-px flex-1 ${done ? 'bg-brand/40' : 'bg-line'}`}
                  />
                )}
              </div>

              <button
                type="button"
                disabled={!movable}
                aria-current={current ? 'step' : undefined}
                aria-label={
                  target?.kind === 'back'
                    ? `${t(`journey.stage.${value}`, label)}: ${t('journey.advance.go_back', 'Go back to this stage')}`
                    : undefined
                }
                onClick={() => go(target)}
                className={`-mt-px rounded pb-3 text-left text-[0.8125rem] leading-snug transition ${
                  current
                    ? 'cursor-default font-semibold text-ink'
                    : movable
                      ? 'text-muted hover:text-brand hover:underline'
                      : 'cursor-default text-muted/50'
                }`}
              >
                {t(`journey.stage.${value}`, label)}
                {current && (
                  <span className="sr-only">
                    {' '}
                    ({t('journey.advance.here', 'you are here')})
                  </span>
                )}
              </button>
            </li>
          )
        })}
      </ol>

      {next ? (
        <>
          <Button
            className="w-full"
            disabled={busy}
            onClick={() => go(next)}
          >
            {t('journey.advance.next', 'Move to {stage}', {
              stage: stageName(t, next.label).toLowerCase(),
            })}
          </Button>
          <p className="mt-1.5 text-[0.75rem] leading-relaxed text-muted">
            {t(
              'journey.advance.hint',
              'Update this as things move. You can go back at any point.'
            )}
          </p>
        </>
      ) : (
        <p className="text-[0.75rem] leading-relaxed text-muted">
          <span className="font-medium text-ink">
            {t('journey.advance.settled', 'Your claim is settled')}
          </span>{' '}
          {t(
            'journey.advance.settled.hint',
            'You can still go back to an earlier stage if something changes.'
          )}
        </p>
      )}

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
    </div>
  )
}

// A screen cannot be put in front of a hospital insurance desk, and a phone
// battery does not last a five-day admission. This is the version somebody can
// argue from, or hand to a relative who has just arrived.
//
// With bills attached it is a folder rather than a page, and the folder is
// packed here: the document comes from the server, which has the policy and
// the ledger, and the bills come from this device, which is the only place
// they have ever been. Nothing else holds both halves.
function TakeAway({ journey, sessionId, papers }) {
  const t = useT()
  const [packing, setPacking] = useState(false)
  const [failed, setFailed] = useState('')

  async function packAll() {
    setPacking(true)
    setFailed('')
    try {
      const { blob, filename } = await packStay({
        reportUrl: api.reportUrl(sessionId),
        papers,
        costs: journey.costs ?? [],
        hospital: journey.hospital_name,
      })
      save(blob, filename)
    } catch (error) {
      setFailed(error.message)
    } finally {
      setPacking(false)
    }
  }

  return (
    <div className="border-t border-line px-5 py-3.5">
      {papers.length > 0 ? (
        <>
          <Button
            variant="secondary"
            disabled={packing}
            onClick={packAll}
            className="w-full"
          >
            {packing ? (
              t('journey.download.packing', 'Putting it together…')
            ) : (
              <>
                <DownloadIcon />
                {t('journey.download.all', 'Download the stay and its {count} bills', {
                  count: papers.length,
                })}
              </>
            )}
          </Button>
          <p className="mt-1.5 hidden text-[0.75rem] leading-relaxed text-muted sm:block">
            {t(
              'journey.download.all.why',
              'One folder: the page below, every bill you attached, and an ' +
                'index tying each one to the charge it belongs to.'
            )}
          </p>
          <a
            href={api.reportUrl(sessionId)}
            className="mt-1.5 inline-block text-[0.75rem] text-brand underline"
          >
            {t('journey.download.page_only', 'Or just the page, without the bills')}
          </a>
        </>
      ) : (
        <>
          <a
            href={api.reportUrl(sessionId)}
            className="inline-flex items-center gap-2 rounded-lg border border-line px-3 py-2 text-[0.8125rem] font-medium transition hover:bg-canvas"
          >
            <DownloadIcon />
            {t('journey.download', 'Download this stay')}
          </a>
          <p className="mt-1.5 hidden text-[0.75rem] leading-relaxed text-muted sm:block">
            {t(
              'journey.download.why',
              'Your cover, the estimate, what is billed, what is left to do. One ' +
                'page for the insurance desk.')}
          </p>
        </>
      )}

      {failed && (
        <p className="mt-2 text-[0.75rem] leading-relaxed text-danger">{failed}</p>
      )}
    </div>
  )
}

// The record of the stay, read three ways.
//
// One ledger of charges, one shelf of the paper behind them, and one account
// of why the family's share is what it is. They are the same stay from three
// sides and they belong in the same place, which is what the tabs are for:
// side by side they were three half-empty cards, and stacked they were a
// scroll each.
//
// The third of them used to unfold underneath the figure it explains, in a
// column too narrow to read a table of deductions in. The figure keeps the
// button; the answer opens here, at full width.
function ChargesCard({
  journey, busy, tab, onTab, papers, papersBusy,
  onUpdateCost, onDeleteCost, className = '', ref,
}) {
  const t = useT()
  const steps = journey.position?.steps ?? []

  const tabs = [
    ['charges', t('journey.tab.charges', 'Charges so far'), journey.costs?.length ?? 0],
    ['papers', t('journey.tab.papers', 'Bills and receipts'), papers.length],
    // Only once there is a share to account for. Nothing is recorded before
    // admission, and a government scheme settles at a package rate that
    // leaves nothing to deduct.
    ...(journey.position ? [['split', t('journey.tab.split', 'What you pay'), 0]] : []),
  ]

  // A tab can go: the last charge is deleted and there is no position left to
  // explain. Falling back keeps the card from showing nothing at all.
  const shown = tabs.some(([id]) => id === tab) ? tab : 'charges'

  return (
    <Card className={className} ref={ref}>
      {/* Wraps rather than scrolls. A grid item is `min-width: auto` by
          default, so a strip that refuses to fold takes the whole page
          sideways; a strip that scrolls instead keeps the page still but hides
          its last tab off the edge of a phone, where nothing says it is there.
          Three chips over two lines are legible and all present. */}
      <div
        role="tablist"
        className="flex min-w-0 flex-wrap gap-1 border-b border-line px-2 py-2"
      >
        {tabs.map(([id, label, count]) => (
          <button
            key={id}
            role="tab"
            aria-selected={shown === id}
            onClick={() => onTab(id)}
            className={`flex shrink-0 items-center gap-1.5 whitespace-nowrap rounded-lg px-3 py-1.5 text-[0.8125rem] font-medium transition ${
              shown === id
                ? 'bg-brand-soft text-brand'
                : 'text-muted hover:bg-canvas hover:text-ink'
            }`}
          >
            {label}
            {count > 0 && (
              <span className="rounded-full bg-canvas px-1.5 text-[0.6875rem] tabular-nums">
                {count}
              </span>
            )}
          </button>
        ))}
      </div>

      {shown === 'charges' &&
        (journey.costs?.length > 0 ? (
          <ChargesList
            journey={journey}
            busy={busy}
            onUpdateCost={onUpdateCost}
            onDeleteCost={onDeleteCost}
            onShowPapers={() => onTab('papers')}
            held={new Set(papers.map((paper) => paper.entry))}
          />
        ) : (
          <p className="px-5 py-6 text-center text-[0.875rem] leading-relaxed text-muted">
            {t(
              'journey.charges.none',
              'Nothing recorded yet. Add each charge as it arrives and the ' +
                'estimate above keeps up with it.'
            )}
          </p>
        ))}

      {shown === 'papers' && <Papers papers={papers} busy={papersBusy} />}

      {shown === 'split' && (
        <Split
          position={journey.position}
          accrued={journey.accrued_display}
          steps={steps}
        />
      )}
    </Card>
  )
}

// Every rupee the family pays and the rule that put it there.
//
// The question this answers is not "how much" but "on what": which of these
// charges came back as a co-payment, which as a room cap, which was never
// payable at all. Each line names the deduction, prices it, and says why in a
// sentence written from this policy's own figures.
function Split({ position, accrued, steps }) {
  const t = useT()

  return (
    <div className="px-5 py-4">
      <p className="text-[0.875rem] leading-relaxed">
        {t(
          'journey.split.head',
          'Of the {billed} billed so far, your insurer covers {covered}. The ' +
            'remaining {yours} is yours.',
          {
            billed: accrued,
            covered: position.insurer_pays_display,
            yours: position.you_pay_display,
          }
        )}
      </p>

      {steps.length === 0 ? (
        <p className="mt-3 text-[0.875rem] leading-relaxed text-muted">
          {t(
            'journey.split.nothing',
            'Nothing has been deducted. Every charge recorded so far falls ' +
              'inside what your policy pays for.'
          )}
        </p>
      ) : (
        <ul className="mt-3 space-y-3 border-t border-line pt-3">
          {steps.map((step, index) => (
            <li key={index}>
              <div className="flex items-baseline justify-between gap-3">
                <span className="text-[0.875rem] font-medium">
                  {t(`waterfall.${step.kind}`, step.label)}
                </span>
                <span className="shrink-0 text-[0.875rem] tabular-nums text-danger">
                  &minus;{step.deducted_display}
                </span>
              </div>
              <p className="mt-0.5 text-[0.8125rem] leading-relaxed text-muted">
                {t(`waterfall.${step.key}.why`, step.explanation, readable(t, step.values))}
              </p>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

function ChargesList({ journey, busy, onUpdateCost, onDeleteCost, onShowPapers, held }) {
  const t = useT()
  const [editing, setEditing] = useState(null)
  const [menuFor, setMenuFor] = useState(null)

  if (!journey.costs?.length) return null

  return (
    <>
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
                    <span className="text-[0.875rem] font-medium">
                      {t(`head.${cost.head_value}`, cost.head)}
                    </span>
                    <span className="text-[0.75rem] text-muted">{moment(cost.at)}</span>
                  </div>
                  {cost.description && (
                    <p className="mt-0.5 text-[0.8125rem] text-muted">{cost.description}</p>
                  )}
                  {/* The paper itself is on this device, not behind a link,
                      so this opens the shelf rather than a URL. And only when
                      the device is actually holding it: the name travels with
                      the stay and the file does not, so a stay restored where
                      its paperwork is not would otherwise offer to open a
                      shelf that has nothing on it. */}
                  {cost.receipt_name && (held.has(cost.id) ? (
                    <button
                      onClick={onShowPapers}
                      className="mt-0.5 flex max-w-full items-center gap-1 text-[0.75rem] text-brand"
                    >
                      <ClipIcon />
                      <span className="truncate underline">{cost.receipt_name}</span>
                    </button>
                  ) : (
                    <span
                      title={t(
                        'journey.receipt.elsewhere',
                        'This bill was attached on another device, so it is not here.'
                      )}
                      className="mt-0.5 flex max-w-full items-center gap-1 text-[0.75rem] text-muted"
                    >
                      <ClipIcon />
                      <span className="truncate">{cost.receipt_name}</span>
                    </span>
                  ))}
                </div>

                <span className="shrink-0 text-[0.875rem] font-medium tabular-nums">
                  {cost.amount_display}
                </span>

                <div className="relative shrink-0">
                  <button
                    aria-label={t('journey.charge.options', 'Options for {head}', {
                      head: cost.head,
                    })}
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
                        aria-label={t('journey.charge.close_menu', 'Close menu')}
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
                          className="block w-full px-3 py-2 text-left text-[0.8125rem] hover:bg-canvas"
                        >
                          {t('journey.charge.edit', 'Edit')}
                        </button>
                        <button
                          role="menuitem"
                          disabled={busy}
                          onClick={() => {
                            setMenuFor(null)
                            onDeleteCost(cost.id)
                          }}
                          className="block w-full px-3 py-2 text-left text-[0.8125rem] text-danger hover:bg-danger-soft"
                        >
                          {t('journey.charge.delete', 'Delete')}
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

      {/* At the foot, where the total of a ledger belongs. It was the card's
          subtitle, and there is no card to be the subtitle of any more. */}
      <p className="border-t border-line px-5 py-2.5 text-right text-[0.75rem] text-muted">
        {t('journey.charges.count', '{count} recorded, {total} in total', {
          count: journey.costs.length, total: journey.accrued_display,
        })}
      </p>
    </>
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
  const t = useT()
  const [head, setHead] = useState(cost.head_value)
  const [amount, setAmount] = useState(String(cost.amount))
  const [at, setAt] = useState(toLocalInput(cost.at))

  return (
    <div className="rounded-lg border border-brand/30 bg-canvas p-3">
      <div className="grid gap-3 sm:grid-cols-2">
        <Field label={t('journey.charge.head', 'What is it for?')}>
          <Select value={head} onChange={(event) => setHead(event.target.value)}>
            {HEADS.map(([value, label]) => (
              <option key={value} value={value}>{t(`head.${value}`, label)}</option>
            ))}
          </Select>
        </Field>

        <Field label={t('journey.charge.amount', 'Amount')}>
          <Input
            type="number"
            value={amount}
            onChange={(event) => setAmount(event.target.value)}
          />
        </Field>

        <div className="sm:col-span-2">
          <Field label={t('journey.charge.when', 'When')}>
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
          {t('journey.charge.save', 'Save')}
        </Button>
        <Button variant="secondary" onClick={onClose}>
          {t('journey.charge.cancel', 'Close')}
        </Button>
      </div>
    </div>
  )
}

function ClipIcon() {
  return (
    <svg
      viewBox="0 0 24 24" aria-hidden="true"
      className="h-3.5 w-3.5 shrink-0" fill="none" stroke="currentColor"
      strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"
    >
      <path d="M21.4 11.05 12.25 20.2a5.5 5.5 0 0 1-7.78-7.78l9.19-9.19a3.67 3.67 0 0 1 5.18 5.18l-9.2 9.2a1.83 1.83 0 0 1-2.59-2.6l8.49-8.48" />
    </svg>
  )
}

function DownloadIcon() {
  return (
    <svg
      viewBox="0 0 16 16" aria-hidden="true"
      className="h-3.5 w-3.5" fill="none" stroke="currentColor" strokeWidth="1.6"
      strokeLinecap="round" strokeLinejoin="round"
    >
      <path d="M8 2v8m0 0 3-3m-3 3L5 7" />
      <path d="M2.5 11v1.5A1.5 1.5 0 0 0 4 14h8a1.5 1.5 0 0 0 1.5-1.5V11" />
    </svg>
  )
}

// What to do here, with this policy's own figures in it.
//
// Advice about hospital admissions in general is available everywhere and helps
// nobody. "Ask for a room at or under ₹5,000 a day" is not available anywhere
// else, and it is the sentence that decides how much of the rest of the bill
// the insurer pays.
//
// Ticks live on the server, so this is a record of what has been dealt with
// rather than a poster that resets on reload, and a second family member
// opening the same stay sees what the first has already done.
function Checklist({ checklist, stageLabel, onToggle, busy }) {
  const t = useT()
  if (!checklist?.items?.length) return null

  const { done, total, items } = checklist
  const complete = done === total

  return (
    <Card>
      <CardHeader
        title={t('journey.checklist', 'Before you leave this stage')}
        subtitle={stageName(t, stageLabel)}
        aside={
          <Badge tone={complete ? 'good' : 'neutral'}>
            {t('journey.checklist.count', '{done} of {total}', { done, total })}
          </Badge>
        }
      />

      <div className="h-1 bg-canvas">
        <div
          className="h-full bg-brand transition-[width] duration-500 ease-out"
          style={{ width: `${total ? (done / total) * 100 : 0}%` }}
        />
      </div>

      {/* The reason under an instruction is worth four lines where being late
          costs money and is worth none where it does not. Every item carried
          one, which made a list of eight into a wall of text in a column a
          phone wide, and the four that matter were lost in the four that did
          not. The rest keep theirs where a pointer can find it. */}
      <ul className="divide-y divide-line">
        {items.map((item) => {
          const said = t(`checklist.${item.key}`, item.text, readable(t, item.values))
          const why =
            item.why &&
            t(`checklist.${item.key}.why`, item.why, readable(t, item.values))
          const explain = Boolean(why) && item.urgent && !item.done

          return (
            <li key={item.id}>
              <label
                className={`flex cursor-pointer gap-2.5 px-5 py-2.5 transition hover:bg-canvas ${
                  item.done ? 'opacity-55' : ''
                }`}
              >
                <input
                  type="checkbox"
                  checked={item.done}
                  disabled={busy}
                  onChange={(e) => onToggle(item.id, e.target.checked)}
                  className="mt-0.5 h-4 w-4 shrink-0 accent-[var(--color-brand)]"
                />
                <span className="min-w-0 flex-1">
                  <span
                    className={`block text-[0.875rem] leading-snug ${
                      item.done ? 'line-through' : 'font-medium'
                    }`}
                    title={explain ? undefined : why || undefined}
                  >
                    {said}
                    {item.urgent && !item.done && (
                      <span className="ml-1.5 align-[0.1em] text-[0.6875rem] font-semibold uppercase tracking-wide text-warn">
                        {t('journey.checklist.now', 'Now')}
                      </span>
                    )}
                  </span>
                  {explain && (
                    <span className="mt-0.5 block text-[0.8125rem] leading-snug text-muted">
                      {why}
                    </span>
                  )}
                </span>
              </label>
            </li>
          )
        })}
      </ul>
    </Card>
  )
}

// The one figure this screen exists to show, and where it came from.
//
// It is what the family pays, not what the hospital has billed. The two
// differ, the estimator on the previous screen had already worked out by how
// much, and showing the hospital's number here left two figures contradicting
// each other with no way for a reader to tell which one to plan against.
function Position({ position, accrued, pins, alertAction, onShowSplit }) {
  const t = useT()
  if (!position) return null

  return (
    <div className="border-t border-line">
      <div className="px-5 py-4">
        {/* The mark sits on the line naming the figure, not on the figure
            itself: what it has to say is always a reason this number is
            higher than it should be. */}
        <p className="flex items-center gap-2 text-[0.875rem] text-muted">
          {t('journey.position.you_pay', 'You will pay, so far')}
          <AlertPin alerts={pins} action={alertAction} />
        </p>
        <p
          key={position.you_pay}
          className="mt-1 rounded text-[2rem] font-semibold leading-tight tabular-nums motion-safe:animate-settle"
        >
          {position.you_pay_display}
        </p>
        <p className="mt-1.5 text-[0.875rem] leading-relaxed text-muted">
          {t(
            'journey.position.split',
            'The hospital has billed {billed}. Your insurer covers {covered} of that.',
            { billed: accrued, covered: position.insurer_pays_display }
          )}
        </p>

        {/* The answer is a table of deductions, each with a sentence under it,
            and this column is a third of the width one is readable in. The
            question is asked here, beside the figure that raises it, and
            answered on the record's own page. */}
        {position.steps.length > 0 && (
          <button
            onClick={onShowSplit}
            className="mt-3 text-[0.875rem] font-medium text-brand transition hover:underline"
          >
            {t('journey.position.show', 'Show where the difference comes from')}
          </button>
        )}
      </div>
    </div>
  )
}

function BurnDown({ burn, accrued, pins, alertAction }) {
  const t = useT()
  const used = Math.min(100, burn.consumed_fraction * 100)
  const projected = Math.min(
    100,
    burn.sum_insured > 0 ? (burn.projected / burn.sum_insured) * 100 : 0
  )

  return (
    <div className="border-t border-line px-5 py-4">
      {/* Wrapping rather than squeezing: in a column this narrow the label
          otherwise breaks mid-phrase to keep the figure on the same line. */}
      <div className="flex flex-wrap items-baseline justify-between gap-x-3">
        <span className="flex items-center gap-2 text-[0.8125rem] text-muted">
          {t('journey.burn.used', 'Cover used so far')}
          <AlertPin alerts={pins} action={alertAction} />
        </span>
        <span className="text-[0.875rem] font-medium tabular-nums">
          {t('journey.burn.of', '{used} of {total}', {
            used: accrued,
            total: `₹${burn.sum_insured.toLocaleString('en-IN')}`,
          })}
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

      <div className="mt-1.5 flex flex-wrap justify-between gap-x-3 text-[0.8125rem] text-muted">
        <span>
          {t('journey.burn.left', '{amount} left', { amount: burn.remaining_display })}
        </span>
        {/* The rate excludes one-off charges. A theatre bill on day one is not
            a daily rate, and a family told their cover ends tomorrow when it
            does not will stop believing anything else on this screen. */}
        {burn.daily_run_rate > 0 && (
          <span className={burn.will_exceed ? 'text-warn' : ''}>
            {t('journey.burn.rate', '{amount} a day', {
              amount: burn.daily_run_rate_display,
            })}
            {burn.days_of_cover_left !== null &&
              burn.days_of_cover_left !== undefined && (
                <>
                  {' · '}
                  {burn.days_of_cover_left === 0
                    ? t('journey.burn.reached', 'cover reached today')
                    : t('journey.burn.days_left', 'about {days} days of cover left', {
                        days: burn.days_of_cover_left,
                      })}
                </>
              )}
          </span>
        )}
      </div>
    </div>
  )
}

// Shown when a move passes over stages. Deliberately quiet: the person reading
// it may be standing in a hospital corridor, and nothing here is an error. It
// states what is being skipped, offers to go on, and offers a way back out.
//
// Rendered into the body rather than where it is written. `position: fixed` is
// measured against the viewport only until some ancestor has a transform, and
// then it is measured against that ancestor instead: this is raised from a
// control inside a card that animates in, and an animation that has finished
// still leaves an identity transform behind. The notice appeared inside that
// card, a third of a screen wide, with the dimming behind it covering one
// column of the page and nothing else.
function SkipDialog({ target, onConfirm, onCancel, busy }) {
  const t = useT()
  const [explain, setExplain] = useState(false)
  const [reason, setReason] = useState('')
  const box = useDialog(true, onCancel)

  const skipped = target.skips ?? []

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-end justify-center p-4 sm:items-center">
      <button
        aria-label={t('journey.skip.cancel', 'Cancel')}
        onClick={onCancel}
        className="absolute inset-0 bg-ink/30"
      />

      <div
        ref={box}
        tabIndex={-1}
        role="dialog"
        aria-modal="true"
        aria-labelledby="skip-title"
        className="relative w-full max-w-md rounded-xl border border-line bg-surface shadow-xl outline-none"
      >
        <div className="px-5 py-4">
          <h3 id="skip-title" className="text-[0.9375rem] font-semibold">
            {t('journey.skip.title', 'Just so you know')}
          </h3>
          <p className="mt-2 text-[0.875rem] leading-relaxed">
            {t(
              'journey.skip.body',
              'Moving straight to {stage} passes over {skipped}.',
              {
                stage: stageName(t, target.label).toLowerCase(),
                skipped: listOf(t, skipped.map((s) => stageName(t, s))),
              }
            )}
          </p>
          <p className="mt-2 text-[0.8125rem] leading-relaxed text-muted">
            {t(
              'journey.skip.reassure',
              'That is often right. Many admissions skip some of these. Your ' +
                'estimate stays accurate, and you can come back to any stage.')}
          </p>

          <label className="mt-4 flex items-start gap-2 text-[0.8125rem] text-muted">
            <input
              type="checkbox"
              checked={explain}
              onChange={(event) => setExplain(event.target.checked)}
              className="mt-0.5 rounded border-line"
            />
            {t('journey.skip.note', 'I would like to note why (optional)')}
          </label>

          {explain && (
            <textarea
              autoFocus
              rows={3}
              value={reason}
              onChange={(event) => setReason(event.target.value)}
              maxLength={600}
              placeholder={t(
                'journey.skip.placeholder',
                'For example: admitted through emergency, so there was no time ' +
                  'for pre-approval.'
              )}
              className="mt-2 w-full rounded-lg border border-line bg-surface px-3 py-2 text-[0.875rem] outline-none focus:border-brand focus:ring-2 focus:ring-brand/15"
            />
          )}
        </div>

        <div className="flex flex-wrap gap-2 border-t border-line px-5 py-3">
          <Button disabled={busy} onClick={() => onConfirm(reason)}>
            {t('journey.skip.confirm', 'Skip to {stage}', {
              stage: stageName(t, target.label).toLowerCase(),
            })}
          </Button>
          <Button variant="secondary" disabled={busy} onClick={onCancel}>
            {t('journey.skip.decline', 'Not yet')}
          </Button>
        </div>
      </div>
    </div>,
    document.body
  )
}

// "a, b and c". The conjunction is translated because it is a word, and the
// comma is not because it is punctuation these scripts share.
function listOf(t, items) {
  const names = items.map((s) => s.toLowerCase())
  if (names.length === 0) return t('list.a_stage', 'a stage')
  if (names.length === 1) return names[0]
  const last = names[names.length - 1]
  return `${names.slice(0, -1).join(', ')} ${t('list.and', 'and')} ${last}`
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

// Two ceilings, because a photograph shrinks and a document does not.
//
// The first is what will be looked at: past it, the file is refused without
// being decoded, so a mis-picked video cannot be turned into a canvas. The
// second is what may be kept, applied to whatever comes back from shrinking,
// which for a phone photograph is most of a megabyte rather than most of ten.
// The browser's own store is finite and shared with everything else this
// device holds.
const MAX_ATTACH_MB = 25
const MAX_RECEIPT_MB = 10

const inMB = (bytes) => (bytes / 1024 / 1024).toFixed(bytes > 1024 * 1024 ? 1 : 2)

// One charge, entered in a hurry, with the paper it came from.
//
// It was a column: a labelled dropdown, a labelled box, a full-width dashed
// button, a checkbox and a full-width button, five rows deep for two facts.
// The two facts and the button that files them are one row now; what is
// optional sits under them, out of the way of somebody entering the fourth
// charge of the day.
//
// The attachment is the part worth having. A charge is a line and a number,
// and what settles an argument at a claims desk is the invoice that line came
// from. Attached now, while it is in somebody's hand, it is filed against this
// charge and cannot be the receipt nobody can find in six weeks.
function CostCard({ onRecordCost, busy, className = '' }) {
  const t = useT()
  const [head, setHead] = useState('room_rent')
  const [amount, setAmount] = useState('')
  const [advanceDay, setAdvanceDay] = useState(true)
  const [receipt, setReceipt] = useState(null)
  const [shrunk, setShrunk] = useState(null)
  const [reading, setReading] = useState(false)
  const [refused, setRefused] = useState('')
  const fileRef = useRef(null)

  function clearFile() {
    setReceipt(null)
    setShrunk(null)
    if (fileRef.current) fileRef.current.value = ''
  }

  function tooLarge(size, limit) {
    setRefused(
      t('journey.receipt.too_large',
        'That file is {size} MB. The largest we can take is {limit} MB.',
        { size: inMB(size), limit })
    )
    clearFile()
  }

  async function attach(file) {
    if (!file) return
    if (!typeOf(file.name)) {
      setRefused(
        t('journey.receipt.wrong_kind',
          'Attach a PDF or a photo of the bill: PDF, JPG, PNG, WEBP, HEIC or TIFF.')
      )
      clearFile()
      return
    }
    if (file.size > MAX_ATTACH_MB * 1024 * 1024) {
      tooLarge(file.size, MAX_ATTACH_MB)
      return
    }

    setRefused('')
    setReading(true)
    // Redrawn smaller before it is held on to, so what the charge carries from
    // here on is one file and not two. Anything this browser cannot decode
    // comes back exactly as it went in.
    const kept = await shrinkImage(file)
    setReading(false)

    if (kept.size > MAX_RECEIPT_MB * 1024 * 1024) {
      tooLarge(kept.size, MAX_RECEIPT_MB)
      return
    }
    setReceipt(kept)
    setShrunk(kept.size < file.size ? { was: file.size, now: kept.size } : null)
  }

  return (
    <Card className={className}>
      <CardHeader
        title={t('journey.add_charge', 'Add a charge')}
        subtitle={t(
          'journey.add_charge.hint',
          'Enter bills as they arrive to keep the estimate current.'
        )}
      />
      <div className="p-5">
        {/* `items-end` puts the button on the line of the boxes rather than of
            the labels above them. */}
        <div className="grid items-end gap-3 sm:grid-cols-[minmax(0,1fr)_minmax(0,12rem)_auto]">
          <Field label={t('journey.charge.head', 'What is it for?')}>
            <Select value={head} onChange={(event) => setHead(event.target.value)}>
              {HEADS.map(([value, label]) => (
                <option key={value} value={value}>{t(`head.${value}`, label)}</option>
              ))}
            </Select>
          </Field>

          <Field label={t('journey.charge.amount', 'Amount')}>
            <Input
              type="number"
              placeholder="0"
              value={amount}
              onChange={(event) => setAmount(event.target.value)}
            />
          </Field>

          <Button
            // Not merely "something was typed": a charge of nothing is a row
            // in a ledger that says nothing, and the box beside this one has
            // always refused it.
            disabled={busy || reading || !(Number(amount) > 0)}
            onClick={() => {
              onRecordCost({ head, amount: Number(amount), advanceDay, receipt })
              setAmount('')
              clearFile()
            }}
          >
            {t('journey.charge.add', 'Add charge')}
          </Button>
        </div>

        <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2">
          {/* Attaching the bill now saves hunting for it at claim time, which
              is the part of this people actually dread. Entirely optional. */}
          <input
            ref={fileRef}
            type="file"
            accept={ACCEPT}
            className="hidden"
            onChange={(event) => attach(event.target.files?.[0])}
          />
          {reading ? (
            <span className="flex items-center gap-2 rounded-lg border border-line bg-canvas px-3 py-1.5 text-[0.8125rem] text-muted">
              <span className="h-3 w-3 animate-spin rounded-full border-2 border-line border-t-brand" />
              {t('journey.receipt.reading', 'Reading the file…')}
            </span>
          ) : receipt ? (
            <span className="flex min-w-0 max-w-full items-center gap-2 rounded-lg border border-line bg-canvas px-3 py-1.5">
              <ClipIcon />
              <span className="min-w-0 truncate text-[0.8125rem]">{receipt.name}</span>
              <button
                onClick={clearFile}
                className="shrink-0 text-[0.75rem] text-muted underline"
              >
                {t('journey.receipt.remove', 'remove')}
              </button>
            </span>
          ) : (
            <button
              onClick={() => fileRef.current?.click()}
              className="flex items-center gap-1.5 rounded-lg border border-dashed border-line px-3 py-1.5 text-[0.8125rem] text-muted transition hover:border-brand/40 hover:text-ink"
            >
              <ClipIcon />
              {t('journey.receipt.attach', 'Attach the bill or receipt (optional)')}
            </button>
          )}

          <label className="flex items-center gap-2 text-[0.8125rem] text-muted">
            <input
              type="checkbox"
              checked={advanceDay}
              onChange={(event) => setAdvanceDay(event.target.checked)}
              className="rounded border-line"
            />
            {t('journey.charge.new_day', 'This is a new day of the stay')}
          </label>
        </div>

        {refused && (
          <p className="mt-2 text-[0.75rem] leading-relaxed text-warn">{refused}</p>
        )}

        {receipt && (
          <p className="mt-2 text-[0.75rem] leading-relaxed text-muted">
            {t(
              'journey.receipt.kept',
              'Kept on this device with the charge. It is never uploaded.'
            )}
            {shrunk && (
              <>
                {' '}
                {t(
                  'journey.receipt.shrunk',
                  'The photo was {was} MB and is kept at {now} MB, which still ' +
                    'reads and is far smaller to send.',
                  { was: inMB(shrunk.was), now: inMB(shrunk.now) }
                )}
              </>
            )}
          </p>
        )}
      </div>
    </Card>
  )
}