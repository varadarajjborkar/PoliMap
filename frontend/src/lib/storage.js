// Local storage, treated as a thing that can fail.
//
// Private browsing refuses writes outright, and every browser has a quota that
// a few saved admissions can reach. Neither is a reason to lose the screen the
// user is on, so every call here returns rather than throws and the caller is
// free to carry on with what it already has in memory.

export function readJSON(key, fallback) {
  try {
    const raw = window.localStorage.getItem(key)
    return raw ? JSON.parse(raw) : fallback
  } catch {
    return fallback
  }
}

export function writeJSON(key, value) {
  try {
    window.localStorage.setItem(key, JSON.stringify(value))
    return true
  } catch {
    return false
  }
}

export function remove(key) {
  try {
    window.localStorage.removeItem(key)
  } catch {
    // Nothing to do. The key is unreachable either way.
  }
}

// Every key belonging to one user, so signing out or starting over can clear
// exactly that person's data and leave anyone else on the device untouched.
export function keysWithPrefix(prefix) {
  const found = []
  try {
    for (let i = 0; i < window.localStorage.length; i += 1) {
      const key = window.localStorage.key(i)
      if (key?.startsWith(prefix)) found.push(key)
    }
  } catch {
    // An unreadable store has nothing to clear.
  }
  return found
}
