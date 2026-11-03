<script setup>
import { ref, watch } from 'vue'
import DateInput from './DateInput.vue'
import TimeInput from './TimeInput.vue'

// A date (JJ/MM/AAAA) and a 24-hour time side by side.
// v-model is "YYYY-MM-DDTHH:MM" once both are filled, '' otherwise.
const model = defineModel({ type: String, default: '' })
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
</script>

<template>
  <div class="datetime-input">
    <DateInput
      v-model="date"
      :min="min.slice(0, 10)"
      :required="required"
      :aria-label="label ? `${label} : date` : undefined"
    />
    <TimeInput
      v-model="time"
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
