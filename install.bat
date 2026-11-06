@echo off
rem Installs and starts Aura with Docker: database, API and web app.
cd /d "%~dp0"

docker compose version >nul 2>&1
if errorlevel 1 (
  echo Docker with Docker Compose is required: https://docs.docker.com/get-docker/
  goto end
)

rem the secret that signs the login tokens, created once
if not exist .env (
  for /f %%s in ('powershell -NoProfile -Command "$b = New-Object byte[] 36; [Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($b); [Convert]::ToBase64String($b).Replace('+', 'A').Replace('/', 'B')"') do (
    >.env echo JWT_SECRET=%%s
  )
)

docker compose build || goto end
docker compose run --rm backend alembic upgrade head || goto end
docker compose run --rm backend python scripts/populate_practitioners.py --password abc || goto end

docker compose up -d || goto end
echo.
echo Aura is running: http://localhost:5173 (log in as demo.medecin, demo.infirmier or demo.kine, password abc)

:end
pause
