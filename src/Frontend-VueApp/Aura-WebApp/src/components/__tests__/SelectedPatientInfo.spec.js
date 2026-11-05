import { afterEach, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import SelectedPatientInfo from '../SelectedPatientInfo.vue'
import { LEA, NORA, appointment, mockApi } from './mockApi.js'

const NOW = new Date(2026, 9, 23, 12, 0) // 23 October 2026, 12:00

const CARE = [
  // late: precise time passed
  appointment(1, LEA, '2026-10-23T09:30:00', { care_type: 'Prise de sang' }),
  // late: the window ended at 11:00
  appointment(2, LEA, '2026-10-22T08:00:00', {
    care_type: 'Pansement',
    time_constraint: 'WEAK',
    scheduled_end: '2026-10-22T11:00:00',
  }),
  // not late: the window is still open
  appointment(3, LEA, '2026-10-23T10:00:00', {
    time_constraint: 'WEAK',
    scheduled_end: '2026-10-23T14:00:00',
  }),
  // not late: later today
  appointment(4, LEA, '2026-10-23T16:00:00'),
  // not late: done or cancelled
  appointment(5, LEA, '2026-10-21T08:00:00', { status: 'DONE' }),
  appointment(6, LEA, '2026-10-21T09:00:00', { status: 'CANCELLED' }),
]

afterEach(() => {
  vi.restoreAllMocks()
})

it('shows the allergies and the late care of the selected patient, oldest first', async () => {
  const api = mockApi([['GET', /\/api\/appointments\?patient_id=3$/, 200, CARE]])
  const wrapper = mount(SelectedPatientInfo, { props: { patient: LEA, now: NOW } })
  await flushPromises()

  expect(api.mock.calls[0][0]).toMatch(/\/api\/appointments\?patient_id=3$/)
  expect(wrapper.get('.allergy').text()).toBe('Pénicilline')
  expect(wrapper.get('.count').text()).toBe('2')
  const late = wrapper.findAll('.late')
  expect(late.map((l) => l.text())).toEqual([
    expect.stringContaining('Pansement'),
    expect.stringContaining('Prise de sang'),
  ])
  expect(late[0].text()).toContain('22/10/2026 de 08:00 à 11:00')
  expect(late[1].text()).toContain('23/10/2026 à 09:30')

  await late[1].trigger('click')
  expect(wrapper.emitted('open-care')[0][0].id).toBe(1)
})

it('says when there is nothing to report', async () => {
  mockApi([['GET', /\/api\/appointments\?/, 200, CARE.slice(2)]])
  const wrapper = mount(SelectedPatientInfo, { props: { patient: NORA, now: NOW } })
  await flushPromises()

  expect(wrapper.text()).toContain('Aucune allergie renseignée')
  expect(wrapper.text()).toContain('Aucun soin en retard')
  expect(wrapper.find('.count').exists()).toBe(false)
})

it('loads the care again when a care is saved', async () => {
  const api = mockApi([['GET', /\/api\/appointments\?/, 200, []]])
  const wrapper = mount(SelectedPatientInfo, {
    props: { patient: LEA, now: NOW, refreshKey: 0 },
  })
  await flushPromises()

  await wrapper.setProps({ refreshKey: 1 })
  await flushPromises()
  expect(api).toHaveBeenCalledTimes(2)
})
