<script setup>
import { computed, ref } from 'vue'
import AppSidebar from './components/AppSidebar.vue'
import AdmissionSearchView from './views/AdmissionSearchView.vue'
import CalendarView from './views/CalendarView.vue'
import CareCreatedView from './views/CareCreatedView.vue'
import CareFormView from './views/CareFormView.vue'
import PatientCreatedView from './views/PatientCreatedView.vue'
import PatientFormView from './views/PatientFormView.vue'
import PatientRecordView from './views/PatientRecordView.vue'
import PatientsView from './views/PatientsView.vue'
import StayCreatedView from './views/StayCreatedView.vue'
import StayFormView from './views/StayFormView.vue'
import { patientName } from './format.js'

// The page shown, with what it needs. Pages by section of the sidebar:
//   Patients:   patients, patient-form, patient-created, patient-record, patient-edit
//   Admission:  admission, admission-patient-form, stay-form, stay-created
//   Calendrier: calendar, care-form, care-created
const page = ref({ name: 'patients' })
const go = (name, params = {}) => (page.value = { name, ...params })

// shared between pages
const selectedPatient = ref(null)
const calendar = ref({ service: true, mine: true, onlySelectedPatient: false })
const admissionCriteria = ref({})

const section = computed(() => {
  const name = page.value.name
  if (['calendar', 'care-form', 'care-created'].includes(name)) return 'calendar'
  if (name === 'stay-form') return page.value.origin === 'care' ? 'calendar' : page.value.section
  if (['admission', 'admission-patient-form', 'stay-created'].includes(name)) return 'admission'
  return 'patients'
})
const selectedPatientName = computed(() =>
  selectedPatient.value ? patientName(selectedPatient.value) || 'Patient sous X' : '',
)

function navigate(target) {
  if (target === 'admission') admissionCriteria.value = {} // the menu starts a fresh admission
  go(target)
}

// ---- patients ----

const openRecord = (patient) => go('patient-record', { patientId: patient.id })

// the calendar filtered on one patient ("Voir le calendrier", "Retour au calendrier")
function openPatientCalendar(patient) {
  selectedPatient.value = patient
  calendar.value.onlySelectedPatient = true
  go('calendar')
}

// ---- stays ----

// origin: where the stay form was opened from, to come back there
//   'admission' (search), 'list' (patient list), 'record' (patient record), 'care' (care form)
function openStayForm(
  patient,
  { origin = 'admission', justCreated = false, careDraft = null } = {},
) {
  const sections = {
    admission: 'admission',
    list: 'patients',
    record: 'patients',
    care: 'calendar',
  }
  go('stay-form', { patient, origin, justCreated, careDraft, section: sections[origin] })
}

function leaveStayForm() {
  const { origin, patient, careDraft } = page.value
  if (origin === 'list') go('patients')
  else if (origin === 'record') openRecord(patient)
  else if (origin === 'care') go('care-form', { patient, draft: careDraft })
  else go('admission')
}

function onStayCreated(hospitalization) {
  const { origin, patient, careDraft } = page.value
  // created because a care needed a stay: resume planning that care
  if (origin === 'care') go('care-form', { patient, draft: careDraft })
  else go('stay-created', { hospitalization })
}

const stayBackLabel = {
  admission: 'Retour à la recherche',
  list: 'Retour à la liste',
  record: 'Retour à la fiche',
  care: 'Retour au soin',
}

// ---- care ----

const planCare = (patient = null) => go('care-form', { patient })
const editCare = (appointment) => go('care-form', { appointment })
</script>

<template>
  <div class="layout">
    <AppSidebar
      :section="section"
      v-model:show-service-care="calendar.service"
      v-model:show-my-care="calendar.mine"
      v-model:show-selected-patient="calendar.onlySelectedPatient"
      :selected-patient-name="selectedPatientName"
      @navigate="navigate"
    />
    <main class="main">
      <!-- Patients -->
      <PatientsView
        v-if="page.name === 'patients'"
        v-model:selected="selectedPatient"
        @create="go('patient-form')"
        @create-stay="openStayForm($event, { origin: 'list' })"
        @open="openRecord"
        @edit="go('patient-edit', { patient: $event })"
      />
      <PatientFormView
        v-else-if="page.name === 'patient-form'"
        @created="go('patient-created', { patient: $event })"
        @cancel="go('patients')"
      />
      <PatientCreatedView
        v-else-if="page.name === 'patient-created'"
        :patient="page.patient"
        @back="go('patients')"
        @calendar="openPatientCalendar(page.patient)"
      />
      <PatientRecordView
        v-else-if="page.name === 'patient-record'"
        :key="page.patientId"
        :patient-id="page.patientId"
        @back="go('patients')"
        @edit="go('patient-edit', { patient: $event })"
        @add-stay="openStayForm($event, { origin: 'record' })"
      />
      <PatientFormView
        v-else-if="page.name === 'patient-edit'"
        :key="`edit-${page.patient.id}`"
        :patient="page.patient"
        @saved="openRecord"
        @cancel="openRecord(page.patient)"
      />

      <!-- Admission -->
      <AdmissionSearchView
        v-else-if="page.name === 'admission'"
        :initial-criteria="admissionCriteria"
        @update:criteria="admissionCriteria = $event"
        @select="openStayForm($event)"
        @create-patient="
          (criteria) => {
            admissionCriteria = criteria
            go('admission-patient-form')
          }
        "
      />
      <PatientFormView
        v-else-if="page.name === 'admission-patient-form'"
        for-admission
        :prefill="admissionCriteria"
        @created="openStayForm($event, { justCreated: true })"
        @cancel="go('admission')"
      />
      <StayFormView
        v-else-if="page.name === 'stay-form'"
        :key="`stay-${page.patient.id}`"
        :patient="page.patient"
        :patient-just-created="page.justCreated"
        :for-care="page.origin === 'care'"
        :back-label="stayBackLabel[page.origin]"
        @created="onStayCreated"
        @back="leaveStayForm"
      />
      <StayCreatedView
        v-else-if="page.name === 'stay-created'"
        :hospitalization="page.hospitalization"
        @new-admission="navigate('admission')"
        @record="openRecord"
      />

      <!-- Calendrier -->
      <CareFormView
        v-else-if="page.name === 'care-form'"
        :key="`care-${page.appointment?.id ?? 'new'}-${page.patient?.id ?? ''}`"
        :initial-patient="page.patient ?? null"
        :appointment="page.appointment ?? null"
        :draft="page.draft ?? null"
        @saved="(a) => go('care-created', { appointment: a, created: !page.appointment })"
        @cancel="go('calendar')"
        @create-stay="
          ({ patient, draft }) => openStayForm(patient, { origin: 'care', careDraft: draft })
        "
      />
      <CareCreatedView
        v-else-if="page.name === 'care-created'"
        :appointment="page.appointment"
        :created="page.created"
        @plan-another="planCare"
        @calendar="openPatientCalendar"
      />
      <CalendarView
        v-else
        :show-service="calendar.service"
        :show-mine="calendar.mine"
        :patient-filter="calendar.onlySelectedPatient ? selectedPatient : null"
        @plan-care="planCare(calendar.onlySelectedPatient ? selectedPatient : null)"
        @edit-care="editCare"
      />
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
