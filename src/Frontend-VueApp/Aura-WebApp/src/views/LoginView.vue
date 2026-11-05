<script setup>
import { computed, ref } from 'vue'
import AppIcon from '../components/AppIcon.vue'
import { getCurrentUser, login } from '../api.js'
import { session, startSession } from '../session.js'

// Figma frame "Authentification"
const username = ref('')
const password = ref('')
const showPassword = ref(false)
const submitting = ref(false)
const error = ref('')

const canSubmit = computed(
  () => username.value.trim() !== '' && password.value !== '' && !submitting.value,
)

function reset() {
  username.value = ''
  password.value = ''
  error.value = ''
}

async function submit() {
  if (!canSubmit.value) return
  submitting.value = true
  error.value = ''
  try {
    const { access_token } = await login(username.value.trim(), password.value)
    startSession(access_token, await getCurrentUser(access_token))
  } catch (e) {
    error.value = e.message
    password.value = ''
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <main class="login-page">
    <form class="card login" novalidate @submit.prevent="submit">
      <div class="login-header">
        <h1 class="card-title">Authentification</h1>
        <div class="hcl-logo" role="img" aria-label="Hospices Civils de Lyon">
          <strong>HCL</strong>
          <span>Hospices civils<br />de Lyon</span>
        </div>
      </div>

      <div class="card-body">
        <div v-if="session.expired && !error" class="notice notice-warning" role="status">
          <AppIcon name="clock" :size="16" />
          Votre session a expiré : reconnectez-vous.
        </div>
        <div v-if="error" class="notice notice-error" role="alert">
          <AppIcon name="alert-circle" :size="16" />
          {{ error }}
        </div>

        <div class="credentials">
          <div class="field">
            <label class="field-label" for="login-username">Identifiant *</label>
            <input
              id="login-username"
              v-model="username"
              class="input"
              autocomplete="username"
              autocapitalize="none"
              spellcheck="false"
              required
              autofocus
            />
          </div>
          <div class="field">
            <label class="field-label" for="login-password">Mot de passe *</label>
            <div class="password">
              <input
                id="login-password"
                v-model="password"
                class="input"
                :type="showPassword ? 'text' : 'password'"
                autocomplete="current-password"
                required
              />
              <button
                type="button"
                class="eye"
                :aria-label="showPassword ? 'Masquer le mot de passe' : 'Afficher le mot de passe'"
                :aria-pressed="showPassword"
                @click="showPassword = !showPassword"
              >
                <AppIcon :name="showPassword ? 'eye-off' : 'eye'" :size="18" />
              </button>
            </div>
          </div>
        </div>

        <div class="actions">
          <span class="muted">* Champs obligatoires</span>
          <div class="buttons">
            <button type="button" class="btn" @click="reset">Annuler</button>
            <button type="submit" class="btn btn-primary" :disabled="!canSubmit">
              {{ submitting ? 'Connexion…' : 'Se connecter' }}
            </button>
          </div>
        </div>
      </div>
    </form>
  </main>
</template>

<style scoped>
.login-page {
  display: grid;
  place-items: center;
  min-height: 100vh;
  padding: 24px 16px;
}

.login {
  width: 100%;
  max-width: 760px;
  border-color: var(--color-primary);
}

.login-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 20px 24px 0;
}

.hcl-logo {
  display: flex;
  flex-shrink: 0;
  flex-direction: column;
  justify-content: center;
  width: 56px;
  height: 56px;
  padding: 0 8px;
  background: #00a3e0;
  color: #fff;
  line-height: 1;
}

.hcl-logo strong {
  font-size: 17px;
  font-weight: 800;
  letter-spacing: -0.5px;
}

.hcl-logo span {
  margin-top: 3px;
  font-size: 4.5px;
  font-weight: 700;
  text-transform: uppercase;
}

/* the fields, centred in a box of their own */
.credentials {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  padding: 32px 16px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
}

.credentials .field {
  width: 100%;
  max-width: 250px;
  text-align: center;
}

.password {
  position: relative;
}

.password .input {
  padding-right: 40px;
}

.eye {
  position: absolute;
  top: 50%;
  right: 8px;
  display: grid;
  place-items: center;
  padding: 4px;
  border: none;
  background: transparent;
  color: var(--color-patient);
  cursor: pointer;
  transform: translateY(-50%);
}
</style>
