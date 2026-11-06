<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import AppIcon from './components/AppIcon.vue'
import AppSidebar from './components/AppSidebar.vue'
import AdmissionSearchView from './views/AdmissionSearchView.vue'
import CalendarView from './views/CalendarView.vue'
import CareCreatedView from './views/CareCreatedView.vue'
import CareFormView from './views/CareFormView.vue'
import LoginView from './views/LoginView.vue'
import PatientCreatedView from './views/PatientCreatedView.vue'
import PatientFormView from './views/PatientFormView.vue'
import PatientRecordView from './views/PatientRecordView.vue'
import PatientsView from './views/PatientsView.vue'
import StayCreatedView from './views/StayCreatedView.vue'
import StayFormView from './views/StayFormView.vue'
import { getCurrentUser, listPatientHospitalizations } from './api.js'
import { patientName } from './format.js'
import { endSession, session, startSession } from './session.js'

// The page shown, with what it needs. Pages by section of the sidebar:
//   Patients:   patients, patient-form, patient-created, patient-record, patient-edit, stay-edit
//   Admission:  admission, admission-patient-form, stay-form, stay-created
//   Calendrier: calendar, care-form, care-created
// The stay and care forms also open from the patient pages: they then stay in that section.
// The first page after login is the calendar.
const HOME = 'calendar'
const page = ref({ name: HOME })
const go = (name, params = {}) => (page.value = { name, ...params })

// shared between pages
const selectedPatient = ref(null)
const calendar = ref({ service: true, mine: true, onlySelectedPatient: false })
const admissionCriteria = ref({})
// counts the care saved, for the sidebar to load them again
const savedCare = ref(0)

// ---- login ----
// Without a logged-in user, only the login page is shown. When the token expires, the
// login page replaces the app and the user comes back to the same page afterwards.

// a token saved by a previous visit: check it, and get the user it belongs to
const restoring = ref(false)
const restoreError = ref('')
async function restoreSession() {
  restoring.value = true
  restoreError.value = ''
  try {
    startSession(session.token, await getCurrentUser())
  } catch (e) {
    // a 401 has already ended the session (see api.js): the login page shows
    if (e.status !== 401) restoreError.value = e.message
  } finally {
    restoring.value = false
  }
}
onMounted(() => {
  if (session.token && !session.user) restoreSession()
})

// the next user starts from scratch
function resetState() {
  selectedPatient.value = null
  calendar.value = { service: true, mine: true, onlySelectedPatient: false }
  admissionCriteria.value = {}
  go(HOME)
}

function logout() {
  endSession()
  resetState()
}

// after an expired token, only the same user comes back to the page they were on
let lastUserId = null
watch(
  () => session.user?.id,
  (id) => {
    if (id == null) return
    if (lastUserId !== null && id !== lastUserId) resetState()
    lastUserId = id
  },
  { immediate: true },
)

// care opened from the patient list or record stays in the Patients section
const careSection = (origin) => (['list', 'record'].includes(origin) ? 'patients' : 'calendar')

