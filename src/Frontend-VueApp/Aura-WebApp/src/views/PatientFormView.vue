<script setup>
import { computed, reactive, ref } from 'vue'
import AppIcon from '../components/AppIcon.vue'
import DateInput from '../components/DateInput.vue'
import { createPatient, updatePatient } from '../api.js'
import { patientName } from '../format.js'

const props = defineProps({
  // criteria typed in the admission search: { nameFamily, nameGiven, ipp, contact }
  prefill: { type: Object, default: () => ({}) },
  // opened from "Nouvelle admission": the stay form follows the creation
  forAdmission: { type: Boolean, default: false },
  // edit mode: the patient whose record is changed
  patient: { type: Object, default: null },
})
const emit = defineEmits(['created', 'saved', 'cancel'])

const editing = computed(() => props.patient !== null)
const start = props.patient
  ? {
      nameFamily: props.patient.person.name_family ?? '',
      nameGiven: props.patient.person.name_given ?? '',
      anonymous: props.patient.identification_status === 'UNKNOWN',
      gender: ['female', 'male'].includes(props.patient.person.gender)
        ? props.patient.person.gender
        : '',
      birthDate: props.patient.person.birth_date ?? '',
      contact: props.patient.contact ?? '',
      ipp: props.patient.ipp ?? '',
      personalInfo: props.patient.personal_info ?? '',
      allergies: props.patient.allergies.map((a) => a.name).join('\n'),
    }
  : {}

const form = reactive({
  nameFamily: start.nameFamily ?? props.prefill.nameFamily ?? '',
  nameGiven: start.nameGiven ?? props.prefill.nameGiven ?? '',
  anonymous: start.anonymous ?? false, // "Patient sous X": names become optional
  gender: start.gender ?? '',
  birthDate: start.birthDate ?? '',
  contact: start.contact ?? props.prefill.contact ?? '',
  ipp: start.ipp ?? props.prefill.ipp ?? '',
  personalInfo: start.personalInfo ?? '',
  allergies: start.allergies ?? '',
})
const submitting = ref(false)
const error = ref('')

const namesFilled = computed(() => form.nameFamily.trim() !== '' && form.nameGiven.trim() !== '')
const canSubmit = computed(() => (form.anonymous || namesFilled.value) && !submitting.value)

const fullName = computed(() => [form.nameGiven.trim(), form.nameFamily.trim()].join(' ').trim())

// texts of the three states of the Figma frame "Formulaire créer patient"
const pageDescription = computed(() => {
  if (editing.value) {
    const name = patientName(props.patient) || 'Patient sous X'
    return `${name} · Identifiant : ${props.patient.ipp || 'non renseigné'}`
  }
  if (props.forAdmission) {
    const who = fullName.value ? `de ${fullName.value}` : 'du patient'
    return `Informations reprises de la recherche. Après validation, vous créerez le séjour ${who}.`
  }
  if (form.anonymous) return 'Option Patient sous X cochée : nom et prénom deviennent facultatifs.'
  if (namesFilled.value)
    return 'Nom et prénom sont renseignés : le bouton Valider est désormais actif.'
  return 'Saisissez les informations obligatoires pour créer un dossier patient.'
})
const cardDescription = computed(() =>
  form.anonymous
    ? 'Nom et prénom sont facultatifs car l’option Patient sous X est cochée.'
    : 'Nom et prénom sont obligatoires, sauf si le patient est sous X.',
)
const statusText = computed(() => {
  if (editing.value) return '* Champs obligatoires · Le séjour se modifie séparément.'
  if (props.forAdmission && canSubmit.value)
    return 'Valider crée le patient, puis ouvre la création de son séjour.'
  if (form.anonymous) return 'Patient sous X : aucun champ obligatoire.'
  if (namesFilled.value) return 'Tous les champs obligatoires sont renseignés.'
  return 'Renseignez le nom et le prénom pour continuer.'
})

// one allergy per line, or separated by commas / semicolons
function parseAllergies(text) {
  return text
    .split(/[\n,;]/)
    .map((a) => a.trim())
    .filter(Boolean)
}

const orNull = (s) => s.trim() || null

