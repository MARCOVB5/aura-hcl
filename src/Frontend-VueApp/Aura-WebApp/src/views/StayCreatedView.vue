<script setup>
import { computed } from 'vue'
import AppIcon from '../components/AppIcon.vue'
import { STAY_STATUSES, STAY_TYPES, formatDateTime, labelOf, patientName } from '../format.js'

const props = defineProps({
  hospitalization: { type: Object, required: true },
})
const emit = defineEmits(['new-admission', 'patients'])

const encounter = computed(() => props.hospitalization.encounter)
const patient = computed(() => encounter.value.patient)
const name = computed(() => patientName(patient.value) || 'Patient sous X')
</script>

<template>
  <header class="page-header">
    <h2 class="service-name">Service de réanimation</h2>
    <div class="title-row">
      <div>
        <h1 class="page-title">Séjour créé</h1>
        <p class="page-description">L’admission de {{ name }} a été enregistrée.</p>
      </div>
    </div>
  </header>

  <div class="page-content">
    <section class="card">
      <div class="card-header">
        <h2 class="card-title">Confirmation de création</h2>
        <p class="card-description">Le séjour est désormais associé au dossier du patient.</p>
      </div>

      <div class="card-body">
        <div class="success" role="status">
          <AppIcon name="check" :size="18" />
          <div>
            <p class="success-title">Le séjour de {{ name }} a bien été créé.</p>
            <p>
              Séjour n° {{ encounter.stay_number }} ·
              {{ labelOf(STAY_TYPES, encounter.encounter_type_code) }} ·
              {{ labelOf(STAY_STATUSES, encounter.status) }}
            </p>
          </div>
        </div>

        <dl class="details">
          <div>
            <dt>Patient</dt>
            <dd>{{ name }}</dd>
            <dd class="muted">{{ patient.ipp || 'IPP non renseigné' }}</dd>
          </div>
          <div>
            <dt>Admission</dt>
            <dd>{{ formatDateTime(encounter.admission_date) }}</dd>
            <dd v-if="encounter.expected_discharge_date" class="muted">
              Sortie prévue : {{ formatDateTime(encounter.expected_discharge_date) }}
            </dd>
          </div>
          <div>
            <dt>Motif</dt>
            <dd>{{ encounter.reason || '—' }}</dd>
          </div>
          <div v-if="patient.allergies.length">
            <dt>Allergies</dt>
            <dd class="allergy">{{ patient.allergies.map((a) => a.name).join(', ') }}</dd>
          </div>
        </dl>

        <div class="actions">
          <span></span>
          <div class="buttons">
            <button type="button" class="btn" @click="emit('new-admission')">
              Nouvelle admission
            </button>
            <button type="button" class="btn btn-primary" @click="emit('patients')">
              Voir la liste des patients
            </button>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.success {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px;
  border-radius: var(--radius);
  background: var(--color-primary-soft);
  color: var(--color-primary);
}

.success p {
  margin: 0;
}

.success-title {
  margin-bottom: 4px !important;
  font-size: 16px;
  font-weight: 600;
}

.details {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin: 0;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--color-border);
}

.details div {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

dt {
  color: var(--color-text-muted);
}

dd {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
}

dd.muted {
  font-size: 13px;
  font-weight: 400;
}
</style>
