<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import AppIcon from '../components/AppIcon.vue'
import { listHospitalizations } from '../api.js'
import { STAY_STATUSES, STAY_TYPES, formatDateTime, labelOf, patientName } from '../format.js'

const props = defineProps({
  // sidebar "Du patient sélectionné": only show this patient's stays
  patientFilter: { type: Object, default: null },
  // current date, injectable for tests
  today: { type: Date, default: () => new Date() },
})
const emit = defineEmits(['new-admission'])

const WEEKDAYS = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']
const pad = (n) => String(n).padStart(2, '0')
// local date as "YYYY-MM-DD", the same format as the start of the backend's datetimes
const dayKey = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
const firstOfMonth = (d) => new Date(d.getFullYear(), d.getMonth(), 1)

const todayKey = dayKey(props.today)
const month = ref(firstOfMonth(props.today))
const hospitalizations = ref([])
const loading = ref(true)
const error = ref('')
const openedEvent = ref(null)

async function load() {
  loading.value = true
  error.value = ''
  try {
    hospitalizations.value = await listHospitalizations()
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
onMounted(load)

const monthTitle = computed(() => {
  const title = new Intl.DateTimeFormat('fr-FR', { month: 'long', year: 'numeric' }).format(
    month.value,
  )
  return title[0].toUpperCase() + title.slice(1)
})

function shiftMonth(delta) {
  month.value = new Date(month.value.getFullYear(), month.value.getMonth() + delta, 1)
}

// one event per admission, expected discharge and actual discharge of each stay
const EVENT_LABELS = { admission: 'Admission', expected: 'Sortie prévue', discharge: 'Sortie' }
const events = computed(() => {
  const list = []
  for (const hospitalization of hospitalizations.value) {
    const encounter = hospitalization.encounter
    if (props.patientFilter && encounter.patient_id !== props.patientFilter.id) continue
    const dates = {
      admission: encounter.admission_date,
      expected: encounter.expected_discharge_date,
      discharge: encounter.actual_discharge_date,
    }
    for (const [kind, at] of Object.entries(dates)) {
      if (!at) continue
      list.push({
        id: `${hospitalization.encounter_id}-${kind}`,
        kind,
        label: EVENT_LABELS[kind],
        name: patientName(encounter.patient) || 'Patient sous X',
        day: at.slice(0, 10),
        time: at.slice(11, 16),
        hospitalization,
      })
    }
  }
  return list.sort((a, b) => `${a.day}${a.time}`.localeCompare(`${b.day}${b.time}`))
})

const eventsByDay = computed(() => {
  const byDay = {}
  for (const event of events.value) (byDay[event.day] ??= []).push(event)
  return byDay
})

// weeks shown for the month, Monday first, with the days of the months around it
const weeks = computed(() => {
  const first = month.value
  const cursor = new Date(first)
  cursor.setDate(1 - ((first.getDay() + 6) % 7))
  const result = []
  do {
    const week = []
    for (let i = 0; i < 7; i++) {
      week.push({
        key: dayKey(cursor),
        number: cursor.getDate(),
        inMonth: cursor.getMonth() === first.getMonth(),
        weekend: i >= 5,
      })
      cursor.setDate(cursor.getDate() + 1)
    }
    result.push(week)
  } while (cursor.getMonth() === first.getMonth())
  return result
})

const monthAdmissions = computed(() => {
  const prefix = dayKey(month.value).slice(0, 7)
  return events.value.filter((e) => e.kind === 'admission' && e.day.startsWith(prefix)).length
})

function onKeydown(event) {
  if (event.key === 'Escape') openedEvent.value = null
}
onMounted(() => window.addEventListener('keydown', onKeydown))
onUnmounted(() => window.removeEventListener('keydown', onKeydown))

const opened = computed(() => {
  if (!openedEvent.value) return null
  const encounter = openedEvent.value.hospitalization.encounter
  return { event: openedEvent.value, encounter, patient: encounter.patient }
})
</script>

<template>
  <header class="page-header">
    <div class="heading">
      <h2 class="service-name">Service de réanimation</h2>
      <button type="button" class="btn btn-primary btn-header" @click="emit('new-admission')">
        <AppIcon name="plus" :size="16" />
        Nouvelle admission
      </button>
    </div>
    <div class="date-controls">
      <div class="month-navigation">
        <h1 class="month-title">{{ monthTitle }}</h1>
        <div class="arrows">
          <button
            type="button"
            class="icon-btn"
            aria-label="Mois précédent"
            @click="shiftMonth(-1)"
          >
            <AppIcon name="chevron-left" :size="17" />
          </button>
          <button type="button" class="icon-btn" aria-label="Mois suivant" @click="shiftMonth(1)">
            <AppIcon name="chevron-right" :size="17" />
          </button>
        </div>
        <button type="button" class="btn btn-today" @click="month = firstOfMonth(today)">
          Aujourd’hui
        </button>
      </div>
      <div class="legend">
        <span v-if="patientFilter" class="filter">
          Séjours de {{ patientName(patientFilter) || 'Patient sous X' }}
        </span>
        <span class="muted">
          {{ monthAdmissions }} admission{{ monthAdmissions > 1 ? 's' : '' }} ce mois-ci
        </span>
        <span class="legend-item"><i class="swatch admission"></i>Admission</span>
        <span class="legend-item"><i class="swatch expected"></i>Sortie prévue</span>
      </div>
    </div>
  </header>

  <div v-if="error" class="notice notice-error error" role="alert">
    <AppIcon name="alert-circle" :size="16" />
    <span>{{ error }}</span>
    <button type="button" class="btn btn-small retry" @click="load">Réessayer</button>
  </div>

  <div class="calendar" :class="{ loading }" :aria-busy="loading">
    <div class="weekdays">
      <div v-for="day in WEEKDAYS" :key="day" class="weekday">{{ day }}</div>
    </div>
    <div v-for="week in weeks" :key="week[0].key" class="week">
      <div
        v-for="day in week"
        :key="day.key"
        class="day"
        :class="{ shaded: !day.inMonth || day.weekend, 'other-month': !day.inMonth }"
        :data-day="day.key"
      >
        <span class="day-number" :class="{ today: day.key === todayKey }">{{ day.number }}</span>
        <button
          v-for="event in eventsByDay[day.key] ?? []"
          :key="event.id"
          type="button"
          class="event"
          :class="event.kind"
          @click="openedEvent = event"
        >
          <span class="event-title">{{ event.name }}</span>
          <span class="event-time">{{ event.time }} · {{ event.label }}</span>
        </button>
      </div>
    </div>
  </div>

  <div v-if="opened" class="overlay" @click.self="openedEvent = null">
    <section class="detail" role="dialog" aria-modal="true" :aria-label="opened.event.label">
      <button type="button" class="icon-btn close" aria-label="Fermer" @click="openedEvent = null">
        <AppIcon name="x" :size="18" />
      </button>
      <h2 class="detail-title">{{ opened.event.label }}</h2>
      <p class="detail-time">
        {{ formatDateTime(`${opened.event.day}T${opened.event.time}`) }}
      </p>
      <p class="detail-patient">
        <span class="muted">Patient&nbsp;: </span>
        <strong>{{ opened.event.name }}</strong>
        <span v-if="opened.patient.ipp" class="muted"> · {{ opened.patient.ipp }}</span>
      </p>
      <p v-if="opened.patient.allergies.length" class="allergy">
        Allergies : {{ opened.patient.allergies.map((a) => a.name).join(', ') }}
      </p>
      <hr />
      <dl>
        <div>
          <dt>Séjour n°</dt>
          <dd>{{ opened.encounter.stay_number }}</dd>
        </div>
        <div>
          <dt>Type</dt>
          <dd>{{ labelOf(STAY_TYPES, opened.encounter.encounter_type_code) }}</dd>
        </div>
        <div>
          <dt>Statut</dt>
          <dd>{{ labelOf(STAY_STATUSES, opened.encounter.status) }}</dd>
        </div>
        <div>
          <dt>Admission</dt>
          <dd>{{ formatDateTime(opened.encounter.admission_date) }}</dd>
        </div>
        <div v-if="opened.encounter.expected_discharge_date">
          <dt>Sortie prévue</dt>
          <dd>{{ formatDateTime(opened.encounter.expected_discharge_date) }}</dd>
        </div>
        <div>
          <dt>Motif</dt>
          <dd>{{ opened.encounter.reason || '—' }}</dd>
        </div>
      </dl>
    </section>
  </div>
</template>

<style scoped>
.heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.btn-header {
  height: 36px;
  padding: 0 12px;
  font-weight: 500;
}

.date-controls {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  min-height: 88px;
}

.month-navigation {
  display: flex;
  align-items: center;
  gap: 24px;
}

.month-title {
  min-width: 190px;
  margin: 0;
  font-size: 26px;
  font-weight: 600;
  letter-spacing: -0.8px;
}

.arrows {
  display: flex;
  gap: 12px;
}

.icon-btn {
  display: grid;
  place-items: center;
  padding: 4px;
  border: none;
  border-radius: var(--radius);
  background: transparent;
  color: var(--color-text-muted);
  cursor: pointer;
}

.icon-btn:hover {
  background: var(--color-primary-soft);
  color: var(--color-primary);
}

.btn-today {
  height: 36px;
  color: var(--color-text);
}

.legend {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 16px;
}

.filter {
  padding: 4px 10px;
  border-radius: 100px;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-weight: 500;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--color-text-muted);
}

.swatch {
  width: 12px;
  height: 12px;
  border-radius: 3px;
}

.error {
  margin: 0 32px 16px;
}

.retry {
  margin-left: auto;
}

.calendar.loading {
  opacity: 0.5;
}

.weekdays,
.week {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
}

.weekdays {
  border-top: 1px solid var(--color-border);
  border-bottom: 1px solid var(--color-border);
}

.weekday {
  padding: 14px 16px;
  color: var(--color-text-muted);
  font-size: 12px;
  font-weight: 500;
}

.day {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 0;
  min-height: 150px;
  padding: 10px 8px;
  border-right: 1px solid var(--color-border);
  border-bottom: 1px solid var(--color-border);
  background: #fff;
}

.day:last-child {
  border-right: none;
}

/* weekends and days of the months around: light grey, like the design */
.day.shaded {
  background: var(--color-table-header);
}

.day-number {
  display: grid;
  place-items: center;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  font-size: 12px;
}

.other-month .day-number {
  color: #a9acb4;
}

.day-number.today {
  background: var(--color-primary);
  color: #fff;
  font-weight: 600;
}

.event {
  display: flex;
  flex-direction: column;
  gap: 3px;
  width: 100%;
  padding: 6px 8px;
  border: 1px solid;
  border-left-width: 3px;
  border-radius: 4px;
  overflow: hidden;
  text-align: left;
  cursor: pointer;
}

/* the patient's name wraps on two lines at most, so narrow columns still show it */
.event-title {
  display: -webkit-box;
  overflow: hidden;
  font-size: 12px;
  font-weight: 500;
  overflow-wrap: break-word;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  line-clamp: 2;
}

.event-time {
  max-width: 100%;
  font-size: 11px;
  overflow-wrap: break-word;
}

.event.admission,
.swatch.admission {
  border-color: var(--color-primary);
  background: var(--color-primary-soft);
  color: var(--color-primary);
}

.event.expected,
.event.discharge,
.swatch.expected {
  border-color: #a9acb4;
  background: var(--color-avatar);
  color: var(--color-primary);
}

.event.expected .event-time,
.event.discharge .event-time {
  color: var(--color-text-muted);
}

.swatch {
  border: 1px solid;
  border-left-width: 3px;
}

.event:hover {
  filter: brightness(0.97);
}

.overlay {
  position: fixed;
  inset: 0;
  z-index: 10;
  display: grid;
  place-items: center;
  padding: 16px;
  background: rgb(39 41 47 / 35%);
}

.detail {
  position: relative;
  width: 420px;
  max-width: 100%;
  padding: 24px;
  border-left: 4px solid var(--color-primary);
  border-radius: var(--radius-card);
  background: var(--color-surface-muted);
  box-shadow: 0 10px 30px rgb(0 0 0 / 20%);
}

.close {
  position: absolute;
  top: 12px;
  right: 12px;
}

.detail p {
  margin: 0 0 8px;
}

.detail-title {
  margin: 0 0 8px;
  color: var(--color-primary);
  font-size: 22px;
  font-weight: 600;
}

.detail-time {
  color: var(--color-text-muted);
  font-size: 15px;
}

.detail-patient {
  font-size: 15px;
}

hr {
  margin: 16px 0;
  border: none;
  border-top: 1px solid var(--color-border-strong);
}

dl {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin: 0;
}

dl div {
  display: flex;
  gap: 8px;
}

dt {
  min-width: 110px;
  color: var(--color-text-muted);
}

dd {
  margin: 0;
  font-weight: 500;
}
</style>
