<script setup>
import AppIcon from './AppIcon.vue'
import SelectedPatientInfo from './SelectedPatientInfo.vue'
import { session } from '../session.js'

defineProps({
  section: { type: String, required: true },
  selectedPatientName: { type: String, default: '' },
  // the patient selected in the list: their allergies and late care are shown
  selectedPatient: { type: Object, default: null },
  // changes when a care is saved, to show the care as it is now
  refreshKey: { type: null, default: null },
})
const emit = defineEmits(['navigate', 'logout', 'open-care'])
// what the calendar shows: the department's care, the user's own care,
// or only the care and stays of the patient selected in the list
const showServiceCare = defineModel('showServiceCare', { type: Boolean, default: true })
const showMyCare = defineModel('showMyCare', { type: Boolean, default: true })
const showSelectedPatient = defineModel('showSelectedPatient', { type: Boolean, default: false })

const NAV_ITEMS = [
  { id: 'calendar', label: 'Calendrier', icon: 'calendar' },
  { id: 'patients', label: 'Patients', icon: 'circle-user' },
  { id: 'admission', label: 'Nouvelle Admission', icon: 'plus' },
]
</script>

<template>
  <aside class="sidebar">
    <div class="brand">
      <AppIcon name="calendar-days" :size="22" class="brand-icon" />
      <span class="brand-name">SI HCL</span>
    </div>

    <nav class="nav" aria-label="Navigation principale">
      <button
        v-for="item in NAV_ITEMS"
        :key="item.id"
        type="button"
        class="nav-item"
        :class="{ active: section === item.id }"
        :aria-current="section === item.id ? 'page' : undefined"
        @click="emit('navigate', item.id)"
      >
        <AppIcon :name="item.icon" />
        {{ item.label }}
      </button>
    </nav>

    <section class="calendars">
      <div class="calendars-heading">
        <span>Calendriers</span>
      </div>
      <label class="calendar-option">
        <input v-model="showServiceCare" type="checkbox" class="checkbox checkbox-grey" />
        Soins du service
      </label>
      <label class="calendar-option">
        <input v-model="showMyCare" type="checkbox" class="checkbox" />
        Mes soins
      </label>
      <label class="calendar-option">
        <input
          v-model="showSelectedPatient"
          type="checkbox"
          class="checkbox checkbox-blue"
          :disabled="!selectedPatientName"
          title="Sélectionnez un patient dans la liste Patients"
        />
        <span>
          Du patient sélectionné :<br />
          <strong>{{ selectedPatientName || 'aucun' }}</strong>
        </span>
      </label>
    </section>

    <SelectedPatientInfo
      v-if="selectedPatient"
      :key="selectedPatient.id"
      :patient="selectedPatient"
      :refresh-key="refreshKey"
      @open-care="emit('open-care', $event)"
    />

    <div v-if="session.user" class="account">
      <div class="avatar">
        {{ (session.user.name_given || session.user.name_family || session.user.username)[0] }}
      </div>
      <div>
        <div class="account-name">
          {{
            [session.user.name_given, session.user.name_family].filter(Boolean).join(' ') ||
            session.user.username
          }}
        </div>
        <div class="account-status">Statut : {{ session.user.profession || 'Non renseigné' }}</div>
      </div>
    </div>
    <button type="button" class="nav-item logout" @click="emit('logout')">
      <AppIcon name="log-out" />
      Déconnexion
    </button>
  </aside>
</template>

<style scoped>
.sidebar {
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  width: 232px;
  /* stays in place while the page scrolls; scrolls on its own if taller than the screen */
  position: sticky;
  top: 0;
  height: 100vh;
  overflow-y: auto;
  padding: 28px 16px 20px;
  border-right: 1px solid var(--color-border);
  background: var(--color-sidebar);
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  height: 28px;
  padding: 0 12px;
}

.brand-icon {
  color: var(--color-primary);
}

.brand-name {
  font-size: 18px;
  font-weight: 600;
  letter-spacing: -0.5px;
}

.nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding-top: 36px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  height: 40px;
  padding: 0 12px;
  border: none;
  border-radius: var(--radius);
  background: transparent;
  color: var(--color-text-faint);
  font-size: 14px;
  font-weight: 600;
  text-align: left;
  cursor: pointer;
}

.nav-item:hover {
  background: var(--color-primary-soft);
}

.nav-item.active {
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-weight: 700;
}

.calendars {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 36px 12px 0;
}

.calendars-heading {
  display: flex;
  justify-content: space-between;
  color: var(--color-text-muted);
  font-size: 12px;
  font-weight: 500;
}

.calendar-option {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
}

.checkbox-grey {
  accent-color: var(--color-text-muted);
}

.checkbox-blue {
  accent-color: var(--color-patient);
}

.account {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: auto;
  padding: 8px;
  border-top: 1px solid var(--color-border);
}

.avatar {
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--color-avatar);
  color: var(--color-text-muted);
  font-size: 11px;
  font-weight: 600;
}

.account-name {
  font-weight: 500;
}

.account-status {
  margin-top: 5px;
  font-size: 10px;
}

.logout {
  color: var(--color-text-muted);
  font-weight: 400;
}
</style>
