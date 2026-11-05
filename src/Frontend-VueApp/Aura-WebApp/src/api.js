import { endSession, session } from './session.js'

// Calls to the FastAPI backend (src/backend). Set VITE_API_URL in .env to point elsewhere.
export const API_URL = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000'

export class ApiError extends Error {
  constructor(message, status = 0, detail = null) {
    super(message)
    this.status = status // HTTP status, 0 when the server could not be reached
    this.detail = detail // the backend's own message, untranslated
  }
}

// messages of src/backend/src/app/services, shown in French in the UI
const BACKEND_MESSAGES = {
  'Invalid credentials or session': 'Identifiant ou mot de passe incorrect.',
  'IPP already registered': 'Cet IPP est déjà attribué à un autre patient.',
  'Stay number already registered': 'Ce numéro de séjour existe déjà.',
  'Patient not found': 'Patient introuvable.',
  'Hospitalization not found': 'Séjour introuvable.',
  'No current stay': 'Ce patient n’a aucun séjour en cours.',
  'Stay has care appointments': 'Ce séjour a des soins planifiés : il ne peut pas être supprimé.',
  'Discharge date before admission date': 'La date de fin doit être après la date de début.',
  'Care type not found': 'Type de soin introuvable.',
  'Practitioner not found': 'Soignant introuvable.',
  'Appointment not found': 'Soin introuvable.',
  'Care outside its stay': 'Le soin doit avoir lieu pendant le séjour.',
  'Stay has care outside its dates': 'Des soins de ce séjour sont en dehors de ces dates.',
}

// The backend sends {"detail": "..."} for 4xx errors and {"detail": [{msg, loc}, ...]} for 422
function errorMessage(status, body) {
  const detail = body?.detail
  if (typeof detail === 'string') return BACKEND_MESSAGES[detail] ?? detail
  if (Array.isArray(detail)) {
    return detail.map((d) => `${d.loc?.slice(1).join('.') || 'requête'} : ${d.msg}`).join(' — ')
  }
  return `Erreur du serveur (${status})`
}

async function request(path, options = {}) {
  // every route but the login needs the token of the logged-in user
  const auth = session.token ? { Authorization: `Bearer ${session.token}` } : {}
  let response
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...options,
      headers: { 'Content-Type': 'application/json', ...auth, ...options.headers },
    })
  } catch {
    throw new ApiError(`Impossible de joindre le serveur (${API_URL}).`)
  }
  const body = await response.json().catch(() => null) // 204 has no body
  if (!response.ok) {
    // the token has expired (after 8 hours) or is no longer valid: back to the login page
    if (response.status === 401 && session.token) endSession({ expired: true })
    throw new ApiError(errorMessage(response.status, body), response.status, body?.detail)
  }
  return body
}

const send = (method, path, data) => request(path, { method, body: JSON.stringify(data) })

// authentication

// gives { access_token, token_type, expires_in }; 401 when the username or password is wrong
export function login(username, password) {
  return send('POST', '/api/auth/login', { username, password })
}

// { id, username, practitioner_id, name_given, name_family, profession }.
// token: the one just received from login, before the session starts
export function getCurrentUser(token = session.token) {
  return request('/api/auth/me', { headers: { Authorization: `Bearer ${token}` } })
}

// patients

export function listPatients(limit = 200) {
  return request(`/api/patients?limit=${limit}`)
}

export function getPatient(id) {
  return request(`/api/patients/${id}`)
}

export function createPatient(patient) {
  return send('POST', '/api/patients', patient)
}

// replaces the whole record: allergies missing from the list are removed
export function updatePatient(id, patient) {
  return send('PUT', `/api/patients/${id}`, patient)
}

// stays

// stays with their patient, ordered by encounter id
export function listHospitalizations(limit = 200) {
  return request(`/api/hospitalizations?limit=${limit}`)
}

export function listPatientHospitalizations(patientId) {
  return request(`/api/patients/${patientId}/hospitalizations`)
}

// the stay in progress, or null when the patient has none
export async function getCurrentHospitalization(patientId) {
  try {
    return await request(`/api/patients/${patientId}/current-hospitalization`)
  } catch (e) {
    if (e.detail === 'No current stay') return null
    throw e
  }
}

// creates the stay (encounter) and its hospitalization for an existing patient
export function createHospitalization(encounter) {
  return send('POST', '/api/hospitalizations', { encounter })
}

// only the fields that are sent are changed
export function updateHospitalization(encounterId, changes) {
  return send('PATCH', `/api/hospitalizations/${encounterId}`, changes)
}

export function deleteHospitalization(encounterId) {
  return request(`/api/hospitalizations/${encounterId}`, { method: 'DELETE' })
}

// reference lists

export const listPractitioners = () => request('/api/practitioners')

// care appointments

// start / end: "YYYY-MM-DD", both included
export function listAppointments({ start, end, patientId } = {}) {
  const params = new URLSearchParams()
  if (start) params.set('start', start)
  if (end) params.set('end', end)
  if (patientId != null) params.set('patient_id', patientId)
  return request(`/api/appointments?${params}`)
}

// the patient's current stay is attached by the backend
export function createAppointment(appointment) {
  return send('POST', '/api/appointments', appointment)
}

export function updateAppointment(id, appointment) {
  return send('PUT', `/api/appointments/${id}`, appointment)
}
