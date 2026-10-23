import { afterEach, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import AdmissionSearchView from '../../views/AdmissionSearchView.vue'
import StayFormView from '../../views/StayFormView.vue'

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

  await wrapper.get('input[placeholder="Ex. : Exemple"]').setValue('exemple')
  await wrapper.get('input[placeholder="Ex. : Léa"]').setValue('lea')
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

  await wrapper.get('input[placeholder="Ex. : Exemple"]').setValue('Delmas')
  await wrapper.get('input[placeholder="Ex. : Léa"]').setValue('Nora')
  await wrapper.get('form').trigger('submit')
  await flushPromises()

  expect(wrapper.text()).toContain('Aucun patient trouvé')
  expect(wrapper.text()).toContain('créez un dossier pour Nora Delmas')
  await wrapper.get('.placeholder .btn-primary').trigger('click')
  expect(wrapper.emitted('create-patient')[0]).toEqual([
    { nameFamily: 'Delmas', nameGiven: 'Nora', ipp: '' },
  ])
})

it('creates the stay for the selected patient', async () => {
  const created = { encounter_id: 1, encounter: { patient: LEA } }
  mockFetch(201, created)
  const wrapper = mount(StayFormView, { props: { patient: LEA } })

  expect(wrapper.text()).toContain('DEMO-003 · Née le 06/11/1990')
  expect(wrapper.get('.allergy').text()).toContain('Pénicilline')

  await wrapper.get('input[maxlength="32"]').setValue('SEJ-TEST-1')
  await wrapper.findAll('input[type="datetime-local"]')[0].setValue('2026-10-23T08:05')
  await wrapper.get('input[maxlength="255"]').setValue('Choc septique')
  await wrapper.get('form').trigger('submit')
  await flushPromises()

  const [url, options] = fetch.mock.calls[0]
  expect(url).toMatch(/\/api\/hospitalizations$/)
  expect(JSON.parse(options.body)).toEqual({
    encounter: {
      patient_id: 3,
      stay_number: 'SEJ-TEST-1',
      status: 'in-progress',
      encounter_type_code: 'INPATIENT',
      admission_date: '2026-10-23T08:05:00',
      expected_discharge_date: null,
      reason: 'Choc septique',
    },
  })
  expect(wrapper.emitted('created')[0]).toEqual([created])
})

it('refuses an expected discharge before the admission', async () => {
  const wrapper = mount(StayFormView, { props: { patient: LEA } })
  const [admission, discharge] = wrapper.findAll('input[type="datetime-local"]')

  await admission.setValue('2026-10-23T08:00')
  await discharge.setValue('2026-10-22T08:00')
  expect(wrapper.get('button[type="submit"]').attributes('disabled')).toBeDefined()
  expect(wrapper.text()).toContain('La sortie prévue doit être après la date d’admission.')
})

it('shows the backend message for a duplicate stay number', async () => {
  mockFetch(409, { detail: 'Stay number already registered' })
  const wrapper = mount(StayFormView, { props: { patient: NICOLAS } })

  await wrapper.get('form').trigger('submit')
  await flushPromises()

  expect(wrapper.get('[role="alert"]').text()).toContain('Ce numéro de séjour existe déjà.')
})
