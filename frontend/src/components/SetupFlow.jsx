import { useCallback, useEffect, useLayoutEffect, useRef } from 'react'
import { useT } from '../hooks/useLanguage'
import { SETUP_STEPS } from '../hooks/useRoute'

// Setting up, as one page rather than three.
//
// The three steps are one piece of work: read the policy, check what it says,
// find somewhere it covers. Splitting them across three screens meant the
// answer to "what was my room limit again" was a page away at the moment it
// mattered, and each transition threw away the sense of having got somewhere.
//
// So they stack, each unlocking as the one above it is answered, and the page
// scrolls to the new one. The thread down the left says how far in you are and
// takes you back; the rail on the right keeps what has been settled in view
// while you work on what has not, because that column was empty and the figures
// are what somebody is checking against.
//
// Nothing is skipped and nothing is hidden: a section that is not reachable yet
// says why rather than not existing, so the shape of the whole task is visible
// from the first screen.

export function SetupFlow({
  step, onStepInView, reached, sections, rail, jump,
}) {
  const t = useT()
  const refs = useRef({})
  const lastScrolled = useRef(null)
  const settling = useRef(false)

  // Once there has been something to show, the column keeps its place. A rail
  // that came and went as you scrolled would move the thing you are reading
  // out from under you, which is worse than either position on its own.
  const everSettled = useRef(false)
  if (rail) everSettled.current = true
  const showRail = Boolean(rail) || everSettled.current

  const scrollTo = useCallback((id, { smooth = true } = {}) => {
    const node = refs.current[id]
    if (!node) return
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    // Suppress the scroll spy while the page is moving under it, or the
    // sections it passes through would each claim to be the current one.
    settling.current = true
    node.scrollIntoView({
      behavior: smooth && !reduced ? 'smooth' : 'instant', block: 'start',
    })
    window.setTimeout(() => { settling.current = false }, smooth && !reduced ? 700 : 0)
  }, [])

  // Land on the section the address bar names, without animating a jump the
  // user did not ask for.
  useLayoutEffect(() => {
    if (lastScrolled.current !== null) return
    lastScrolled.current = step
    if (step !== SETUP_STEPS[0].id) scrollTo(step, { smooth: false })
  }, [step, scrollTo])

  // Move to a section as it becomes answerable, once.
  //
  // Keyed on the id rather than on `reached`, which is rebuilt every render and
  // would otherwise run this on each one.
  const furthest =
    [...SETUP_STEPS].reverse().find((s) => reached[s.id])?.id ?? SETUP_STEPS[0].id

  useEffect(() => {
    if (furthest === lastScrolled.current) return
    lastScrolled.current = furthest
    scrollTo(furthest)
  }, [furthest, scrollTo])

  // A move asked for from inside a section: "continue", or a line on the rail
  // saying "check what we read". These used to navigate, which changed the
  // address bar and left the page exactly where it was, because in a scrolling
  // flow the destination is already on screen somewhere.
  useEffect(() => {
    if (jump?.id) scrollTo(jump.id)
  }, [jump, scrollTo])

  // Which section the reader is actually looking at, so the thread and the
  // address bar agree with the screen.
  const report = useRef(onStepInView)
  report.current = onStepInView

  // An observation already queued when this comes off screen is still
  // delivered afterwards, and it would report a section of a flow the reader
  // has left. Disconnecting is not enough on its own; this says so outright.
  const watching = useRef(true)

  useEffect(() => {
    const nodes = SETUP_STEPS.map((s) => refs.current[s.id]).filter(Boolean)
    if (!nodes.length) return

    const observer = new IntersectionObserver(
      (entries) => {
        if (settling.current || !watching.current) return
        const visible = entries
          .filter((e) => e.isIntersecting)
          .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)[0]
        if (visible?.target.dataset.step) report.current(visible.target.dataset.step)
      },
      // A band across the upper middle of the viewport: whatever is being read
      // is there, not at the very top where the header sits.
      { rootMargin: '-20% 0px -55% 0px', threshold: 0 }
    )
    watching.current = true
    nodes.forEach((node) => observer.observe(node))
    return () => {
      watching.current = false
      observer.disconnect()
    }
  }, [])

  return (
    // The phone's step bar sits above the row rather than inside it. It is a
    // sticky block in its own right, and as a child of the flex container it
    // became a column of its own and squeezed the reading width to nothing.
    <>
      <ThreadBar step={step} reached={reached} onGo={scrollTo} />

      <div className="flex gap-6 pb-6">
        <Thread step={step} reached={reached} onGo={scrollTo} />

        <div className="min-w-0 flex-1 space-y-16 pt-6">
          {SETUP_STEPS.map(({ id, label }) => (
            <section
              key={id}
              data-step={id}
              ref={(node) => { refs.current[id] = node }}
              aria-label={t(`step.${id}`, label)}
              className="scroll-mt-[calc(var(--header-h)+3.5rem)] lg:scroll-mt-[calc(var(--header-h)+1.5rem)]"
            >
              {sections[id]}
            </section>
          ))}
          {/* Room to scroll the last section to the top, so the thread's final
              knot can actually be reached. */}
          <div aria-hidden="true" className="h-[40vh]" />
        </div>

        {showRail ? (
          <aside className="sticky top-[calc(var(--header-h)+1.5rem)] hidden h-fit w-64 shrink-0 lg:block">
            {rail}
          </aside>
        ) : (
          /* Nothing settled yet, so nothing to put here. The thread on the
             left is still 11rem wide, and without something matching it on the
             right the work sits off centre. This is that something: it holds
             the column in the middle of the page until there is a reason
             not to. */
          <div aria-hidden="true" className="hidden w-44 shrink-0 lg:block" />
        )}
      </div>
    </>
  )
}

