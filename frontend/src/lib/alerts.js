// Which alert belongs beside which part of the page.
//
// By kind, because that is what the server guarantees; by key where one kind
// says two different things. A room that costs more than the cover is a fact
// about the money, and a room billing at a rate the stay was not set up with
// is a fact about the line naming that rate, and both arrive as room_over_limit.
const ANCHOR = {
  room_rate_conflict: 'room',

  room_over_limit: 'money',
  room_downgrade_saving: 'money',
  non_payable_accumulating: 'money',
  cover_nearly_exhausted: 'cover',
  sublimit_nearly_used: 'cover',
  cover_healthy: 'cover',
  pre_auth_due: 'stage',
  documents_needed: 'stage',
}

// Anything unrecognised goes beside the stage marker, which is the one place
// on the screen that is about the stay as a whole rather than about a figure.
export function pinAlerts(alerts = []) {
  const pinned = { room: [], money: [], cover: [], stage: [] }
  for (const alert of alerts) {
    const where = ANCHOR[alert.key] ?? ANCHOR[alert.kind] ?? 'stage'
    pinned[where].push(alert)
  }
  return pinned
}