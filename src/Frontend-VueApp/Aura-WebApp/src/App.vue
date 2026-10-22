<script setup>
import { computed, ref } from 'vue'
import AppSidebar from './components/AppSidebar.vue'
import ComingSoonView from './views/ComingSoonView.vue'
import PatientCreatedView from './views/PatientCreatedView.vue'
import PatientFormView from './views/PatientFormView.vue'
import PatientsView from './views/PatientsView.vue'
import { patientName } from './format.js'

// 'patients' | 'patient-form' | 'patient-created' | 'calendar' | 'admission'
const view = ref('patients')
const selectedPatient = ref(null)
const createdPatient = ref(null)

const section = computed(() => (view.value.startsWith('patient') ? 'patients' : view.value))
const selectedPatientName = computed(() =>
  selectedPatient.value ? patientName(selectedPatient.value) || 'Patient sous X' : '',
)

function onPatientCreated(patient) {
  createdPatient.value = patient
  view.value = 'patient-created'
}
</script>

<template>
  <div class="layout">
    <AppSidebar
      :section="section"
      :selected-patient-name="selectedPatientName"
      @navigate="view = $event"
    />
    <main class="main">
      <PatientsView
        v-if="view === 'patients'"
        v-model:selected="selectedPatient"
        @create="view = 'patient-form'"
      />
      <PatientFormView
        v-else-if="view === 'patient-form'"
        @created="onPatientCreated"
        @cancel="view = 'patients'"
      />
      <PatientCreatedView
        v-else-if="view === 'patient-created'"
        :patient="createdPatient"
        @back="view = 'patients'"
        @calendar="view = 'calendar'"
      />
      <ComingSoonView v-else-if="view === 'calendar'" title="Calendrier" />
      <ComingSoonView v-else title="Nouvelle admission" />
    </main>
  </div>
</template>

<style scoped>
.layout {
  display: flex;
  min-height: 100vh;
}

.main {
  flex: 1;
  min-width: 0;
}
</style>
