// Tickets raised from the help desk, kept on this device.
//
// The same place a stay is kept and for the same reason: there is nothing
// behind this app to keep them for. The server mints the reference and forgets
// it, the browser holds it, and the tracker says plainly that nothing is
// working on it. A status bar that crept along on its own would be the one
// dishonest thing in the app.

import { keysWithPrefix, readJSON, remove, writeJSON } from './storage'

const PREFIX = 'polimap.ticket'
const MAX_TICKETS = 30

const slug = (name) => encodeURIComponent(name.trim().toLowerCase())
const key = (user) => `${PREFIX}.${slug(user)}`

export function listTickets(user) {
  if (!user) return []
  const held = readJSON(key(user), [])
  return Array.isArray(held) ? held : []
}

export function saveTicket(user, ticket) {
  if (!user || !ticket?.ticket_id) return
  const rest = listTickets(user).filter((t) => t.ticket_id !== ticket.ticket_id)
  writeJSON(key(user), [ticket, ...rest].slice(0, MAX_TICKETS))
}

export function deleteTicket(user, ticketId) {
  if (!user) return
  writeJSON(user && key(user), listTickets(user).filter((t) => t.ticket_id !== ticketId))
}

// Everything belonging to one name, cleared alongside their stays.
export function deleteAllTickets(user) {
  if (!user) return
  for (const k of keysWithPrefix(key(user))) remove(k)
}