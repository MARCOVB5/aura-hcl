import { afterEach, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import PatientRecordView from '../../views/PatientRecordView.vue'
import { appointment, hospitalizationOf, mockApi, stay } from './mockApi.js'

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
const CARE = [
  appointment(1, THOMAS, '2026-10-20T09:30:00', { status: 'DONE' }),
  appointment(2, THOMAS, '2020-11-01T10:00:00', { care_type: 'Pansement' }), // planned, passed
  appointment(3, THOMAS, '2099-11-02T10:00:00', { performers: [], status: 'CANCELLED' }),
]

function mountRecord(care = CARE) {
  mockApi([
    ['GET', /\/api\/patients\/2$/, 200, THOMAS],
    ['GET', /\/api\/patients\/2\/hospitalizations$/, 200, STAYS],
    ['GET', /\/api\/appointments\?patient_id=2$/, 200, care],
  ])
  return mount(PatientRecordView, { props: { patientId: 2 } })
}

const button = (wrapper, text) => wrapper.findAll('button').find((b) => b.text() === text)

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

it('does not show a stay ended or cancelled without a discharge date as in progress', async () => {
  const cancelled = { ...stay(42, THOMAS, '2026-09-01T09:00:00'), status: 'cancelled' }
  mockApi([
    ['GET', /\/api\/patients\/2$/, 200, THOMAS],
    ['GET', /\/api\/patients\/2\/hospitalizations$/, 200, [hospitalizationOf(cancelled)]],
    ['GET', /\/api\/appointments\?patient_id=2$/, 200, []],
  ])
  const wrapper = mount(PatientRecordView, { props: { patientId: 2 } })
  await flushPromises()

  expect(wrapper.get('.stay').text()).toContain('Annulé')
  expect(wrapper.get('.stay').text()).not.toContain('En cours')
})

it('opens each stay on its own page to change it', async () => {
  const wrapper = mountRecord()
  await flushPromises()

  await wrapper.findAll('.stay')[1].get('button').trigger('click')
  expect(wrapper.emitted('edit-stay')[0][0].id).toBe(41)
})

it('lists the care of the patient, to plan one or open one', async () => {
  const wrapper = mountRecord()
  await flushPromises()

  expect(wrapper.text()).toContain('3 soins')
  const rows = wrapper.findAll('.care-table tbody tr')
  expect(rows.map((r) => r.get('.status').text())).toEqual(['Réalisé', 'En retard', 'Annulé'])
  expect(rows[0].text()).toContain('20/10/2026 à 09:30')
  expect(rows[0].text()).toContain('Bruno Azerty')
  expect(rows[2].text()).toContain('Non renseigné') // no caregiver

  await rows[1].trigger('click')
  expect(wrapper.emitted('open-care')[0][0].id).toBe(2)
  await button(wrapper, 'Planifier un soin').trigger('click')
  expect(wrapper.emitted('plan-care')[0][0].id).toBe(2)
})

it('says when no care is planned', async () => {
  const wrapper = mountRecord([])
  await flushPromises()

  expect(wrapper.text()).toContain('Aucun soin n’est planifié pour ce patient.')
  expect(wrapper.find('.care-table').exists()).toBe(false)
})

it('shows the record even when the care cannot be loaded', async () => {
  mockApi([
    ['GET', /\/api\/patients\/2$/, 200, THOMAS],
    ['GET', /\/api\/patients\/2\/hospitalizations$/, 200, STAYS],
    ['GET', /\/api\/appointments\?patient_id=2$/, 500, null],
  ])
  const wrapper = mount(PatientRecordView, { props: { patientId: 2 } })
  await flushPromises()

  expect(wrapper.get('h1').text()).toBe('Thomas Larmou')
  expect(wrapper.findAll('.stay')).toHaveLength(2)
  expect(wrapper.get('[role="alert"]').text()).toContain('Erreur du serveur (500)')
  expect(button(wrapper, 'Réessayer').exists()).toBe(true)
})
