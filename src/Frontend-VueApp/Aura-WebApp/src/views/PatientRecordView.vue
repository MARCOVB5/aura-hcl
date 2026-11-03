<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import AppIcon from '../components/AppIcon.vue'
import DateInput from '../components/DateInput.vue'
import {
  deleteHospitalization,
  getPatient,
  listLocations,
  listPatientHospitalizations,
  updateHospitalization,
} from '../api.js'
import { formatDate, patientName, stayEnd } from '../format.js'

const GENDER_LABELS = { female: 'Féminin', male: 'Masculin', other: 'Autre' }

const props = defineProps({
  patientId: { type: Number, required: true },
})
const emit = defineEmits(['back', 'edit', 'add-stay'])

const patient = ref(null)
const stays = ref([])
const locations = ref([])
const loading = ref(true)
const error = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [p, h, l] = await Promise.all([
      getPatient(props.patientId),
      listPatientHospitalizations(props.patientId),
      listLocations(),
    ])
    patient.value = p
    stays.value = h.map((x) => x.encounter)
    locations.value = l
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
onMounted(load)

const NOT_SET = 'Non renseigné'
const name = computed(() => (patient.value ? patientName(patient.value) || 'Patient sous X' : ''))
const fields = computed(() => {
  const p = patient.value
  if (!p) return []
  return [
    { label: 'Nom', value: p.person.name_family, span: 'third' },
    { label: 'Prénom', value: p.person.name_given, span: 'third' },
    {
      label: 'Patient sous X',
      value: p.identification_status === 'UNKNOWN' ? 'Oui' : 'Non',
      span: 'third',
    },
    { label: 'Sexe', value: GENDER_LABELS[p.person.gender] },
    { label: 'Date de naissance', value: formatDate(p.person.birth_date) },
    { label: 'Contact', value: p.contact },
    { label: 'IPP', value: p.ipp },
    { label: 'Informations personnelles', value: p.personal_info, span: 'half' },
  ]
})

// ---- stays: read mode, or edit mode with one row per stay ----

const editingStays = ref(false)
const drafts = ref([]) // { id, start, end, locationId, removed }
const savingStays = ref(false)
const staysError = ref('')

const dateOf = (iso) => (iso ? iso.slice(0, 10) : '')

function startEditing() {
  drafts.value = stays.value.map((s) =>
    reactive({
      id: s.id,
      start: dateOf(s.admission_date),
      end: dateOf(s.actual_discharge_date),
      locationId: s.current_location?.id ?? '',
      removed: false,
    }),
  )
  staysError.value = ''
  editingStays.value = true
}

// the date inputs only change the day: the time of the original value is kept
function withDay(day, originalIso, defaultTime) {
  const time = originalIso ? originalIso.slice(11, 19) : defaultTime
  return `${day}T${time}`
}

async function saveStays() {
  savingStays.value = true
  staysError.value = ''
  let saved = 0 // stays already changed when an error stops the loop
  try {
    for (const draft of drafts.value) {
      const stay = stays.value.find((s) => s.id === draft.id)
      if (!stay) continue // deleted by a previous attempt
      if (draft.removed) {
        await deleteHospitalization(draft.id)
        saved++
        continue
      }
      const changes = {}
      if (draft.start && draft.start !== dateOf(stay.admission_date))
        changes.admission_date = withDay(draft.start, stay.admission_date, '08:00:00')
      if (draft.end !== dateOf(stay.actual_discharge_date))
        changes.actual_discharge_date = draft.end
          ? withDay(draft.end, stay.actual_discharge_date, '12:00:00')
          : null
      if ((draft.locationId || null) !== (stay.current_location?.id ?? null))
        changes.current_location_id = draft.locationId || null
      if (Object.keys(changes).length) {
        await updateHospitalization(draft.id, changes)
        saved++
      }
    }
    editingStays.value = false
  } catch (e) {
    staysError.value = saved
      ? `${e.message} Les modifications précédentes ont été enregistrées.`
      : e.message
  } finally {
    savingStays.value = false
    // what was saved before an error is kept: show the stays as they are now
    const h = await listPatientHospitalizations(props.patientId).catch(() => null)
    if (h) stays.value = h.map((x) => x.encounter)
  }
}
</script>