async function submit() {
  if (!canSubmit.value) return
  submitting.value = true
  error.value = ''
  const data = {
    person: {
      name_family: orNull(form.nameFamily),
      name_given: orNull(form.nameGiven),
      birth_date: form.birthDate || null,
      gender: form.gender || 'unknown',
    },
    ipp: orNull(form.ipp),
    identification_status: form.anonymous ? 'UNKNOWN' : 'PROVISIONAL',
    contact: orNull(form.contact),
    personal_info: orNull(form.personalInfo),
    allergies: parseAllergies(form.allergies),
  }
  try {
    if (editing.value) emit('saved', await updatePatient(props.patient.id, data))
    else emit('created', await createPatient(data))
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
        <h1 class="page-title">
          {{ editing ? 'Modifier les informations du patient' : 'Créer un patient' }}
        </h1>
        <p class="page-description">{{ pageDescription }}</p>
      </div>
      <button v-if="forAdmission" type="button" class="btn btn-small" @click="emit('cancel')">
        Retour à la recherche
      </button>
      <button v-else-if="editing" type="button" class="btn btn-small" @click="emit('cancel')">
        Retour à la fiche
      </button>
    </div>
  </header>

  <div class="page-content">
    <form class="card" novalidate @submit.prevent="submit">
      <div class="card-header">
        <h2 class="card-title">Informations du patient</h2>
        <p class="card-description">{{ cardDescription }}</p>
      </div>

      <div class="card-body">
        <div class="block">
          <div class="row row-2">
            <label class="field">
              <span class="field-label">Nom{{ form.anonymous ? '' : ' *' }}</span>
              <input
                v-model="form.nameFamily"
                class="input"
                placeholder="Ex. : Doe"
                maxlength="128"
                :required="!form.anonymous"
              />
            </label>
            <label class="field">
              <span class="field-label">Prénom{{ form.anonymous ? '' : ' *' }}</span>
              <input
                v-model="form.nameGiven"
                class="input"
                placeholder="Ex. : John"
                maxlength="128"
                :required="!form.anonymous"
              />
            </label>
          </div>
          <label class="inline-option">
            <input v-model="form.anonymous" type="checkbox" class="checkbox" />
            Patient sous X (nom et prénom facultatifs)
          </label>
        </div>

        <div class="row row-admin">
          <fieldset class="field sex">
            <legend class="field-label">Sexe</legend>
            <div class="sex-options">
              <label class="inline-option">
                <input v-model="form.gender" type="radio" value="female" class="radio" />
                <strong>F</strong>
              </label>
              <label class="inline-option">
                <input v-model="form.gender" type="radio" value="male" class="radio" />
                <strong>M</strong>
              </label>
            </div>
          </fieldset>
          <label class="field">
            <span class="field-label">Date de naissance</span>
            <DateInput v-model="form.birthDate" />
          </label>
          <label class="field">
            <span class="field-label">Contact</span>
            <input
              v-model="form.contact"
              type="tel"
              class="input"
              placeholder="Ex. : 06 12 34 56 78"
            />
          </label>
          <label class="field">
            <span class="field-label">IPP</span>
            <input v-model="form.ipp" class="input" placeholder="Ex. : 123456789" maxlength="32" />
          </label>
        </div>

        <div class="row row-2">
          <label class="field">
            <span class="field-label">Informations personnelles</span>
            <textarea
              v-model="form.personalInfo"
              class="input"
              placeholder="Ex. : antécédents, contexte, particularités…"
            ></textarea>
          </label>
          <label class="field">
            <span class="field-label">Allergies</span>
            <textarea
              v-model="form.allergies"
              class="input"
              placeholder="Ex. : médicaments, produits, précautions… (une par ligne)"
            ></textarea>
          </label>
        </div>

        <div class="block block-validation">
          <div v-if="!editing" class="notice">
            <AppIcon name="info" :size="16" />
            IPP, contact, informations personnelles et allergies peuvent être ajoutés plus tard.
          </div>
          <div v-if="error" class="notice notice-error" role="alert">
            <AppIcon name="alert-circle" :size="16" />
            {{ error }}
          </div>
          <div class="actions">
            <span class="muted">{{ statusText }}</span>
            <div class="buttons">
              <button v-if="!forAdmission" type="button" class="btn" @click="emit('cancel')">
                Annuler
              </button>
              <button type="submit" class="btn btn-primary" :disabled="!canSubmit">
                {{ submitting ? 'Envoi…' : editing ? 'Enregistrer' : 'Valider' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </form>
  </div>
</template>

<style scoped>
.block {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.block-validation {
  gap: 12px;
}

.row {
  display: grid;
  gap: 20px;
}

.row-2 {
  grid-template-columns: 1fr 1fr;
}

.row-admin {
  grid-template-columns: 143px 1fr 1fr 1fr;
}

@media (max-width: 1000px) {
  .row-2,
  .row-admin {
    grid-template-columns: 1fr;
  }
}

.inline-option {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
}

.sex {
  margin: 0;
  padding: 0;
  border: none;
}

.sex legend {
  padding: 0;
  margin-bottom: 6px;
}

.sex-options {
  display: flex;
  align-items: center;
  gap: 16px;
  height: 36px;
}

.sex-options .inline-option {
  gap: 6px;
}
</style>