// The thread, with a knot per step.
//
// Sticky, so it is a sense of place rather than a menu you have to scroll back
// to find. A step already reached stays clickable, because comparing what you
// were shown at one against another is the reason anybody moves backwards here.
function Thread({ step, reached, onGo }) {
  const t = useT()
  const current = SETUP_STEPS.findIndex((s) => s.id === step)

  return (
    <nav
      aria-label={t('nav.setup', 'Setting up')}
      className="sticky top-[calc(var(--header-h)+1.5rem)] hidden h-fit w-44 shrink-0 lg:block"
    >
      <ol>
        {SETUP_STEPS.map(({ id, label }, index) => {
          const isCurrent = id === step
          const done = index < current && reached[id]
          const open = reached[id]
          const last = index === SETUP_STEPS.length - 1

          return (
            <li key={id} className="flex gap-3">
              <div className="flex flex-col items-center">
                <span
                  className={`flex h-3.5 w-3.5 shrink-0 items-center justify-center rounded-full border text-[0.5rem] leading-none transition ${
                    done
                      ? 'border-brand bg-brand text-on-brand'
                      : isCurrent
                        ? 'border-brand bg-surface ring-4 ring-brand/15'
                        : 'border-line bg-surface'
                  }`}
                >
                  {done ? '✓' : ''}
                </span>
                {!last && (
                  <span
                    className={`w-px flex-1 transition-colors ${
                      done ? 'bg-brand/40' : 'bg-line'
                    }`}
                  />
                )}
              </div>

              <button
                disabled={!open}
                aria-current={isCurrent ? 'step' : undefined}
                onClick={() => onGo(id)}
                className={`-mt-1 pb-8 text-left text-[0.875rem] leading-snug transition ${
                  isCurrent
                    ? 'font-semibold text-ink'
                    : open
                      ? 'text-muted hover:text-brand'
                      : 'cursor-not-allowed text-muted/45'
                }`}
              >
                {t(`step.${id}`, label)}
              </button>
            </li>
          )
        })}
      </ol>
    </nav>
  )
}

