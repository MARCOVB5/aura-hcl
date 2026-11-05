<script setup>
import { computed, reactive, ref } from 'vue'
import AppIcon from '../components/AppIcon.vue'
import DateTimeInput from '../components/DateTimeInput.vue'
import { createHospitalization, deleteHospitalization, updateHospitalization } from '../api.js'
import {
  STAY_EDIT_STATUSES,
  STAY_STATUSES,
  STAY_TYPES,
  patientDetails,
  patientName,
} from '../format.js'

const props = defineProps({
  patient: { type: Object, required: true },
  // edit mode: the stay (encounter) to change
  stay: { type: Object, default: null },
  // opened from "Planifier un soin" because the patient has no current stay
  forCare: { type: Boolean, default: false },
  backLabel: { type: String, default: 'Retour à la recherche' },
})
const emit = defineEmits(['created', 'saved', 'deleted', 'back'])

const editing = computed(() => props.stay !== null)

// value of a DateTimeInput, in local time: "2026-10-23T08:05"
function localDateTime(date) {
  const pad = (n) => String(n).padStart(2, '0')
  return (
    `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}` +
    `T${pad(date.getHours())}:${pad(date.getMinutes())}`
  )
}

// the brief says the stay number is generated when the patient arrives
function newStayNumber(date) {
  return `SEJ-${localDateTime(date).replace(/[-:]/g, '').replace('T', '-')}`
}

// "2026-10-23T08:05:00" -> "2026-10-23T08:05", the value of a DateTimeInput
const toInput = (iso) => (iso ? iso.slice(0, 16) : '')

const now = new Date()
const form = reactive(
  props.stay
    ? {
        stayNumber: props.stay.stay_number,
        admissionDate: toInput(props.stay.admission_date),
        status: props.stay.status,
        type: props.stay.encounter_type_code,
        expectedDischargeDate: toInput(props.stay.expected_discharge_date),
        actualDischargeDate: toInput(props.stay.actual_discharge_date),
        reason: props.stay.reason ?? '',
        location: props.stay.location ?? '',
      }
    : {
        stayNumber: newStayNumber(now),
        admissionDate: localDateTime(now),
        status: 'in-progress',
        type: 'INPATIENT',
        expectedDischargeDate: '',
        actualDischargeDate: '',
        reason: '',
        location: '',
      },
)
const statuses = computed(() => (editing.value ? STAY_EDIT_STATUSES : STAY_STATUSES))
// date and time fields typed only in part (e.g. a discharge date without its time)
const incomplete = reactive({ admission: false, expected: false, actual: false })
const INCOMPLETE_LABELS = {
  admission: 'l’admission',
  expected: 'la sortie prévue',
  actual: 'la sortie effective',
}
const incompleteFields = computed(() =>
  Object.keys(incomplete)
    .filter((k) => incomplete[k])
    .map((k) => INCOMPLETE_LABELS[k]),
)
const submitting = ref(false)
const error = ref('')

const name = computed(() => patientName(props.patient) || 'Patient sous X')
// the first location is required when the stay is created; an older stay may have none
const requiredFilled = computed(
  () =>
    form.stayNumber.trim() !== '' &&
    form.admissionDate !== '' &&
    (editing.value || form.location.trim() !== ''),
)
// the values have the same "YYYY-MM-DDTHH:mm" format, so they compare as strings
const beforeAdmission = (value) => value !== '' && value < form.admissionDate
const dischargeBeforeAdmission = computed(() => beforeAdmission(form.expectedDischargeDate))
const actualBeforeAdmission = computed(() => beforeAdmission(form.actualDischargeDate))
const canSubmit = computed(
  () =>
    requiredFilled.value &&
    !dischargeBeforeAdmission.value &&
    !actualBeforeAdmission.value &&
    !incompleteFields.value.length &&
    !submitting.value,
)

const toApi = (value) => (value ? `${value}:00` : null)

async function submit() {
  if (!canSubmit.value) return
  submitting.value = true
  error.value = ''
  const fields = {
    stay_number: form.stayNumber.trim(),
    status: form.status,
    encounter_type_code: form.type,
    admission_date: toApi(form.admissionDate),
    expected_discharge_date: toApi(form.expectedDischargeDate),
    reason: form.reason.trim() || null,
    location: form.location.trim() || null,
  }
  try {
    if (editing.value) {
      const actual_discharge_date = toApi(form.actualDischargeDate)
      emit(
        'saved',
        await updateHospitalization(props.stay.id, { ...fields, actual_discharge_date }),
      )
    } else {
      emit('created', await createHospitalization({ patient_id: props.patient.id, ...fields }))
    }
  } catch (e) {
    error.value = e.message
  } finally {
    submitting.value = false
  }
}

