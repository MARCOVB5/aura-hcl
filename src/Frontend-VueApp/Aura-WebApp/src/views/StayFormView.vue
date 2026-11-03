<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import AppIcon from '../components/AppIcon.vue'
import DateTimeInput from '../components/DateTimeInput.vue'
import { createHospitalization, listLocations } from '../api.js'
import { STAY_STATUSES, STAY_TYPES, patientDetails, patientName } from '../format.js'

const props = defineProps({
  patient: { type: Object, required: true },
  // the patient was just created from the admission search
  patientJustCreated: { type: Boolean, default: false },
  // opened from "Planifier un soin" because the patient has no current stay
  forCare: { type: Boolean, default: false },
  backLabel: { type: String, default: 'Retour à la recherche' },
})
const emit = defineEmits(['created', 'back'])

const locations = ref([])
onMounted(async () => {
  try {
    locations.value = await listLocations()
  } catch (e) {
    error.value = e.message
  }
})

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

const now = new Date()
const form = reactive({
  stayNumber: newStayNumber(now),
  admissionDate: localDateTime(now),
  status: 'in-progress',
  type: 'INPATIENT',
  expectedDischargeDate: '',
  reason: '',
  locationId: '',
})
const submitting = ref(false)
const error = ref('')

const name = computed(() => patientName(props.patient) || 'Patient sous X')
const requiredFilled = computed(
  () => form.stayNumber.trim() !== '' && form.admissionDate !== '' && form.locationId !== '',
)
// both values have the same "YYYY-MM-DDTHH:mm" format, so they compare as strings
const dischargeBeforeAdmission = computed(
  () => form.expectedDischargeDate !== '' && form.expectedDischargeDate < form.admissionDate,
)
const canSubmit = computed(
  () => requiredFilled.value && !dischargeBeforeAdmission.value && !submitting.value,
)

const statusText = computed(() => {
  if (dischargeBeforeAdmission.value) return 'La sortie prévue doit être après la date d’admission.'
  if (requiredFilled.value)
    return 'Toutes les informations obligatoires sont renseignées. Vous pouvez créer le séjour.'
  return 'Renseignez le numéro de séjour, la date d’admission et la première localisation pour activer le bouton Valider.'
})

const toApi = (value) => (value ? `${value}:00` : null)

async function submit() {
  if (!canSubmit.value) return
  submitting.value = true
  error.value = ''
  try {
    const hospitalization = await createHospitalization({
      patient_id: props.patient.id,
      stay_number: form.stayNumber.trim(),
      status: form.status,
      encounter_type_code: form.type,
      admission_date: toApi(form.admissionDate),
      expected_discharge_date: toApi(form.expectedDischargeDate),
      reason: form.reason.trim() || null,
      current_location_id: form.locationId,
    })
    emit('created', hospitalization)
  } catch (e) {
    error.value = e.message
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
        <h1 class="page-title">Créer un séjour</h1>
        <p class="page-description">
          {{
            patientJustCreated
              ? 'Le dossier patient est créé. Complétez maintenant les informations de son séjour.'
              : 'Renseignez les informations du séjour pour le patient sélectionné.'
          }}
        </p>
      </div>
      <button type="button" class="btn btn-small" @click="emit('back')">{{ backLabel }}</button>
    </div>
  </header>

  <div class="page-content">
    <div v-if="patientJustCreated" class="notice notice-primary">
      <AppIcon name="check" :size="16" />
      Le patient {{ name }}{{ patient.ipp ? ` (${patient.ipp})` : '' }} a bien été créé et est déjà
      sélectionné pour ce séjour.
    </div>
    <div v-if="forCare" class="notice notice-primary">
      <AppIcon name="info" :size="16" />
      {{ name }} n’a aucun séjour en cours. Après la création du séjour, la planification du soin
      reprendra avec ce patient.
    </div>

    <form class="card" novalidate @submit.prevent="submit">
      <div class="card-header">
        <h2 class="card-title">Informations du séjour</h2>
        <p class="card-description">
          Le patient, le numéro de séjour, la date d’admission et la première localisation sont
          obligatoires.
        </p>
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
            <button type="button" class="btn btn-small" @click="emit('back')">
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
            <DateTimeInput v-model="form.admissionDate" label="Admission" required />
          </div>
          <label class="field">
            <span class="field-label">Première localisation *</span>
            <select v-model="form.locationId" class="input" required>
              <option value="" disabled>Sélectionner un service, une chambre et un lit</option>
              <option v-for="l in locations" :key="l.id" :value="l.id">{{ l.name }}</option>
            </select>
          </label>
          <label class="field">
            <span class="field-label">Statut</span>
            <select v-model="form.status" class="input">
              <option v-for="s in STAY_STATUSES" :key="s.value" :value="s.value">
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
              label="Sortie prévue"
              :min="form.admissionDate"
            />
          </div>
          <label class="field">
            <span class="field-label">Motif d’admission</span>
            <input
              v-model="form.reason"
              class="input"
              maxlength="255"
              placeholder="Ex. : choc septique, détresse respiratoire…"
            />
          </label>
        </div>

        <div class="notice" :class="{ 'notice-error': dischargeBeforeAdmission }">
          <AppIcon name="info" :size="16" />
          {{ statusText }}
        </div>
        <div v-if="error" class="notice notice-error" role="alert">
          <AppIcon name="alert-circle" :size="16" />
          {{ error }}
        </div>

        <div class="actions">
          <span class="muted">* Champs obligatoires</span>
          <div class="buttons">
            <button type="button" class="btn" @click="emit('back')">Annuler</button>
            <button type="submit" class="btn btn-primary" :disabled="!canSubmit">
              {{ submitting ? 'Envoi…' : 'Valider' }}
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
</style>
