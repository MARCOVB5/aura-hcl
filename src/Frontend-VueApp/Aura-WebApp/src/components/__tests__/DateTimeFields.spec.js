import { expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import DateInput from '../DateInput.vue'
import DateTimeInput from '../DateTimeInput.vue'
import TimeInput from '../TimeInput.vue'

// mounts a field with a working v-model, like a parent component would
function withModel(component, modelValue = '', props = {}) {
  const wrapper = mount(component, {
    props: {
      modelValue,
      'onUpdate:modelValue': (value) => wrapper.setProps({ modelValue: value }),
      ...props,
    },
  })
  return wrapper
}
const textField = (wrapper) => wrapper.get('input:not([type="date"])')

it('shows a date as JJ/MM/AAAA and gives back an ISO date', async () => {
  const wrapper = withModel(DateInput, '1990-11-06')
  expect(textField(wrapper).element.value).toBe('06/11/1990')

  await textField(wrapper).setValue('2108')
  expect(textField(wrapper).element.value).toBe('21/08') // slashes are added while typing
  expect(wrapper.props('modelValue')).toBe('') // incomplete: no date yet

  await textField(wrapper).setValue('21082026')
  expect(textField(wrapper).element.value).toBe('21/08/2026')
  expect(wrapper.props('modelValue')).toBe('2026-08-21')
})

it('refuses a date that does not exist', async () => {
  const wrapper = withModel(DateInput)

  await textField(wrapper).setValue('31/02/2026')
  expect(wrapper.props('modelValue')).toBe('')
  expect(wrapper.text()).not.toContain('Date invalide') // not while typing
  await textField(wrapper).trigger('blur')
  expect(wrapper.text()).toContain('Date invalide')
})

it('takes the date chosen in the calendar', async () => {
  const wrapper = withModel(DateInput)

  await wrapper.get('input[type="date"]').setValue('2026-10-23')
  expect(wrapper.props('modelValue')).toBe('2026-10-23')
  expect(textField(wrapper).element.value).toBe('23/10/2026')
})

it('updates the text when the value changes from outside', async () => {
  const wrapper = withModel(DateInput, '2026-10-23')
  await wrapper.setProps({ modelValue: '2026-01-05' })
  expect(textField(wrapper).element.value).toBe('05/01/2026')
})

it('uses 24-hour times', async () => {
  const wrapper = withModel(TimeInput)

  await textField(wrapper).setValue('1730')
  expect(textField(wrapper).element.value).toBe('17:30')
  expect(wrapper.props('modelValue')).toBe('17:30')

  await textField(wrapper).setValue('25:00')
  expect(wrapper.props('modelValue')).toBe('')
  await textField(wrapper).trigger('blur')
  expect(wrapper.text()).toContain('Heure invalide')
})

it('combines a date and a time, only once both are filled', async () => {
  const wrapper = withModel(DateTimeInput, '2026-10-23T08:05', { label: 'Admission' })
  const date = wrapper.get('[aria-label="Admission : date"]')
  const time = wrapper.get('[aria-label="Admission : heure"]')
  expect(date.element.value).toBe('23/10/2026')
  expect(time.element.value).toBe('08:05')

  await time.setValue('')
  expect(wrapper.props('modelValue')).toBe('')
  await time.setValue('2215')
  expect(wrapper.props('modelValue')).toBe('2026-10-23T22:15')
})
