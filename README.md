# Aura

Application de gestion des soins en réanimation : patients, séjours et agenda des soins.

- `src/backend/` : API FastAPI ([README](src/backend/README.md))
- `src/Frontend-VueApp/Aura-WebApp/` : application Vue ([README](src/Frontend-VueApp/Aura-WebApp/README.md))
- `database/` : image Docker de la base MariaDB

## Prérequis

- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- [Node.js](https://nodejs.org/)
- Docker avec Docker Compose

## Installation

Depuis la racine du dépôt :

```bash
docker compose up -d db
cp src/backend/.env.example src/backend/.env
```

Sous Windows (cmd), utilisez `copy` au lieu de `cp`.

Dans `src/backend/.env`, remplacez `JWT_SECRET` par le résultat de :

```bash
uv run python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Puis :

```bash
cd src/backend
uv sync
uv run alembic upgrade head
uv run python scripts/populate_practitioners.py
cd ../Frontend-VueApp/Aura-WebApp
npm install
```

La commande `populate_practitioners.py` demande un mot de passe et crée trois comptes avec :
`demo.medecin`, `demo.infirmier` et `demo.kine`.

## Lancement

Dans un terminal :

```bash
cd src/backend
uv run fastapi dev
```

Dans un autre :

```bash
cd src/Frontend-VueApp/Aura-WebApp
npm run dev
```

Ouvrez http://localhost:5173 et connectez-vous avec un des comptes de démonstration.

## Documentation

- [Vision](docs/product/vision.md)
- [Périmètre](docs/product/scope.md)
- [Exigences](docs/requirements/requirements.md)
- [Stratégie de test](docs/testing/test-strategy.md)
- [Definition of Ready](docs/agile/definition-of-ready.md)
- [Definition of Done](docs/agile/definition-of-done.md)
