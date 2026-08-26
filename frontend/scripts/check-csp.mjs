// The policy the built page ships with still permits what the page does.
//
// This check exists because of one bug. Bills attached to a stay are held on
// the device and shown from a blob URL, and the policy allowed `data:` images
// and no frames at all. Nothing in development is subject to it, so every test
// passed, every screen worked, and the page that shipped refused to show a
// single bill: the thumbnails were blocked as images and the PDF viewer was
// blocked as a frame, which from the outside looked like unreadable files.
//
// A policy is tightened by somebody being careful, and it breaks a screen
// nobody thought to open afterwards. So each thing the page needs is written
// down here beside the reason it needs it, and each thing it must never be
// allowed is written down beside what it would cost.

import { readFileSync, existsSync } from 'node:fs'
import { directives, policyFor } from './csp.mjs'

const DIST = new URL('../dist/index.html', import.meta.url).pathname

// What the page cannot work without, and why. Checked as a source in a
// directive rather than a string match, so reordering or adding sources beside
// them changes nothing.
const NEEDED = [
  ['img-src', 'blob:', 'a bill attached to a charge is shown from the device'],
  ['img-src', "'self'", 'the logo and the icons'],
  ['frame-src', 'blob:', 'a PDF bill is shown in a frame of its own'],
  ['connect-src', "'self'", 'the API, when it is served from this origin'],
  ['script-src', "'self'", 'the bundle'],
  ['style-src', "'unsafe-inline'", 'React writes the few widths it computes'],
]

// What must never be permitted, and what allowing it would mean.
const FORBIDDEN = [
  ['script-src', "'unsafe-inline'", 'any injected string becomes a script'],
  ['script-src', "'unsafe-eval'", 'the bundle needs neither, so nothing should'],
  ['script-src', '*', 'a script from anywhere is a script from anywhere'],
  ['object-src', "'self'", 'plugins are not how anything here is displayed'],
  ['object-src', 'blob:', 'plugins are not how anything here is displayed'],
  ['default-src', '*', 'the fallback for everything not named'],
]

function sourcesOf(list, name) {
  const found = list.find((d) => d === name || d.startsWith(`${name} `))
  if (found === undefined) return null
  return found.slice(name.length).trim().split(/\s+/).filter(Boolean)
}

const problems = []

// Both shapes the policy is built in: served from the API's own origin, and
// pointed at an API somewhere else.
for (const apiBase of ['', 'https://api.example.org']) {
  const where = apiBase || 'same origin'
  const list = directives(apiBase)

  for (const [name, source, why] of NEEDED) {
    const sources = sourcesOf(list, name)
    if (sources === null) {
      problems.push(`${where}: no ${name} at all, and it needs ${source}: ${why}`)
    } else if (!sources.includes(source)) {
      problems.push(`${where}: ${name} does not allow ${source}: ${why}`)
    }
  }

  for (const [name, source, cost] of FORBIDDEN) {
    const sources = sourcesOf(list, name)
    if (sources?.includes(source)) {
      problems.push(`${where}: ${name} allows ${source}: ${cost}`)
    }
  }

  if (apiBase && !sourcesOf(list, 'connect-src')?.includes(apiBase)) {
    problems.push(`${where}: connect-src does not name the API it was built for`)
  }
}

// And that the page actually carries it, when there is a page to look at. The
// policy is injected by a build-only plugin, so it can be correct here and
// absent from the file that ships.
if (existsSync(DIST)) {
  const html = readFileSync(DIST, 'utf8')
  const tag = html.match(
    /<meta http-equiv="Content-Security-Policy" content="([^"]+)"/
  )
  if (!tag) {
    problems.push('dist/index.html carries no policy at all')
  } else if (tag[1] !== policyFor(process.env.VITE_API_BASE ?? '')) {
    // Only worth saying when the build was for this same API base; a dist
    // built against another one is not wrong, just not this.
    if (!process.env.VITE_API_BASE) {
      problems.push('dist/index.html carries a policy this module did not write')
    }
  }
}

if (problems.length) {
  for (const problem of problems) console.error(problem)
  process.exit(1)
}
console.log(
  `csp: ${NEEDED.length} sources the page needs, ` +
    `${FORBIDDEN.length} it must not have`
)
