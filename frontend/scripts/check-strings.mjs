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
  'accred.': ['none', 'nabh_entry', 'nabh_full', 'jci'],
  // A waiting period as a unit and a count. "24 months" is a phrase no table
  // can reach inside, so the span travels in parts and is rebuilt where it is
  // read, both inside a sentence and on its own beside the period it belongs to.
  'dur.': ['days', 'months', 'months_days', 'years'],
  'waitkind.': [
    'initial', 'pre_existing', 'specific_ailment', 'maternity', 'other',
  ],
  // A room or ICU cap is a sentence with figures in it, so the shape it takes
  // is the key and the figures travel beside it.
  'roomlimit.': ['none', 'per_day', 'category', 'per_day_category'],
  // What makes the high end of an estimate high.
  'driver.': ['longer_stay', 'longer_stay_implant', 'package_fixed'],

  // --- what the server writes ---------------------------------------------
  //
  // These sentences are composed in Python, where the policy and the bill are,
  // and arrive with the key they are read under. So the keys are listed rather
  // than found: nothing in this directory names them one by one, and without
  // this list a language could be missing every one and still pass.
  //
  // Each mirrors something in backend/app. A key added there without a line
  // here renders English; a line here the interface never asks for fails on
  // the next run, because no language will have been given a use for it.
  'checklist.': [
    'ask_cost_first', 'ask_for_room', 'carry_card', 'chase_preauth',
    'check_deduction', 'check_deductions', 'check_non_payables',
    'check_room_rate', 'claim_deadline', 'confirm_network',
    'consumables_running', 'daily_bill', 'diagnostics_sublimit',
    'discharge_summary', 'expect_consumables', 'final_approval',
    'gather_pre_bills', 'implant_invoice', 'itemised_bill', 'keep_receipts',
    'note_remaining', 'originals', 'post_window', 'post_window_until',
    'room_within_cap', 'settlement_letter', 'watch_the_room',
  ],
  // The deduction's name, and under the same stem the sentence beneath it.
  // Two wordings of one deduction are two keys: a co-payment banded on age and
  // one that is not are the same money and different sentences.
  'waterfall.': [
    'copay', 'copay_age', 'deductible', 'non_payable',
    'non_payable_consumables', 'procedure_cap', 'proportionate',
    'room_rent_cap', 'scheme_not_empanelled', 'scheme_package_rate',
    'second_policy', 'sublimit', 'sum_insured_exhausted',
  ],
  'alert.': [
    'cover_almost_gone', 'cover_most_used', 'cover_on_track_days',
    'cover_on_track_soon', 'cover_on_track_today', 'non_payable_accumulating',
    'pre_auth_due', 'room_over_limit', 'room_over_limit_knock_on',
    'room_rate_conflict', 'sublimit_nearly_used',
  ],
  'billnote.': ['icu_days', 'nights', 'non_medical', 'tier_scaled'],
  'elig.': [
    'daycare_excluded', 'daycare_unknown', 'initial_accident', 'initial_days',
    'initial_months', 'initial_years', 'named_days', 'named_months',
    'named_years', 'no_start_date', 'pre_existing_ask', 'pre_existing_days',
    'pre_existing_months', 'pre_existing_years', 'scheme',
  ],
  // The two findings that a single answer from the user would settle.
  'eligask.': ['no_start_date', 'pre_existing_ask'],
  'relax.': [
    'bed_availability', 'non_network', 'room_category', 'wider_radius',
  ],
  'advice.': [
    'no_bed_available', 'no_eligible_room', 'not_cashless',
    'procedure_unavailable', 'specialty_unavailable', 'too_far',
  ],
  // The help desk's own sentences. Everything it wrote down travels with the
  // key it is read under; a model's answer does not, because that one came back
  // in the language it was asked in. `helpq.` is the question on a chip,
  // `helpsay.` is anything the desk says that this repository wrote.
  'helpq.': [
    'bill_check', 'cashless', 'claim_papers', 'cover_left', 'no_document',
    'non_payable', 'pre_existing', 'privacy', 'room_limit', 'second_policy',
    'what_this_is', 'whose_name', 'which_document', 'wrong_figure',
  ],
  'helpsay.': [
    'opening', 'unknown',
    'refuse.action', 'refuse.clinical', 'refuse.other_peoples_data',
    'refuse.ruling',
    'answer.bill_check', 'answer.cashless', 'answer.claim_papers',
    'answer.cover_left', 'answer.no_document', 'answer.non_payable',
    'answer.pre_existing', 'answer.privacy', 'answer.room_limit',
    'answer.second_policy', 'answer.what_this_is', 'answer.whose_name',
    'answer.which_document', 'answer.wrong_figure',
  ],
  'ticket.': ['data', 'feedback', 'problem'],
  // What kind of thing was found on a bill, which is a name and not a
  // sentence. The sentences are under `finding.` below.
  'findkind.': [
    'consumables', 'duplicate', 'line_arithmetic', 'optional_item',
    'proportionate', 'room_above_cap', 'sublimit', 'subsumed',
    'total_mismatch', 'uncertain_read', 'unplaced',
  ],
  'finding.': [
    'consumables', 'duplicate', 'line_arithmetic_over',
    'line_arithmetic_under', 'listing.in_procedure', 'listing.in_room',
    'listing.in_treatment', 'listing.optional', 'proportionate',
    'room_rent_cap', 'sublimit', 'total_mismatch', 'uncertain_read',
    'uncertain_read_no_total', 'unplaced',
  ],
}

