<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import AppIcon from '../components/AppIcon.vue'
import DateInput from '../components/DateInput.vue'
import TimeInput from '../components/TimeInput.vue'
import {
  createAppointment,
  getCurrentHospitalization,
  listPatients,
  listPractitioners,
  updateAppointment,
} from '../api.js'
import {
  TIME_CONSTRAINTS,
  dayKey,
  formatDate,
  formatDateTime,
  formatTime,
  normalize,
  patientDetails,
  patientName,
  practitionerName,
} from '../format.js'

const props = defineProps({
  // patient chosen before opening the form (selected patient, or after creating their stay)
  initialPatient: { type: Object, default: null },
  // edit mode: the care appointment to change (its patient and stay cannot change)
  appointment: { type: Object, default: null },
  // values typed before leaving to create the missing stay
  draft: { type: Object, default: null },
  // current date, injectable for tests
  today: { type: Date, default: () => new Date() },
  // the page the form was opened from
  backLabel: { type: String, default: 'Retour au calendrier' },
})
const emit = defineEmits(['saved', 'cancel', 'create-stay'])

const editing = computed(() => props.appointment !== null)

// ---- reference list ----

const practitioners = ref([])
const error = ref('')
onMounted(async () => {
  try {
    practitioners.value = await listPractitioners()
  } catch (e) {
    error.value = e.message
  }
})

// ---- form ----

function valuesOf(a) {
  const weak = a.time_constraint === 'WEAK'
  return {
    prescribedOn: a.prescribed_on,
    careType: a.care_type,
    constraint: a.time_constraint,
    date: a.scheduled_start.slice(0, 10),
    start: weak ? formatTime(a.scheduled_start) : '',
    end: weak ? formatTime(a.scheduled_end) : '',
    exactTime: weak ? '' : formatTime(a.scheduled_start),
    performerIds: a.performers.map((p) => p.id),
    validatorId: a.validated_by?.id ?? '',
    note: a.note ?? '',
  }
}

const form = reactive({
  prescribedOn: dayKey(props.today),
  careType: '',
  constraint: '', // 'WEAK' (time window) or 'STRONG' (precise time)
  date: dayKey(props.today),
  start: '',
  end: '',
  exactTime: '',
  performerIds: [],
  validatorId: '',
  note: '',
  ...props.draft,
  ...(props.appointment && valuesOf(props.appointment)),
})
const submitting = ref(false)

// ---- patient: search by name, then choose a record ----

const patient = ref(props.appointment?.patient ?? props.initialPatient ?? null)
const search = reactive({ nameFamily: '', nameGiven: '' })
const allPatients = ref(null) // loaded on the first search

const searching = computed(
  () => !patient.value && (search.nameFamily.trim() !== '' || search.nameGiven.trim() !== ''),
)
watch(searching, async (now) => {
  if (!now || allPatients.value !== null) return
  try {
    allPatients.value = await listPatients()
  } catch (e) {
    error.value = e.message
  }
})
const results = computed(() => {
  if (!searching.value || !allPatients.value) return []
  const family = normalize(search.nameFamily.trim())
  const given = normalize(search.nameGiven.trim())
  return allPatients.value.filter(
    (p) =>
      normalize(p.person.name_family).includes(family) &&
      normalize(p.person.name_given).includes(given),
  )
})

function changePatient() {
  patient.value = null
}

// ---- the patient's current stay, attached automatically ----

const stay = ref(props.appointment?.encounter ?? null)
// 'none' (no patient), 'loading', 'found', 'missing' (no current stay)
const stayState = ref(props.appointment ? 'found' : 'none')

watch(
  patient,
  async (p) => {
    if (editing.value) return
    stay.value = null
    if (!p) {
      stayState.value = 'none'
      return
    }
    stayState.value = 'loading'
    try {
      const current = await getCurrentHospitalization(p.id)
      if (patient.value?.id !== p.id) return // another patient was chosen meanwhile
      stay.value = current?.encounter ?? null
      stayState.value = current ? 'found' : 'missing'
    } catch (e) {
      error.value = e.message
      stayState.value = 'none'
    }
  },
  { immediate: true },
)

// ---- validation ----

