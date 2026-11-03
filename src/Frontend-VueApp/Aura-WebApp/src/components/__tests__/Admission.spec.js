import { afterEach, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import AdmissionSearchView from '../../views/AdmissionSearchView.vue'
import StayFormView from '../../views/StayFormView.vue'
import { mockApi, sentTo } from './mockApi.js'

// the input of the field whose label starts with this text
const input = (wrapper, label) =>
  wrapper
    .findAll('.field')
    .find((f) => f.find('.field-label').exists() && f.get('.field-label').text().startsWith(label))
    .get('input')

const LEA = {
  id: 3,
  ipp: 'DEMO-003',
  person: { name_family: 'Exemple', name_given: 'Léa', birth_date: '1990-11-06', gender: 'female' },
  allergies: [{ id: 1, name: 'Pénicilline' }],
}
const NICOLAS = {
  id: 4,
  ipp: 'DEMO-004',
  person: { name_family: 'Exemple', name_given: 'Nicolas', birth_date: null, gender: 'male' },
  allergies: [],
}

function mockFetch(status, body) {
  globalThis.fetch = vi.fn().mockResolvedValue({
    ok: status < 400,
    status,
    json: async () => body,
  })
}

afterEach(() => {
  vi.restoreAllMocks()
})

it('finds patients matching every filled criterion, ignoring accents', async () => {
  mockFetch(200, [LEA, NICOLAS])
  const wrapper = mount(AdmissionSearchView)
  expect(wrapper.get('button[type="submit"]').attributes('disabled')).toBeDefined()

  await input(wrapper, 'Nom').setValue('exemple')
  await input(wrapper, 'Prénom').setValue('lea')
  await wrapper.get('form').trigger('submit')
  await flushPromises()

  const rows = wrapper.findAll('tbody tr')
  expect(rows).toHaveLength(1)
  expect(rows[0].text()).toContain('Léa Exemple')
  // a single match is selected right away
  await wrapper.findAll('.buttons button')[1].trigger('click')
  expect(wrapper.emitted('select')[0]).toEqual([LEA])
})

it('offers to create the patient with the search criteria when nothing matches', async () => {
  mockFetch(200, [LEA])
  const wrapper = mount(AdmissionSearchView)

  await input(wrapper, 'Nom').setValue('Delmas')
  await input(wrapper, 'Prénom').setValue('Nora')
  await wrapper.get('form').trigger('submit')
  await flushPromises()

  expect(wrapper.text()).toContain('Aucun patient trouvé')
  await wrapper.get('.placeholder .btn-primary').trigger('click')
  expect(wrapper.emitted('create-patient')[0]).toEqual([
    { nameFamily: 'Delmas', nameGiven: 'Nora', ipp: '' },
  ])
})

it('creates the stay for the selected patient, in the chosen room', async () => {
  const created = { encounter_id: 1, encounter: { patient: LEA } }
  mockApi([['POST', /\/api\/hospitalizations$/, 201, created]])
  const wrapper = mount(StayFormView, { props: { patient: LEA } })
  await flushPromises()

  expect(wrapper.text()).toContain('DEMO-003 · Née le 06/11/1990')
  expect(wrapper.get('.allergy').text()).toContain('Pénicilline')

  await wrapper.get('input[maxlength="32"]').setValue('SEJ-TEST-1')
  await wrapper.get('[aria-label="Admission : date"]').setValue('23/10/2026')
  await wrapper.get('[aria-label="Admission : heure"]').setValue('08:05')
  await wrapper.get('input[maxlength="255"]').setValue('Choc septique')
  // the first location is required
  expect(wrapper.get('button[type="submit"]').attributes('disabled')).toBeDefined()
  await wrapper.get('input[maxlength="128"]').setValue('  Chambre 12, lit A ')
  await wrapper.get('form').trigger('submit')
  await flushPromises()

  expect(sentTo('POST', /\/api\/hospitalizations$/)).toEqual([
    {
      encounter: {
        patient_id: 3,
        stay_number: 'SEJ-TEST-1',
        status: 'in-progress',
        encounter_type_code: 'INPATIENT',
        admission_date: '2026-10-23T08:05:00',
        expected_discharge_date: null,
        reason: 'Choc septique',
        location: 'Chambre 12, lit A',
      },
    },
  ])
  expect(wrapper.emitted('created')[0]).toEqual([created])
})

it('refuses an expected discharge before the admission', async () => {
  const wrapper = mount(StayFormView, { props: { patient: LEA } })
  const field = (name) => wrapper.get(`[aria-label="${name}"]`)

  await field('Admission : date').setValue('23/10/2026')
  await field('Admission : heure').setValue('08:00')
  await field('Sortie prévue : date').setValue('22/10/2026')
  await field('Sortie prévue : heure').setValue('08:00')
  expect(wrapper.get('button[type="submit"]').attributes('disabled')).toBeDefined()
  expect(wrapper.text()).toContain('La sortie prévue doit être après la date d’admission.')
})

it('shows the backend message for a duplicate stay number', async () => {
  mockApi([['POST', /\/api\/hospitalizations$/, 409, { detail: 'Stay number already registered' }]])
  const wrapper = mount(StayFormView, { props: { patient: NICOLAS } })
  await flushPromises()

  await wrapper.get('input[maxlength="128"]').setValue('Box 3')
  await wrapper.get('form').trigger('submit')
  await flushPromises()

  expect(wrapper.get('[role="alert"]').text()).toContain('Ce numéro de séjour existe déjà.')
})