// Sentences whose key already names its own family, so the call site passes it
// through whole rather than building it. Same contract as the templates above.
const SERVER_KEYS = [
  'counterfactual.saving', 'counterfactual.within_cap',
  'doc.hard_to_read', 'doc.no_schedule', 'doc.unreadable',
  'doc.unreadable_pages',
  'note.consumables_covered', 'note.copay_not_applicable', 'note.restore',
  'note.scheme_nothing_to_pay', 'note.scheme_room_free',
  'note.scheme_window_after', 'note.scheme_window_both',
  'note.which_insurer_first',
  'order.cheaper', 'order.forced', 'order.same',
  'reason.accredited', 'reason.balanced', 'reason.best_equipped',
  'reason.cashless', 'reason.cheapest', 'reason.nearest',
  'search.found', 'search.found_relaxed', 'search.no_estimate',
  'search.no_treatment', 'search.none', 'search.none_offering',
  'search.starved',
  'tradeoff.costlier', 'tradeoff.further', 'tradeoff.pay_first',
  'warn.cover_used_up', 'warn.not_cashless', 'warn.proportionate',
  'warn.room_category', 'warn.scheme_cover_short', 'warn.scheme_unusable',
  'warn.scheme_unusable_reimbursable', 'warn.scheme_upgrade',
]

// Keys asked for from lib/, not from a component.
//
// The progress panel's phase names and the line under the phase being worked
// on are chosen from tables in lib/progress.js by a key the scan below cannot
// see: the call site passes a variable. They are listed for the same reason the
// server's keys are, and with the same consequence either way round.
const LIB_KEYS = [
  'count.pages', 'count.sections',
  'note.compiled', 'note.costed', 'note.findings', 'note.insurer',
  'note.ledger', 'note.lines', 'note.matched', 'note.model_kept',
  'note.opened', 'note.page_ocr', 'note.page_text', 'note.page_vision',
  'note.pages_read', 'note.questions', 'note.reading', 'note.rules_found',
  'note.sections', 'note.shortlisted',
  'phase.against_policy', 'phase.build', 'phase.check', 'phase.cost',
  'phase.doc', 'phase.find', 'phase.lines', 'phase.pages', 'phase.rank',
  'phase.sort', 'phase.terms',
]

function walk(dir) {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name)
    return statSync(path).isDirectory() ? walk(path) : [path]
  })
}

const used = new Set([...SERVER_KEYS, ...LIB_KEYS])
// Both extensions: a few strings are asked for from lib/ rather than from a
// component, and one of them sat in a .js file long enough to go missing from
// two languages without this noticing. The tables themselves are read further
// down and are not call sites.
const sources = walk(SRC).filter(
  (p) => (p.endsWith('.jsx') || p.endsWith('.js')) && !p.includes('/lib/lang/')
)
for (const path of sources) {
  const text = readFileSync(path, 'utf8')
  for (const [, key] of text.matchAll(/\bt\(\s*'([a-z][a-z0-9._]*)'/g)) {
    // Other calls end in "t(" too, and only a dotted key is one of ours.
    if (key.includes('.') || key === 'disclaimer') used.add(key)
  }
  for (const [, template] of text.matchAll(/\bt\(`([^`]+)`/g)) {
    const at = template.indexOf('${')
    const stem = template.slice(0, at)
    // Anything after the expression counts too. `checklist.${id}` and
    // `checklist.${id}.why` are one family read two ways, and dropping the
    // tail would make the second look like the first and hide half the keys.
    const tail = template.slice(template.indexOf('}', at) + 1)
    const values = TEMPLATES[stem]
    if (!values) {
      console.error(`unknown key template ${template} in ${path}`)
      process.exit(1)
    }
    for (const value of values) used.add(stem + value + tail)
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