const section = computed(() => {
  const { name, origin, careOrigin } = page.value
  if (['care-form', 'care-created'].includes(name)) return careSection(origin)
  if (name === 'calendar') return 'calendar'
  if (name === 'stay-form') return origin === 'care' ? careSection(careOrigin) : page.value.section
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

const openRecord = (patient, { focusStays = false } = {}) =>
  go('patient-record', { patientId: patient.id, focusStays })

// the sidebar shows the selected patient (allergies…): it gets the saved version
function onPatientSaved(patient) {
  if (selectedPatient.value?.id === patient.id) selectedPatient.value = patient
  openRecord(patient)
}

// the calendar filtered on one patient ("Voir le calendrier", "Retour au calendrier")
function openPatientCalendar(patient) {
  selectedPatient.value = patient
  calendar.value.onlySelectedPatient = true
  go('calendar')
}

// ---- stays ----

// origin: where the stay form was opened from, to come back there
//   'admission' (search), 'list' (patient list), 'record' (patient record), 'care' (care form)
//   careOrigin: for 'care', where the care form itself was opened from
function openStayForm(patient, { origin = 'admission', careDraft = null, careOrigin } = {}) {
  const sections = {
    admission: 'admission',
    list: 'patients',
    record: 'patients',
    care: 'calendar',
  }
  go('stay-form', { patient, origin, careDraft, careOrigin, section: sections[origin] })
}

function leaveStayForm() {
  const { origin, patient, careDraft, careOrigin } = page.value
  if (origin === 'list') go('patients')
  else if (origin === 'record') openRecord(patient)
  else if (origin === 'care') go('care-form', { patient, draft: careDraft, origin: careOrigin })
  else go('admission')
}

function onStayCreated(hospitalization) {
  const { origin, patient, careDraft, careOrigin } = page.value
  // created because a care needed a stay: resume planning that care
  if (origin === 'care') go('care-form', { patient, draft: careDraft, origin: careOrigin })
  else go('stay-created', { hospitalization })
}

// changing a stay: from its record ('record'), or from the patient list ('list')
const openStayEdit = (stay, origin) => go('stay-edit', { stay, origin })

const leaveStayEdit = () =>
  page.value.origin === 'list' ? go('patients') : openRecord(page.value.stay.patient)

// "Modifier le séjour" of the list: a patient with one stay goes straight to it,
// otherwise to the stays of their record, to choose one
async function editStayFromList(patient) {
  const from = page.value
  const stays = await listPatientHospitalizations(patient.id).catch(() => null)
  if (page.value !== from) return // the user went elsewhere meanwhile
  if (stays?.length === 1) openStayEdit(stays[0].encounter, 'list')
  else openRecord(patient, { focusStays: true })
}

const stayBackLabel = {
  admission: 'Retour à la recherche',
  list: 'Retour à la liste',
  record: 'Retour à la fiche',
  care: 'Retour au soin',
}

// ---- care ----

// origin: where the care form was opened from, to come back there
//   'calendar' (calendar, sidebar), 'list' (patient list), 'record' (patient record)
const planCare = (patient = null, origin = 'calendar') => go('care-form', { patient, origin })
const editCare = (appointment, origin = 'calendar') => go('care-form', { appointment, origin })

// a late care of the sidebar: back to the record or the list when one of them is shown
function openSidebarCare(appointment) {
  const { name, patientId } = page.value
  if (name === 'patient-record' && patientId === appointment.patient.id) {
    editCare(appointment, 'record')
  } else {
    editCare(appointment, section.value === 'patients' ? 'list' : 'calendar')
  }
}

const careBackLabel = {
  calendar: 'Retour au calendrier',
  list: 'Retour à la liste',
  record: 'Retour à la fiche',
}

// patient: the care's patient, to come back to their record or calendar
function leaveCare(patient) {
  const { origin, name } = page.value
  if (origin === 'list') go('patients')
  else if (origin === 'record' && patient) openRecord(patient)
  // after saving, the calendar shows the care just saved: the one of its patient
  else if (name === 'care-created') openPatientCalendar(patient)
  else go('calendar')
}
</script>

<template>
  <div v-if="restoring || restoreError" class="restoring">
    <template v-if="restoreError">
      <div class="notice notice-error" role="alert">
        <AppIcon name="alert-circle" :size="16" />
        {{ restoreError }}
      </div>
      <div class="buttons">
        <button type="button" class="btn" @click="logout">Se reconnecter</button>
        <button type="button" class="btn btn-primary" @click="restoreSession">Réessayer</button>
      </div>
    </template>
    <p v-else class="muted">Chargement…</p>
  </div>
  <LoginView v-else-if="!session.user" />
  <div v-else class="layout">
    <AppSidebar
      :section="section"
      v-model:show-service-care="calendar.service"
      v-model:show-my-care="calendar.mine"
      v-model:show-selected-patient="calendar.onlySelectedPatient"
      :selected-patient-name="selectedPatientName"
      :selected-patient="selectedPatient"
      :refresh-key="savedCare"
      @navigate="navigate"
      @open-care="openSidebarCare"
      @logout="logout"
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
        @edit-stay="editStayFromList"
        @plan-care="planCare($event, 'list')"
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
        :focus-stays="page.focusStays"
        @back="go('patients')"
        @edit="go('patient-edit', { patient: $event })"
        @add-stay="openStayForm($event, { origin: 'record' })"
        @edit-stay="openStayEdit($event, 'record')"
        @plan-care="planCare($event, 'record')"
        @open-care="editCare($event, 'record')"
      />
      <StayFormView
        v-else-if="page.name === 'stay-edit'"
        :key="`stay-edit-${page.stay.id}`"
        :patient="page.stay.patient"
        :stay="page.stay"
        :back-label="page.origin === 'list' ? 'Retour à la liste' : 'Retour à la fiche'"
        @saved="openRecord(page.stay.patient)"
        @deleted="openRecord(page.stay.patient)"
        @back="leaveStayEdit"
      />
      <PatientFormView
        v-else-if="page.name === 'patient-edit'"
        :key="`edit-${page.patient.id}`"
        :patient="page.patient"
        @saved="onPatientSaved"
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
        @created="openStayForm($event)"
        @cancel="go('admission')"
      />
      <StayFormView
        v-else-if="page.name === 'stay-form'"
        :key="`stay-${page.patient.id}`"
        :patient="page.patient"
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
        @plan-care="planCare($event, 'record')"
      />

      <!-- Calendrier -->
      <CareFormView
        v-else-if="page.name === 'care-form'"
        :key="`care-${page.appointment?.id ?? 'new'}-${page.patient?.id ?? ''}`"
        :initial-patient="page.patient ?? null"
        :appointment="page.appointment ?? null"
        :draft="page.draft ?? null"
        :back-label="careBackLabel[page.origin]"
        @saved="
          (a) => {
            savedCare++
            go('care-created', { appointment: a, created: !page.appointment, origin: page.origin })
          }
        "
        @cancel="leaveCare(page.patient ?? page.appointment?.patient)"
        @create-stay="
          ({ patient, draft }) =>
            openStayForm(patient, { origin: 'care', careDraft: draft, careOrigin: page.origin })
        "
      />
      <CareCreatedView
        v-else-if="page.name === 'care-created'"
        :appointment="page.appointment"
        :created="page.created"
        :back-label="careBackLabel[page.origin]"
        @plan-another="planCare($event, page.origin)"
        @back="leaveCare"
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
.restoring {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  min-height: 100vh;
  padding: 24px 16px;
}

.layout {
  display: flex;
  min-height: 100vh;
}

.main {
  flex: 1;
  min-width: 0;
}
</style>
