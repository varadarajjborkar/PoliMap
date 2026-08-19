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

// A sentence the server composed, read in the reader's language.
//
// The server sends three things for each of these: the key that says which
// sentence it is, the English as it composed it, and the values it wrote in.
// Everything here does is put them in the order `t` takes them.
//
// The keys are listed in scripts/check-strings.mjs rather than found in the
// source, because they are written in Python. That list is what makes a
// sentence the server can send but no language can say fail the build.
export function said(t, phrase, prefix = '') {
  if (!phrase) return ''
  return t(prefix + phrase.key, phrase.text, readable(t, phrase.values))
}

// The values inside a sentence, said in the reader's language.
//
// A sentence composed on the server arrives with its figures beside it, and
// most of them need nothing: a rupee amount reads the same in every one of
// these languages, and a hospital's name is its name. Three kinds do need
// something, and each announces itself by the shape of its own name:
//
//   period_unit   a span, as a unit and its numbers rather than as "24 months"
//   x_iso         a date, in the only form another language can write out
//   x_key         a name this app holds in five languages, e.g. a room category
//
// All three exist for the same reason. The sentence can be looked up whole,
// but a value already written in English cannot: by the time it arrives it has
// closed over the English word inside it, and no table can reach in there.
export function readable(t, values) {
  if (!values) return values
  let out = values

  const change = (name, text) => {
    if (out === values) out = { ...values }
    out[name] = text
  }

  if (values.period_unit) {
    change('period', t(`dur.${values.period_unit}`, values.period, {
      n: values.period_n, d: values.period_d,
    }))
  }

  for (const [name, value] of Object.entries(values)) {
    if (name.endsWith('_iso')) {
      const under = name.slice(0, -4)
      const written = date(value, {
        // Whether the year belongs on it is the server's decision, not this
        // one: a deadline three days out is a day and a month, a waiting period
        // ending in 2028 is not. It said which by writing one.
        year: /\d{4}/.test(String(values[under] ?? '')) ? 'numeric' : undefined,
      })
      if (written) change(under, written)
    } else if (name.endsWith('_key') && value) {
      const under = name.slice(0, -4)
      if (under in values) change(under, t(value, values[under]))
    }
  }

  return out
}

// A room or ICU cap, said in the reader's language.
//
// "₹5,000 per day · up to Twin sharing" is two figures and a room name inside a
// sentence, and all three parts move: the sentence is looked up under the key
// the server chose for its shape, and the room name under the key it sent
// beside it.
export function capped(t, limit) {
  if (!limit) return ''
  return t(`roomlimit.${limit.description_key}`, limit.description,
           readable(t, limit.description_values))
}

// A date, written the way the reader's language writes dates. The language
// comes off the document rather than being threaded through every call: the
// settings hook sets `lang` on the root element for screen readers and for the
// browser's own font choice, and this is the same question.
export function date(value, options = {}) {
  const at = new Date(value)
  if (Number.isNaN(at.getTime())) return ''
  return at.toLocaleDateString(`${document.documentElement.lang || 'en'}-IN`, {
    day: 'numeric', month: 'long', ...options,
  })
}

// The same, with the time of day on it: when a charge was entered, when a
// stage was moved.
export function moment(value) {
  const at = new Date(value)
  if (Number.isNaN(at.getTime())) return ''
  return at.toLocaleString(`${document.documentElement.lang || 'en'}-IN`, {
    day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit',
  })
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