<template>
  <header class="page-header">
    <h2 class="service-name">Service de réanimation</h2>
    <div class="title-row">
      <div>
        <h1 class="page-title">{{ loading ? 'Fiche patient' : name }}</h1>
        <p class="page-description">
          Fiche patient · Identifiant : {{ patient?.ipp || 'non renseigné' }}
        </p>
      </div>
      <button type="button" class="btn btn-small" @click="emit('back')">
        <AppIcon name="chevron-left" :size="14" />
        Retour aux patients
      </button>
    </div>
  </header>

  <div class="page-content">
    <div v-if="error" class="notice notice-error" role="alert">
      <AppIcon name="alert-circle" :size="16" />
      <span>{{ error }}</span>
      <button type="button" class="btn btn-small retry" @click="load">Réessayer</button>
    </div>
    <p v-else-if="loading" class="muted">Chargement…</p>

    <template v-else>
      <section class="card">
        <div class="card-header with-action">
          <div>
            <h2 class="card-title">Informations du patient</h2>
            <p class="card-description">Identité et informations personnelles</p>
          </div>
          <button type="button" class="btn btn-primary" @click="emit('edit', patient)">
            <AppIcon name="pencil" :size="16" />
            Modifier les informations
          </button>
        </div>
        <div class="card-body">
          <dl class="fields">
            <div v-for="f in fields" :key="f.label" :class="f.span">
              <dt>{{ f.label }}</dt>
              <dd :class="{ 'not-set': !f.value }">{{ f.value || NOT_SET }}</dd>
            </div>
            <div class="half">
              <dt>Allergies</dt>
              <dd v-if="patient.allergies.length" class="allergy">
                {{ patient.allergies.map((a) => a.name).join(', ') }}
              </dd>
              <dd v-else class="not-set">{{ NOT_SET }}</dd>
            </div>
          </dl>
          <div class="notice">
            Les informations absentes du dossier sont indiquées « Non renseigné ».
          </div>
        </div>
      </section>

      <section class="card">
        <div class="card-header with-action">
          <div>
            <h2 class="card-title">Informations du séjour</h2>
            <p class="card-description">
              {{
                stays.length
                  ? `${stays.length} séjour${stays.length > 1 ? 's' : ''}`
                  : 'Aucun séjour'
              }}
            </p>
          </div>
          <div v-if="editingStays" class="buttons">
            <button type="button" class="btn" :disabled="savingStays" @click="editingStays = false">
              Annuler
            </button>
            <button
              type="button"
              class="btn btn-primary"
              :disabled="savingStays"
              @click="saveStays"
            >
              {{ savingStays ? 'Enregistrement…' : 'Enregistrer' }}
            </button>
          </div>
          <button
            v-else-if="stays.length"
            type="button"
            class="btn btn-small"
            @click="startEditing"
          >
            <AppIcon name="pencil" :size="14" />
            Modifier le séjour
          </button>
        </div>

        <div class="card-body">
          <div v-if="staysError" class="notice notice-error" role="alert">
            <AppIcon name="alert-circle" :size="16" />
            {{ staysError }}
          </div>

          <template v-if="!editingStays">
            <dl v-for="stay in stays" :key="stay.id" class="stay">
              <div>
                <dt>Date de début</dt>
                <dd>{{ formatDate(dateOf(stay.admission_date)) }}</dd>
              </div>
              <div>
                <dt>Date de fin</dt>
                <dd :class="{ 'not-set': !stayEnd(stay) }">
                  {{ stayEnd(stay) ? formatDate(dateOf(stayEnd(stay))) : 'En cours' }}
                  <span
                    v-if="!stay.actual_discharge_date && stay.expected_discharge_date"
                    class="muted"
                  >
                    (prévue)
                  </span>
                </dd>
              </div>
              <div>
                <dt>Localisation</dt>
                <dd :class="{ 'not-set': !stay.current_location }">
                  {{ stay.current_location?.name || NOT_SET }}
                </dd>
              </div>
              <div>
                <dt>Séjour n°</dt>
                <dd>{{ stay.stay_number }}</dd>
              </div>
            </dl>
            <p v-if="!stays.length" class="muted">Ce patient n’a aucun séjour.</p>
          </template>

          <template v-else>
            <div
              v-for="draft in drafts"
              :key="draft.id"
              class="stay-row"
              :class="{ removed: draft.removed }"
            >
              <label class="field">
                <span class="field-label">Date de début</span>
                <DateInput v-model="draft.start" :disabled="draft.removed" />
              </label>
              <label class="field">
                <span class="field-label">Date de fin</span>
                <DateInput v-model="draft.end" :min="draft.start" :disabled="draft.removed" />
              </label>
              <label class="field">
                <span class="field-label">Localisation</span>
                <select v-model="draft.locationId" class="input" :disabled="draft.removed">
                  <option value="">Non renseignée</option>
                  <option v-for="l in locations" :key="l.id" :value="l.id">{{ l.name }}</option>
                </select>
              </label>
              <button
                type="button"
                class="icon-btn delete"
                :aria-label="draft.removed ? 'Annuler la suppression' : 'Supprimer ce séjour'"
                :title="draft.removed ? 'Annuler la suppression' : 'Supprimer ce séjour'"
                @click="draft.removed = !draft.removed"
              >
                <AppIcon :name="draft.removed ? 'x' : 'trash'" :size="20" />
              </button>
            </div>
          </template>

          <button type="button" class="add-stay" @click="emit('add-stay', patient)">
            <AppIcon name="plus" :size="16" />
            Ajouter un séjour
          </button>
        </div>
      </section>
    </template>
  </div>
</template>

<style scoped>
.with-action {
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.retry {
  margin-left: auto;
}

.fields {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: 24px;
  margin: 0;
}

.fields > div {
  grid-column: span 3;
}

.fields > .third {
  grid-column: span 4;
}

.fields > .half {
  grid-column: span 6;
}

@media (max-width: 1000px) {
  .fields > div,
  .fields > .third,
  .fields > .half {
    grid-column: span 12;
  }
}

dt {
  margin-bottom: 6px;
  color: var(--color-text-muted);
}

dd {
  margin: 0;
  font-size: 14px;
  white-space: pre-line;
}

.not-set {
  color: var(--color-text-muted);
}

.stay {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
  margin: 0;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--color-border);
}

.stay-row {
  display: grid;
  grid-template-columns: 1fr 1fr 1.4fr 40px;
  align-items: end;
  gap: 20px;
}

.stay-row.removed .field {
  opacity: 0.45;
}

.icon-btn {
  display: grid;
  place-items: center;
  height: 44px;
  border: none;
  background: transparent;
  cursor: pointer;
}

.delete {
  color: var(--color-danger);
}

.add-stay {
  display: inline-flex;
  align-items: center;
  align-self: flex-start;
  gap: 8px;
  padding: 0;
  border: none;
  background: transparent;
  color: var(--color-success);
  cursor: pointer;
}
</style>
