<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import AppIcon from '../components/AppIcon.vue'
import DateInput from '../components/DateInput.vue'
import TimeInput from '../components/TimeInput.vue'
import {
  createAppointment,
  getCurrentHospitalization,
  listCareTypes,
  listPatients,
  listPractitioners,
  updateAppointment,
} from '../api.js'
import {
  TIME_CONSTRAINTS,
  dayKey,
  formatDate,
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
})
const emit = defineEmits(['saved', 'cancel', 'create-stay'])

const editing = computed(() => props.appointment !== null)

// ---- reference lists ----

const careTypes = ref([])
const practitioners = ref([])
const error = ref('')
onMounted(async () => {
  try {
    ;[careTypes.value, practitioners.value] = await Promise.all([
      listCareTypes(),
      listPractitioners(),
    ])
  } catch (e) {
    error.value = e.message
  }
})

// ---- form ----

function valuesOf(a) {
  const weak = a.time_constraint === 'WEAK'
  return {
    prescribedOn: a.prescribed_on,
    careTypeId: a.activity_definition.id,
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
  careTypeId: '',
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
  () => form.prescribedOn && form.careTypeId && form.date && timeFilled.value,
)
const canSubmit = computed(
  () => patient.value && stayState.value === 'found' && fieldsFilled.value && !submitting.value,
)

const status = computed(() => {
  if (stayState.value === 'missing') {
    const record = patient.value.ipp || patientName(patient.value) || 'sélectionné'
    return {
      kind: 'warning',
      text: `Validation impossible : aucun séjour en cours pour le dossier ${record}.`,
    }
  }
  if (windowInvalid.value)
    return { kind: 'error', text: 'La fin de la plage doit être après son début.' }
  if (patient.value && stayState.value === 'found' && fieldsFilled.value)
    return {
      kind: 'info',
      text: 'Toutes les informations obligatoires sont renseignées. Les soignants et la note peuvent rester vides.',
    }
  return {
    kind: 'info',
    text: 'Sélectionnez un patient et renseignez les informations obligatoires pour activer le bouton Valider.',
  }
})

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
    activity_definition_id: form.careTypeId,
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
        <p class="page-description">
          {{
            editing
              ? `${appointment.activity_definition.name} · ${patientName(appointment.patient) || 'Patient sous X'}`
              : 'Sélectionnez un patient, puis renseignez les informations du soin.'
          }}
        </p>
      </div>
      <button type="button" class="btn btn-small" @click="emit('cancel')">
        Retour au calendrier
      </button>
    </div>
  </header>

  <div class="page-content">
    <form class="card" novalidate @submit.prevent="submit">
      <div class="card-header">
        <h2 class="card-title">Informations du soin</h2>
        <p class="card-description">
          Les champs marqués d’un astérisque sont obligatoires. Le séjour en cours est associé
          automatiquement.
        </p>
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
                <input
                  v-model="search.nameFamily"
                  class="input"
                  placeholder="Nom du patient sélectionné (sinon vide)"
                />
              </label>
              <label class="field">
                <span class="field-label">Prénom</span>
                <input
                  v-model="search.nameGiven"
                  class="input"
                  placeholder="Prénom du patient sélectionné (sinon vide)"
                />
              </label>
            </div>
            <p v-if="!searching" class="muted hint">
              Renseignez le nom et le prénom, puis choisissez un dossier parmi les résultats.
            </p>
            <template v-else>
              <p class="muted hint">
                {{
                  results.length
                    ? `${results.length} dossier${results.length > 1 ? 's correspondent' : ' correspond'}. Choisissez le patient concerné.`
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
              <p class="hint not-selected">
                Aucun patient sélectionné : la saisie du nom et du prénom ne suffit pas.
              </p>
            </template>
          </template>
        </div>

        <!-- current stay -->
        <div class="stay-box" :class="{ warning: stayState === 'missing' }">
          <div class="stay-head">
            <strong>Séjour en cours</strong>
            <span class="muted">Association automatique</span>
          </div>
          <p v-if="stayState === 'none'">
            Sélectionnez un patient pour afficher et associer son séjour en cours. Aucune saisie de
            séjour n’est nécessaire.
          </p>
          <p v-else-if="stayState === 'loading'" class="muted">Recherche du séjour en cours…</p>
          <p v-else-if="stayState === 'found'">
            <strong>Débuté le {{ formatDate(stay.admission_date.slice(0, 10)) }}</strong>
            <template v-if="stay.current_location"> · {{ stay.current_location.name }}</template>
            <span class="muted"> · Séjour n° {{ stay.stay_number }}</span>
          </p>
          <template v-else>
            <p class="stay-missing">Aucun séjour en cours</p>
            <p>
              Ce soin ne peut pas être créé sans séjour. Créez un séjour pour ce patient ou
              choisissez un autre dossier.
            </p>
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
            <select v-model="form.careTypeId" class="input" required>
              <option value="" disabled>Sélectionner un type de soin</option>
              <option v-for="t in careTypes" :key="t.id" :value="t.id">{{ t.name }}</option>
            </select>
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
          <p class="muted hint">
            Choisissez faible pour une plage horaire ou forte pour une heure précise.
          </p>
        </fieldset>

        <div class="row" :class="form.constraint === 'STRONG' ? 'row-2' : 'row-3'">
          <label class="field">
            <span class="field-label">Date de réalisation *</span>
            <DateInput v-model="form.date" required />
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
        <p v-if="form.constraint !== 'STRONG'" class="muted hint tight">
          Si la contrainte est forte, une heure précise remplace les champs de début et de fin.
        </p>

        <div class="row">
          <div class="field">
            <span class="field-label">Soignant(s) en charge · facultatif</span>
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
            <span class="field-label">Soignant ayant validé la prescription · facultatif</span>
            <select v-model="form.validatorId" class="input">
              <option value="">Sélectionner un soignant</option>
              <option v-for="p in practitioners" :key="p.id" :value="p.id">
                {{ practitionerLabel(p) }}
              </option>
            </select>
          </label>
        </div>

        <label class="field">
          <span class="field-label">Note sur les conditions de réalisation · facultatif</span>
          <textarea
            v-model="form.note"
            class="input"
            placeholder="Ajouter une note sur les conditions de réalisation…"
          ></textarea>
        </label>

        <div
          class="notice"
          :class="{
            'notice-warning': status.kind === 'warning',
            'notice-error': status.kind === 'error',
          }"
        >
          <AppIcon :name="status.kind === 'warning' ? 'alert-triangle' : 'info'" :size="16" />
          {{ status.text }}
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
    <p class="muted footnote">Données de démonstration · Aucun dossier médical réel</p>
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

.hint.tight {
  margin-top: -8px;
}

.not-selected {
  color: var(--color-primary);
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

.footnote {
  margin: 0;
}
</style>
