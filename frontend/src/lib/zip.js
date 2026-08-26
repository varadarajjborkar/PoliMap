// One archive, written in the browser, so a stay can be handed over whole.
//
// The stay document is a page the server renders. The bills behind it never
// leave this device, so nothing but this device can put the two in one file,
// and a family at a claims counter needs one file rather than a page and a
// folder of photographs they have to find again.
//
// Entries are stored, not deflated. Everything going in is a PDF or a
// photograph, both already compressed, so deflating them would cost time on a
// phone and save nothing. Stored entries are a handful of headers and the
// bytes themselves, which is why this is a hundred lines rather than a
// dependency.

const LOCAL = 0x04034b50
const CENTRAL = 0x02014b50
const END = 0x06054b50

// UTF-8 names, so a receipt called "बिल.pdf" survives being archived.
const UTF8_NAME = 0x0800

let table = null

function crcTable() {
  if (table) return table
  table = new Uint32Array(256)
  for (let i = 0; i < 256; i += 1) {
    let value = i
    for (let bit = 0; bit < 8; bit += 1) {
      value = value & 1 ? 0xedb88320 ^ (value >>> 1) : value >>> 1
    }
    table[i] = value >>> 0
  }
  return table
}

function crc32(bytes) {
  const lookup = crcTable()
  let crc = 0xffffffff
  for (let i = 0; i < bytes.length; i += 1) {
    crc = lookup[(crc ^ bytes[i]) & 0xff] ^ (crc >>> 8)
  }
  return (crc ^ 0xffffffff) >>> 0
}

// Zip keeps time the way MS-DOS did: a packed local date, two-second
// resolution, no zone. Nothing reads it but a file listing.
function dosStamp(when) {
  const year = Math.max(1980, when.getFullYear())
  return {
    time:
      (when.getHours() << 11) |
      (when.getMinutes() << 5) |
      Math.floor(when.getSeconds() / 2),
    date: ((year - 1980) << 9) | ((when.getMonth() + 1) << 5) | when.getDate(),
  }
}

class Writer {
  constructor(size) {
    this.bytes = new Uint8Array(size)
    this.view = new DataView(this.bytes.buffer)
    this.at = 0
  }

  u16(value) {
    this.view.setUint16(this.at, value, true)
    this.at += 2
  }

  u32(value) {
    this.view.setUint32(this.at, value >>> 0, true)
    this.at += 4
  }

  raw(bytes) {
    this.bytes.set(bytes, this.at)
    this.at += bytes.length
  }
}

/**
 * Build a zip from `[{ name, data }]`, where data is a Uint8Array.
 * Returns a Blob. Names may contain `/` to make folders.
 */
export function zip(entries, when = new Date()) {
  const stamp = dosStamp(when)
  const encoder = new TextEncoder()

  const prepared = entries.map((entry) => {
    const name = encoder.encode(entry.name)
    return { name, data: entry.data, crc: crc32(entry.data) }
  })

  const localSize = prepared.reduce(
    (total, e) => total + 30 + e.name.length + e.data.length, 0
  )
  const centralSize = prepared.reduce(
    (total, e) => total + 46 + e.name.length, 0
  )

  const out = new Writer(localSize + centralSize + 22)
  const offsets = []

  for (const entry of prepared) {
    offsets.push(out.at)
    out.u32(LOCAL)
    out.u16(20)                 // version needed
    out.u16(UTF8_NAME)
    out.u16(0)                  // stored
    out.u16(stamp.time)
    out.u16(stamp.date)
    out.u32(entry.crc)
    out.u32(entry.data.length)  // compressed
    out.u32(entry.data.length)  // uncompressed
    out.u16(entry.name.length)
    out.u16(0)                  // no extra field
    out.raw(entry.name)
    out.raw(entry.data)
  }

  const centralAt = out.at
  prepared.forEach((entry, index) => {
    out.u32(CENTRAL)
    out.u16(20)                 // version made by
    out.u16(20)                 // version needed
    out.u16(UTF8_NAME)
    out.u16(0)                  // stored
    out.u16(stamp.time)
    out.u16(stamp.date)
    out.u32(entry.crc)
    out.u32(entry.data.length)
    out.u32(entry.data.length)
    out.u16(entry.name.length)
    out.u16(0)                  // extra
    out.u16(0)                  // comment
    out.u16(0)                  // disk
    out.u16(0)                  // internal attributes
    out.u32(0)                  // external attributes
    out.u32(offsets[index])
    out.raw(entry.name)
  })

  // Measured before the trailer is written, not from inside it. Taken after,
  // it counts the twelve bytes of trailer already laid down as part of the
  // directory, and every reader then says the archive is twelve bytes short.
  const centralSpan = out.at - centralAt

  out.u32(END)
  out.u16(0)                    // this disk
  out.u16(0)                    // disk holding the directory
  out.u16(prepared.length)
  out.u16(prepared.length)
  out.u32(centralSpan)
  out.u32(centralAt)
  out.u16(0)                    // no comment

  return new Blob([out.bytes], { type: 'application/zip' })
}

// A name safe on every filesystem somebody might unpack this on, and readable
// once it is there.
export function safeName(text, fallback = 'file') {
  const cleaned = String(text)
    .normalize('NFKD')
    // An apostrophe is dropped rather than turned into a separator, so a
    // surgeon's fee files as `Surgeons-fee` and not as `Surgeon-s-fee`.
    .replace(/['\u2019]/g, '')
    .replace(/[^\w.\- ]+/g, ' ')
    .trim()
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .slice(0, 60)
    .replace(/^[.-]+|[.-]+$/g, '')
  return cleaned || fallback
}

// Hand a blob to the browser as a saved file. Revoked on the next turn of the
// loop: the download has been started by then, and holding the URL open pins
// the whole archive in memory.
export function save(blob, filename) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  setTimeout(() => URL.revokeObjectURL(url), 0)
}