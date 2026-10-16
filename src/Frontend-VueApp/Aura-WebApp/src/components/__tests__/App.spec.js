import { expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import App from '../../App.vue'

it('shows the app heading', () => {
  const wrapper = mount(App)

  expect(wrapper.get('h1').text()).toBe('My Vue App')
})