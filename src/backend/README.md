# Backend

FastAPI API on MariaDB. MariaDB runs in Docker, and the tables are created and
updated by Alembic migrations (`migrations/versions/`).

## Requirements

- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Docker with Docker Compose (Linux: your user must be in the `docker` group)

## Setup (once)

From the repository root:

```bash
docker compose up -d db                       # start MariaDB (first start creates the database and user)
docker compose ps                             # wait until the status shows "healthy"
cp src/backend/.env.example src/backend/.env  # tells the backend where the database is
cd src/backend
uv sync
uv run alembic upgrade head                   # create the tables
```

If running on Windows, use `copy` instead of `cp`.

## Run

```bash
cd src/backend
uv run fastapi dev
```

Open http://127.0.0.1:8000/docs to see and try the endpoints.
The frontend dev server (`http://localhost:5173`) is allowed to call the API.

The database must be running (`docker compose up -d db`). It keeps its data between restarts.

## After a `git pull`

```bash
uv sync                       # new dependencies
uv run alembic upgrade head   # new migrations
```

## Changing a model

The models in `src/app/models/` describe the tables. A change only reaches the database through a migration:

1. Edit the model. If it is a new file, import it in `src/app/models/__init__.py`, otherwise Alembic does not see it.
2. Generate the migration: `uv run alembic revision --autogenerate -m "some description"`
3. **Read the generated file** in `migrations/versions/`. Autogenerate cannot detect renames:
   it writes "drop + add", which loses the data. Use `op.alter_column` instead.
4. Apply it: `uv run alembic upgrade head`
5. Commit the model change and the migration together.

Rules / Notes:
- Never edit a migration that has already been pushed. Write a new one.
- Reference data (rows the code relies on) goes in a hand-written migration (`uv run alembic revision -m "..."`).
- If Alembic reports "multiple heads" (two people created migrations at the same time): `uv run alembic merge heads -m "merge"`.

## Useful commands

| Command | What it does |
|---|---|
| `uv run alembic current` | revision the database is on |
| `uv run alembic history` | list of migrations |
| `uv run alembic check` | checks that the models and the database match |
| `uv run alembic downgrade -1` | undo the last migration |
| `docker compose down -v` | **deletes the database** (then `docker compose up -d db` + `alembic upgrade head`) |
| `docker exec -it aura-db mariadb -uaura -paura si_hospitalier_db` | SQL shell in the database |

## Practitioner authentication

Before running migrations or starting the API, generate a signing secret:

```bash
uv run python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the output into `JWT_SECRET` in your local `.env` (at least 32 characters).
Replace the example placeholder; do not commit the generated secret. Keep it
stable across restarts; changing it invalidates outstanding tokens.

From `src/backend`, install dependencies and migrate:

```bash
uv sync
uv run alembic upgrade head
```

Populate three synthetic practitioners and their accounts for local demos:

```bash
uv run python scripts/populate_practitioners.py
```

The script prompts for a password and confirmation without displaying it. The
three accounts (`demo.medecin`, `demo.infirmier`, `demo.kine`) share that supplied
password, each stored as a separate Argon2 hash. Repeating the script leaves
matching accounts and their passwords unchanged. Conflicting demo records abort
and roll back the whole operation. Run only against the intended local demo DB.

To give an existing active practitioner an account:

```bash
uv run python scripts/create_user.py --practitioner-id 1 --username my.username
```

Usernames are trimmed and lowercased. Each practitioner can have at most one
account. Passwords are preserved exactly and stored only as hashes. Neither
script prints passwords or hashes. There is no public registration endpoint.

Login accepts JSON at `POST /api/auth/login`:

```json
{"username": "demo.medecin", "password": "the password you supplied"}
```

It returns `access_token`, `token_type: "bearer"`, and `expires_in: 28800`.
Send the returned token with every application API call:

```http
GET /api/auth/me
Authorization: Bearer <access_token>
```

`/api/auth/me` returns `id`, `username`, `practitioner_id`, `name_given`,
`name_family`, and `profession`. All patient, hospitalization, care, and reference
endpoints now require authentication. All active practitioners have the same
existing permissions. Missing/invalid/expired tokens and accounts linked to an
inactive practitioner receive `401`. Credentials are never returned.

Sessions expire after eight hours without renewal. Logout is performed by the
client discarding its token; there is no logout endpoint, refresh flow, or token
revocation table. A copied token stays valid until expiry unless its account is
deleted or practitioner deactivated. Use HTTPS when sending credentials/tokens
outside local development.

The frontend is not integrated yet: its existing API requests will receive `401`
until it adds login and bearer headers. Existing CORS settings are unchanged.
