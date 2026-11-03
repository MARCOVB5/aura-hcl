<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import AppIcon from '../components/AppIcon.vue'
import { listAppointments, listPatientHospitalizations } from '../api.js'
import { isCurrentUser } from '../currentUser.js'
import {
  TIME_CONSTRAINTS,
  dayKey,
  formatDate,
  formatTime,
  labelOf,
  patientName,
  practitionerName,
  stayEnd,
} from '../format.js'

const props = defineProps({
  // sidebar "Calendriers": the department's care / the user's own care
  showService: { type: Boolean, default: true },
  showMine: { type: Boolean, default: true },
  // sidebar "Du patient sélectionné": only this patient's care, and their stays
  patientFilter: { type: Object, default: null },
  // current date, injectable for tests
  today: { type: Date, default: () => new Date() },
})
const emit = defineEmits(['plan-care', 'edit-care'])

const WEEKDAYS = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']
const firstOfMonth = (d) => new Date(d.getFullYear(), d.getMonth(), 1)

const todayKey = dayKey(props.today)
const month = ref(firstOfMonth(props.today))
const appointments = ref([])
const stays = ref([])
const loading = ref(true)
const error = ref('')
const opened = ref(null)

const monthTitle = computed(() => {
  const title = new Intl.DateTimeFormat('fr-FR', { month: 'long', year: 'numeric' }).format(
    month.value,
  )
  return title[0].toUpperCase() + title.slice(1)
})

function shiftMonth(delta) {
  month.value = new Date(month.value.getFullYear(), month.value.getMonth() + delta, 1)
}

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

