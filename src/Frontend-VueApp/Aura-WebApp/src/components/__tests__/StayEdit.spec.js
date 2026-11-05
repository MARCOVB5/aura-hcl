import { afterEach, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import StayFormView from '../../views/StayFormView.vue'
import { LEA, hospitalizationOf, mockApi, sentTo, stay } from './mockApi.js'

const STAY = {
  ...stay(40, LEA, '2026-10-19T08:30:00', { expected: '2026-10-25T12:00:00' }),
  reason: 'Choc septique',
}

const field = (wrapper, name) => wrapper.get(`[aria-label="${name}"]`)
const submit = (wrapper) => wrapper.get('button[type="submit"]')
const button = (wrapper, text) => wrapper.findAll('button').find((b) => b.text().includes(text))

function mountEdit(routes = []) {
  mockApi(routes)
  return mount(StayFormView, { props: { patient: LEA, stay: STAY } })
}

afterEach(() => {
  vi.restoreAllMocks()
})

it('changes every field of the stay, like its creation', async () => {
  const saved = hospitalizationOf({ ...STAY, location: 'Box 3' })
  const wrapper = mountEdit([['PATCH', /\/api\/hospitalizations\/40$/, 200, saved]])

  expect(wrapper.get('h1').text()).toBe('Modifier le séjour')
  expect(wrapper.text()).not.toContain('Changer de patient')
  expect(wrapper.get('input[maxlength="32"]').element.value).toBe('SEJ-40')
  expect(field(wrapper, 'Admission : date').element.value).toBe('19/10/2026')
  expect(field(wrapper, 'Admission : heure').element.value).toBe('08:30')
  expect(field(wrapper, 'Sortie prévue : date').element.value).toBe('25/10/2026')
  expect(wrapper.get('input[maxlength="255"]').element.value).toBe('Choc septique')

  await wrapper.get('input[maxlength="128"]').setValue(' Box 3 ')
  await wrapper.findAll('select')[0].setValue('finished')
  await field(wrapper, 'Sortie effective : date').setValue('24/10/2026')
  await field(wrapper, 'Sortie effective : heure').setValue('17:00')
  await wrapper.get('form').trigger('submit')
  await flushPromises()

  expect(sentTo('PATCH', /\/api\/hospitalizations\/40$/)).toEqual([
    {
      stay_number: 'SEJ-40',
      status: 'finished',
      encounter_type_code: 'INPATIENT',
      admission_date: '2026-10-19T08:30:00',
      expected_discharge_date: '2026-10-25T12:00:00',
      actual_discharge_date: '2026-10-24T17:00:00',
      reason: 'Choc septique',
      location: 'Box 3',
    },
  ])
  expect(wrapper.emitted('saved')[0]).toEqual([saved])
})

it('refuses a discharge before the admission', async () => {
  const wrapper = mountEdit()

  await field(wrapper, 'Sortie effective : date').setValue('18/10/2026')
  await field(wrapper, 'Sortie effective : heure').setValue('08:00')
  expect(submit(wrapper).attributes('disabled')).toBeDefined()
  expect(wrapper.text()).toContain('La sortie effective doit être après la date d’admission.')
})

it('shows why the backend refused the new dates', async () => {
  const wrapper = mountEdit([
    ['PATCH', /\/api\/hospitalizations\/40$/, 409, { detail: 'Stay has care outside its dates' }],
  ])

  await wrapper.get('form').trigger('submit')
  await flushPromises()
  expect(wrapper.get('[role="alert"]').text()).toContain(
    'Des soins de ce séjour sont en dehors de ces dates.',
  )
})

it('deletes the stay after a confirmation', async () => {
  const wrapper = mountEdit([['DELETE', /\/api\/hospitalizations\/40$/, 204, null]])

  await button(wrapper, 'Supprimer le séjour').trigger('click')
  expect(fetch).not.toHaveBeenCalled()
  expect(wrapper.text()).toContain('Supprimer définitivement ce séjour ?')

  await wrapper.get('.btn-danger').trigger('click')
  await flushPromises()
  expect(fetch.mock.calls.map(([url, o]) => [o.method, url])).toEqual([
    ['DELETE', expect.stringMatching(/\/api\/hospitalizations\/40$/)],
  ])
  expect(wrapper.emitted('deleted')).toHaveLength(1)
})

it('does not delete a stay that has care', async () => {
  const wrapper = mountEdit([
    ['DELETE', /\/api\/hospitalizations\/40$/, 409, { detail: 'Stay has care appointments' }],
  ])

  await button(wrapper, 'Supprimer le séjour').trigger('click')
  await wrapper.get('.btn-danger').trigger('click')
  await flushPromises()
  expect(wrapper.get('[role="alert"]').text()).toContain('Ce séjour a des soins planifiés')
  expect(wrapper.emitted('deleted')).toBeUndefined()
})
