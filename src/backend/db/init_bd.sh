#!/usr/bin/env bash

#this is a quickly done thing but okj

# Creates the database, the backend user and the .env file.
# The tables are NOT created here: the backend creates them from the ORM models
# (app/models) when it starts. database/schema.sql (repo root) is only kept as a reference.
#
# Usage:
#   ./init_bd.sh            # safe to re-run: never deletes data
#   ./init_bd.sh --reset    # DROPS the database and recreates it (dev only, asks first)
#
# Optional overrides (environment variables):
#   DB_NAME      default: myapp
#   DB_USER      default: myapp
#   DB_PASS      default: random 32-char password (re-generated on each run)
#   DB_HOST      default: 127.0.0.1
#   DB_PORT      default: 3306
#   ENV_FILE     default: src/backend/.env (where app/config.py reads it)
#   ADMIN_CMD    how to open an admin session
#                default: "sudo mariadb" on Linux, "mariadb" on macOS (Homebrew)
#                if your root user has a password: ADMIN_CMD="mariadb -u root -p"
#
# Example:
#   DB_NAME=shop DB_USER=shop_api ./init_bd.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

DB_NAME="${DB_NAME:-myapp}"
DB_USER="${DB_USER:-myapp}"
DB_PASS="${DB_PASS:-$(openssl rand -hex 16)}"
DB_HOST="${DB_HOST:-127.0.0.1}"
DB_PORT="${DB_PORT:-3306}"
ENV_FILE="${ENV_FILE:-$SCRIPT_DIR/../.env}"

if [[ -z "${ADMIN_CMD:-}" ]]; then
  if [[ "$(uname)" == "Darwin" ]]; then ADMIN_CMD="mariadb"; else ADMIN_CMD="sudo mariadb"; fi
fi

RESET=false
case "${1:-}" in
  "") ;;
  --reset) RESET=true ;;
  *) echo "Unknown option: $1 (use --reset or nothing)" >&2; exit 1 ;;
esac

fail() { echo "Error: $*" >&2; exit 1; }

# --- Sanity checks -----------------------------------------------------------

[[ "$DB_NAME" =~ ^[A-Za-z0-9_]+$ ]] || fail "DB_NAME may only contain letters, digits and _"
[[ "$DB_USER" =~ ^[A-Za-z0-9_]+$ ]] || fail "DB_USER may only contain letters, digits and _"
[[ "$DB_PASS" != *"'"* && "$DB_PASS" != *\\* ]] || fail "DB_PASS must not contain ' or \\"
command -v python3 >/dev/null || fail "python3 is required (used to URL-encode the password)"

echo "Connecting to MariaDB as admin ($ADMIN_CMD)..."
$ADMIN_CMD -e "SELECT 1" >/dev/null || fail "cannot connect to MariaDB. Is the server running?
  Linux: sudo systemctl start mariadb
  macOS: brew services start mariadb"

# --- Optional reset ----------------------------------------------------------

if $RESET; then
  echo
  echo "--reset will permanently DELETE the database '$DB_NAME' and all its data."
  read -r -p "Type the database name to confirm: " answer
  [[ "$answer" == "$DB_NAME" ]] || fail "confirmation did not match, nothing was deleted"
  $ADMIN_CMD -e "DROP DATABASE IF EXISTS \`$DB_NAME\`;"
  echo "Database '$DB_NAME' dropped."
fi

# --- Database and user -------------------------------------------------------
# The user is created for both 'localhost' and '127.0.0.1' because, depending on
# server settings, a TCP connection to 127.0.0.1 may not match 'localhost'.
# ALTER USER keeps the password in sync with .env when the script is re-run.

echo "Creating database '$DB_NAME' and user '$DB_USER'..."
$ADMIN_CMD <<SQL
CREATE DATABASE IF NOT EXISTS \`$DB_NAME\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASS';
CREATE USER IF NOT EXISTS '$DB_USER'@'127.0.0.1' IDENTIFIED BY '$DB_PASS';
ALTER USER '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASS';
ALTER USER '$DB_USER'@'127.0.0.1' IDENTIFIED BY '$DB_PASS';

GRANT ALL PRIVILEGES ON \`$DB_NAME\`.* TO '$DB_USER'@'localhost';
GRANT ALL PRIVILEGES ON \`$DB_NAME\`.* TO '$DB_USER'@'127.0.0.1';
FLUSH PRIVILEGES;
SQL

# --- .env --------------------------------------------------------------------

url_pass=$(python3 -c 'import sys, urllib.parse; print(urllib.parse.quote(sys.argv[1], safe=""))' "$DB_PASS")
DATABASE_URL="mysql+pymysql://${DB_USER}:${url_pass}@${DB_HOST}:${DB_PORT}/${DB_NAME}?charset=utf8mb4"

touch "$ENV_FILE"
{ grep -v '^DATABASE_URL=' "$ENV_FILE" || true; echo "DATABASE_URL=$DATABASE_URL"; } > "$ENV_FILE.tmp"
mv "$ENV_FILE.tmp" "$ENV_FILE"
chmod 600 "$ENV_FILE"
echo "Wrote DATABASE_URL to $ENV_FILE"

# --- Verify the backend user can connect --------------------------------------

echo "Checking connection as '$DB_USER'..."
tables=$(MYSQL_PWD="$DB_PASS" mariadb -u "$DB_USER" -h "$DB_HOST" -P "$DB_PORT" \
  -N -B -e "SHOW TABLES;" "$DB_NAME") || fail "the app user could not connect"

echo
echo "Done. Tables in '$DB_NAME' (created by the backend on startup):"
echo "${tables:-  (none)}" | sed 's/^/  /'
