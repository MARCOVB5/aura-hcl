import { afterEach, beforeEach, expect, it, vi } from 'vitest'
import { enableAutoUnmount, flushPromises, mount } from '@vue/test-utils'
import App from '../../App.vue'
import { endSession, session, startSession } from '../../session.js'
import { hospitalizationOf, mockApi, stay } from './mockApi.js'

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

const ME = {
  id: 1,
  username: 'demo.medecin',
  practitioner_id: 1,
  name_given: 'Camille',
  name_family: 'Demo',
  profession: 'Médecin',
}

// the session is shared: an app left mounted by a previous test would react to this test's login
enableAutoUnmount(afterEach)

// these tests start logged in; the ones about logging in end the session first
beforeEach(() => {
  localStorage.clear()
  startSession('token-of-camille', ME)
})

afterEach(() => {
  endSession()
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

const CAMILLE = { ...PATIENTS[0], identification_status: 'PROVISIONAL', contact: null }
const rowButton = (wrapper, text) =>
  wrapper
    .findAll('tbody tr')[0]
    .findAll('button')
    .find((b) => b.text() === text)

it('opens the only stay of the patient from Modifier le séjour, and comes back', async () => {
  mockApi([
    ['GET', /\/api\/patients\?/, 200, PATIENTS],
    ['GET', /\/api\/patients\/1$/, 200, CAMILLE],
    [
      'GET',
      /\/api\/patients\/1\/hospitalizations$/,
      200,
      [hospitalizationOf(stay(9, CAMILLE, '2026-10-20T08:00:00'))],
    ],
    ['GET', /\/api\/appointments\?/, 200, []],
  ])
  const wrapper = mount(App)
  await flushPromises()

  await rowButton(wrapper, 'Modifier le séjour').trigger('click')
  await flushPromises()
  expect(wrapper.get('h1').text()).toBe('Modifier le séjour')
  expect(wrapper.text()).toContain('Séjour n° SEJ-9 · Camille Benoit')

  await wrapper
    .findAll('button')
    .find((b) => b.text() === 'Retour à la liste')
    .trigger('click')
  await flushPromises()
  expect(wrapper.get('h1').text()).toBe('Patients')
})

it('opens the stays of the record when the patient has several', async () => {
  const stays = [
    hospitalizationOf(stay(8, CAMILLE, '2026-09-01T08:00:00', { actual: '2026-09-10T08:00:00' })),
    hospitalizationOf(stay(9, CAMILLE, '2026-10-20T08:00:00')),
  ]
  mockApi([
    ['GET', /\/api\/patients\?/, 200, PATIENTS],
    ['GET', /\/api\/patients\/1$/, 200, CAMILLE],
    ['GET', /\/api\/patients\/1\/hospitalizations$/, 200, stays],
    ['GET', /\/api\/appointments\?/, 200, []],
  ])
  const wrapper = mount(App)
  await flushPromises()

  await rowButton(wrapper, 'Modifier le séjour').trigger('click')
  await flushPromises()
  expect(wrapper.get('h1').text()).toBe('Camille Benoit')
  expect(wrapper.findAll('.stay')).toHaveLength(2)
})

it('plans a care from the patient list, and comes back to the list', async () => {
  mockApi([
    ['GET', /\/api\/patients\?/, 200, PATIENTS],
    ['GET', /\/api\/practitioners$/, 200, []],
    [
      'GET',
      /\/api\/patients\/1\/current-hospitalization$/,
      200,
      hospitalizationOf(stay(9, CAMILLE, '2026-10-20T08:00:00')),
    ],
  ])
  const wrapper = mount(App)
  await flushPromises()

  await rowButton(wrapper, 'Planifier un soin').trigger('click')
  await flushPromises()
  expect(wrapper.get('h1').text()).toBe('Planifier un soin')
  expect(wrapper.get('.patient-box').text()).toContain('Camille Benoit')
  expect(wrapper.get('.stay-box').text()).toContain('Séjour n° SEJ-9')
  expect(wrapper.get('aside .active').text()).toContain('Patients')

  await wrapper
    .findAll('button')
    .find((b) => b.text() === 'Retour à la liste')
    .trigger('click')
  expect(wrapper.get('h1').text()).toBe('Patients')
})

// ---- login and logout ----

it('sends the token with every request and shows who is logged in', async () => {
  mockFetch(PATIENTS)
  const wrapper = mount(App)
  await flushPromises()

  expect(fetch.mock.calls[0][1].headers.Authorization).toBe('Bearer token-of-camille')
  expect(wrapper.get('aside').text()).toContain('Camille Demo')
  expect(wrapper.get('aside').text()).toContain('Statut : Médecin')
})

it('asks to log in first, then opens the app', async () => {
  endSession()
  mockApi([
    ['POST', /\/api\/auth\/login$/, 200, { access_token: 'new-token', token_type: 'bearer' }],
    ['GET', /\/api\/auth\/me$/, 200, ME],
    ['GET', /\/api\/patients\?/, 200, PATIENTS],
  ])
  const wrapper = mount(App)
  await flushPromises()

  expect(wrapper.get('h1').text()).toBe('Authentification')
  expect(wrapper.find('aside').exists()).toBe(false)
  expect(fetch).not.toHaveBeenCalled()
  const button = wrapper.get('button[type="submit"]')
  expect(button.attributes('disabled')).toBeDefined()

  await wrapper.get('#login-username').setValue(' demo.medecin ')
  await wrapper.get('#login-password').setValue('secret')
  expect(button.attributes('disabled')).toBeUndefined()
  await wrapper.get('form').trigger('submit')
  await flushPromises()

  const [url, options] = fetch.mock.calls[0]
  expect(url).toMatch(/\/api\/auth\/login$/)
  expect(options.headers.Authorization).toBeUndefined()
  expect(JSON.parse(options.body)).toEqual({ username: 'demo.medecin', password: 'secret' })
  // who the new token belongs to
  expect(fetch.mock.calls[1][1].headers.Authorization).toBe('Bearer new-token')

  expect(wrapper.get('h1').text()).toBe('Patients')
  expect(localStorage.getItem('aura.token')).toBe('new-token')
})

it('shows or hides the password with the eye button', async () => {
  endSession()
  const wrapper = mount(App)
  const password = wrapper.get('#login-password')
  expect(password.attributes('type')).toBe('password')

  await wrapper.get('[aria-label="Afficher le mot de passe"]').trigger('click')
  expect(password.attributes('type')).toBe('text')
  await wrapper.get('[aria-label="Masquer le mot de passe"]').trigger('click')
  expect(password.attributes('type')).toBe('password')
})

it('says when the username or password is wrong, and Annuler clears the fields', async () => {
  endSession()
  mockApi([['POST', /\/api\/auth\/login$/, 401, { detail: 'Invalid credentials or session' }]])
  const wrapper = mount(App)

  await wrapper.get('#login-username').setValue('demo.medecin')
  await wrapper.get('#login-password').setValue('wrong')
  await wrapper.get('form').trigger('submit')
  await flushPromises()

  expect(wrapper.get('[role="alert"]').text()).toContain('Identifiant ou mot de passe incorrect.')
  expect(wrapper.get('#login-password').element.value).toBe('')
  expect(wrapper.get('h1').text()).toBe('Authentification')

  await wrapper
    .findAll('button')
    .find((b) => b.text() === 'Annuler')
    .trigger('click')
  expect(wrapper.get('#login-username').element.value).toBe('')
  expect(wrapper.find('[role="alert"]').exists()).toBe(false)
})

it('keeps the user logged in after a reload, with the saved token', async () => {
  endSession()
  localStorage.setItem('aura.token', 'saved-token')
  session.token = 'saved-token' // what session.js reads when the page loads
  mockApi([
    ['GET', /\/api\/auth\/me$/, 200, ME],
    ['GET', /\/api\/patients\?/, 200, PATIENTS],
  ])
  const wrapper = mount(App)
  await flushPromises()

  expect(fetch.mock.calls[0][1].headers.Authorization).toBe('Bearer saved-token')
  expect(wrapper.get('h1').text()).toBe('Patients')
})

it('goes back to the login page when the token has expired', async () => {
  mockApi([['GET', /\/api\/patients\?/, 401, { detail: 'Invalid credentials or session' }]])
  const wrapper = mount(App)
  await flushPromises()

  expect(wrapper.get('h1').text()).toBe('Authentification')
  expect(wrapper.get('[role="status"]').text()).toContain('Votre session a expiré')
  expect(localStorage.getItem('aura.token')).toBeNull()
})

it('logs out with Déconnexion', async () => {
  mockFetch(PATIENTS)
  const wrapper = mount(App)
  await flushPromises()

  await wrapper.get('.logout').trigger('click')
  expect(wrapper.get('h1').text()).toBe('Authentification')
  expect(wrapper.find('[role="status"]').exists()).toBe(false) // not "expired"
  expect(session.token).toBeNull()
  expect(localStorage.getItem('aura.token')).toBeNull()
})

// ---- the patient list and the sidebar ----

it('stays on the page the user went to while Modifier le séjour was loading', async () => {
  const api = mockApi([
    ['GET', /\/api\/patients\?/, 200, PATIENTS],
    [
      'GET',
      /\/api\/patients\/1\/hospitalizations$/,
      200,
      [hospitalizationOf(stay(9, CAMILLE, '2026-10-20T08:00:00'))],
    ],
  ])
  // the stays come back only after the user has gone to the calendar
  let answer
  const slow = new Promise((resolve) => (answer = resolve))
  globalThis.fetch = vi.fn(async (url, options) => {
    if (url.endsWith('/hospitalizations')) await slow
    return api(url, options)
  })
  const wrapper = mount(App)
  await flushPromises()

  await rowButton(wrapper, 'Modifier le séjour').trigger('click')
  await wrapper
    .findAll('aside .nav-item')
    .find((b) => b.text().includes('Calendrier'))
    .trigger('click')
  answer()
  await flushPromises()

  expect(wrapper.get('h1').text()).not.toBe('Modifier le séjour')
  expect(wrapper.get('aside .active').text()).toContain('Calendrier')
})

it('shows the selected patient as they are now when the list is loaded again', async () => {
  let loads = 0
  const withAllergy = { ...CAMILLE, allergies: [{ id: 1, name: 'Latex' }] }
  mockApi([
    [
      'GET',
      /\/api\/patients\?/,
      200,
      () => (++loads === 1 ? PATIENTS : [withAllergy, PATIENTS[1]]),
    ],
    ['GET', /\/api\/patients\/1$/, 200, CAMILLE],
    ['GET', /\/api\/patients\/1\/hospitalizations$/, 200, []],
    ['GET', /\/api\/appointments\?/, 200, []],
  ])
  const wrapper = mount(App)
  await flushPromises()

  await wrapper.findAll('tbody tr')[0].trigger('click')
  await flushPromises()
  expect(wrapper.get('aside').text()).toContain('Aucune allergie renseignée')

  await wrapper.get('.patient-link').trigger('click')
  await flushPromises()
  await wrapper
    .findAll('button')
    .find((b) => b.text() === 'Retour aux patients')
    .trigger('click')
  await flushPromises()
  expect(wrapper.get('aside .allergy').text()).toBe('Latex')
})