// deleting asks for a second click
const confirmingDelete = ref(false)
async function remove() {
  submitting.value = true
  error.value = ''
  try {
    await deleteHospitalization(props.stay.id)
    emit('deleted', props.stay)
  } catch (e) {
    error.value = e.message
    confirmingDelete.value = false
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <header class="page-header">
    <h2 class="service-name">Service de réanimation</h2>
    <div class="title-row">
      <div>
        <h1 class="page-title">{{ editing ? 'Modifier le séjour' : 'Créer un séjour' }}</h1>
        <p v-if="editing" class="page-description">Séjour n° {{ stay.stay_number }} · {{ name }}</p>
      </div>
      <button type="button" class="btn btn-small" @click="emit('back')">{{ backLabel }}</button>
    </div>
  </header>

  <div class="page-content">
    <div v-if="forCare" class="notice notice-primary">
      <AppIcon name="info" :size="16" />
      {{ name }} n’a aucun séjour en cours : créez-le pour planifier le soin.
    </div>

    <form class="card" novalidate @submit.prevent="submit">
      <div class="card-header">
        <h2 class="card-title">Informations du séjour</h2>
      </div>

      <div class="card-body">
        <div class="field">
          <span class="field-label">Patient *</span>
          <div class="patient-box">
            <AppIcon name="circle-user" :size="20" class="patient-icon" />
            <div class="patient-info">
              <span class="patient-name">{{ name }}</span>
              <span class="muted">{{ patientDetails(patient) }}</span>
              <span v-if="patient.allergies.length" class="allergy">
                Allergies : {{ patient.allergies.map((a) => a.name).join(', ') }}
              </span>
            </div>
            <button v-if="!editing" type="button" class="btn btn-small" @click="emit('back')">
              Changer de patient
            </button>
          </div>
        </div>

        <div class="row">
          <label class="field">
            <span class="field-label">Numéro de séjour *</span>
            <input v-model="form.stayNumber" class="input" maxlength="32" required />
          </label>
          <div class="field">
            <span class="field-label">Date et heure d’admission *</span>
            <DateTimeInput
              v-model="form.admissionDate"
              v-model:incomplete="incomplete.admission"
              label="Admission"
              required
            />
          </div>
          <label class="field">
            <span class="field-label">{{
              editing ? 'Localisation' : 'Première localisation *'
            }}</span>
            <input v-model="form.location" class="input" maxlength="128" :required="!editing" />
          </label>
          <label class="field">
            <span class="field-label">Statut</span>
            <select v-model="form.status" class="input">
              <option v-for="s in statuses" :key="s.value" :value="s.value">
                {{ s.label }}
              </option>
            </select>
          </label>
          <label class="field">
            <span class="field-label">Type de séjour</span>
            <select v-model="form.type" class="input">
              <option v-for="t in STAY_TYPES" :key="t.value" :value="t.value">
                {{ t.label }}
              </option>
            </select>
          </label>
          <div class="field">
            <span class="field-label">Sortie prévue</span>
            <DateTimeInput
              v-model="form.expectedDischargeDate"
              v-model:incomplete="incomplete.expected"
              label="Sortie prévue"
              :min="form.admissionDate"
            />
          </div>
          <div v-if="editing" class="field">
            <span class="field-label">Sortie effective</span>
            <DateTimeInput
              v-model="form.actualDischargeDate"
              v-model:incomplete="incomplete.actual"
              label="Sortie effective"
              :min="form.admissionDate"
            />
          </div>
          <label class="field">
            <span class="field-label">Motif d’admission</span>
            <input v-model="form.reason" class="input" maxlength="255" />
          </label>
        </div>

        <div v-if="incompleteFields.length" class="notice notice-error">
          <AppIcon name="alert-circle" :size="16" />
          Indiquez la date et l’heure de {{ incompleteFields.join(' et de ') }}.
        </div>
        <div v-if="dischargeBeforeAdmission" class="notice notice-error">
          <AppIcon name="alert-circle" :size="16" />
          La sortie prévue doit être après la date d’admission.
        </div>
        <div v-if="actualBeforeAdmission" class="notice notice-error">
          <AppIcon name="alert-circle" :size="16" />
          La sortie effective doit être après la date d’admission.
        </div>
        <div v-if="confirmingDelete" class="notice notice-error confirm-delete" role="alert">
          <AppIcon name="alert-circle" :size="16" />
          <span>Supprimer définitivement ce séjour ?</span>
          <div class="buttons">
            <button type="button" class="btn btn-small" @click="confirmingDelete = false">
              Annuler
            </button>
            <button
              type="button"
              class="btn btn-small btn-danger"
              :disabled="submitting"
              @click="remove"
            >
              Supprimer
            </button>
          </div>
        </div>
        <div v-if="error" class="notice notice-error" role="alert">
          <AppIcon name="alert-circle" :size="16" />
          {{ error }}
        </div>

        <div class="actions">
          <button
            v-if="editing"
            type="button"
            class="btn btn-danger-outline"
            :disabled="submitting || confirmingDelete"
            @click="confirmingDelete = true"
          >
            <AppIcon name="trash" :size="16" />
            Supprimer le séjour
          </button>
          <span v-else class="muted">* Champs obligatoires</span>
          <div class="buttons">
            <button type="button" class="btn" @click="emit('back')">Annuler</button>
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
.patient-box {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
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

.row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

@media (max-width: 1000px) {
  .row {
    grid-template-columns: 1fr;
  }
}

select.input {
  cursor: pointer;
}

.confirm-delete .buttons {
  margin-left: auto;
}

.btn-danger-outline {
  border-color: var(--color-danger-border);
  color: var(--color-danger);
}

.btn-danger {
  border-color: var(--color-danger);
  background: var(--color-danger);
  color: #fff;
}
</style>
