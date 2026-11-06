# Aura

Application de gestion des soins en réanimation : patients, séjours et agenda des soins.

- `src/backend/` : API FastAPI ([README](src/backend/README.md))
- `src/Frontend-VueApp/Aura-WebApp/` : application Vue ([README](src/Frontend-VueApp/Aura-WebApp/README.md))
- `database/` : image Docker de la base MariaDB

## Installation rapide (Docker)

Il faut seulement Docker :

- Windows et macOS : installez [Docker Desktop](https://www.docker.com/products/docker-desktop/) (il contient Docker Compose), puis ouvrez-le. Il doit rester ouvert pendant l'installation et l'utilisation.
- Linux : installez [Docker Engine](https://docs.docker.com/engine/install/) avec le paquet `docker-compose-plugin`, puis lancez `sudo usermod -aG docker $USER` et reconnectez-vous (sinon, lancez le script avec `sudo`).

Depuis la racine du dépôt, lancez `sh install.sh` (Linux, macOS) ou `install.bat` (Windows).

Le script construit et démarre la base, l'API et l'application. Ouvrez ensuite http://localhost:5173 et connectez-vous avec
`demo.medecin`, `demo.infirmier` ou `demo.kine`, mot de passe `abc`.

- Arrêter : `docker compose down`
- Relancer : `docker compose up -d`
- Après un `git pull` : `docker compose up -d --build`

Les ports 3306 (base), 8000 (API) et 5173 (application) doivent être libres. Si besoin (facultatif), arrêtez avant un MySQL ou MariaDB installé sur la machine, ainsi que `uv run fastapi dev` et `npm run dev` s'ils sont lancés.
Pour garder un MySQL déjà installé, ajoutez plutôt la ligne `DB_PORT=3307` au fichier `.env` à la racine (créé par le script).

## Installation pour le développement

Il faut [uv](https://docs.astral.sh/uv/getting-started/installation/), [Node.js](https://nodejs.org/) et Docker avec Docker Compose.

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
