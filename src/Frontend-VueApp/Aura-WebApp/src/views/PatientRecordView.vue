<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import AppIcon from '../components/AppIcon.vue'
import { getPatient, listAppointments, listPatientHospitalizations } from '../api.js'
import {
  CARE_STATUSES,
  careWhen,
  formatDate,
  isLateCare,
  labelOf,
  patientName,
  practitionerName,
  stayEnd,
} from '../format.js'

const GENDER_LABELS = { female: 'Féminin', male: 'Masculin', other: 'Autre' }

const props = defineProps({
  patientId: { type: Number, required: true },
  // opened with "Modifier le séjour" from the patient list: the page scrolls to the stays
  focusStays: { type: Boolean, default: false },
})
const emit = defineEmits(['back', 'edit', 'add-stay', 'edit-stay', 'plan-care', 'open-care'])

const patient = ref(null)
const stays = ref([])
const appointments = ref([])
const loading = ref(true)
const error = ref('')

// the care are loaded on their own: an error there only shows in the care card
const careError = ref('')
async function loadCare() {
  careError.value = ''
  try {
    appointments.value = await listAppointments({ patientId: props.patientId })
  } catch (e) {
    careError.value = e.message
  }
}

async function load() {
  loading.value = true
  error.value = ''
  const care = loadCare()
  try {
    const [p, h] = await Promise.all([
      getPatient(props.patientId),
      listPatientHospitalizations(props.patientId),
    ])
    patient.value = p
    stays.value = h.map((x) => x.encounter)
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
  await care
}
const staysCard = ref(null)
onMounted(async () => {
  await load()
  if (!props.focusStays || error.value) return
  await nextTick()
  staysCard.value?.scrollIntoView?.({ block: 'start' })
})

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

const dateOf = (iso) => (iso ? iso.slice(0, 10) : '')

const countLabel = (n, word) => (n ? `${n} ${word}${n > 1 ? 's' : ''}` : `Aucun ${word}`)
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
        </div>
      </section>

      <section ref="staysCard" class="card">
        <div class="card-header with-action">
          <div>
            <h2 class="card-title">Informations du séjour</h2>
            <p class="card-description">{{ countLabel(stays.length, 'séjour') }}</p>
          </div>
        </div>

        <div class="card-body">
          <div v-for="stay in stays" :key="stay.id" class="stay">
            <dl>
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
                <dd :class="{ 'not-set': !stay.location }">
                  {{ stay.location || NOT_SET }}
                </dd>
              </div>
              <div>
                <dt>Séjour n°</dt>
                <dd>{{ stay.stay_number }}</dd>
              </div>
            </dl>
            <button type="button" class="btn btn-small" @click="emit('edit-stay', stay)">
              <AppIcon name="pencil" :size="14" />
              Modifier
            </button>
          </div>
          <p v-if="!stays.length" class="muted">Ce patient n’a aucun séjour.</p>

          <button type="button" class="add-stay" @click="emit('add-stay', patient)">
            <AppIcon name="plus" :size="16" />
            Ajouter un séjour
          </button>
        </div>
      </section>

      <section class="card">
        <div class="card-header with-action">
          <div>
            <h2 class="card-title">Informations des soins</h2>
            <p v-if="!careError" class="card-description">
              {{ countLabel(appointments.length, 'soin') }}
            </p>
          </div>
          <button type="button" class="btn btn-primary" @click="emit('plan-care', patient)">
            <AppIcon name="plus" :size="16" />
            Planifier un soin
          </button>
        </div>

        <div class="card-body">
          <div v-if="careError" class="notice notice-error" role="alert">
            <AppIcon name="alert-circle" :size="16" />
            <span>{{ careError }}</span>
            <button type="button" class="btn btn-small retry" @click="loadCare">Réessayer</button>
          </div>
          <table v-else-if="appointments.length" class="table care-table">
            <thead>
              <tr>
                <th>Date et heure</th>
                <th>Type de soin</th>
                <th>Soignant(s) en charge</th>
                <th>Statut</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="a in appointments"
                :key="a.id"
                title="Modifier le soin"
                @click="emit('open-care', a)"
              >
                <td>{{ careWhen(a) }}</td>
                <td class="care-type">{{ a.care_type }}</td>
                <td :class="{ 'not-set': !a.performers.length }">
                  {{ a.performers.map(practitionerName).join(', ') || NOT_SET }}
                </td>
                <td>
                  <span v-if="isLateCare(a)" class="status late">En retard</span>
                  <span v-else class="status" :class="a.status.toLowerCase()">
                    {{ labelOf(CARE_STATUSES, a.status) }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
          <p v-else class="muted">Aucun soin n’est planifié pour ce patient.</p>
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
  display: flex;
  align-items: center;
  gap: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--color-border);
}

.stay dl {
  display: grid;
  flex: 1;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
  margin: 0;
}

.care-table td {
  height: 52px;
}

.care-type {
  font-weight: 600;
}

.status {
  padding: 2px 8px;
  border-radius: 10px;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
}

.status.done {
  background: var(--color-success-soft);
  color: var(--color-success);
}

.status.cancelled {
  background: var(--color-surface-muted);
  color: var(--color-text-muted);
}

.status.late {
  background: var(--color-warning-soft);
  color: var(--color-warning);
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
