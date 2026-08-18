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
const TEMPLATES = {
  'journey.stage.${value}': [
    'pre_admission', 'admitted', 'discharge_planning', 'settled',
  ],
  'step.${id}': ['upload', 'policy', 'search'],
  'step.short.${id}': ['upload', 'policy', 'search'],
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
    const values = TEMPLATES[template]
    if (!values) {
      console.error(`unknown key template ${template} in ${path}`)
      process.exit(1)
    }
    const stem = template.slice(0, template.indexOf('${'))
    for (const value of values) used.add(stem + value)
  }
}

const source = readFileSync(join(SRC, 'lib/i18n.js'), 'utf8')
const problems = []
for (const code of ['hi', 'kn', 'mr', 'te']) {
  const block = source.match(new RegExp(`^const ${code} = \\{(.*?)^\\}`, 'ms'))
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
