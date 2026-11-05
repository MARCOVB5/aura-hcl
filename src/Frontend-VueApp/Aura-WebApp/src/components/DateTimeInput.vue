<script setup>
import { ref, watch } from 'vue'
import DateInput from './DateInput.vue'
import TimeInput from './TimeInput.vue'

// A date (JJ/MM/AAAA) and a 24-hour time side by side.
// v-model is "YYYY-MM-DDTHH:MM" once both are filled, '' otherwise.
// v-model:incomplete is true when something is typed but the value is not complete
// (a date without its time, a half-typed date…): the form must not take it as empty.
const model = defineModel({ type: String, default: '' })
const incomplete = defineModel('incomplete', { type: Boolean, default: false })
defineProps({
  min: { type: String, default: '' }, // ISO date or datetime: only its date limits the calendar
  required: { type: Boolean, default: false },
  label: { type: String, default: '' }, // for the screen-reader names of the two fields
})

const date = ref(model.value.slice(0, 10))
const time = ref(model.value.slice(11, 16))

watch(model, (value) => {
  if (value === combined()) return
  date.value = value.slice(0, 10)
  time.value = value.slice(11, 16)
})

const combined = () => (date.value && time.value ? `${date.value}T${time.value}` : '')
watch([date, time], () => (model.value = combined()))

const dateFilled = ref(false)
const timeFilled = ref(false)
watch(
  [dateFilled, timeFilled, model],
  () => (incomplete.value = (dateFilled.value || timeFilled.value) && model.value === ''),
)
</script>

<template>
  <div class="datetime-input">
    <DateInput
      v-model="date"
      v-model:filled="dateFilled"
      :min="min.slice(0, 10)"
      :required="required"
      :aria-label="label ? `${label} : date` : undefined"
    />
    <TimeInput
      v-model="time"
      v-model:filled="timeFilled"
      :required="required"
      :aria-label="label ? `${label} : heure` : undefined"
    />
  </div>
</template>

<style scoped>
.datetime-input {
  display: grid;
  grid-template-columns: 1fr 120px;
  gap: 8px;
}
</style>