// care of every day on screen, and the selected patient's stays
async function load() {
  loading.value = true
  error.value = ''
  const days = weeks.value.flat()
  try {
    const [care, patientStays] = await Promise.all([
      listAppointments({ start: days[0].key, end: days.at(-1).key }),
      props.patientFilter ? listPatientHospitalizations(props.patientFilter.id) : [],
    ])
    appointments.value = care
    stays.value = patientStays.map((h) => h.encounter)
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
onMounted(load)
watch([month, () => props.patientFilter?.id], load)

// ---- care events ----

const performerLine = (a) => {
  const [first, ...others] = a.performers
  if (!first) return ''
  return practitionerName(first) + (others.length ? ` +${others.length}` : '')
}
const timeLine = (a) =>
  a.time_constraint === 'WEAK'
    ? `${formatTime(a.scheduled_start)}–${formatTime(a.scheduled_end)}`
    : formatTime(a.scheduled_start)

// "patient" (patient view), "mine" (the user is in charge) or "service" (everyone else's)
const events = computed(() =>
  appointments.value
    .map((a) => {
      let kind
      if (props.patientFilter) {
        if (a.patient.id !== props.patientFilter.id) return null
        kind = 'patient'
      } else {
        kind = a.performers.some(isCurrentUser) ? 'mine' : 'service'
        if ((kind === 'mine' && !props.showMine) || (kind === 'service' && !props.showService))
          return null
      }
      return {
        id: a.id,
        kind,
        day: a.scheduled_start.slice(0, 10),
        title: a.activity_definition.name,
        subtitle: [timeLine(a), performerLine(a)].filter(Boolean).join(' · '),
        appointment: a,
      }
    })
    .filter(Boolean),
)

const eventsByDay = computed(() => {
  const byDay = {}
  for (const event of events.value) (byDay[event.day] ??= []).push(event)
  return byDay
})

// ---- stays of the selected patient: a bar across the days of each week ----

function stayLabel(stay) {
  const start = formatDate(stay.admission_date.slice(0, 10))
  const end = stayEnd(stay)
  const period = end
    ? `du ${start} au ${formatDate(end.slice(0, 10))}`
    : `en cours depuis le ${start}`
  return [`Séjour ${period}`, stay.current_location?.name].filter(Boolean).join(' · ')
}

function bandsOf(week) {
  return stays.value
    .map((stay) => {
      const start = stay.admission_date.slice(0, 10)
      const end = stayEnd(stay)?.slice(0, 10) ?? '9999-12-31' // still in progress
      const first = week.findIndex((d) => d.key >= start)
      const last = week.findLastIndex((d) => d.key <= end)
      if (first === -1 || last === -1 || first > last) return null
      return { id: stay.id, first, last, label: stayLabel(stay) }
    })
    .filter(Boolean)
}

// ---- detail card ----

function onKeydown(event) {
  if (event.key === 'Escape') opened.value = null
}
onMounted(() => window.addEventListener('keydown', onKeydown))
onUnmounted(() => window.removeEventListener('keydown', onKeydown))

function whenLong(a) {
  const date = new Date(a.scheduled_start)
  const weekday = new Intl.DateTimeFormat('fr-FR', { weekday: 'long' }).format(date)
  const day = formatDate(a.scheduled_start.slice(0, 10))
  const time =
    a.time_constraint === 'WEAK'
      ? `de ${formatTime(a.scheduled_start)} à ${formatTime(a.scheduled_end)}`
      : `à ${formatTime(a.scheduled_start)}`
  return `${weekday[0].toUpperCase()}${weekday.slice(1)} ${day} ${time}`
}
</script>

<template>
  <header class="page-header">
    <div class="heading">
      <h2 class="service-name">Service de réanimation</h2>
      <button type="button" class="btn btn-primary btn-header" @click="emit('plan-care')">
        <AppIcon name="plus" :size="16" />
        Planifier un soin
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
      <div v-if="!patientFilter" class="legend">
        <span class="legend-item"><i class="swatch mine"></i>Mes soins</span>
        <span class="legend-item"><i class="swatch service"></i>Soins du service</span>
      </div>
    </div>
  </header>

  <div v-if="patientFilter" class="patient-bar">
    <span>
      <strong>{{ patientName(patientFilter) || 'Patient sous X' }}</strong>
      <span class="muted"> · {{ patientFilter.ipp || 'IPP non renseigné' }}</span>
    </span>
    <span class="legend">
      <span class="legend-item"><i class="swatch patient"></i>Soins du patient</span>
      <span class="legend-item"><i class="swatch stay"></i>Séjour du patient</span>
    </span>
  </div>

  <div v-if="error" class="notice notice-error error" role="alert">
    <AppIcon name="alert-circle" :size="16" />
    <span>{{ error }}</span>
    <button type="button" class="btn btn-small retry" @click="load">Réessayer</button>
  </div>

  <div class="calendar" :class="{ loading }" :aria-busy="loading">
    <div class="weekdays">
      <div v-for="day in WEEKDAYS" :key="day" class="weekday">{{ day }}</div>
    </div>
    <div
      v-for="week in weeks"
      :key="week[0].key"
      class="week"
      :class="{ 'has-band': bandsOf(week).length }"
    >
      <div
        v-for="band in bandsOf(week)"
        :key="band.id"
        class="stay-band"
        :data-first-day="band.first"
        :data-days="band.last - band.first + 1"
        :style="{
          left: `calc(${band.first} * 100% / 7 + 6px)`,
          width: `calc(${band.last - band.first + 1} * 100% / 7 - 12px)`,
        }"
        :title="band.label"
      >
        {{ band.label }}
      </div>
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
          @click="opened = event.appointment"
        >
          <span class="event-title">{{ event.title }}</span>
          <span class="event-time">{{ event.subtitle }}</span>
        </button>
      </div>
    </div>
  </div>

  <div v-if="opened" class="overlay" @click.self="opened = null">
    <section
      class="detail"
      :class="{ patient: patientFilter }"
      role="dialog"
      aria-modal="true"
      :aria-label="opened.activity_definition.name"
    >
      <button type="button" class="icon-btn close" aria-label="Fermer" @click="opened = null">
        <AppIcon name="x" :size="18" />
      </button>
      <h2 class="detail-title">{{ opened.activity_definition.name }}</h2>
      <p class="detail-time">{{ whenLong(opened) }}</p>
      <p class="detail-patient">
        <span class="muted">Patient&nbsp;: </span>
        <strong>{{ patientName(opened.patient) || 'Patient sous X' }}</strong>
        <span v-if="opened.patient.ipp" class="muted"> · {{ opened.patient.ipp }}</span>
      </p>
      <p v-if="opened.encounter.current_location">{{ opened.encounter.current_location.name }}</p>
      <p v-if="opened.patient.allergies.length" class="allergy">
        Allergies : {{ opened.patient.allergies.map((a) => a.name).join(', ') }}
      </p>
      <hr />
      <p>
        <span class="muted">Soignant en charge&nbsp;: </span>
        <strong>{{ opened.performers.map(practitionerName).join(', ') || 'Non renseigné' }}</strong>
      </p>
      <p class="muted">
        Prescrit par&nbsp;: {{ practitionerName(opened.validated_by) || 'Non renseigné' }}
      </p>
      <p class="muted">Contrainte&nbsp;: {{ labelOf(TIME_CONSTRAINTS, opened.time_constraint) }}</p>
      <dl>
        <dt>Objet</dt>
        <dd>{{ opened.activity_definition.name }}</dd>
        <dt>Notes</dt>
        <dd>{{ opened.note || 'Aucune note.' }}</dd>
      </dl>
      <button type="button" class="btn btn-primary" @click="emit('edit-care', opened)">
        Modifier
      </button>
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
}

