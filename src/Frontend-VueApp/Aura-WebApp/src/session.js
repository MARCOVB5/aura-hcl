import { reactive } from 'vue'

// The logged-in caregiver. The token is kept in the browser (localStorage) so a page
// reload doesn't log out; the user is fetched again from the backend (/api/auth/me).
// "Mes soins" in the calendar are the care appointments this caregiver performs.

const TOKEN_KEY = 'aura.token'

// localStorage can be blocked (private browsing, strict settings): the app then
// still works, the user just logs in again after a reload
function readToken() {
  try {
    return localStorage.getItem(TOKEN_KEY)
  } catch {
    return null
  }
}

function writeToken(token) {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token)
    else localStorage.removeItem(TOKEN_KEY)
  } catch {
    // nothing to do: see readToken
  }
}

export const session = reactive({
  token: readToken(),
  // { id, username, practitioner_id, name_given, name_family, profession }
  user: null,
  expired: false, // logged out by the backend (token too old), not by the user
})

export function startSession(token, user) {
  session.token = token
  session.user = user
  session.expired = false
  writeToken(token)
}

export function endSession({ expired = false } = {}) {
  session.token = null
  session.user = null
  session.expired = expired
  writeToken(null)
}

export function isCurrentUser(practitioner) {
  return Boolean(session.user && practitioner && practitioner.id === session.user.practitioner_id)
}