const windowInvalid = computed(
  () => form.constraint === 'WEAK' && form.start && form.end && form.end <= form.start,
)
const timeFilled = computed(() =>
  form.constraint === 'STRONG'
    ? form.exactTime !== ''
    : form.constraint === 'WEAK' && form.start !== '' && form.end !== '' && !windowInvalid.value,
)
const fieldsFilled = computed(
  () => form.prescribedOn && form.careType.trim() && form.date && timeFilled.value,
)

// the care takes place during its stay: from the admission to the discharge, if there is one
// (same check as the backend). The values are "YYYY-MM-DDTHH:mm": they compare as strings
const outsideStay = computed(() => {
  if (!stay.value || !form.date || !timeFilled.value) return false
  const weak = form.constraint === 'WEAK'
  const first = `${form.date}T${weak ? form.start : form.exactTime}`
  const last = weak ? `${form.date}T${form.end}` : first
  const discharge = stay.value.actual_discharge_date?.slice(0, 16)
  return first < stay.value.admission_date.slice(0, 16) || (discharge && last > discharge)
})
const stayDates = computed(() => {
  if (!stay.value) return ''
  const from = formatDateTime(stay.value.admission_date)
  const to = stay.value.actual_discharge_date
  return to ? `du ${from} au ${formatDateTime(to)}` : `à partir du ${from}`
})

const canSubmit = computed(
  () =>
    patient.value &&
    stayState.value === 'found' &&
    fieldsFilled.value &&
    !outsideStay.value &&
    !submitting.value,
)

// ---- caregivers in charge: chips + a select to add one ----

const adding = ref('')
const remaining = computed(() =>
  practitioners.value.filter((p) => !form.performerIds.includes(p.id)),
)
const practitionerById = (id) => practitioners.value.find((p) => p.id === id)
function addPerformer() {
  if (adding.value !== '') form.performerIds.push(adding.value)
  adding.value = ''
}
function removePerformer(id) {
  form.performerIds = form.performerIds.filter((x) => x !== id)
}
const practitionerLabel = (p) => [practitionerName(p), p.profession].filter(Boolean).join(' · ')

// ---- save ----

async function submit() {
  if (!canSubmit.value) return
  submitting.value = true
  error.value = ''
  const weak = form.constraint === 'WEAK'
  const body = {
    care_type: form.careType.trim(),
    prescribed_on: form.prescribedOn,
    time_constraint: form.constraint,
    scheduled_start: `${form.date}T${weak ? form.start : form.exactTime}:00`,
    scheduled_end: weak ? `${form.date}T${form.end}:00` : null,
    performer_ids: form.performerIds,
    validated_by_id: form.validatorId || null,
    note: form.note.trim() || null,
  }
  try {
    const saved = editing.value
      ? await updateAppointment(props.appointment.id, { ...body, status: props.appointment.status })
      : await createAppointment({ ...body, patient_id: patient.value.id })
    emit('saved', saved)
  } catch (e) {
    error.value = e.message
  } finally {
    submitting.value = false
  }
}

function createStay() {
  emit('create-stay', {
    patient: patient.value,
    draft: { ...form, performerIds: [...form.performerIds] },
  })
}
</script>

