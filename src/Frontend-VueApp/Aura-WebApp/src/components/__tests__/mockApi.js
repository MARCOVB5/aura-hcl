import { vi } from 'vitest'

// Fakes the backend: each route is [method, path regex, status, body].
// body can be a function of the request's parsed JSON body. Unmatched requests get a 404.
export function mockApi(routes) {
  globalThis.fetch = vi.fn(async (url, options = {}) => {
    const method = options.method ?? 'GET'
    const { pathname, search } = new URL(url)
    const route = routes.find(([m, path]) => m === method && path.test(pathname + search))
    const [, , status, body] = route ?? [method, null, 404, { detail: 'Not mocked' }]
    const sent = options.body ? JSON.parse(options.body) : undefined
    return {
      ok: status < 400,
      status,
      json: async () => (typeof body === 'function' ? body(sent) : body),
    }
  })
  return globalThis.fetch
}

// the JSON bodies sent with this method to paths matching the regex
export function sentTo(method, path) {
  return fetch.mock.calls
    .filter(([url, options = {}]) => (options.method ?? 'GET') === method && path.test(url))
    .map(([, options]) => JSON.parse(options.body))
}

// sample data in the backend's format
export const LOCATION = 'Réanimation · Chambre 12 · Lit A'

export const CARE_TYPES = [
  { id: 1, code: 'PRISE_SANG', name: 'Prise de sang' },
  { id: 2, code: 'REEVAL_RESP', name: 'Réévaluation respiratoire' },
]

const staff = (id, given, family, profession) => ({
  id,
  profession,
  person: { id: 100 + id, name_given: given, name_family: family, birth_date: null },
})
export const PRACTITIONERS = [
  staff(1, 'Bruno', 'Azerty', 'Médecin'),
  staff(2, 'Alice', 'Merveille', 'Infirmière'),
  staff(3, 'Simon', 'Armand', 'Médecin'),
]

export const LEA = {
  id: 3,
  ipp: 'DEMO-003',
  identification_status: 'PROVISIONAL',
  person: { name_family: 'Exemple', name_given: 'Léa', birth_date: '1990-11-06', gender: 'female' },
  allergies: [{ id: 1, name: 'Pénicilline' }],
  contact: null,
  personal_info: null,
}

export const LEA_2 = {
  ...LEA,
  id: 7,
  ipp: 'DEMO-007',
  person: { ...LEA.person, birth_date: '1984-05-21' },
  allergies: [],
}

export const NORA = {
  id: 5,
  ipp: null,
  identification_status: 'PROVISIONAL',
  person: { name_family: 'Delmas', name_given: 'Nora', birth_date: null, gender: 'unknown' },
  allergies: [],
  contact: null,
  personal_info: null,
}

export function stay(
  id,
  patient,
  admission,
  { expected = null, actual = null, location = LOCATION } = {},
) {
  return {
    id,
    stay_number: `SEJ-${id}`,
    patient_id: patient.id,
    patient,
    status: 'in-progress',
    encounter_type_code: 'INPATIENT',
    admission_date: admission,
    expected_discharge_date: expected,
    actual_discharge_date: actual,
    reason: null,
    location,
  }
}

export const hospitalizationOf = (encounter) => ({
  encounter_id: encounter.id,
  encounter,
  admission_status: 'IN_PROGRESS',
  assessment_completed_at: null,
})

export function appointment(id, patient, start, overrides = {}) {
  return {
    id,
    patient,
    encounter: stay(10 + patient.id, patient, '2026-10-19T08:00:00'),
    activity_definition: CARE_TYPES[0],
    prescribed_on: start.slice(0, 10),
    time_constraint: 'STRONG',
    scheduled_start: start,
    scheduled_end: null,
    performers: [PRACTITIONERS[0]],
    validated_by: null,
    note: null,
    status: 'PLANNED',
    ...overrides,
  }
}
