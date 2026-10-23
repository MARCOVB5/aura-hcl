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

export const STAY_TYPES = [
  { value: 'INPATIENT', label: 'Hospitalisation' },
  { value: 'EMERGENCY', label: 'Urgence' },
  { value: 'OUTPATIENT', label: 'Ambulatoire' },
]

export const labelOf = (options, value) => options.find((o) => o.value === value)?.label ?? value
