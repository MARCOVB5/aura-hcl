<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import AppIcon from '../components/AppIcon.vue'
import { listPatients } from '../api.js'
import { formatDate, normalize, patientName } from '../format.js'

const props = defineProps({
  // criteria of the previous search, kept when coming back from the next steps
  initialCriteria: { type: Object, default: () => ({}) },
})
const emit = defineEmits(['select', 'create-patient', 'update:criteria'])

const criteria = reactive({
  nameFamily: props.initialCriteria.nameFamily ?? '',
  nameGiven: props.initialCriteria.nameGiven ?? '',
  ipp: props.initialCriteria.ipp ?? '',
})
const results = ref(null) // null until the first search
const selected = ref(null)
const loading = ref(false)
const error = ref('')

const hasCriteria = computed(() => Object.values(criteria).some((v) => v.trim() !== ''))
const searchedName = computed(() =>
  [criteria.nameGiven.trim(), criteria.nameFamily.trim()].join(' ').trim(),
)

// every filled criterion must match (case and accents ignored)
function matches(patient) {
  const fields = [
    [criteria.nameFamily, patient.person.name_family],
    [criteria.nameGiven, patient.person.name_given],
    [criteria.ipp, patient.ipp],
  ]
  return fields.every(([wanted, value]) => {
    const q = normalize(wanted.trim())
    return !q || normalize(value).includes(q)
  })
}

async function search() {
  if (!hasCriteria.value) return
  loading.value = true
  error.value = ''
  selected.value = null
  emit('update:criteria', { ...criteria })
  try {
    // the backend has no search endpoint yet: filter the department's patients here
    const patients = await listPatients()
    results.value = patients.filter(matches)
    if (results.value.length === 1) selected.value = results.value[0]
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

// coming back from the stay form: show the same results again
onMounted(() => {
  if (hasCriteria.value) search()
})

const countLabel = computed(() => {
  const n = results.value?.length ?? 0
  return `${n} correspondance${n > 1 ? 's' : ''}`
})
</script>

<template>
  <header class="page-header">
    <h2 class="service-name">Service de réanimation</h2>
    <div class="title-row">
      <div>
        <h1 class="page-title">Nouvelle admission</h1>
        <p class="page-description">
          Identifiez le patient, puis renseignez les informations de son séjour.
        </p>
      </div>
    </div>
  </header>

  <div class="page-content">
    <form class="card" novalidate @submit.prevent="search">
      <div class="card-header">
        <h2 class="card-title">Rechercher un patient</h2>
        <p class="card-description">
          Recherchez un dossier existant avant de créer une nouvelle admission.
        </p>
      </div>
      <div class="card-body">
        <div class="criteria">
          <label class="field">
            <span class="field-label">Nom</span>
            <input v-model="criteria.nameFamily" class="input" placeholder="Ex. : Exemple" />
          </label>
          <label class="field">
            <span class="field-label">Prénom</span>
            <input v-model="criteria.nameGiven" class="input" placeholder="Ex. : Léa" />
          </label>
          <label class="field">
            <span class="field-label">IPP</span>
            <input v-model="criteria.ipp" class="input" placeholder="Identifiant du patient" />
          </label>
        </div>
        <div class="actions">
          <span class="muted">Renseignez au moins un critère pour rechercher un patient.</span>
          <button type="submit" class="btn btn-primary" :disabled="!hasCriteria || loading">
            {{ loading ? 'Recherche…' : 'Rechercher' }}
          </button>
        </div>
      </div>
    </form>

    <div v-if="error" class="notice notice-error" role="alert">
      <AppIcon name="alert-circle" :size="16" />
      {{ error }}
    </div>

    <div v-else-if="results === null" class="placeholder">
      <AppIcon name="search" :size="20" class="muted" />
      <p class="placeholder-title">Commencez par rechercher le patient</p>
      <p class="muted">
        Les correspondances s’afficheront ici après la recherche. Vous pourrez ensuite sélectionner
        un patient ou créer son dossier.
      </p>
    </div>

    <div v-else-if="results.length === 0" class="placeholder card">
      <AppIcon name="search" :size="20" class="muted" />
      <p class="placeholder-title">Aucun patient trouvé</p>
      <p class="muted">
        Aucun dossier ne correspond aux informations saisies. Vérifiez les critères ou créez un
        dossier{{ searchedName ? ` pour ${searchedName}` : '' }}.
      </p>
      <p class="muted">
        Les informations de recherche seront préremplies. Vous pourrez ensuite créer son séjour.
      </p>
      <button
        type="button"
        class="btn btn-primary"
        @click="emit('create-patient', { ...criteria })"
      >
        Créer un patient avec ces informations
      </button>
    </div>

    <template v-else>
      <div class="results-header">
        <h2 class="card-title">Patients retrouvés</h2>
        <span class="muted">{{ countLabel }}</span>
      </div>
      <table class="table">
        <thead>
          <tr>
            <th class="col-patient">Patient</th>
            <th class="col-id">Identifiant</th>
            <th class="col-birth">Date de naissance</th>
            <th class="col-action">Sélection</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="patient in results"
            :key="patient.id"
            :class="{ selected: selected?.id === patient.id }"
            @click="selected = patient"
          >
            <td class="col-patient">
              <label class="patient-select">
                <input
                  type="radio"
                  name="admission-patient"
                  class="radio"
                  :checked="selected?.id === patient.id"
                  @change="selected = patient"
                />
                <span class="patient-name">{{ patientName(patient) || 'Patient sous X' }}</span>
              </label>
            </td>
            <td class="col-id muted">{{ patient.ipp || 'Non renseigné' }}</td>
            <td class="col-birth">{{ formatDate(patient.person.birth_date) || '—' }}</td>
            <td class="col-action" :class="selected?.id === patient.id ? 'chosen' : 'muted'">
              {{ selected?.id === patient.id ? 'Sélectionné' : 'Sélectionner' }}
            </td>
          </tr>
        </tbody>
      </table>
      <div class="actions">
        <span class="muted">
          <template v-if="selected">
            Patient sélectionné : {{ patientName(selected) || 'Patient sous X' }}
            {{ selected.ipp ? `· ${selected.ipp}` : '' }}
          </template>
          <template v-else>Sélectionnez un patient dans la liste.</template>
        </span>
        <div class="buttons">
          <button type="button" class="btn" @click="emit('create-patient', { ...criteria })">
            Aucun ne correspond : créer un patient
          </button>
          <button
            type="button"
            class="btn btn-primary"
            :disabled="!selected"
            @click="emit('select', selected)"
          >
            Créer un nouveau séjour pour ce patient
          </button>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.criteria {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

@media (max-width: 1000px) {
  .criteria {
    grid-template-columns: 1fr;
  }
}

.placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 40px 24px;
  text-align: center;
}

.placeholder p {
  margin: 0;
}

.placeholder .btn {
  margin-top: 8px;
}

.placeholder-title {
  font-size: 16px;
  font-weight: 600;
}

.results-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.chosen {
  color: var(--color-primary);
  font-weight: 500;
}
</style>
