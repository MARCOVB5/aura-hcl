<script setup>
import AppIcon from '../components/AppIcon.vue'
import { formatDate } from '../format.js'

defineProps({
  patient: { type: Object, required: true },
})
const emit = defineEmits(['back', 'calendar'])
</script>

<template>
  <header class="page-header">
    <h2 class="service-name">Service de réanimation</h2>
    <div class="title-row">
      <h1 class="page-title">Créer un patient</h1>
    </div>
  </header>

  <div class="page-content">
    <section class="card">
      <div class="card-header">
        <h2 class="card-title">Confirmation</h2>
      </div>

      <div class="card-body">
        <div class="success" role="status">
          <span class="success-icon"><AppIcon name="check" :size="16" /></span>
          <div>
            <p class="success-title">Patient créé</p>
          </div>
        </div>

        <div class="summary">
          <h3 class="summary-title">Résumé</h3>
          <dl>
            <div v-if="!patient.person.name_family && !patient.person.name_given">
              <dt>Identité</dt>
              <dd>Patient sous X</dd>
            </div>
            <template v-else>
              <div>
                <dt>Nom</dt>
                <dd>{{ patient.person.name_family || '—' }}</dd>
              </div>
              <div>
                <dt>Prénom</dt>
                <dd>{{ patient.person.name_given || '—' }}</dd>
              </div>
            </template>
            <div v-if="patient.person.birth_date">
              <dt>Date de naissance</dt>
              <dd>{{ formatDate(patient.person.birth_date) }}</dd>
            </div>
            <div v-if="patient.ipp">
              <dt>IPP</dt>
              <dd>{{ patient.ipp }}</dd>
            </div>
            <div v-if="patient.allergies.length">
              <dt>Allergies</dt>
              <dd class="allergy">{{ patient.allergies.map((a) => a.name).join(', ') }}</dd>
            </div>
          </dl>
        </div>

        <div class="actions">
          <div class="buttons">
            <button type="button" class="btn" @click="emit('back')">Retour à la liste</button>
            <button type="button" class="btn btn-primary" @click="emit('calendar')">
              Voir le calendrier
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
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  background: var(--color-surface-muted);
}

.success p {
  margin: 0;
}

.success-icon {
  display: grid;
  flex-shrink: 0;
  place-items: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--color-success-soft);
  color: var(--color-success);
}

.success-title {
  margin-bottom: 4px !important;
  font-size: 16px;
  font-weight: 600;
}

.summary-title {
  margin: 0 0 12px;
  font-size: 13px;
  font-weight: 600;
}

dl {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin: 0;
}

dl > div {
  display: flex;
  justify-content: space-between;
  gap: 16px;
}

dt {
  color: var(--color-text-muted);
}

dd {
  margin: 0;
  font-weight: 600;
  text-align: right;
}
</style>
