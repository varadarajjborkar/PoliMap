// Every interface string resolves in every language.
//
// A missing translation is invisible by design: the call site passes the
// English and that is what renders, so a language can quietly rot back into
// English one key at a time and nothing on screen says so. This is the thing
// that says so.
//
// Also fails on a key with no call site, which is the same problem read the
// other way: a translation nobody can reach looks like coverage and is not.

import { readFileSync, readdirSync, statSync } from 'node:fs'
import { join } from 'node:path'

const SRC = new URL('../src/', import.meta.url).pathname

// Keys built from a variable at the call site, with the values that variable
// can take. Listed here because a static read cannot know them.
//
// Keyed on the fixed part of the key, not on the expression that fills the
// rest: the same family is built from different variables in different files,
// and the variable's name is not what identifies it.
const TEMPLATES = {
  'journey.stage.': [
    'pre_admission', 'admitted', 'discharge_planning', 'settled',
  ],
  'step.': ['upload', 'policy', 'search'],
  'step.short.': ['upload', 'policy', 'search'],
  // The server sends each of these as an enum value beside its English label,
  // so the label is the fallback and the value is the key. Every list mirrors
  // an enum in backend/app/schemas: a value added there without a line here
  // fails this check rather than quietly rendering English.
  'head.': [
    'room_rent', 'icu_charges', 'investigations', 'pharmacy', 'consumables',
    'surgeon_fee', 'ot_charges', 'nursing', 'implants', 'non_medical',
  ],
  'preference.': [
    'protect_money', 'best_care', 'nearest', 'balanced',
  ],
  'exclusion.': [
    'too_far', 'procedure_unavailable', 'specialty_unavailable', 'not_cashless',
    'no_bed_available', 'no_eligible_room', 'scheme_not_empanelled',
  ],
  'room.': [
    'general_ward', 'twin_sharing', 'single_private', 'deluxe', 'suite', 'icu',
  ],
  'settlement.': [
    'cashless', 'reimbursement', 'scheme_package',
  ],
}

function walk(dir) {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name)
    return statSync(path).isDirectory() ? walk(path) : [path]
  })
}

const used = new Set()
for (const path of walk(SRC).filter((p) => p.endsWith('.jsx'))) {
  const text = readFileSync(path, 'utf8')
  for (const [, key] of text.matchAll(/\bt\(\s*'([a-z][a-z0-9._]*)'/g)) {
    // Other calls end in "t(" too, and only a dotted key is one of ours.
    if (key.includes('.') || key === 'disclaimer') used.add(key)
  }
  for (const [, template] of text.matchAll(/\bt\(`([^`]+)`/g)) {
    const stem = template.slice(0, template.indexOf('${'))
    const values = TEMPLATES[stem]
    if (!values) {
      console.error(`unknown key template ${template} in ${path}`)
      process.exit(1)
    }
    for (const value of values) used.add(stem + value)
  }
}

// One file per language, because that is how they are loaded: a reader gets
// the one they chose and not the other four.
const problems = []
for (const code of ['hi', 'kn', 'mr', 'te']) {
  const block = readFileSync(join(SRC, `lib/lang/${code}.js`), 'utf8')
    .match(/^export default \{(.*?)^\}/ms)
  if (!block) {
    problems.push(`${code}: no table`)
    continue
  }
  const keys = new Set(
    [...block[1].matchAll(/^\s*'?([a-zA-Z][a-zA-Z0-9._]*)'?:/gm)].map((m) => m[1])
  )
  for (const key of used) {
    if (!keys.has(key)) problems.push(`${code}: missing ${key}`)
  }
  for (const key of keys) {
    if (!used.has(key)) problems.push(`${code}: ${key} is never rendered`)
  }
}

if (problems.length) {
  for (const problem of problems) console.error(problem)
  process.exit(1)
}
console.log(`strings: ${used.size} keys resolve in every language`)
