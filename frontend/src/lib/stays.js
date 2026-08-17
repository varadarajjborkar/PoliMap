// Saved admissions, kept on this device.
//
// Two things live here per stay: a short index entry, which is what the home
// screen lists and is cheap enough to read on every render, and the snapshot,
// which is the server's own session state and is large. They are separate keys
// so that listing ten stays does not deserialise ten policies.
//
// A name is an identity, not an account. Nothing is checked against a server,
// so the same name on two devices gives two unrelated sets of stays, and two
// names on one device cannot see each other's. That is the whole model: it
// makes "my stay is still here tomorrow" true without asking a family in a
// hospital to invent a password.

import { keysWithPrefix, readJSON, remove, writeJSON } from './storage'

const USER_KEY = 'polimap.user'
const PREFIX = 'polimap.stay'

// Old snapshots are worth less than the newest ones and the quota is finite.
// Twenty admissions is far beyond what anyone will accumulate in earnest.
const MAX_STAYS = 20

const slug = (name) => encodeURIComponent(name.trim().toLowerCase())
const indexKey = (user) => `${PREFIX}.${slug(user)}.index`
const snapshotKey = (user, id) => `${PREFIX}.${slug(user)}.snap.${id}`

export function readUser() {
  try {
    return window.localStorage.getItem(USER_KEY) || ''
  } catch {
    return ''
  }
}

export function writeUser(name) {
  try {
    window.localStorage.setItem(USER_KEY, name.trim())
  } catch {
    // The name still holds for this tab, which is enough to keep working.
  }
}

export function clearUser() {
  remove(USER_KEY)
}

// --- the index -------------------------------------------------------------

export function listStays(user) {
  if (!user) return []
  const stays = readJSON(indexKey(user), [])
  return Array.isArray(stays)
    ? [...stays].sort((a, b) => (b.updatedAt ?? 0) - (a.updatedAt ?? 0))
    : []
}

function writeIndex(user, stays) {
  writeJSON(indexKey(user), stays.slice(0, MAX_STAYS))
  // Snapshots for stays that fell off the end are now unreachable, and they
  // are the bulky half. Dropping them here is what keeps the quota honest.
  const live = new Set(stays.slice(0, MAX_STAYS).map((s) => s.id))
  for (const key of keysWithPrefix(`${PREFIX}.${slug(user)}.snap.`)) {
    if (!live.has(key.split('.').pop())) remove(key)
  }
}

export function newStayId() {
  return Math.random().toString(36).slice(2, 10)
}

export function saveStay(user, stay) {
  if (!user || !stay?.id) return
  const rest = listStays(user).filter((s) => s.id !== stay.id)
  writeIndex(user, [{ ...stay, updatedAt: Date.now() }, ...rest])
}

export function getStay(user, id) {
  return listStays(user).find((s) => s.id === id) ?? null
}

export function deleteStay(user, id) {
  if (!user || !id) return
  remove(snapshotKey(user, id))
  writeIndex(user, listStays(user).filter((s) => s.id !== id))
}

// Everything belonging to one name. Another name on the same device keeps its
// own stays, which is what makes a shared phone usable at all.
export function deleteAllStays(user) {
  if (!user) return
  for (const key of keysWithPrefix(`${PREFIX}.${slug(user)}.`)) remove(key)
}

// --- snapshots -------------------------------------------------------------

export function readSnapshot(user, id) {
  return readJSON(snapshotKey(user, id), null)
}

export function writeSnapshot(user, id, snapshot) {
  if (!user || !id || !snapshot) return
  // A full store is not worth an error on screen: the stay stays usable in
  // this tab, and the index entry still lists it.
  writeJSON(snapshotKey(user, id), snapshot)
}

// A stay needs a name a person recognises a day later. The hospital is the
// thing they remember; the treatment is the fallback; the date is the floor.
export function describeStay(stay) {
  if (stay.hospital) return stay.hospital
  if (stay.procedure) return stay.procedure
  return `Stay of ${new Date(stay.createdAt ?? Date.now()).toLocaleDateString()}`
}
