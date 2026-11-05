<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import AppIcon from './AppIcon.vue'
import { listAppointments } from '../api.js'
import { careDueAt, careWhen, isLateCare } from '../format.js'

// In the sidebar, under the calendars: what to keep in mind about the selected patient
const props = defineProps({
  patient: { type: Object, required: true },
  // changes when a care is saved: the care are loaded again
  refreshKey: { type: null, default: null },
  // current time, injectable for tests
  now: { type: Date, default: null },
})
const emit = defineEmits(['open-care'])

const appointments = ref([])
const loading = ref(true)
const error = ref('')

let lastLoad = 0
async function load() {
  const current = ++lastLoad // a slower, older answer must not replace a newer one
  loading.value = true
  error.value = ''
  try {
    const found = await listAppointments({ patientId: props.patient.id })
    if (current === lastLoad) appointments.value = found
  } catch (e) {
    if (current === lastLoad) error.value = e.message
  } finally {
    if (current === lastLoad) loading.value = false
  }
}
onMounted(load)
watch(() => props.refreshKey, load)

// a care becomes late while the page is open: the clock is checked every minute
const clock = ref(new Date())
let timer
onMounted(() => (timer = setInterval(() => (clock.value = new Date()), 60_000)))
onUnmounted(() => clearInterval(timer))

const late = computed(() => {
  const now = props.now ?? clock.value
  return appointments.value
    .filter((a) => isLateCare(a, now))
    .sort((a, b) => careDueAt(a) - careDueAt(b))
})

const allergies = computed(() => props.patient.allergies.map((a) => a.name).join(', '))
</script>

<template>
  <section class="patient-info" aria-label="Informations du patient sélectionné">
    <div class="block">
      <h3 class="title">Allergies</h3>
      <p v-if="allergies" class="allergy">{{ allergies }}</p>
      <p v-else class="muted">Aucune allergie renseignée</p>
    </div>

    <div class="block">
      <h3 class="title">
        Soins en retard
        <span v-if="!loading && !error && late.length" class="count">{{ late.length }}</span>
      </h3>
      <p v-if="loading && !appointments.length" class="muted">Chargement…</p>
      <p v-else-if="error" class="error" role="alert">{{ error }}</p>
      <ul v-else-if="late.length" class="late-list">
        <li v-for="a in late" :key="a.id">
          <button type="button" class="late" @click="emit('open-care', a)">
            <AppIcon name="clock" :size="14" />
            <span>
              <strong>{{ a.care_type }}</strong>
              <span class="when">{{ careWhen(a) }}</span>
            </span>
          </button>
        </li>
      </ul>
      <p v-else class="muted">Aucun soin en retard</p>
    </div>
  </section>
</template>

<style scoped>
.patient-info {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-top: 20px;
  padding: 16px 12px 0;
  border-top: 1px solid var(--color-border);
}

.block p {
  margin: 0;
}

.title {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 0 0 6px;
  color: var(--color-text-muted);
  font-size: 13px;
  font-weight: 500;
}

.count {
  padding: 0 6px;
  border-radius: 10px;
  background: var(--color-warning-soft);
  color: var(--color-warning);
  font-size: 12px;
  font-weight: 600;
}

.error {
  color: var(--color-danger);
}

.late-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.late {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  width: 100%;
  padding: 8px;
  border: 1px solid var(--color-warning-border);
  border-radius: var(--radius);
  background: var(--color-warning-soft);
  color: var(--color-warning);
  text-align: left;
  cursor: pointer;
}

.late:hover {
  border-color: var(--color-warning);
}

.late .icon {
  margin-top: 2px;
}

.late strong {
  display: block;
  font-weight: 600;
}

.when {
  font-size: 12px;
}
</style>
