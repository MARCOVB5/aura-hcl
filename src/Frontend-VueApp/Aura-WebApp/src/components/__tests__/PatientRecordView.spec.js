import { afterEach, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import PatientRecordView from '../../views/PatientRecordView.vue'
import { hospitalizationOf, mockApi, sentTo, stay } from './mockApi.js'

const THOMAS = {
  id: 2,
  ipp: 'DEMO-002',
  identification_status: 'PROVISIONAL',
  person: {
    name_family: 'Larmou',
    name_given: 'Thomas',
    birth_date: '1975-08-27',
    gender: 'unknown',
  },
  allergies: [],
  contact: null,
  personal_info: null,
}
const STAYS = [
  hospitalizationOf(stay(40, THOMAS, '2026-10-19T08:30:00', { actual: '2026-10-23T11:00:00' })),
  hospitalizationOf(stay(41, THOMAS, '2026-11-01T09:00:00', { location: null })),
]

function mountRecord(extra = []) {
  mockApi([
    ['GET', /\/api\/patients\/2$/, 200, THOMAS],
    ['GET', /\/api\/patients\/2\/hospitalizations$/, 200, STAYS],
    ...extra,
  ])
  return mount(PatientRecordView, { props: { patientId: 2 } })
}

afterEach(() => {
  vi.restoreAllMocks()
})

it('shows the record, with "Non renseigné" for what is missing', async () => {
  const wrapper = mountRecord()
  await flushPromises()

  expect(wrapper.get('h1').text()).toBe('Thomas Larmou')
  expect(wrapper.text()).toContain('Fiche patient · Identifiant : DEMO-002')
  expect(wrapper.text()).toContain('27/08/1975')
  expect(wrapper.findAll('.not-set').length).toBeGreaterThanOrEqual(4) // sex, contact, info, allergies

  const stays = wrapper.findAll('.stay')
  expect(stays).toHaveLength(2)
  expect(stays[0].text()).toContain('19/10/2026')
  expect(stays[0].text()).toContain('23/10/2026')
  expect(stays[0].text()).toContain('Réanimation · Chambre 12 · Lit A')
  expect(stays[1].text()).toContain('En cours')

  await wrapper.get('.with-action .btn-primary').trigger('click')
  expect(wrapper.emitted('edit')[0][0].id).toBe(2)
})

it('edits the stays: changed fields are patched, removed stays deleted', async () => {
  const wrapper = mountRecord([
    ['PATCH', /\/api\/hospitalizations\/40$/, 200, STAYS[0]],
    ['DELETE', /\/api\/hospitalizations\/41$/, 204, null],
  ])
  await flushPromises()

  await wrapper
    .findAll('button')
    .find((b) => b.text().includes('Modifier le séjour'))
    .trigger('click')
  const rows = wrapper.findAll('.stay-row')
  expect(rows).toHaveLength(2)

  await rows[0].findAll('input[placeholder="JJ/MM/AAAA"]')[1].setValue('25/10/2026') // new end date
  await rows[0].get('input[maxlength="128"]').setValue(' Box 3 ')
  await rows[1].get('.delete').trigger('click')
  await wrapper
    .findAll('button')
    .find((b) => b.text() === 'Enregistrer')
    .trigger('click')
  await flushPromises()

  expect(sentTo('PATCH', /\/api\/hospitalizations\/40$/)).toEqual([
    // the time of the original value is kept
    { actual_discharge_date: '2026-10-25T11:00:00', location: 'Box 3' },
  ])
  const deletes = fetch.mock.calls.filter(([, o = {}]) => o.method === 'DELETE')
  expect(deletes.map(([url]) => url)).toEqual([
    expect.stringMatching(/\/api\/hospitalizations\/41$/),
  ])
})

it('keeps edit mode and shows why a stay could not be deleted', async () => {
  const wrapper = mountRecord([
    ['DELETE', /\/api\/hospitalizations\/41$/, 409, { detail: 'Stay has care appointments' }],
  ])
  await flushPromises()

  await wrapper
    .findAll('button')
    .find((b) => b.text().includes('Modifier le séjour'))
    .trigger('click')
  await wrapper.findAll('.stay-row')[1].get('.delete').trigger('click')
  await wrapper
    .findAll('button')
    .find((b) => b.text() === 'Enregistrer')
    .trigger('click')
  await flushPromises()

  expect(wrapper.get('[role="alert"]').text()).toContain('Ce séjour a des soins planifiés')
  expect(wrapper.findAll('.stay-row')).toHaveLength(2)
})

it('opens with the stays in edit mode from "Modifier le séjour" of the patient list', async () => {
  mockApi([
    ['GET', /\/api\/patients\/2$/, 200, THOMAS],
    ['GET', /\/api\/patients\/2\/hospitalizations$/, 200, STAYS],
  ])
  const wrapper = mount(PatientRecordView, { props: { patientId: 2, editStays: true } })
  await flushPromises()

  expect(wrapper.findAll('.stay-row')).toHaveLength(2)
  expect(wrapper.findAll('button').some((b) => b.text() === 'Enregistrer')).toBe(true)
})
