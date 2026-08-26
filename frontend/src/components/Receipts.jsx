import { useEffect, useMemo, useState } from 'react'
import { createPortal } from 'react-dom'
import { useDialog } from '../hooks/useDialog'
import { useT } from '../hooks/useLanguage'
import { canShowPdf, isImage } from '../lib/receipts'
import { moment } from '../lib/i18n'
import { save } from '../lib/zip'

// The paperwork behind the ledger.
//
// A charge is a line and a number. What settles an argument at a claims desk
// is the piece of paper that line came from, and by the time anybody asks for
// it the paper is at the bottom of a bag or has been thrown away. So every
// charge can carry its own bill, and this is where they are all kept: grouped
// by what they were paid for, the way photographs group into albums, and
// openable one by one without leaving the stay.
//
// The files never left this device. See lib/receipts.js.

// One album per head, in the order the first paper in each was added, so the
// shelf does not reorder itself under somebody who is halfway down it.
function albums(papers) {
  const byHead = new Map()
  for (const paper of papers) {
    const key = paper.head || 'other'
    if (!byHead.has(key)) byHead.set(key, [])
    byHead.get(key).push(paper)
  }
  return [...byHead.entries()].map(([head, items]) => ({ head, items }))
}

export function Papers({ papers, busy }) {
  const t = useT()
  const [at, setAt] = useState(null)
  const shelves = useMemo(() => albums(papers), [papers])

  // A phone photograph is often HEIC, which is an image this browser will not
  // decode. Without this the shelf showed it as a broken picture, which reads
  // as a lost file rather than an unopenable one.
  const [unshowable, setUnshowable] = useState(() => new Set())

  // Object URLs for the thumbnails, made when the shelf changes and given back
  // when it changes again. Left to the garbage collector they pin every
  // photograph on the stay in memory for as long as the tab is open.
  //
  // Made inside the effect that gives them back, not in a memo beside it. A
  // memo is not re-run when an effect is torn down and set up again, which is
  // what React does to every effect on mount in development: the URLs were
  // handed back a moment after being made and never made again, and every
  // thumbnail on the shelf was a broken image.
  const [urls, setUrls] = useState(new Map())
  useEffect(() => {
    const made = new Map()
    for (const paper of papers) {
      if (isImage(paper.type)) made.set(paper.id, URL.createObjectURL(paper.blob))
    }
    setUrls(made)
    return () => {
      for (const url of made.values()) URL.revokeObjectURL(url)
      setUrls(new Map())
    }
  }, [papers])

  if (busy) {
    return (
      <p className="px-5 py-6 text-center text-[0.875rem] text-muted">
        {t('journey.papers.reading', 'Opening your files…')}
      </p>
    )
  }

  if (papers.length === 0) {
    return (
      <p className="px-5 py-6 text-center text-[0.875rem] leading-relaxed text-muted">
        {t(
          'journey.papers.none',
          'Nothing attached yet. When you add a charge, attach the bill or ' +
            'receipt with it and it is filed here, against that charge.'
        )}
      </p>
    )
  }

  return (
    <>
      <div className="space-y-4 px-5 py-4">
        {shelves.map((shelf) => (
          <section key={shelf.head}>
            <h3 className="flex items-baseline gap-2 text-[0.8125rem] font-medium">
              {shelf.items[0].headLabel}
              <span className="text-[0.75rem] font-normal text-muted">
                {t('journey.papers.count', '{count} attached', {
                  count: shelf.items.length,
                })}
              </span>
            </h3>

            <ul className="mt-2 grid grid-cols-[repeat(auto-fill,minmax(6.5rem,1fr))] gap-2.5">
              {shelf.items.map((paper) => (
                <li key={paper.id}>
                  <button
                    onClick={() => setAt(papers.indexOf(paper))}
                    className="group w-full overflow-hidden rounded-lg border border-line text-left transition hover:border-brand/50"
                  >
                    {/* Sized by the column rather than fixed, so a phone,
                        which gives each of two columns half of a narrow
                        screen, does not show an eighty-pixel sliver of an A4
                        page. Anchored to the top because that is where a bill
                        puts the hospital's name and its number, which is what
                        somebody is looking for when they scan a shelf. */}
                    <span className="flex aspect-[4/3] items-center justify-center overflow-hidden bg-canvas">
                      {urls.has(paper.id) && !unshowable.has(paper.id) ? (
                        <img
                          src={urls.get(paper.id)}
                          alt=""
                          onError={() =>
                            setUnshowable((known) => new Set(known).add(paper.id))
                          }
                          className="h-full w-full object-cover object-top"
                        />
                      ) : (
                        <PaperIcon />
                      )}
                    </span>
                    <span className="block truncate px-2 py-1.5 text-[0.75rem] text-muted group-hover:text-ink">
                      {paper.name}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          </section>
        ))}
      </div>

      <p className="border-t border-line px-5 py-2.5 text-[0.75rem] leading-relaxed text-muted">
        {t(
          'journey.papers.where',
          'Held on this device only, and never sent anywhere. They travel with ' +
            'the stay when you download it.'
        )}
      </p>

      {at !== null && (
        <Preview
          papers={papers}
          at={at}
          onMove={setAt}
          onClose={() => setAt(null)}
        />
      )}
    </>
  )
}

// One paper, filling the window it was opened from.
//
// Into the body rather than where it is written, for the same reason the skip
// notice is: this is raised from inside a card that animates in, and a
// finished animation leaves a transform behind, which is enough to make
// `position: fixed` measure itself against that card instead of the screen.
function Preview({ papers, at, onMove, onClose }) {
  const t = useT()
  const paper = papers[at]
  const box = useDialog(true, onClose)
  const [broken, setBroken] = useState(false)

  // Same as the thumbnails above: made in the effect that revokes it, so a
  // development remount does not leave this holding a URL it has given back.
  const [url, setUrl] = useState('')
  useEffect(() => {
    const made = URL.createObjectURL(paper.blob)
    setUrl(made)
    setBroken(false)
    return () => {
      URL.revokeObjectURL(made)
      setUrl('')
    }
  }, [paper.blob])

  // What this file can actually be shown as here, decided once. A phone
  // browser with no PDF viewer is told apart from a file that failed to
  // decode, because the answer to both is the same panel and the same button.
  const shows =
    broken ? 'none'
      : isImage(paper.type) ? 'image'
        : paper.type === 'application/pdf' && canShowPdf() ? 'pdf'
          : 'none'

  useEffect(() => {
    const onKey = (event) => {
      if (event.key === 'ArrowRight' && at < papers.length - 1) onMove(at + 1)
      if (event.key === 'ArrowLeft' && at > 0) onMove(at - 1)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [at, papers.length, onMove])

  return createPortal(
    <div className="fixed inset-0 z-50 flex flex-col bg-black/70 p-3 sm:p-6 motion-safe:animate-fade">
      <button
        aria-label={t('journey.papers.close', 'Close')}
        onClick={onClose}
        className="absolute inset-0 cursor-default"
      />

      <div
        ref={box}
        tabIndex={-1}
        role="dialog"
        aria-modal="true"
        aria-label={paper.name}
        className="relative mx-auto flex min-h-0 w-full max-w-4xl flex-1 flex-col overflow-hidden rounded-xl border border-line bg-surface outline-none"
      >
        <header className="flex items-center gap-3 border-b border-line px-4 py-2.5">
          <div className="min-w-0 flex-1">
            <p className="truncate text-[0.875rem] font-medium">{paper.name}</p>
            <p className="truncate text-[0.75rem] text-muted">
              {t('journey.papers.for', '{head} · {amount} · added {when}', {
                head: paper.headLabel,
                amount: paper.amount,
                when: moment(paper.at),
              })}
            </p>
          </div>

          <button
            onClick={() => save(paper.blob, paper.name)}
            className="shrink-0 rounded-lg border border-line px-2.5 py-1.5 text-[0.8125rem] transition hover:bg-canvas"
          >
            {t('journey.papers.save', 'Save')}
          </button>
          <button
            aria-label={t('journey.papers.close', 'Close')}
            onClick={onClose}
            className="shrink-0 rounded-lg px-2 py-1 text-[1.125rem] leading-none text-muted transition hover:bg-canvas hover:text-ink"
          >
            &times;
          </button>
        </header>

        <div className="flex min-h-0 flex-1 items-center justify-center overflow-auto bg-canvas">
          {/* Nothing until there is something to point at. An `<img>` given an
              empty source fails to load, and failing to load is how this
              decides a file cannot be shown. */}
          {!url ? null : shows === 'image' ? (
            <img
              src={url}
              alt={paper.name}
              onError={() => setBroken(true)}
              className="max-h-full max-w-full object-contain"
            />
          ) : shows === 'pdf' ? (
            // Not sandboxed, deliberately, and the reasoning is worth keeping.
            //
            // A sandboxed frame is one Chrome will not run its PDF viewer in:
            // it paints the broken-document icon and nothing else, which is
            // what this screen did until it was looked at under the policy the
            // built page actually ships with. What makes dropping it safe is
            // upstream of here. The blob was typed from the file's own
            // extension against a fixed list, never from its contents or from
            // what it claims, so this frame is only ever handed
            // `application/pdf`, and a browser handed that runs its PDF viewer
            // and never its HTML parser. A page wearing a `.pdf` suffix is a
            // PDF that fails to parse. The policy allows `frame-src blob:` and
            // nothing else, so no other document can be put here at all.
            <iframe
              title={paper.name}
              src={url}
              referrerPolicy="no-referrer"
              className="h-full w-full border-0"
            />
          ) : (
            <Unshowable name={paper.name} onSave={() => save(paper.blob, paper.name)} />
          )}
        </div>

        {papers.length > 1 && (
          <footer className="flex items-center justify-between gap-3 border-t border-line px-4 py-2">
            <button
              disabled={at === 0}
              onClick={() => onMove(at - 1)}
              className="rounded-lg px-2.5 py-1.5 text-[0.8125rem] transition hover:bg-canvas disabled:opacity-40"
            >
              {t('journey.papers.previous', 'Previous')}
            </button>
            <span className="text-[0.75rem] text-muted">
              {t('journey.papers.position', '{at} of {total}', {
                at: at + 1, total: papers.length,
              })}
            </span>
            <button
              disabled={at === papers.length - 1}
              onClick={() => onMove(at + 1)}
              className="rounded-lg px-2.5 py-1.5 text-[0.8125rem] transition hover:bg-canvas disabled:opacity-40"
            >
              {t('journey.papers.next', 'Next')}
            </button>
          </footer>
        )}
      </div>
    </div>,
    document.body
  )
}

// A phone photograph is often HEIC, which most browsers will not decode. The
// file is still the right file and still goes into the download; it just
// cannot be shown here.
function Unshowable({ name, onSave }) {
  const t = useT()
  return (
    <div className="px-6 py-10 text-center">
      <PaperIcon large />
      <p className="mt-3 text-[0.875rem] font-medium">{name}</p>
      <p className="mx-auto mt-1.5 max-w-sm text-[0.8125rem] leading-relaxed text-muted">
        {t(
          'journey.papers.unshowable',
          'This browser will not open that kind of file. It is kept as it was ' +
            'and still goes into the download.'
        )}
      </p>
      <button
        onClick={onSave}
        className="mt-3 rounded-lg border border-line bg-surface px-3 py-1.5 text-[0.8125rem] transition hover:bg-canvas"
      >
        {t('journey.papers.save', 'Save')}
      </button>
    </div>
  )
}

function PaperIcon({ large = false }) {
  return (
    <svg
      viewBox="0 0 24 24" aria-hidden="true"
      className={`${large ? 'mx-auto h-8 w-8' : 'h-6 w-6'} text-muted`}
      fill="none" stroke="currentColor" strokeWidth="1.5"
      strokeLinecap="round" strokeLinejoin="round"
    >
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <path d="M14 2v6h6" />
      <path d="M8 13h8M8 17h5" />
    </svg>
  )
}