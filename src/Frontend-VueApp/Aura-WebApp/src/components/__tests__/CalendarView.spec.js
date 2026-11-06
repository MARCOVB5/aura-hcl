import { afterEach, beforeEach, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import CalendarView from '../../views/CalendarView.vue'
import { endSession, startSession } from '../../session.js'
import {
  CARE_TYPES,
  LEA,
  NORA,
  PRACTITIONERS,
  appointment,
  hospitalizationOf,
  mockApi,
  stay,
} from './mockApi.js'

const [BRUNO, ALICE, SIMON] = PRACTITIONERS // Bruno Azerty is the logged-in user
const TODAY = new Date(2026, 9, 23, 12, 0) // 23 October 2026

const CARE = [
  // mine: Bruno is in charge
  appointment(1, LEA, '2026-10-20T09:30:00', {
    care_type: CARE_TYPES[1],
    performers: [BRUNO, ALICE],
    validated_by: SIMON,
    note: 'À jeun',
  }),
  // the department's: someone else in charge, time window
  appointment(2, NORA, '2026-10-23T13:00:00', {
    time_constraint: 'WEAK',
    scheduled_end: '2026-10-23T15:00:00',
    performers: [ALICE],
  }),
  appointment(3, NORA, '2026-11-02T08:00:00'),
]
const NORA_STAYS = [
  hospitalizationOf(stay(30, NORA, '2026-10-19T08:00:00', { actual: '2026-10-27T10:00:00' })),
]

let api
function mountCalendar(props = {}) {
  api = mockApi([
    ['GET', /\/api\/appointments\?/, 200, CARE],
    ['GET', /\/api\/patients\/5\/hospitalizations$/, 200, NORA_STAYS],
  ])
  return mount(CalendarView, { props: { today: TODAY, ...props } })
}

const eventsOn = (wrapper, day) => wrapper.findAll(`[data-day="${day}"] .event`)

beforeEach(() => {
  startSession('token', { id: 1, username: 'bazerty', practitioner_id: BRUNO.id })
})

afterEach(() => {
  endSession()
  vi.restoreAllMocks()
})

it('shows the current month, Monday first, with today highlighted', async () => {
  const wrapper = mountCalendar()
  await flushPromises()

  expect(wrapper.get('h1').text()).toBe('Octobre 2026')
  // October 2026 starts on a Thursday: the grid starts on Monday 28 September
  expect(wrapper.findAll('.day')[0].attributes('data-day')).toBe('2026-09-28')
  expect(wrapper.findAll('.week')).toHaveLength(5)
  expect(wrapper.get('.today').text()).toBe('23')
  // the care of every day on screen is requested, borders included
  expect(api.mock.calls[0][0]).toContain('start=2026-09-28&end=2026-11-01')
})

it('shows my care in purple and the department’s in grey', async () => {
  const wrapper = mountCalendar()
  await flushPromises()

  const [mine] = eventsOn(wrapper, '2026-10-20')
  expect(mine.classes()).toContain('mine')
  expect(mine.text()).toContain('Réévaluation respiratoire')
  expect(mine.text()).toContain('09:30 · Bruno Azerty +1')

  const [service] = eventsOn(wrapper, '2026-10-23')
  expect(service.classes()).toContain('service')
  expect(service.text()).toContain('13:00–15:00 · Alice Merveille')
})

it('hides each group with its sidebar checkbox', async () => {
  const wrapper = mountCalendar({ showMine: false })
  await flushPromises()
  expect(eventsOn(wrapper, '2026-10-20')).toHaveLength(0)
  expect(eventsOn(wrapper, '2026-10-23')).toHaveLength(1)

  await wrapper.setProps({ showMine: true, showService: false })
  expect(eventsOn(wrapper, '2026-10-20')).toHaveLength(1)
  expect(eventsOn(wrapper, '2026-10-23')).toHaveLength(0)
})

it('shows only the selected patient’s care, and their stay as a bar', async () => {
  const wrapper = mountCalendar({ patientFilter: NORA })
  await flushPromises()

  expect(eventsOn(wrapper, '2026-10-20')).toHaveLength(0)
  expect(eventsOn(wrapper, '2026-10-23')[0].classes()).toContain('patient')
  expect(wrapper.get('.patient-bar').text()).toContain('Nora Delmas')

  // the stay runs 19 -> 27 October: Monday to Sunday of week 4, Monday to Tuesday of week 5
  const bands = wrapper.findAll('.stay-band')
  expect(bands).toHaveLength(2)
  expect(bands[0].text()).toContain('Séjour du 19/10/2026 au 27/10/2026')
  expect(bands[0].text()).toContain('Chambre 12')
  expect(bands[0].attributes()).toMatchObject({ 'data-first-day': '0', 'data-days': '7' })
  expect(bands[1].attributes()).toMatchObject({ 'data-first-day': '0', 'data-days': '2' })
})

it('loads the next month with the arrows and comes back with Aujourd’hui', async () => {
  const wrapper = mountCalendar()
  await flushPromises()

  await wrapper.get('[aria-label="Mois suivant"]').trigger('click')
  await flushPromises()
  expect(wrapper.get('h1').text()).toBe('Novembre 2026')
  expect(api.mock.calls.at(-1)[0]).toContain('start=2026-10-26&end=2026-12-06')
  expect(eventsOn(wrapper, '2026-11-02')[0].text()).toContain('Prise de sang')

  await wrapper.get('.btn-today').trigger('click')
  expect(wrapper.get('h1').text()).toBe('Octobre 2026')
})

it('shows the month chosen last, even if an older month answers after it', async () => {
  const api = mockApi([['GET', /\/api\/appointments\?/, 200, []]])
  // November answers only after December, with a care of 30 November cancelled since
  const november = [appointment(4, NORA, '2026-11-30T08:00:00')]
  let answerNovember
  const slow = new Promise((resolve) => (answerNovember = resolve))
  globalThis.fetch = vi.fn(async (url, options) => {
    if (url.includes('start=2026-10-26')) {
      await slow
      return { ok: true, status: 200, json: async () => november }
    }
    return api(url, options)
  })
  const wrapper = mount(CalendarView, { props: { today: TODAY } })
  await flushPromises()

  await wrapper.get('[aria-label="Mois suivant"]').trigger('click') // November
  await wrapper.get('[aria-label="Mois suivant"]').trigger('click') // December
  await flushPromises()
  globalThis.fetch.mockClear()
  answerNovember()
  await flushPromises()

  expect(wrapper.get('h1').text()).toBe('Décembre 2026')
  expect(wrapper.findAll('.event')).toHaveLength(0)
})

it('opens the care details, with a button to change the care', async () => {
  const wrapper = mountCalendar()
  await flushPromises()

  await eventsOn(wrapper, '2026-10-20')[0].trigger('click')
  const detail = wrapper.get('[role="dialog"]')
  expect(detail.text()).toContain('Mardi 20/10/2026 à 09:30')
  expect(detail.text()).toContain('Léa Exemple')
  expect(detail.text()).toContain('Réanimation · Chambre 12 · Lit A')
  expect(detail.get('.allergy').text()).toContain('Pénicilline')
  expect(detail.text()).toContain('Bruno Azerty, Alice Merveille')
  expect(detail.text()).toMatch(/Prescrit par\s: Simon Armand/) // non-breaking space before ":"
  expect(detail.text()).toContain('À jeun')

  await detail.get('.btn-primary').trigger('click')
  expect(wrapper.emitted('edit-care')[0][0].id).toBe(1)

  await wrapper.get('[aria-label="Fermer"]').trigger('click')
  expect(wrapper.find('[role="dialog"]').exists()).toBe(false)
})
