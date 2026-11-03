import { afterEach, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import PatientFormView from '../../views/PatientFormView.vue'

const submitButton = (wrapper) => wrapper.get('button[type="submit"]')

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

it('requires last and first name before Valider is enabled', async () => {
  const wrapper = mount(PatientFormView)
  expect(submitButton(wrapper).attributes('disabled')).toBeDefined()

  await wrapper.get('input[placeholder="Ex. : Doe"]').setValue('Doxa')
  expect(submitButton(wrapper).attributes('disabled')).toBeDefined()

  await wrapper.get('input[placeholder="Ex. : John"]').setValue('Loui')
  expect(submitButton(wrapper).attributes('disabled')).toBeUndefined()
  expect(wrapper.text()).toContain('Tous les champs obligatoires sont renseignés.')
})

it('makes names optional for a "Patient sous X"', async () => {
  const wrapper = mount(PatientFormView)
  await wrapper.get('input[type="checkbox"]').setValue(true)

  expect(submitButton(wrapper).attributes('disabled')).toBeUndefined()
  expect(wrapper.text()).toContain('Patient sous X : aucun champ obligatoire.')
})

it('sends the patient to the API and emits the created patient', async () => {
  const created = { id: 7, ipp: '123', person: {}, allergies: [] }
  mockFetch(201, created)
  const wrapper = mount(PatientFormView)

  await wrapper.get('input[placeholder="Ex. : Doe"]').setValue('  Doxa ')
  await wrapper.get('input[placeholder="Ex. : John"]').setValue('Loui')
  await wrapper.get('input[value="female"]').setValue(true)
  await wrapper.get('input[placeholder="JJ/MM/AAAA"]').setValue('06/11/1990')
  await wrapper.get('input[placeholder="Ex. : 123456789"]').setValue('123')
  await wrapper.get('input[type="tel"]').setValue(' 06 12 34 56 78 ')
  await wrapper.findAll('textarea')[0].setValue('Antécédents cardiaques')
  await wrapper.findAll('textarea')[1].setValue('Pénicilline\nLatex, Iode')
  await wrapper.get('form').trigger('submit')
  await flushPromises()

  const [url, options] = fetch.mock.calls[0]
  expect(url).toMatch(/\/api\/patients$/)
  expect(options.method).toBe('POST')
  expect(JSON.parse(options.body)).toEqual({
    person: { name_family: 'Doxa', name_given: 'Loui', birth_date: '1990-11-06', gender: 'female' },
    ipp: '123',
    identification_status: 'PROVISIONAL',
    contact: '06 12 34 56 78',
    personal_info: 'Antécédents cardiaques',
    allergies: ['Pénicilline', 'Latex', 'Iode'],
  })
  expect(wrapper.emitted('created')[0]).toEqual([created])
})

it('edits an existing patient: prefilled, then saved with PUT', async () => {
  const patient = {
    id: 2,
    ipp: 'DEMO-002',
    identification_status: 'PROVISIONAL',
    person: {
      name_family: 'Larmou',
      name_given: 'Thomas',
      birth_date: '1975-08-27',
      gender: 'unknown',
    },
    allergies: [{ id: 1, name: 'Latex' }],
    contact: null,
    personal_info: null,
  }
  mockFetch(200, { ...patient, ipp: 'DEMO-002-B' })
  const wrapper = mount(PatientFormView, { props: { patient } })

  expect(wrapper.get('h1').text()).toBe('Modifier les informations du patient')
  expect(wrapper.text()).toContain('Thomas Larmou · Identifiant : DEMO-002')
  expect(wrapper.get('input[placeholder="Ex. : Doe"]').element.value).toBe('Larmou')
  expect(wrapper.get('input[placeholder="JJ/MM/AAAA"]').element.value).toBe('27/08/1975')
  expect(wrapper.findAll('textarea')[1].element.value).toBe('Latex')

  await wrapper.get('input[placeholder="Ex. : 123456789"]').setValue('DEMO-002-B')
  await wrapper.get('form').trigger('submit')
  await flushPromises()

  const [url, options] = fetch.mock.calls[0]
  expect(url).toMatch(/\/api\/patients\/2$/)
  expect(options.method).toBe('PUT')
  expect(JSON.parse(options.body)).toMatchObject({ ipp: 'DEMO-002-B', allergies: ['Latex'] })
  expect(wrapper.emitted('saved')[0][0].ipp).toBe('DEMO-002-B')
})

it('sends gender "unknown" when no sex is chosen', async () => {
  mockFetch(201, { id: 8, person: {}, allergies: [] })
  const wrapper = mount(PatientFormView)

  await wrapper.get('input[type="checkbox"]').setValue(true)
  await wrapper.get('form').trigger('submit')
  await flushPromises()

  expect(JSON.parse(fetch.mock.calls[0][1].body).person.gender).toBe('unknown')
})

it('is prefilled from the admission search', async () => {
  const wrapper = mount(PatientFormView, {
    props: {
      forAdmission: true,
      prefill: { nameFamily: 'Delmas', nameGiven: 'Nora', ipp: 'IPP-1' },
    },
  })

  expect(wrapper.get('input[placeholder="Ex. : Doe"]').element.value).toBe('Delmas')
  expect(wrapper.get('input[placeholder="Ex. : 123456789"]').element.value).toBe('IPP-1')
  expect(wrapper.text()).toContain('vous créerez le séjour de Nora Delmas')
  expect(wrapper.text()).toContain('Valider crée le patient, puis ouvre la création de son séjour.')
})

it('shows the backend message when the IPP is already registered', async () => {
  mockFetch(409, { detail: 'IPP already registered' })
  const wrapper = mount(PatientFormView)

  await wrapper.get('input[type="checkbox"]').setValue(true)
  await wrapper.get('form').trigger('submit')
  await flushPromises()

  expect(wrapper.get('[role="alert"]').text()).toContain('Cet IPP est déjà attribué')
  expect(wrapper.emitted('created')).toBeUndefined()
})
