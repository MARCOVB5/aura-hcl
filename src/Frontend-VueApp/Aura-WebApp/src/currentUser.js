// The person using the app. There is no login yet: this is the doctor of the mock-ups,
// who exists as a practitioner in the database (seeded by a migration).
// "Mes soins" in the calendar are the care appointments this person is in charge of.
export const CURRENT_USER = {
  name_given: 'Bruno',
  name_family: 'Azerty',
  status: 'Médecin',
}

export function isCurrentUser(practitioner) {
  return (
    practitioner?.person?.name_given === CURRENT_USER.name_given &&
    practitioner?.person?.name_family === CURRENT_USER.name_family
  )
}
