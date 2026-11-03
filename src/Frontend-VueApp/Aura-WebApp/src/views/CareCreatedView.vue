<script setup>
import { computed } from 'vue'
import AppIcon from '../components/AppIcon.vue'
import {
  TIME_CONSTRAINTS,
  careWhen,
  formatDate,
  labelOf,
  patientDetails,
  patientName,
  practitionerName,
} from '../format.js'

const props = defineProps({
  appointment: { type: Object, required: true },
  // false after "Modifier": same page, other titles
  created: { type: Boolean, default: true },
})
const emit = defineEmits(['plan-another', 'calendar'])

const a = computed(() => props.appointment)
const NOT_SET = 'Non renseigné'
const details = computed(() => [
  { label: 'Type de soin', value: a.value.activity_definition.name },
  { label: 'Date de prescription', value: formatDate(a.value.prescribed_on) },
  { label: 'Date et heure de réalisation', value: careWhen(a.value) },
  { label: 'Contrainte sur l’horaire', value: labelOf(TIME_CONSTRAINTS, a.value.time_constraint) },
  {
    label: 'Soignant en charge',
    value: a.value.performers.map(practitionerName).join(', ') || NOT_SET,
  },
  {
    label: 'Soignant ayant validé la prescription',
    value: practitionerName(a.value.validated_by) || NOT_SET,
  },
  { label: 'Note sur les conditions de réalisation', value: a.value.note || 'Non renseignée' },
])
</script>

<template>
  <header class="page-header">
    <h2 class="service-name">Service de réanimation</h2>
    <div class="title-row">
      <h1 class="page-title">{{ created ? 'Création du soin' : 'Modification du soin' }}</h1>
    </div>
  </header>

  <div class="page-content">
    <section class="card">
      <div class="card-header success-header" role="status">
        <span class="success-icon"><AppIcon name="check" :size="18" /></span>
        <div>
          <h2 class="card-title">
            {{ created ? 'Soin créé' : 'Soin modifié' }}
          </h2>
          <p class="card-description">{{ a.activity_definition.name }} · Le {{ careWhen(a) }}</p>
        </div>
      </div>

      <div class="card-body">
        <h3 class="section-title">Patient et séjour associés</h3>
        <div class="patient-box">
          <AppIcon name="circle-user" :size="20" class="patient-icon" />
          <div class="patient-info">
            <span class="patient-name">{{ patientName(a.patient) || 'Patient sous X' }}</span>
            <span class="muted">{{ patientDetails(a.patient) }}</span>
            <span v-if="a.patient.allergies.length" class="allergy">
              Allergies : {{ a.patient.allergies.map((x) => x.name).join(', ') }}
            </span>
          </div>
        </div>
        <div class="stay-box">
          <div class="stay-head">
            <strong>Séjour en cours</strong>
          </div>
          <p class="stay-start">
            Débuté le {{ formatDate(a.encounter.admission_date.slice(0, 10)) }}
          </p>
          <p>
            {{ a.encounter.location || 'Localisation non renseignée' }} · Séjour n°
            {{ a.encounter.stay_number }}
          </p>
        </div>

        <hr />

        <h3 class="section-title">Informations du soin</h3>
        <dl class="details">
          <div v-for="d in details" :key="d.label">
            <dt>{{ d.label }}</dt>
            <dd>{{ d.value }}</dd>
          </div>
        </dl>

        <div class="actions">
          <div class="buttons">
            <button type="button" class="btn" @click="emit('plan-another', a.patient)">
              Planifier un autre soin
            </button>
            <button type="button" class="btn btn-primary" @click="emit('calendar', a.patient)">
              Retour au calendrier
            </button>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.success-header {
  flex-direction: row;
  align-items: center;
  gap: 16px;
}

.success-icon {
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: var(--color-primary-soft);
  color: var(--color-primary);
}

.section-title {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
}

.patient-box {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
}

.patient-icon {
  color: var(--color-primary);
}

.patient-info {
  display: flex;
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

.stay-start {
  font-size: 15px;
  font-weight: 600;
}

hr {
  width: 100%;
  margin: 0;
  border: none;
  border-top: 1px solid var(--color-border);
}

.details {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px 24px;
  margin: 0;
}

dt {
  margin-bottom: 6px;
  color: var(--color-text-muted);
}

dd {
  margin: 0;
  font-size: 14px;
  font-weight: 500;
  white-space: pre-line;
}
</style>
