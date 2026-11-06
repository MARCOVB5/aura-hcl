#!/bin/sh
# Installs and starts Aura with Docker: database, API and web app.
set -e
cd "$(dirname "$0")"

if ! docker compose version >/dev/null 2>&1; then
  echo "Docker with Docker Compose is required: https://docs.docker.com/get-docker/" >&2
  exit 1
fi

# the secret that signs the login tokens, created once
if [ ! -f .env ]; then
  printf 'JWT_SECRET=%s\n' "$(LC_ALL=C tr -dc 'A-Za-z0-9' </dev/urandom | head -c 48)" > .env
fi

docker compose build
docker compose run --rm backend alembic upgrade head
docker compose run --rm backend python scripts/populate_practitioners.py --password abc

docker compose up -d
echo
echo "Aura is running: http://localhost:5173 (log in as demo.medecin, demo.infirmier or demo.kine, password abc)"
