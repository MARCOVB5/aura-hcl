import { afterEach, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import App from '../../App.vue'

const PATIENTS = [
  {
    id: 1,
    ipp: 'DEMO-001',
    person: { id: 1, name_family: 'Benoit', name_given: 'Camille', birth_date: '1982-03-14' },
    allergies: [],
  },
  {
    id: 2,
    ipp: null,
    person: { id: 2, name_family: null, name_given: null, birth_date: null },
    allergies: [],
  },
]

function mockFetch(body, ok = true) {
  globalThis.fetch = vi
    .fn()
    .mockResolvedValue({ ok, status: ok ? 200 : 500, json: async () => body })
}

afterEach(() => {
  vi.restoreAllMocks()
})

it('opens on the patient list, loaded from the API', async () => {
  mockFetch(PATIENTS)
  const wrapper = mount(App)
  await flushPromises()

  expect(wrapper.get('h1').text()).toBe('Patients')
  expect(fetch).toHaveBeenCalledWith(
    expect.stringContaining('/api/patients?limit=200'),
    expect.any(Object),
  )
  const rows = wrapper.findAll('tbody tr')
  expect(rows).toHaveLength(2)
  expect(rows[0].text()).toContain('Camille Benoit')
  expect(rows[0].text()).toContain('14/03/1982')
  expect(rows[1].text()).toContain('Patient sous X')
  expect(wrapper.text()).toContain('2 patients')
})

it('filters the list with the search box', async () => {
  mockFetch(PATIENTS)
  const wrapper = mount(App)
  await flushPromises()

  await wrapper.get('input[type="search"]').setValue('benoît')
  expect(wrapper.findAll('tbody tr')).toHaveLength(1)
  expect(wrapper.text()).toContain('1 patient')
})

it('shows the selected patient in the sidebar', async () => {
  mockFetch(PATIENTS)
  const wrapper = mount(App)
  await flushPromises()

  await wrapper.findAll('tbody tr')[0].trigger('click')
  expect(wrapper.get('aside').text()).toContain('Camille Benoit')
})

it('shows an error when the API cannot be reached', async () => {
  globalThis.fetch = vi.fn().mockRejectedValue(new TypeError('Failed to fetch'))
  const wrapper = mount(App)
  await flushPromises()

  expect(wrapper.get('[role="alert"]').text()).toContain('Impossible de joindre le serveur')
})

it('opens the create form from the list', async () => {
  mockFetch(PATIENTS)
  const wrapper = mount(App)
  await flushPromises()

  await wrapper.get('.btn-create').trigger('click')
  expect(wrapper.get('h1').text()).toBe('Créer un patient')
})
