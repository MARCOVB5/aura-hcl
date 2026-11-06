# Aura WebApp

Application Vue 3 (Vite).

## Installation

Il faut [Node.js](https://nodejs.org/) et le backend lancé (voir `src/backend/README.md`).

```sh
npm install
npm run dev
```

Ouvrez http://localhost:5173 et connectez-vous avec un compte de démonstration (`demo.medecin`, `demo.infirmier` ou `demo.kine`).

Le frontend appelle le backend sur http://127.0.0.1:8000. Pour une autre adresse, créez un fichier `.env` ici avec :

```
VITE_API_URL=http://127.0.0.1:8000
```

Tests : `npm run test:unit`.