<template>
  <header class="page-header">
    <h2 class="service-name">Service de réanimation</h2>
    <div class="title-row">
      <div>
        <h1 class="page-title">{{ editing ? 'Modifier le soin' : 'Planifier un soin' }}</h1>
        <p v-if="editing" class="page-description">
          {{ appointment.care_type }} ·
          {{ patientName(appointment.patient) || 'Patient sous X' }}
        </p>
      </div>
      <button type="button" class="btn btn-small" @click="emit('cancel')">
        {{ backLabel }}
      </button>
    </div>
  </header>

  <div class="page-content">
    <form class="card" novalidate @submit.prevent="submit">
      <div class="card-header">
        <h2 class="card-title">Informations du soin</h2>
      </div>

      <div class="card-body">
        <!-- patient -->
        <div class="field">
          <span class="field-label">Patient *</span>
          <div v-if="patient" class="patient-box">
            <AppIcon name="circle-user" :size="20" class="patient-icon" />
            <div class="patient-info">
              <span class="patient-name">{{ patientName(patient) || 'Patient sous X' }}</span>
              <span class="muted">{{ patientDetails(patient) }}</span>
              <span v-if="patient.allergies.length" class="allergy">
                Allergies : {{ patient.allergies.map((a) => a.name).join(', ') }}
              </span>
            </div>
            <button v-if="!editing" type="button" class="btn btn-small" @click="changePatient">
              Changer de patient
            </button>
          </div>

          <template v-else>
            <div class="row">
              <label class="field">
                <span class="field-label">Nom</span>
                <input v-model="search.nameFamily" class="input" />
              </label>
              <label class="field">
                <span class="field-label">Prénom</span>
                <input v-model="search.nameGiven" class="input" />
              </label>
            </div>
            <template v-if="searching">
              <p class="muted hint">
                {{
                  results.length
                    ? `${results.length} dossier${results.length > 1 ? 's correspondent' : ' correspond'}.`
                    : 'Aucun dossier ne correspond.'
                }}
              </p>
              <div v-for="p in results" :key="p.id" class="patient-box result">
                <AppIcon name="circle-user" :size="20" class="patient-icon" />
                <div class="patient-info">
                  <span class="patient-name">{{ patientName(p) || 'Patient sous X' }}</span>
                  <span class="muted">{{ patientDetails(p) }}</span>
                </div>
                <button type="button" class="btn btn-small" @click="patient = p">
                  Choisir ce patient
                </button>
              </div>
            </template>
          </template>
        </div>

        <!-- current stay -->
        <div
          v-if="stayState !== 'none'"
          class="stay-box"
          :class="{ warning: stayState === 'missing' }"
        >
          <div class="stay-head">
            <strong>Séjour en cours</strong>
          </div>
          <p v-if="stayState === 'loading'" class="muted">Recherche du séjour en cours…</p>
          <p v-else-if="stayState === 'found'">
            <strong>Débuté le {{ formatDate(stay.admission_date.slice(0, 10)) }}</strong>
            <template v-if="stay.location"> · {{ stay.location }}</template>
            <span class="muted"> · Séjour n° {{ stay.stay_number }}</span>
          </p>
          <template v-else>
            <p class="stay-missing">Aucun séjour en cours</p>
            <div class="buttons">
              <button type="button" class="btn btn-small" @click="createStay">
                Créer un séjour pour ce patient
              </button>
              <button type="button" class="btn btn-small" @click="changePatient">
                Retour au choix du patient
              </button>
            </div>
          </template>
        </div>

        <div class="row">
          <label class="field">
            <span class="field-label">Date de prescription *</span>
            <DateInput v-model="form.prescribedOn" required />
          </label>
          <label class="field">
            <span class="field-label">Type de soin *</span>
            <input v-model="form.careType" class="input" maxlength="255" required />
          </label>
        </div>

        <fieldset class="constraint">
          <legend class="field-label">Contrainte sur l’horaire *</legend>
          <div class="constraint-options">
            <label v-for="c in TIME_CONSTRAINTS" :key="c.value" class="inline-option">
              <input v-model="form.constraint" type="radio" :value="c.value" class="radio" />
              {{ c.label }}
            </label>
          </div>
        </fieldset>

        <div class="row" :class="form.constraint === 'STRONG' ? 'row-2' : 'row-3'">
          <label class="field">
            <span class="field-label">Date de réalisation *</span>
            <DateInput v-model="form.date" :min="stay?.admission_date.slice(0, 10)" required />
          </label>
          <label v-if="form.constraint === 'STRONG'" class="field">
            <span class="field-label">Heure précise *</span>
            <TimeInput v-model="form.exactTime" required />
          </label>
          <template v-else>
            <label class="field">
              <span class="field-label">
                Début de la plage{{ form.constraint === 'WEAK' ? ' *' : ' (si faible)' }}
              </span>
              <TimeInput v-model="form.start" :disabled="form.constraint !== 'WEAK'" />
            </label>
            <label class="field">
              <span class="field-label">
                Fin de la plage{{ form.constraint === 'WEAK' ? ' *' : ' (si faible)' }}
              </span>
              <TimeInput v-model="form.end" :disabled="form.constraint !== 'WEAK'" />
            </label>
          </template>
        </div>

        <div class="row">
          <div class="field">
            <span class="field-label">Soignant(s) en charge</span>
            <div class="chips">
              <span v-for="id in form.performerIds" :key="id" class="chip">
                {{ practitionerName(practitionerById(id)) || 'Soignant' }}
                <button
                  type="button"
                  class="chip-remove"
                  :aria-label="`Retirer ${practitionerName(practitionerById(id))}`"
                  @click="removePerformer(id)"
                >
                  <AppIcon name="x" :size="12" />
                </button>
              </span>
              <select
                v-model="adding"
                class="chip-select"
                aria-label="Ajouter un soignant en charge"
                @change="addPerformer"
              >
                <option value="">
                  {{ form.performerIds.length ? 'Ajouter…' : 'Ajouter un ou plusieurs soignants' }}
                </option>
                <option v-for="p in remaining" :key="p.id" :value="p.id">
                  {{ practitionerLabel(p) }}
                </option>
              </select>
            </div>
          </div>
          <label class="field">
            <span class="field-label">Soignant ayant validé la prescription</span>
            <select v-model="form.validatorId" class="input">
              <option value="">Sélectionner un soignant</option>
              <option v-for="p in practitioners" :key="p.id" :value="p.id">
                {{ practitionerLabel(p) }}
              </option>
            </select>
          </label>
        </div>

        <label class="field">
          <span class="field-label">Note sur les conditions de réalisation</span>
          <textarea v-model="form.note" class="input"></textarea>
        </label>

        <div v-if="windowInvalid" class="notice notice-error">
          <AppIcon name="alert-circle" :size="16" />
          La fin de la plage doit être après son début.
        </div>
        <div v-if="outsideStay" class="notice notice-error">
          <AppIcon name="alert-circle" :size="16" />
          Le soin doit avoir lieu pendant le séjour ({{ stayDates }}).
        </div>
        <div v-if="error" class="notice notice-error" role="alert">
          <AppIcon name="alert-circle" :size="16" />
          {{ error }}
        </div>

        <div class="actions">
          <span class="muted">* Champs obligatoires</span>
          <div class="buttons">
            <button type="button" class="btn" @click="emit('cancel')">Annuler</button>
            <button type="submit" class="btn btn-primary" :disabled="!canSubmit">
              {{ submitting ? 'Envoi…' : editing ? 'Enregistrer' : 'Valider' }}
            </button>
          </div>
        </div>
      </div>
    </form>
  </div>
