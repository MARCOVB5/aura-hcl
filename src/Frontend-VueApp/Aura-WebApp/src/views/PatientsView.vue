<script setup>
import { computed, onMounted, ref } from 'vue'
import AppIcon from '../components/AppIcon.vue'
import { listPatients } from '../api.js'
import { formatDate, normalize, patientName } from '../format.js'

const selected = defineModel('selected', { type: Object, default: null })
const emit = defineEmits(['create', 'create-stay', 'open', 'edit', 'edit-stay', 'plan-care'])

const patients = ref([])
const loading = ref(true)
const error = ref('')
const search = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    patients.value = await listPatients()
    // the selected patient may have changed since it was picked (allergies…)
    if (selected.value)
      selected.value = patients.value.find((p) => p.id === selected.value.id) ?? selected.value
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
onMounted(load)

// filters on first name, last name or IPP, ignoring case and accents
const filtered = computed(() => {
  const q = normalize(search.value.trim())
  if (!q) return patients.value
  return patients.value.filter((p) =>
    normalize(`${patientName(p)} ${p.person.name_family ?? ''} ${p.ipp ?? ''}`).includes(q),
  )
})

const countLabel = computed(() => {
  const n = filtered.value.length
  return `${n} patient${n > 1 ? 's' : ''}`
})
</script>

<template>
  <header class="page-header">
    <h2 class="service-name">Service de réanimation</h2>
    <div class="title-row">
      <div>
        <h1 class="page-title">Patients</h1>
        <p class="page-description">Liste des patients du service</p>
      </div>
      <button type="button" class="btn btn-primary btn-create" @click="emit('create')">
        <AppIcon name="plus" :size="16" />
        Créer un patient
      </button>
    </div>
  </header>

  <div class="page-content">
    <div class="toolbar">
      <label class="search">
        <AppIcon name="search" :size="16" class="muted" />
        <input v-model="search" type="search" aria-label="Rechercher un patient" />
      </label>
      <span class="muted">{{ countLabel }}</span>
    </div>

    <div v-if="error" class="notice notice-error" role="alert">
      <AppIcon name="alert-circle" :size="16" />
      <span>{{ error }}</span>
      <button type="button" class="btn btn-small retry" @click="load">Réessayer</button>
    </div>

    <table class="table">
      <thead>
        <tr>
          <th class="col-patient">Patient</th>
          <th class="col-id">Identifiant</th>
          <th class="col-birth">Date de naissance</th>
          <th class="col-action">Modification</th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="loading">
          <td colspan="4" class="empty muted">Chargement…</td>
        </tr>
        <tr v-else-if="!error && filtered.length === 0">
          <td colspan="4" class="empty muted">
            {{
              search
                ? 'Aucun patient ne correspond à la recherche.'
                : 'Aucun patient pour le moment.'
            }}
          </td>
        </tr>
        <tr
          v-for="patient in loading ? [] : filtered"
          :key="patient.id"
          :class="{ selected: selected?.id === patient.id }"
          @click="selected = patient"
        >
          <td class="col-patient">
            <div class="patient-select">
              <input
                type="radio"
                name="selected-patient"
                class="radio"
                :aria-label="`Sélectionner ${patientName(patient) || 'ce patient sous X'}`"
                :checked="selected?.id === patient.id"
                @change="selected = patient"
              />
              <button
                type="button"
                class="patient-link"
                title="Ouvrir la fiche patient"
                @click.stop="emit('open', patient)"
              >
                <span v-if="patientName(patient)" class="patient-name">{{
                  patientName(patient)
                }}</span>
                <span v-else class="patient-name muted"><em>Patient sous X</em></span>
              </button>
              <button
                type="button"
                class="btn btn-small open-record"
                @click.stop="emit('open', patient)"
              >
                <AppIcon name="eye" :size="14" />
                Voir la fiche
              </button>
            </div>
          </td>
          <td class="col-id muted">{{ patient.ipp || 'Non renseigné' }}</td>
          <td class="col-birth">{{ formatDate(patient.person.birth_date) || '—' }}</td>
          <td class="col-action">
            <div class="row-buttons">
              <button type="button" class="btn btn-small" @click.stop="emit('edit', patient)">
                <AppIcon name="pencil" :size="14" />
                Modifier
              </button>
              <button type="button" class="btn btn-small" @click.stop="emit('edit-stay', patient)">
                <AppIcon name="calendar" :size="14" />
                Modifier le séjour
              </button>
              <button type="button" class="btn btn-small" @click.stop="emit('plan-care', patient)">
                <AppIcon name="plus" :size="14" />
                Planifier un soin
              </button>
            </div>
          </td>
        </tr>
      </tbody>
    </table>

    <div v-if="selected">
      <button type="button" class="btn btn-small" @click="emit('create-stay', selected)">
        <AppIcon name="plus" :size="14" />
        Créer un séjour pour {{ patientName(selected) || 'ce patient' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.btn-create {
  height: 36px;
  padding: 0 12px;
  font-weight: 500;
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.search {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 360px;
  max-width: 100%;
  height: 36px;
  padding: 0 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
}

.search:focus-within {
  outline: 2px solid var(--color-primary);
  outline-offset: 1px;
}

.search input {
  flex: 1;
  min-width: 0;
  border: none;
  outline: none;
  background: transparent;
}

.retry {
  margin-left: auto;
}

.row-buttons {
  display: inline-flex;
  gap: 8px;
  white-space: nowrap;
}

/* the name opens the patient record */
.patient-link {
  padding: 0;
  border: none;
  background: transparent;
  text-align: left;
  cursor: pointer;
}

.patient-link:hover .patient-name {
  color: var(--color-primary);
  text-decoration: underline;
}

/* on the right of the patient column, apart from the buttons that change the patient */
.open-record {
  margin-left: auto;
  white-space: nowrap;
}
</style>
