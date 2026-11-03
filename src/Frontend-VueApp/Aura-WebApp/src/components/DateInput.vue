<script setup>
import { ref, useTemplateRef, watch } from 'vue'
import AppIcon from './AppIcon.vue'

// A date field that always shows JJ/MM/AAAA. A native <input type="date"> follows the
// browser's language instead (mm/dd/yyyy in an English browser).
// v-model is the ISO date "YYYY-MM-DD", or '' while the field is empty or incomplete.
defineOptions({ inheritAttrs: false }) // attributes (aria-label…) go to the text field
const model = defineModel({ type: String, default: '' })
const props = defineProps({
  min: { type: String, default: '' }, // ISO, limits the calendar
  disabled: { type: Boolean, default: false },
  required: { type: Boolean, default: false },
})

// "1990-11-06" -> "06/11/1990"
const toDisplay = (iso) => (iso ? iso.split('-').reverse().join('/') : '')

// keeps the digits and adds the slashes as they are typed: "061119" -> "06/11/19"
function mask(raw) {
  const digits = raw.replace(/\D/g, '').slice(0, 8)
  return [digits.slice(0, 2), digits.slice(2, 4), digits.slice(4)].filter(Boolean).join('/')
}

// "06/11/1990" -> "1990-11-06", or '' if it is not a real date (31/02, 13th month…)
function parse(text) {
  const match = /^(\d{2})\/(\d{2})\/(\d{4})$/.exec(text)
  if (!match) return ''
  const [, day, month, year] = match
  const date = new Date(Number(year), Number(month) - 1, Number(day))
  const real = date.getDate() === Number(day) && date.getMonth() === Number(month) - 1
  return real ? `${year}-${month}-${day}` : ''
}

const text = ref(toDisplay(model.value))
const invalid = ref(false)

// a value set from outside (form reset, calendar) replaces what is shown
watch(model, (iso) => {
  if (iso !== parse(text.value)) text.value = toDisplay(iso)
})

function onInput(event) {
  text.value = mask(event.target.value)
  event.target.value = text.value
  invalid.value = false
  model.value = parse(text.value)
}

// only flag it once the user leaves the field, not while they are typing
function onBlur() {
  invalid.value = text.value !== '' && parse(text.value) === ''
}

// the calendar is the browser's own date picker, on a hidden native field
const picker = useTemplateRef('picker')
function openCalendar() {
  try {
    picker.value.showPicker()
  } catch {
    picker.value.focus() // browsers without showPicker()
  }
}
function onPick(event) {
  model.value = event.target.value
  text.value = toDisplay(event.target.value)
  invalid.value = false
}
</script>

<template>
  <div class="date-input" :class="{ invalid }">
    <input
      v-bind="$attrs"
      :value="text"
      class="input"
      placeholder="JJ/MM/AAAA"
      inputmode="numeric"
      maxlength="10"
      autocomplete="off"
      :disabled="disabled"
      :required="required"
      :aria-invalid="invalid"
      @input="onInput"
      @blur="onBlur"
    />
    <button
      type="button"
      class="calendar-button"
      aria-label="Ouvrir le calendrier"
      :disabled="disabled"
      @click="openCalendar"
    >
      <AppIcon name="calendar" :size="18" />
    </button>
    <input
      ref="picker"
      type="date"
      class="native-picker"
      tabindex="-1"
      aria-hidden="true"
      :value="model"
      :min="props.min || undefined"
      @change="onPick"
    />
    <span v-if="invalid" class="error-text">Date invalide (JJ/MM/AAAA)</span>
  </div>
</template>

<style scoped>
.date-input {
  position: relative;
}

.input {
  padding-right: 44px;
}

.invalid .input {
  border-color: var(--color-danger);
}

.calendar-button {
  position: absolute;
  top: 0;
  right: 0;
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  border: none;
  background: transparent;
  color: var(--color-text-muted);
  cursor: pointer;
}

.calendar-button:hover:not(:disabled) {
  color: var(--color-primary);
}

.calendar-button:disabled {
  cursor: not-allowed;
}

/* kept in the page (showPicker needs a rendered field) but invisible, under the text field
   so the browser opens its calendar at the right place */
.native-picker {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 1px;
  height: 1px;
  padding: 0;
  border: 0;
  opacity: 0;
  pointer-events: none;
}

.error-text {
  display: block;
  margin-top: 4px;
  color: var(--color-danger);
  font-size: 12px;
}
</style>
