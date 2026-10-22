// Calls to the FastAPI backend (src/backend). Set VITE_API_URL in .env to point elsewhere.
export const API_URL = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000'

export class ApiError extends Error {}

// messages of src/backend/src/app/services, shown in French in the UI
const BACKEND_MESSAGES = {
  'IPP already registered': 'Cet IPP est déjà attribué à un autre patient.',
  'Stay number already registered': 'Ce numéro de séjour existe déjà.',
  'Patient not found': 'Patient introuvable.',
}

// The backend sends {"detail": "..."} for 404/409 and {"detail": [{msg, loc}, ...]} for 422
function errorMessage(status, body) {
  const detail = body?.detail
  if (typeof detail === 'string') return BACKEND_MESSAGES[detail] ?? detail
  if (Array.isArray(detail)) {
    return detail.map((d) => `${d.loc?.slice(1).join('.') || 'requête'} : ${d.msg}`).join(' — ')
  }
  return `Erreur du serveur (${status})`
}

async function request(path, options = {}) {
  let response
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...options,
      headers: { 'Content-Type': 'application/json', ...options.headers },
    })
  } catch {
    throw new ApiError(`Impossible de joindre le serveur (${API_URL}).`)
  }
  const body = await response.json().catch(() => null)
  if (!response.ok) throw new ApiError(errorMessage(response.status, body))
  return body
}

export function listPatients(limit = 200) {
  return request(`/api/patients?limit=${limit}`)
}

export function createPatient(patient) {
  return request('/api/patients', { method: 'POST', body: JSON.stringify(patient) })
}