</template>

<style scoped>
.row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.row-3 {
  grid-template-columns: 1fr 1fr 1fr;
}

@media (max-width: 1000px) {
  .row,
  .row-3 {
    grid-template-columns: 1fr;
  }
}

.hint {
  margin: 4px 0 0;
}

.patient-box {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
}

.patient-box.result {
  margin-top: 8px;
}

.patient-icon {
  color: var(--color-primary);
}

.patient-info {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 4px;
}

.patient-info .patient-name {
  font-weight: 600;
}

.stay-box {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 16px 20px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: var(--color-surface-muted);
}

.stay-box p {
  margin: 0;
}

.stay-head {
  display: flex;
  justify-content: space-between;
}

.stay-box.warning {
  border-color: var(--color-warning-border);
  background: var(--color-warning-soft);
  color: var(--color-warning);
}

.stay-missing {
  font-size: 15px;
  font-weight: 600;
}

.constraint {
  margin: 0;
  padding: 0;
  border: none;
}

.constraint legend {
  padding: 0;
  margin-bottom: 10px;
}

.constraint-options {
  display: flex;
  gap: 24px;
}

.inline-option {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.chips {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  min-height: 44px;
  padding: 6px 8px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
}

.chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  border-radius: var(--radius);
  background: var(--color-primary-soft);
  color: var(--color-primary);
}

.chip-remove {
  display: grid;
  place-items: center;
  padding: 0;
  border: none;
  background: transparent;
  color: inherit;
  cursor: pointer;
}

.chip-select {
  flex: 1;
  min-width: 160px;
  height: 30px;
  border: none;
  background: transparent;
  color: var(--color-text-muted);
  font-size: 14px;
  cursor: pointer;
}
</style>
