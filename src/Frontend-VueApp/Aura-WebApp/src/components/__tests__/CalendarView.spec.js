import { afterEach, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import CalendarView from '../../views/CalendarView.vue'

const LEA = {
  id: 3,
  ipp: 'DEMO-003',
  person: { name_family: 'Exemple', name_given: 'Léa' },
  allergies: [{ id: 1, name: 'Latex' }],
}
const NORA = {
  id: 5,
  ipp: null,
  person: { name_family: 'Delmas', name_given: 'Nora' },
  allergies: [],
}

const stay = (id, patient, admission, expected = null) => ({
  encounter_id: id,
  admission_status: 'IN_PROGRESS',
  encounter: {
    id,
    stay_number: `SEJ-${id}`,
    patient_id: patient.id,
    patient,
    status: 'in-progress',
    encounter_type_code: 'INPATIENT',
    admission_date: admission,
    expected_discharge_date: expected,
    actual_discharge_date: null,
    reason: 'Choc septique',
  },
})

const STAYS = [
  stay(1, LEA, '2026-10-20T09:30:00', '2026-10-28T10:00:00'),
  stay(2, NORA, '2026-10-23T14:00:00'),
  stay(3, NORA, '2026-11-02T08:00:00'),
]
const TODAY = new Date(2026, 9, 23, 12, 0) // 23 October 2026

function mockFetch(body) {
  globalThis.fetch = vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => body })
}

async function mountCalendar(props = {}) {
  mockFetch(STAYS)
  const wrapper = mount(CalendarView, { props: { today: TODAY, ...props } })
  await flushPromises()
  return wrapper
}

const eventsOn = (wrapper, day) => wrapper.findAll(`[data-day="${day}"] .event`)

afterEach(() => {
  vi.restoreAllMocks()
})

it('shows the current month, Monday first, with today highlighted', async () => {
  const wrapper = await mountCalendar()

  expect(wrapper.get('h1').text()).toBe('Octobre 2026')
  // October 2026 starts on a Thursday: the grid starts on Monday 28 September
  expect(wrapper.findAll('.day')[0].attributes('data-day')).toBe('2026-09-28')
  expect(wrapper.findAll('.week')).toHaveLength(5)
  expect(wrapper.get('.today').text()).toBe('23')
})

it('puts admissions and expected discharges on their day', async () => {
  const wrapper = await mountCalendar()

  const admission = eventsOn(wrapper, '2026-10-20')
  expect(admission).toHaveLength(1)
  expect(admission[0].classes()).toContain('admission')
  expect(admission[0].text()).toContain('Léa Exemple')
  expect(admission[0].text()).toContain('09:30 · Admission')

  const discharge = eventsOn(wrapper, '2026-10-28')
  expect(discharge[0].classes()).toContain('expected')
  expect(discharge[0].text()).toContain('10:00 · Sortie prévue')

  expect(wrapper.text()).toContain('2 admissions ce mois-ci')
})

it('changes month with the arrows and comes back with Aujourd’hui', async () => {
  const wrapper = await mountCalendar()

  await wrapper.get('[aria-label="Mois suivant"]').trigger('click')
  expect(wrapper.get('h1').text()).toBe('Novembre 2026')
  expect(eventsOn(wrapper, '2026-11-02')[0].text()).toContain('Nora Delmas')

  await wrapper.get('.btn-today').trigger('click')
  expect(wrapper.get('h1').text()).toBe('Octobre 2026')
})

it('only shows the selected patient when filtered', async () => {
  const wrapper = await mountCalendar({ patientFilter: NORA })

  expect(eventsOn(wrapper, '2026-10-20')).toHaveLength(0)
  expect(eventsOn(wrapper, '2026-10-23')).toHaveLength(1)
  expect(wrapper.text()).toContain('Séjours de Nora Delmas')
})

it('opens the stay details when an event is clicked', async () => {
  const wrapper = await mountCalendar()

  await eventsOn(wrapper, '2026-10-20')[0].trigger('click')
  const detail = wrapper.get('[role="dialog"]')
  expect(detail.text()).toContain('SEJ-1')
  expect(detail.text()).toContain('20/10/2026 09:30')
  expect(detail.text()).toContain('Choc septique')
  expect(detail.get('.allergy').text()).toContain('Latex')

  await wrapper.get('[aria-label="Fermer"]').trigger('click')
  expect(wrapper.find('[role="dialog"]').exists()).toBe(false)
})
