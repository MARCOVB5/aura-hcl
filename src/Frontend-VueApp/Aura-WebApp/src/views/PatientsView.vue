<script setup>
import { computed, onMounted, ref } from 'vue'
import AppIcon from '../components/AppIcon.vue'
import { listPatients } from '../api.js'
import { formatDate, patientName } from '../format.js'

const selected = defineModel('selected', { type: Object, default: null })
const emit = defineEmits(['create'])

const patients = ref([])
const loading = ref(true)
const error = ref('')
const search = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    patients.value = await listPatients()
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
onMounted(load)

// filters on first name, last name or IPP, ignoring case and accents
const normalize = (s) =>
  (s ?? '')
    .normalize('NFD')
    .replace(/\p{Diacritic}/gu, '')
    .toLowerCase()
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
        <input
          v-model="search"
          type="search"
          placeholder="Rechercher un patient…"
          aria-label="Rechercher un patient"
        />
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
            <label class="patient-select">
              <input
                type="radio"
                name="selected-patient"
                class="radio"
                :checked="selected?.id === patient.id"
                @change="selected = patient"
              />
              <span v-if="patientName(patient)" class="patient-name">{{
                patientName(patient)
              }}</span>
              <span v-else class="patient-name muted"><em>Patient sous X</em></span>
            </label>
          </td>
          <td class="col-id muted">{{ patient.ipp || 'Non renseigné' }}</td>
          <td class="col-birth">{{ formatDate(patient.person.birth_date) || '—' }}</td>
          <td class="col-action">
            <button
              type="button"
              class="btn btn-small"
              disabled
              title="La modification d’un patient n’est pas encore disponible"
            >
              <AppIcon name="pencil" :size="14" />
              Modifier
            </button>
          </td>
        </tr>
      </tbody>
    </table>

    <div v-if="selected">
      <button
        type="button"
        class="btn btn-small"
        disabled
        title="Disponible avec la nouvelle admission"
      >
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

.search input::placeholder {
  color: var(--color-text-muted);
}

.retry {
  margin-left: auto;
}

.table {
  width: 100%;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  border-collapse: separate;
  border-spacing: 0;
  overflow: hidden;
}

th,
td {
  padding: 0 20px;
  border-bottom: 1px solid var(--color-border);
  text-align: left;
}

tbody tr:last-child td {
  border-bottom: none;
}

th {
  height: 42px;
  background: var(--color-table-header);
  color: var(--color-text-muted);
  font-size: 12px;
  font-weight: 500;
}

td {
  height: 68px;
}

tbody tr:not(:has(.empty)) {
  cursor: pointer;
}

tbody tr:not(:has(.empty)):hover,
tr.selected {
  background: var(--color-primary-soft);
}

.col-patient {
  width: 40%;
}

.col-id,
.col-birth {
  width: 20%;
}

.col-action {
  text-align: right;
}

.patient-select {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
}

.patient-name {
  font-size: 14px;
  font-weight: 500;
}

.empty {
  text-align: center;
}
</style>
