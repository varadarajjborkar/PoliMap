// Interface language.
//
// Scoped deliberately. What gets translated here is the interface's own words:
// navigation, buttons, headings, the fixed guidance this app wrote itself.
// What never gets translated is anything read out of somebody's policy. A
// clause paraphrased into another language and shown as what the document says
// is a claim about their cover that nobody has checked, and this whole system
// is built on not doing that.
//
// Call sites pass the English alongside the key:
//
//     t('journey.download', 'Download this stay')
//
// so the source stays readable, a missing translation renders English rather
// than a key, and there is no separate English file to drift from the JSX.
//
// Amounts are left alone. Rupees group the same way in every one of these
// languages, and a family reading a figure off this screen has to be able to
// point at the same figure on a bill.

export const LANGUAGES = [
  { code: 'en', endonym: 'English' },
  { code: 'hi', endonym: 'हिन्दी' },
  { code: 'kn', endonym: 'ಕನ್ನಡ' },
  { code: 'mr', endonym: 'मराठी' },
  { code: 'te', endonym: 'తెలుగు' },
]

export const LANGUAGE_CODES = LANGUAGES.map((language) => language.code)

// One language is downloaded, not five.
//
// Held as plain imports, the four tables were the larger part of what every
// visitor fetched, and four fifths of it was a script they will never read.
// Written as literal imports over a known set, the bundler gives each its own
// file and the browser asks for the one that was chosen.
//
// It has to be a literal per language rather than one import built from a
// variable, because the bundler can only emit what it can see named here.
const TABLES = {
  hi: () => import('./lang/hi.js'),
  kn: () => import('./lang/kn.js'),
  mr: () => import('./lang/mr.js'),
  te: () => import('./lang/te.js'),
}

// English is the source, so it has no table: a key with no translation renders
// the English the call site passed, which is also what a partially translated
// language does. Nothing ever renders a key.
export function isTranslated(code) {
  return Object.hasOwn(TABLES, code)
}

// The promise is what is kept, not the table, so asking twice before the first
// answer arrives is still one request. Switching back to a language already
// read is free.
const pending = new Map()

export function loadStrings(code) {
  if (!isTranslated(code)) return Promise.resolve(null)
  if (!pending.has(code)) {
    pending.set(code, TABLES[code]().then((module) => module.default))
  }
  return pending.get(code)
}

// Takes the table rather than the code, because by the time anything renders
// the table has already been fetched and there is nothing left to look up.
export function translator(table) {
  return (key, english, values) => {
    const text = (table && table[key]) || english
    if (!values) return text
    // Placeholders rather than concatenation, because the order a sentence
    // puts its figure and its noun in is not the same in every one of these
    // languages, and a translator has to be able to move them.
    return text.replace(/\{(\w+)\}/g, (whole, name) =>
      Object.hasOwn(values, name) ? String(values[name]) : whole
    )
  }
}