// The same thread, laid on its side, for a screen with no room beside the
// content. Sticky under the header, because on a phone the way back to a figure
// two sections up is otherwise a long scroll with nothing to aim at.
function ThreadBar({ step, reached, onGo }) {
  const t = useT()
  const current = SETUP_STEPS.findIndex((s) => s.id === step)

  // Sticky, not fixed. Fixed placed it against whatever its containing block
  // happened to be, and a spacer elsewhere in the tree had to guess its height
  // to stop it landing on the heading. Sticky is in the flow, so it occupies
  // its own space and needs nobody to reserve it.
  return (
    <nav
      aria-label={t('nav.setup', 'Setting up')}
      className="sticky top-[var(--header-h)] z-10 -mx-4 border-b border-line bg-surface/95 px-4 backdrop-blur lg:hidden"
    >
      <ol className="mx-auto flex max-w-3xl items-center px-4 py-2">
        {SETUP_STEPS.map(({ id, short }, index) => {
          const isCurrent = id === step
          const done = index < current && reached[id]
          return (
            <li key={id} className="flex flex-1 items-center last:flex-none">
              <button
                disabled={!reached[id]}
                aria-current={isCurrent ? 'step' : undefined}
                onClick={() => onGo(id)}
                className="flex items-center gap-1.5 disabled:cursor-not-allowed"
              >
                <span
                  className={`flex h-3.5 w-3.5 shrink-0 items-center justify-center rounded-full border text-[0.5rem] leading-none transition ${
                    done
                      ? 'border-brand bg-brand text-on-brand'
                      : isCurrent
                        ? 'border-brand bg-surface ring-4 ring-brand/15'
                        : 'border-line bg-surface'
                  }`}
                >
                  {done ? '✓' : ''}
                </span>
                <span
                  className={`text-[0.75rem] leading-none transition ${
                    isCurrent
                      ? 'font-semibold text-ink'
                      : reached[id] ? 'text-muted' : 'text-muted/45'
                  }`}
                >
                  {t(`step.short.${id}`, short)}
                </span>
              </button>
              {index < SETUP_STEPS.length - 1 && (
                <span
                  className={`mx-2 h-px flex-1 ${done ? 'bg-brand/40' : 'bg-line'}`}
                />
              )}
            </li>
          )
        })}
      </ol>
    </nav>
  )
}

// A section that cannot be worked on yet.
//
// Shown rather than hidden. Somebody who can see the whole shape of the task
// knows how much is left, and a step that appears out of nowhere reads as the
// application changing its mind.
export function Locked({ title, children }) {
  return (
    <div className="rounded-xl border border-dashed border-line px-5 py-8 text-center">
      <h2 className="text-[0.9375rem] font-semibold text-muted">{title}</h2>
      <p className="mx-auto mt-1.5 max-w-sm text-[0.875rem] leading-relaxed text-muted/80">
        {children}
      </p>
    </div>
  )
}

// What has been settled, kept beside what has not.
//
// The right column was empty, and the figures somebody is checking a hospital
// against are the ones they read two sections ago. Each line takes you back to
// where it can be changed.
export function SettledRail({ items }) {
  const t = useT()
  const shown = items.filter(Boolean)
  if (!shown.length) return null

  return (
    <div className="rounded-xl border border-line bg-surface motion-safe:animate-fade">
      <h2 className="border-b border-line px-4 py-2.5 text-[0.75rem] font-semibold uppercase tracking-wide text-muted">
        {t('rail.title', 'So far')}
      </h2>
      <dl className="divide-y divide-line">
        {shown.map((item) => (
          <div key={item.label} className="px-4 py-2.5">
            <dt className="text-[0.75rem] text-muted">{item.label}</dt>
            <dd className="mt-0.5 text-[0.875rem] font-medium leading-snug">
              {item.value}
            </dd>
            {item.onChange && (
              <button
                onClick={item.onChange}
                className="mt-1 text-[0.75rem] text-brand transition hover:underline"
              >
                {item.changeLabel ?? t('rail.change', 'Change')}
              </button>
            )}
          </div>
        ))}
      </dl>
    </div>
  )
}