.legend {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 16px;
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
  border: 1px solid;
  border-left-width: 3px;
  border-radius: 3px;
}

.patient-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 32px;
  border-top: 1px solid var(--color-border);
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

.week {
  position: relative;
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

/* room for the stay bar under the day numbers */
.has-band .day-number {
  margin-bottom: 30px;
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

.stay-band {
  position: absolute;
  top: 44px;
  z-index: 1;
  overflow: hidden;
  padding: 4px 10px;
  border: 1px solid var(--color-border-strong);
  border-radius: 4px;
  background: var(--color-surface-muted);
  font-size: 12px;
  white-space: nowrap;
  text-overflow: ellipsis;
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

/* the care type wraps on two lines at most, so narrow columns still show it */
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

.event.mine,
.swatch.mine {
  border-color: var(--color-primary);
  background: var(--color-primary-soft);
  color: var(--color-primary);
}

.event.service,
.swatch.service {
  border-color: #a9acb4;
  background: var(--color-avatar);
  color: var(--color-primary);
}

.event.service .event-time {
  color: var(--color-text-muted);
}

.event.patient,
.swatch.patient {
  border-color: var(--color-patient);
  background: var(--color-patient-soft);
  color: var(--color-patient);
}

.swatch.stay {
  width: 22px;
  border-width: 1px;
  border-color: var(--color-border-strong);
  background: var(--color-surface-muted);
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
  width: 440px;
  max-width: 100%;
  max-height: calc(100vh - 32px);
  overflow: auto;
  padding: 24px;
  border-left: 4px solid var(--color-primary);
  border-radius: var(--radius-card);
  background: var(--color-surface-muted);
  box-shadow: 0 10px 30px rgb(0 0 0 / 20%);
}

.detail.patient {
  border-left-color: var(--color-patient);
}

.close {
  position: absolute;
  top: 12px;
  right: 12px;
}

.detail p {
  margin: 0 0 6px;
}

.detail-title {
  margin: 0 0 6px;
  color: var(--color-primary);
  font-size: 22px;
  font-weight: 600;
}

.detail.patient .detail-title {
  color: var(--color-patient);
}

.detail-time {
  font-size: 15px;
}

.detail-patient {
  font-size: 15px;
}

hr {
  margin: 14px 0;
  border: none;
  border-top: 1px solid var(--color-border-strong);
}

dl {
  margin: 14px 0 18px;
}

dt {
  margin-top: 10px;
  color: var(--color-text-muted);
}

dd {
  margin: 4px 0 0;
  white-space: pre-line;
}
</style>
