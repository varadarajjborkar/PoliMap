import { useEffect, useId, useMemo, useRef, useState } from 'react'
import { useT } from '../hooks/useLanguage'

// Choosing a treatment by typing, but only ever choosing a real one.
//
// A dropdown of 126 clinical names assumes the person searching already knows
// the clinical name. They do not: they were handed a chit an hour ago and were
// told their father needs "a stent". So the box takes free text and matches it
// against the catalogue name, the specialty, and the words people actually use.
//
// What it will not do is accept whatever was typed. Everything downstream is
// costed against a catalogue entry, so a free-text treatment would be a
// treatment with no package price, no length of stay and no cost split. The
// input is a way of finding a row, not a way of inventing one.

const MAX_SHOWN = 8

// The best of every route to this row, not the first one that hits.
//
// Returning early on a name match was wrong in a way that showed: "Angioplasty
// with single stent" contains the word "stent", so a search for "stent" scored
// it on the weak name-contains rule and never reached the exact synonym that
// makes it the right answer. A ureteric stent came first.
//
// An exact layman word outranks any name match, because somebody typing "piles"
// means the one row that word belongs to. A specialty term ranks below every
// name match, because "bone" narrows the field without naming anything in it.
function score(procedure, needle) {
  const name = procedure.name.toLowerCase()
  let best = 0

  if (name === needle) best = 100
  else if (name.startsWith(needle)) best = 90
  else if (name.includes(needle)) best = 70

  const synonyms = procedure.synonyms ?? []
  if (synonyms.some((s) => s === needle)) best = Math.max(best, 95)
  else if (synonyms.some((s) => s.startsWith(needle))) best = Math.max(best, 80)
  else if (synonyms.some((s) => s.includes(needle))) best = Math.max(best, 55)

  const terms = procedure.specialty_terms ?? []
  if (terms.some((t) => t === needle)) best = Math.max(best, 40)
  else if (terms.some((t) => t.includes(needle))) best = Math.max(best, 25)

  if (procedure.specialty_label?.toLowerCase().includes(needle)) {
    best = Math.max(best, 20)
  }
  return best
}

export function TreatmentPicker({ procedures, value, onChange, id }) {
  const t = useT()
  const selected = procedures.find((p) => p.code === value) ?? null
  const [query, setQuery] = useState('')
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState(0)
  const boxRef = useRef(null)
  const listId = useId()

  // Show the chosen treatment's name when the box is not being edited, so the
  // field reads as an answer rather than as an empty search.
  const text = open ? query : selected?.name ?? ''

  const matches = useMemo(() => {
    const needle = query.trim().toLowerCase()
    if (!needle) {
      // Before anything is typed, offer the common admissions rather than the
      // alphabetical head of a list nobody wants to read.
      return procedures.slice(0, MAX_SHOWN)
    }
    return procedures
      .map((p) => [score(p, needle), p])
      .filter(([s]) => s > 0)
      .sort((a, b) => b[0] - a[0] || a[1].name.localeCompare(b[1].name))
      .slice(0, MAX_SHOWN)
      .map(([, p]) => p)
  }, [procedures, query])

  useEffect(() => setActive(0), [query])

  useEffect(() => {
    if (!open) return
    const away = (event) => {
      if (!boxRef.current?.contains(event.target)) setOpen(false)
    }
    document.addEventListener('mousedown', away)
    return () => document.removeEventListener('mousedown', away)
  }, [open])

  // Opening is one thing whichever way it is asked for, and it always starts
  // from an empty query so the common admissions are offered rather than the
  // name already chosen, which matches nothing.
  function openList() {
    setQuery('')
    setOpen(true)
  }

  function choose(procedure) {
    onChange(procedure.code)
    setQuery('')
    setOpen(false)
  }

  function onKeyDown(event) {
    if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
      event.preventDefault()
      setOpen(true)
      setActive((i) => {
        const step = event.key === 'ArrowDown' ? 1 : -1
        return (i + step + matches.length) % Math.max(matches.length, 1)
      })
    } else if (event.key === 'Enter' && open && matches[active]) {
      event.preventDefault()
      choose(matches[active])
    } else if (event.key === 'Escape') {
      setOpen(false)
    }
  }

  return (
    <div ref={boxRef} className="relative">
      <input
        id={id}
        type="text"
        role="combobox"
        aria-expanded={open}
        aria-controls={listId}
        aria-autocomplete="list"
        autoComplete="off"
        value={text}
        placeholder={t(
          'treatment.placeholder',
          'Type what you were told, e.g. stent, delivery, gall bladder'
        )}
        onFocus={openList}
        // Choosing never moves focus away from this box, so coming back to it
        // fires no focus event and the list would stay shut. A click while it
        // is already open is somebody putting the cursor somewhere in what
        // they have typed, and must not wipe it.
        onClick={() => { if (!open) openList() }}
        onChange={(e) => { setQuery(e.target.value); setOpen(true) }}
        onKeyDown={onKeyDown}
        className="w-full rounded-lg border border-line bg-surface px-3 py-2.5 text-[0.9375rem] outline-none transition focus:border-brand focus:ring-2 focus:ring-brand/15"
      />

      {open && (
        <ul
          id={listId}
          role="listbox"
          className="absolute z-30 mt-1 max-h-72 w-full overflow-auto rounded-lg border border-line bg-surface shadow-lg motion-safe:animate-fade"
        >
          {matches.length === 0 && (
            <li className="px-3 py-3 text-[0.875rem] leading-relaxed text-muted">
              {t(
                'treatment.no_match',
                'Nothing matched that. Try a simpler word, like the part of ' +
                  "the body, or the word on your doctor's note."
              )}
            </li>
          )}
          {matches.map((procedure, index) => (
            <li key={procedure.code} role="option" aria-selected={index === active}>
              <button
                type="button"
                onMouseEnter={() => setActive(index)}
                // Pressing an option must not take focus off the box. It is
                // the standard behaviour for a list like this, and here it is
                // also what stops anything outside from reacting to the box
                // being focused all over again a moment after a choice.
                onMouseDown={(event) => event.preventDefault()}
                onClick={() => choose(procedure)}
                className={`flex w-full items-baseline justify-between gap-3 px-3 py-2.5 text-left transition ${
                  index === active ? 'bg-brand-soft' : ''
                }`}
              >
                <span className="min-w-0">
                  <span className="block truncate text-[0.9375rem]">
                    {procedure.name}
                  </span>
                  <span className="block truncate text-[0.8125rem] text-muted">
                    {procedure.specialty_label}
                    {procedure.typical_stay_days
                      ? ` · usually ${procedure.typical_stay_days} day${
                          procedure.typical_stay_days === 1 ? '' : 's'
                        }`
                      : ''}
                  </span>
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
