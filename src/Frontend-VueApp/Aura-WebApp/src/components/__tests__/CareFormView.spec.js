import { afterEach, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import CareFormView from '../../views/CareFormView.vue'
import {
  CARE_TYPES,
  LEA,
  LEA_2,
  NORA,
  PRACTITIONERS,
  appointment,
  hospitalizationOf,
  mockApi,
  sentTo,
  stay,
} from './mockApi.js'

const TODAY = new Date(2026, 9, 23, 12, 0) // 23 October 2026
const LEA_STAY = hospitalizationOf(stay(20, LEA, '2026-10-20T08:00:00'))

function mockBackend(extra = []) {
  return mockApi([
    ['GET', /\/api\/care-types$/, 200, CARE_TYPES],
    ['GET', /\/api\/practitioners$/, 200, PRACTITIONERS],
    ['GET', /\/api\/patients\?/, 200, [LEA, LEA_2, NORA]],
    ['GET', /\/api\/patients\/3\/current-hospitalization$/, 200, LEA_STAY],
    // DEMO-007 has no stay in progress (the blocking case of the design)
    ['GET', /\/api\/patients\/7\/current-hospitalization$/, 404, { detail: 'No current stay' }],
    ...extra,
  ])
}

const submit = (wrapper) => wrapper.get('button[type="submit"]')
const input = (wrapper, label) =>
  wrapper.findAll('.field').find((f) => f.find('.field-label').text().startsWith(label))

async function fillStrongCare(wrapper) {
  await wrapper.get('select[required]').setValue(CARE_TYPES[0].id)
  await wrapper.get('input[value="STRONG"]').setValue(true)
  await input(wrapper, 'Heure précise').get('input').setValue('14:00')
}

afterEach(() => {
  vi.restoreAllMocks()
})

it('finds patients by name and needs one to be chosen', async () => {
  mockBackend()
  const wrapper = mount(CareFormView, { props: { today: TODAY } })
  await flushPromises()

  expect(wrapper.text()).toContain('Sélectionnez un patient pour afficher et associer son séjour')
  await input(wrapper, 'Nom').get('input').setValue('exemple')
  await input(wrapper, 'Prénom').get('input').setValue('lea')
  await flushPromises()

  expect(wrapper.text()).toContain('2 dossiers correspondent')
  expect(wrapper.text()).toContain('la saisie du nom et du prénom ne suffit pas')
  await fillStrongCare(wrapper)
  expect(submit(wrapper).attributes('disabled')).toBeDefined()

  await wrapper.findAll('.result button')[0].trigger('click')
  await flushPromises()
  expect(wrapper.text()).toContain('Débuté le 20/10/2026 · Réanimation · Chambre 12 · Lit A')
  expect(submit(wrapper).attributes('disabled')).toBeUndefined()
})

it('blocks a patient without a current stay and offers to create it', async () => {
  mockBackend()
  const wrapper = mount(CareFormView, { props: { today: TODAY, initialPatient: LEA_2 } })
  await flushPromises()
  await fillStrongCare(wrapper)

  expect(wrapper.text()).toContain('Aucun séjour en cours')
  expect(wrapper.text()).toContain(
    'Validation impossible : aucun séjour en cours pour le dossier DEMO-007.',
  )
  expect(submit(wrapper).attributes('disabled')).toBeDefined()

  const create = wrapper
    .findAll('.stay-box button')
    .find((b) => b.text().includes('Créer un séjour'))
  await create.trigger('click')
  const [{ patient, draft }] = wrapper.emitted('create-stay')[0]
  expect(patient.id).toBe(7)
  // what was typed is kept, to resume after creating the stay
  expect(draft).toMatchObject({
    careTypeId: CARE_TYPES[0].id,
    constraint: 'STRONG',
    exactTime: '14:00',
  })
})

it('resumes a draft after the stay was created', async () => {
  mockBackend()
  const draft = { careTypeId: 2, constraint: 'STRONG', date: '2026-10-24', exactTime: '09:00' }
  const wrapper = mount(CareFormView, { props: { today: TODAY, initialPatient: LEA, draft } })
  await flushPromises()

  expect(wrapper.get('select[required]').element.value).toBe('2')
  expect(input(wrapper, 'Heure précise').get('input').element.value).toBe('09:00')
  expect(submit(wrapper).attributes('disabled')).toBeUndefined()
})

it('creates a care with a time window, caregivers and a validator', async () => {
  const created = appointment(1, LEA, '2026-10-23T13:00:00')
  mockBackend([['POST', /\/api\/appointments$/, 201, created]])
  const wrapper = mount(CareFormView, { props: { today: TODAY, initialPatient: LEA } })
  await flushPromises()

  await wrapper.get('select[required]').setValue(CARE_TYPES[1].id)
  await wrapper.get('input[value="WEAK"]').setValue(true)
  await input(wrapper, 'Début de la plage').get('input').setValue('15:00')
  await input(wrapper, 'Fin de la plage').get('input').setValue('13:00')
  expect(wrapper.text()).toContain('La fin de la plage doit être après son début.')
  expect(submit(wrapper).attributes('disabled')).toBeDefined()
  await input(wrapper, 'Début de la plage').get('input').setValue('13:00')
  await input(wrapper, 'Fin de la plage').get('input').setValue('15:00')

  const add = wrapper.get('.chip-select')
  await add.setValue(PRACTITIONERS[0].id)
  await add.setValue(PRACTITIONERS[1].id)
  expect(wrapper.findAll('.chip').map((c) => c.text())).toEqual(['Bruno Azerty', 'Alice Merveille'])
  await wrapper.findAll('.chip-remove')[1].trigger('click')
  await input(wrapper, 'Soignant ayant validé').get('select').setValue(PRACTITIONERS[2].id)
  await wrapper.get('textarea').setValue('  À jeun ')

  await wrapper.get('form').trigger('submit')
  await flushPromises()

  expect(sentTo('POST', /\/api\/appointments$/)).toEqual([
    {
      patient_id: 3,
      activity_definition_id: CARE_TYPES[1].id,
      prescribed_on: '2026-10-23',
      time_constraint: 'WEAK',
      scheduled_start: '2026-10-23T13:00:00',
      scheduled_end: '2026-10-23T15:00:00',
      performer_ids: [PRACTITIONERS[0].id],
      validated_by_id: PRACTITIONERS[2].id,
      note: 'À jeun',
    },
  ])
  expect(wrapper.emitted('saved')[0]).toEqual([created])
})

it('edits a care: prefilled, patient fixed, saved with PUT', async () => {
  const care = appointment(9, LEA, '2026-10-20T09:30:00', { performers: [PRACTITIONERS[1]] })
  mockBackend([['PUT', /\/api\/appointments\/9$/, 200, care]])
  const wrapper = mount(CareFormView, { props: { today: TODAY, appointment: care } })
  await flushPromises()

  expect(wrapper.get('h1').text()).toBe('Modifier le soin')
  expect(wrapper.text()).not.toContain('Changer de patient')
  expect(input(wrapper, 'Heure précise').get('input').element.value).toBe('09:30')
  expect(wrapper.findAll('.chip').map((c) => c.text())).toEqual(['Alice Merveille'])

  await input(wrapper, 'Heure précise').get('input').setValue('10:00')
  await wrapper.get('form').trigger('submit')
  await flushPromises()

  const [body] = sentTo('PUT', /\/api\/appointments\/9$/)
  expect(body).toMatchObject({ scheduled_start: '2026-10-20T10:00:00', status: 'PLANNED' })
  expect(body.patient_id).toBeUndefined()
})
