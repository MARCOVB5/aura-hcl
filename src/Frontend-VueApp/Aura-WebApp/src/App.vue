<script setup>
import { computed, ref } from 'vue'
import AppSidebar from './components/AppSidebar.vue'
import AdmissionSearchView from './views/AdmissionSearchView.vue'
import ComingSoonView from './views/ComingSoonView.vue'
import PatientCreatedView from './views/PatientCreatedView.vue'
import PatientFormView from './views/PatientFormView.vue'
import PatientsView from './views/PatientsView.vue'
import StayCreatedView from './views/StayCreatedView.vue'
import StayFormView from './views/StayFormView.vue'
import { patientName } from './format.js'

// Patients:  'patients' -> 'patient-form' -> 'patient-created'
// Admission: 'admission' -> ('admission-patient-form') -> 'stay-form' -> 'stay-created'
// Other:     'calendar'
const view = ref('patients')
const selectedPatient = ref(null)
const createdPatient = ref(null)

const admissionCriteria = ref({})
const stayPatient = ref(null)
const stayPatientJustCreated = ref(false)
const stayFromPatientList = ref(false)
const createdHospitalization = ref(null)

const section = computed(() => {
  if (['patients', 'patient-form', 'patient-created'].includes(view.value)) return 'patients'
  if (view.value === 'calendar') return 'calendar'
  return 'admission'
})
const selectedPatientName = computed(() =>
  selectedPatient.value ? patientName(selectedPatient.value) || 'Patient sous X' : '',
)

function navigate(target) {
  if (target === 'admission') admissionCriteria.value = {} // the menu starts a fresh admission
  view.value = target
}

function onPatientCreated(patient) {
  createdPatient.value = patient
  view.value = 'patient-created'
}

// no match in the admission search: create the patient, prefilled with the criteria
function createPatientForAdmission(criteria) {
  admissionCriteria.value = criteria
  view.value = 'admission-patient-form'
}

function openStayForm(patient, { justCreated = false, fromList = false } = {}) {
  stayPatient.value = patient
  stayPatientJustCreated.value = justCreated
  stayFromPatientList.value = fromList
  view.value = 'stay-form'
}

function onHospitalizationCreated(hospitalization) {
  createdHospitalization.value = hospitalization
  view.value = 'stay-created'
}
</script>

<template>
  <div class="layout">
    <AppSidebar
      :section="section"
      :selected-patient-name="selectedPatientName"
      @navigate="navigate"
    />
    <main class="main">
      <PatientsView
        v-if="view === 'patients'"
        v-model:selected="selectedPatient"
        @create="view = 'patient-form'"
        @create-stay="openStayForm($event, { fromList: true })"
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
      <AdmissionSearchView
        v-else-if="view === 'admission'"
        :initial-criteria="admissionCriteria"
        @update:criteria="admissionCriteria = $event"
        @select="openStayForm($event)"
        @create-patient="createPatientForAdmission"
      />
      <PatientFormView
        v-else-if="view === 'admission-patient-form'"
        for-admission
        :prefill="admissionCriteria"
        @created="openStayForm($event, { justCreated: true })"
        @cancel="view = 'admission'"
      />
      <StayFormView
        v-else-if="view === 'stay-form'"
        :patient="stayPatient"
        :patient-just-created="stayPatientJustCreated"
        :back-label="stayFromPatientList ? 'Retour à la liste' : 'Retour à la recherche'"
        @created="onHospitalizationCreated"
        @back="view = stayFromPatientList ? 'patients' : 'admission'"
      />
      <StayCreatedView
        v-else-if="view === 'stay-created'"
        :hospitalization="createdHospitalization"
        @new-admission="navigate('admission')"
        @patients="view = 'patients'"
      />
      <ComingSoonView v-else title="Calendrier" />
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
