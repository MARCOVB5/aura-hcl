# Backend

FastAPI API on MariaDB. Tables are created automatically when the server starts.

## Setup (once)

Requires [uv](https://docs.astral.sh/uv/getting-started/installation/) and a running MariaDB.

Linux / macOS:

```bash
cd src/backend/db
bash init_bd.sh
```

Windows: create a database and user in MariaDB, then create `src/backend/.env` with:

```
DATABASE_URL=mysql+pymysql://USER:PASSWORD@127.0.0.1:3306/DATABASE?charset=utf8mb4
```

## Run

```bash
cd src/backend
uv sync
uv run fastapi dev
```

Open http://127.0.0.1:8000/docs to see and try the endpoints.

The frontend dev server (`http://localhost:5173`) is allowed to call the API.
