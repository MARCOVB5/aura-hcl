// Display helpers shared by the views

export function patientName(patient) {
  const { name_given, name_family } = patient.person
  return [name_given, name_family].filter(Boolean).join(' ')
}

// "1990-11-06" -> "06/11/1990"
export function formatDate(isoDate) {
  if (!isoDate) return ''
  const [year, month, day] = isoDate.split('-')
  return `${day}/${month}/${year}`
}

// "2026-10-23T08:05:00" -> "23/10/2026 08:05"
export function formatDateTime(isoDateTime) {
  if (!isoDateTime) return ''
  const [date, time] = isoDateTime.split('T')
  return `${formatDate(date)} ${time.slice(0, 5)}`
}

// "DEMO-003 · Née le 06/11/1990"
export function patientDetails(patient) {
  const born = { female: 'Née', male: 'Né' }[patient.person.gender] ?? 'Né(e)'
  const birth = patient.person.birth_date && `${born} le ${formatDate(patient.person.birth_date)}`
  return [patient.ipp || 'IPP non renseigné', birth].filter(Boolean).join(' · ')
}

// lowercase without accents, for searches
export function normalize(text) {
  return (text ?? '')
    .normalize('NFD')
    .replace(/\p{Diacritic}/gu, '')
    .toLowerCase()
}

export const STAY_STATUSES = [
  { value: 'planned', label: 'Prévu' },
  { value: 'arrived', label: 'Arrivé' },
  { value: 'in-progress', label: 'En cours' },
]

// a stay being changed can also be ended or cancelled
export const STAY_EDIT_STATUSES = [
  ...STAY_STATUSES,
  { value: 'finished', label: 'Terminé' },
  { value: 'cancelled', label: 'Annulé' },
]

export const STAY_TYPES = [
  { value: 'INPATIENT', label: 'Hospitalisation' },
  { value: 'EMERGENCY', label: 'Urgence' },
  { value: 'OUTPATIENT', label: 'Ambulatoire' },
]

export const labelOf = (options, value) => options.find((o) => o.value === value)?.label ?? value

export const GENDERS = [
  { value: 'female', label: 'F' },
  { value: 'male', label: 'M' },
]

export const CARE_STATUSES = [
  { value: 'PLANNED', label: 'Planifié' },
  { value: 'DONE', label: 'Réalisé' },
  { value: 'CANCELLED', label: 'Annulé' },
]

export const TIME_CONSTRAINTS = [
  { value: 'WEAK', label: 'Faible · plage horaire' },
  { value: 'STRONG', label: 'Forte · heure précise' },
]

// "Bruno Azerty"
export function practitionerName(practitioner) {
  return practitioner ? patientName(practitioner) : ''
}

// "2026-10-23T08:05:00" -> "08:05"
export const formatTime = (isoDateTime) => (isoDateTime ? isoDateTime.slice(11, 16) : '')

// when a care is due: "23/10/2026 à 14:00" or "23/10/2026 de 13:00 à 15:00"
export function careWhen(appointment) {
  const day = formatDate(appointment.scheduled_start.slice(0, 10))
  const start = formatTime(appointment.scheduled_start)
  return appointment.time_constraint === 'WEAK'
    ? `${day} de ${start} à ${formatTime(appointment.scheduled_end)}`
    : `${day} à ${start}`
}

// a care is late when it is still planned and its time has passed
// (the end of the window for a weak constraint). Times are local, like the clock
export const careDueAt = (a) =>
  new Date(a.time_constraint === 'WEAK' ? a.scheduled_end : a.scheduled_start)
export const isLateCare = (a, now = new Date()) => a.status === 'PLANNED' && careDueAt(a) < now

// a stay ended or cancelled, even without a discharge date (encounter_dao.CLOSED_STATUSES)
const CLOSED_STAY_STATUSES = ['finished', 'cancelled', 'entered-in-error']
export const isStayClosed = (encounter) => CLOSED_STAY_STATUSES.includes(encounter.status)

// the stay in progress, as the backend sees it (encounter_dao.get_current)
export function isStayInProgress(encounter, now = new Date()) {
  const discharge = encounter.actual_discharge_date
  return (
    !isStayClosed(encounter) &&
    new Date(encounter.admission_date) <= now &&
    (!discharge || new Date(discharge) > now)
  )
}

// the date part of a stay's end: actual discharge, or the expected one
export function stayEnd(encounter) {
  return encounter.actual_discharge_date ?? encounter.expected_discharge_date ?? null
}

// local date as "YYYY-MM-DD"
export function dayKey(date) {
  const pad = (n) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}
