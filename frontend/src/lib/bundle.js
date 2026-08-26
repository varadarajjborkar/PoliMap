// The whole stay in one file: the document the server renders, and every bill
// behind it from this device.
//
// The two halves live in different places and only the browser holds both. The
// server has the policy, the estimate and the ledger and can print them; it has
// never seen the photographs, because those were never sent. So the archive is
// assembled here, and the numbering is what ties the halves together: row 3 of
// the ledger in the document is the file that starts `03-` in the folder.
//
// English throughout, like the document itself. It is written to be handed to
// an insurance desk alongside a claim form, and those are filled in English.

import { safeName, zip } from './zip'
import { extensionOf } from './receipts'

const pad = (n) => String(n).padStart(2, '0')

function stamp(when = new Date()) {
  return `${when.getFullYear()}-${pad(when.getMonth() + 1)}-${pad(when.getDate())}`
}

// The same row number the printed ledger uses, so a file can be traced back to
// the line it documents without opening it.
function rowOf(costs, entryId) {
  const at = costs.findIndex((cost) => cost.id === entryId)
  return at < 0 ? 0 : at + 1
}

function contents({ hospital, costs, filed, when }) {
  const lines = [
    'WHAT IS IN THIS FOLDER',
    '',
    hospital ? `Stay at ${hospital}` : 'Hospital stay',
    `Packed ${when.toDateString()}`,
    '',
    'stay.pdf',
    '    Your cover, what was estimated, what has been billed, and what is',
    '    still to do. Every figure on it is traced back to the policy.',
    '',
  ]

  if (filed.length === 0) {
    lines.push('No bills or receipts were attached to this stay.')
  } else {
    lines.push(`bills/  (${filed.length})`)
    lines.push(
      '    Each file is named for the row it belongs to in the ledger on',
      '    page 1 of stay.pdf, so row 03 there is the file starting 03- here.',
      ''
    )
    for (const paper of filed) {
      const row = rowOf(costs, paper.entry)
      const cost = costs.find((c) => c.id === paper.entry)
      lines.push(`    ${paper.path}`)
      lines.push(
        `        row ${pad(row)} · ${paper.headLabel}` +
          (cost ? ` · ${cost.amount_display}` : '') +
          (cost?.description ? ` · ${cost.description}` : '')
      )
    }
  }

  lines.push(
    '',
    'These figures are estimates for guidance, not a quote and not an',
    'approval. Confirm every amount with your insurer and the hospital',
    'insurance desk.',
    ''
  )
  return lines.join('\n')
}

/**
 * Pack a stay. Returns `{ blob, filename }`, or throws if the document itself
 * cannot be fetched, because an archive without it is not worth handing over.
 */
export async function packStay({ reportUrl, papers, costs = [], hospital = '' }) {
  const response = await fetch(reportUrl)
  if (!response.ok) {
    throw new Error(`The stay document could not be prepared (${response.status}).`)
  }
  const pdf = new Uint8Array(await response.arrayBuffer())
  const when = new Date()

  // Named before anything is written, so the folder listing and the index
  // agree, and so two receipts with the same filename cannot collide.
  const filed = papers.map((paper) => {
    const row = pad(rowOf(costs, paper.entry))
    const extension = extensionOf(paper.name) || 'bin'
    const base = safeName(paper.name.replace(/\.[^.]*$/, ''), 'bill')
    return {
      ...paper,
      path: `bills/${row}-${safeName(paper.headLabel, 'charge')}-${base}.${extension}`,
    }
  })

  const encoder = new TextEncoder()
  const entries = [
    { name: 'stay.pdf', data: pdf },
    { name: 'contents.txt', data: encoder.encode(contents({ hospital, costs, filed, when })) },
  ]
  for (const paper of filed) {
    entries.push({ name: paper.path, data: new Uint8Array(await paper.blob.arrayBuffer()) })
  }

  return {
    blob: zip(entries, when),
    filename: `${safeName(hospital || 'hospital-stay', 'hospital-stay')}-${stamp(when)}.zip`,
  }
}