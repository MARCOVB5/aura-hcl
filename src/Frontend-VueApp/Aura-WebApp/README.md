# Aura WebApp

Application Vue 3 utilisant Vite. L'utilisateur doit dans un premier lieu s'authentifier en tant que soignant. Il découvre ainsi un agenda des soins qu'il a effectué et qu'il aura à effectuer.

## Lancer le projet

```sh
npm install
npm run dev
```

Ouvrez l’adresse locale affichée dans le terminal (http://localhost:5173).

Le backend (`src/backend`, voir son README) doit tourner sur http://127.0.0.1:8000. Pour utiliser une autre adresse, créez un fichier `.env` ici avec :

```
VITE_API_URL=http://127.0.0.1:8000
```

Tests : `npm run test:unit`.

## Dossiers du projet

- `src/` contient le code de l’application.
- `src/views/` contient les pages (liste des patients, création d’un patient…).
- `src/components/` contient les composants Vue réutilisables.
- `src/api.js` contient les appels au backend.
- `src/assets/` contient les styles et ressources utilisés par l’application.
- `public/` contient les fichiers servis tels quels, comme les images.
