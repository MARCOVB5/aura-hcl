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
  await wrapper.get('input[type="date"]').setValue('1990-11-06')
  await wrapper.get('input[placeholder="Ex. : 123456789"]').setValue('123')
  await wrapper.findAll('textarea')[1].setValue('Pénicilline\nLatex, Iode')
  await wrapper.get('form').trigger('submit')
  await flushPromises()

  const [url, options] = fetch.mock.calls[0]
  expect(url).toMatch(/\/api\/patients$/)
  expect(options.method).toBe('POST')
  expect(JSON.parse(options.body)).toEqual({
    person: { name_family: 'Doxa', name_given: 'Loui', birth_date: '1990-11-06', gender: 'female' },
    ipp: '123',
    allergies: ['Pénicilline', 'Latex', 'Iode'],
  })
  expect(wrapper.emitted('created')[0]).toEqual([created])
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
