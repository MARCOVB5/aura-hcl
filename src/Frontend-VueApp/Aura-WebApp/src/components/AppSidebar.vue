<script setup>
import { ref } from 'vue'
import AppIcon from './AppIcon.vue'

defineProps({
  section: { type: String, required: true },
  selectedPatientName: { type: String, default: '' },
})
const emit = defineEmits(['navigate'])

const NAV_ITEMS = [
  { id: 'calendar', label: 'Calendrier', icon: 'calendar' },
  { id: 'patients', label: 'Patients', icon: 'circle-user' },
  { id: 'admission', label: 'Nouvelle Admission', icon: 'plus' },
]

// calendar filters: no effect until the calendar exists
const showServiceCare = ref(true)
const showMyCare = ref(true)
const showSelectedPatient = ref(false)
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
        <AppIcon name="plus" :size="15" />
      </div>
      <label class="calendar-option">
        <input v-model="showServiceCare" type="checkbox" class="checkbox" />
        Soins du service
      </label>
      <label class="calendar-option">
        <input v-model="showMyCare" type="checkbox" class="checkbox checkbox-grey" />
        Mes soins
      </label>
      <label class="calendar-option">
        <input v-model="showSelectedPatient" type="checkbox" class="checkbox" />
        <span>
          Du patient sélectionné :<br />
          <strong>{{ selectedPatientName || 'aucun' }}</strong>
        </span>
      </label>
    </section>

    <div class="account">
      <div class="avatar">B</div>
      <div>
        <div class="account-name">Bruno</div>
        <div class="account-status">Statut : Médecin</div>
      </div>
    </div>
    <button type="button" class="nav-item logout">
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
  min-height: 100vh;
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
