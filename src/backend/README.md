# Backend

FastAPI API on MariaDB.

## Requirements

- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Docker with Docker Compose

## Setup

From the repository root:

```bash
docker compose up -d db
cp src/backend/.env.example src/backend/.env
```

On Windows (cmd), use `copy` instead of `cp`.

In `src/backend/.env`, set `JWT_SECRET` to the output of:

```bash
uv run python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Then, from `src/backend`:

```bash
uv sync
uv run alembic upgrade head
uv run python scripts/populate_practitioners.py
```

The last command asks for a password and creates three accounts with it:
`demo.medecin`, `demo.infirmier` and `demo.kine`.

## Run

```bash
cd src/backend
uv run fastapi dev
```

The API runs on http://127.0.0.1:8000 (endpoints at http://127.0.0.1:8000/docs).

## After a `git pull`

```bash
uv sync
uv run alembic upgrade head
```
