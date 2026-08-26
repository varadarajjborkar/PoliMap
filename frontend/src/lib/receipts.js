// The bills and receipts themselves, kept on the device that took them.
//
// There is no cloud here. A photograph of a pharmacy bill is somebody's
// hospital paperwork, and the only place it goes is the browser it was taken
// in, in an IndexedDB store keyed by the name that added it and the stay it
// belongs to. Nothing is sent anywhere: the server is told the file's name so
// the ledger can say a charge has paper behind it, and never the file.
//
// Keyed on the stay id rather than the session id on purpose. Sessions expire
// on the server and a restart mints a new id for the same admission, so a
// receipt filed under one would go missing on the first reload. The stay id is
// this device's own and outlives all of that.
//
// Everything here answers rather than throws. Private browsing refuses to open
// a database at all, and a stay that cannot keep its paperwork is still a stay
// worth using.

const DB_NAME = 'polimap.files'
const STORE = 'receipts'
const VERSION = 1

// What a file may be, decided by its name and not by what the file claims
// about itself.
//
// The type recorded here is the type the preview will be handed, so an HTML
// page renamed to .png is opened as an image, fails to decode, and shows the
// "cannot be shown" panel. It is the client-side half of the same reasoning
// that makes the API serve uploads with sniffing turned off: a file somebody
// else supplied must never be rendered as a document on this origin.
const TYPES = {
  pdf: 'application/pdf',
  jpg: 'image/jpeg',
  jpeg: 'image/jpeg',
  png: 'image/png',
  webp: 'image/webp',
  heic: 'image/heic',
  tif: 'image/tiff',
  tiff: 'image/tiff',
}

export const ACCEPT = Object.keys(TYPES).map((ext) => `.${ext}`).join(',')

export function extensionOf(name = '') {
  const at = name.lastIndexOf('.')
  return at < 0 ? '' : name.slice(at + 1).toLowerCase()
}

// The type this file will be shown as, or '' for one we will not show at all.
export function typeOf(name = '') {
  return TYPES[extensionOf(name)] ?? ''
}

export const isImage = (type) => type.startsWith('image/')

// Whether this browser will show a PDF if one is put in front of it.
//
// Chrome, Firefox and desktop Safari all frame a blob and render it. Most
// phone browsers do not, and say so here rather than leaving a frame that
// paints nothing: a blank rectangle reads as a lost file, and the file is not
// lost, it is just not viewable in this browser.
export const canShowPdf = () => navigator.pdfViewerEnabled !== false

// --- making a photograph small enough to keep ------------------------------
//
// A phone photograph of a bill is twelve megapixels of a sheet of A4. Every
// figure on it is legible at a fraction of that, and the difference is several
// megabytes of a device's storage and of the archive somebody sends to an
// insurer. So a large photograph is redrawn smaller on the way in, once, and
// what is kept from then on is the smaller one.
//
// It is a redraw rather than a crop or a filter: nothing is cut off and no
// figure moves. Anything this browser cannot decode is kept exactly as it
// arrived, which is the case that matters most, because the file it cannot
// decode is usually the one from somebody's phone camera.
const MAX_EDGE = 2400
const SHRINK_OVER = 900 * 1024
const QUALITY = 0.82

function asJpegName(name) {
  return /\.jpe?g$/i.test(name) ? name : `${name.replace(/\.[^.]*$/, '')}.jpg`
}

export async function shrinkImage(file) {
  const type = typeOf(file?.name)
  if (!file || !isImage(type)) return file

  // Decoded before deciding, because the file's size does not tell you its
  // size. A photograph of a white page compresses to a few hundred kilobytes
  // and is still four thousand pixels across, and it is the pixels that cost a
  // phone something every time the shelf is opened.
  let bitmap
  try {
    bitmap = await createImageBitmap(file)
  } catch {
    return file
  }

  try {
    const edge = Math.max(bitmap.width, bitmap.height)
    if (edge <= MAX_EDGE && file.size <= SHRINK_OVER) return file

    const scale = Math.min(1, MAX_EDGE / edge)
    const width = Math.max(1, Math.round(bitmap.width * scale))
    const height = Math.max(1, Math.round(bitmap.height * scale))

    const canvas = document.createElement('canvas')
    canvas.width = width
    canvas.height = height
    const context = canvas.getContext('2d')
    if (!context) return file
    // JPEG has no transparency, and a transparent PNG drawn onto an empty
    // canvas comes out black. A bill is on white paper.
    context.fillStyle = '#ffffff'
    context.fillRect(0, 0, width, height)
    context.drawImage(bitmap, 0, 0, width, height)

    const smaller = await new Promise((resolve) => {
      canvas.toBlob(resolve, 'image/jpeg', QUALITY)
    })
    // Some files are already smaller than anything we would produce. Redrawing
    // one of those only loses a little of it for nothing.
    if (!smaller || smaller.size >= file.size) return file
    return new File([smaller], asJpegName(file.name), { type: 'image/jpeg' })
  } catch {
    return file
  } finally {
    bitmap.close?.()
  }
}

