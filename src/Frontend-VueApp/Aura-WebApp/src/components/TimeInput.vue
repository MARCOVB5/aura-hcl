<script setup>
import { ref, watch } from 'vue'
import AppIcon from './AppIcon.vue'

// A 24-hour time field (HH:MM). A native <input type="time"> follows the browser's
// language instead (AM/PM in an English browser).
// v-model is "HH:MM", or '' while the field is empty or incomplete.
defineOptions({ inheritAttrs: false }) // attributes (aria-label…) go to the text field
const model = defineModel({ type: String, default: '' })
defineProps({
  disabled: { type: Boolean, default: false },
  required: { type: Boolean, default: false },
})

// keeps the digits and adds the colon as they are typed: "0930" -> "09:30"
function mask(raw) {
  const digits = raw.replace(/\D/g, '').slice(0, 4)
  return digits.length > 2 ? `${digits.slice(0, 2)}:${digits.slice(2)}` : digits
}

// "09:30" -> "09:30", or '' if it is not a real time (25:00, 10:75…)
function parse(text) {
  const match = /^(\d{2}):(\d{2})$/.exec(text)
  if (!match) return ''
  return Number(match[1]) < 24 && Number(match[2]) < 60 ? text : ''
}

const text = ref(model.value)
const invalid = ref(false)

watch(model, (value) => {
  if (value !== parse(text.value)) text.value = value
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
</script>

<template>
  <div class="time-input" :class="{ invalid }">
    <input
      v-bind="$attrs"
      :value="text"
      class="input"
      placeholder="HH:MM"
      inputmode="numeric"
      maxlength="5"
      autocomplete="off"
      :disabled="disabled"
      :required="required"
      :aria-invalid="invalid"
      @input="onInput"
      @blur="onBlur"
    />
    <AppIcon name="clock" :size="18" class="clock" />
    <span v-if="invalid" class="error-text">Heure invalide (HH:MM, de 00:00 à 23:59)</span>
  </div>
</template>

<style scoped>
.time-input {
  position: relative;
}

.input {
  padding-right: 44px;
}

.invalid .input {
  border-color: var(--color-danger);
}

.clock {
  position: absolute;
  top: 13px;
  right: 13px;
  color: var(--color-text-muted);
  pointer-events: none;
}

.error-text {
  display: block;
  margin-top: 4px;
  color: var(--color-danger);
  font-size: 12px;
}
</style>
