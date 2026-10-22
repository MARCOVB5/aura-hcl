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