const slug = (name) => encodeURIComponent(String(name).trim().toLowerCase())
const owner = (user, stayId) => `${slug(user)}|${stayId}`
const idOf = (user, stayId, entryId) => `${owner(user, stayId)}|${entryId}`

let opening = null

function open() {
  if (opening) return opening
  opening = new Promise((resolve) => {
    let request
    try {
      request = window.indexedDB.open(DB_NAME, VERSION)
    } catch {
      resolve(null)
      return
    }
    request.onupgradeneeded = () => {
      const db = request.result
      if (!db.objectStoreNames.contains(STORE)) {
        const store = db.createObjectStore(STORE, { keyPath: 'id' })
        // Two ways in, and both are a wipe: everything for one stay when that
        // stay is deleted, everything for one name when that name leaves the
        // device.
        store.createIndex('owner', 'owner')
        store.createIndex('user', 'user')
      }
    }
    request.onsuccess = () => resolve(request.result)
    request.onerror = () => resolve(null)
    request.onblocked = () => resolve(null)
  })
  return opening
}

async function transact(mode, work) {
  const db = await open()
  if (!db) return null
  return new Promise((resolve) => {
    let tx
    try {
      tx = db.transaction(STORE, mode)
    } catch {
      resolve(null)
      return
    }
    let outcome = null
    tx.oncomplete = () => resolve(outcome)
    tx.onerror = () => resolve(null)
    tx.onabort = () => resolve(null)
    try {
      work(tx.objectStore(STORE), (value) => { outcome = value })
    } catch {
      resolve(null)
    }
  })
}

// --- writing ---------------------------------------------------------------

// Save the file behind one charge. `entry` is the charge's own id, so the two
// are the same record read from either end.
export async function keepReceipt(user, stayId, entryId, file, about = {}) {
  const type = typeOf(file?.name)
  if (!user || !stayId || !entryId || !file || !type) return false

  // Re-typed on the way in rather than trusting `file.type`, which is the
  // browser's guess from the same name and is empty often enough to matter.
  const blob = new Blob([file], { type })
  const saved = await transact('readwrite', (store, done) => {
    store.put({
      id: idOf(user, stayId, entryId),
      owner: owner(user, stayId),
      user: slug(user),
      entry: entryId,
      name: file.name,
      type,
      size: blob.size,
      at: Date.now(),
      head: about.head ?? '',
      headLabel: about.headLabel ?? '',
      amount: about.amount ?? '',
      blob,
    })
    done(true)
  })
  return saved === true
}

// --- reading ---------------------------------------------------------------

export async function listReceipts(user, stayId) {
  if (!user || !stayId) return []
  const found = await transact('readonly', (store, done) => {
    const request = store.index('owner').getAll(owner(user, stayId))
    request.onsuccess = () => done(request.result ?? [])
  })
  return (found ?? []).sort((a, b) => a.at - b.at)
}

export async function getReceipt(user, stayId, entryId) {
  if (!user || !stayId || !entryId) return null
  const found = await transact('readonly', (store, done) => {
    const request = store.get(idOf(user, stayId, entryId))
    request.onsuccess = () => done(request.result ?? null)
  })
  return found ?? null
}

// --- forgetting ------------------------------------------------------------

export async function dropReceipt(user, stayId, entryId) {
  if (!user || !stayId || !entryId) return
  await transact('readwrite', (store, done) => {
    store.delete(idOf(user, stayId, entryId))
    done(true)
  })
}

async function dropWhere(index, value) {
  await transact('readwrite', (store, done) => {
    const request = store.index(index).getAllKeys(value)
    request.onsuccess = () => {
      for (const key of request.result ?? []) store.delete(key)
      done(true)
    }
  })
}

// Everything filed against one stay, for when that stay is thrown away.
export async function dropStayReceipts(user, stayId) {
  if (!user || !stayId) return
  await dropWhere('owner', owner(user, stayId))
}

// Everything filed by one name, for when that name leaves the device. Another
// name's paperwork on the same device is untouched, which is the whole reason
// names exist here.
export async function dropUserReceipts(user) {
  if (!user) return
  await dropWhere('user', slug(user))
}