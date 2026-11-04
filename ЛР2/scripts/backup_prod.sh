#!/usr/bin/env bash
set -euo pipefail

PROD_HOST="${PROD_HOST:-10.10.0.5}"
PROD_USER="${PROD_USER:-student}"
PROD_KEY="${PROD_KEY:-/data/teamcity_agent/conf/stage_key}"
PROD_DIR="${PROD_DIR:-/home/student/menu-stolovoy}"
APP_TAG="${APP_TAG:-prod}"
PROD_DB_CONTAINER="${PROD_DB_CONTAINER:-menu_prod_db}"
POSTGRES_USER="${POSTGRES_USER:-menu_user}"
POSTGRES_DB="${POSTGRES_DB:-menu_stolovoy}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

SSH_OPTS=(
  -i "${PROD_KEY}"
  -o StrictHostKeyChecking=no
  -o UserKnownHostsFile=/dev/null
  -o ConnectTimeout=10
)
SSH=(ssh "${SSH_OPTS[@]}")

echo "==> Резервное копирование БД prod"

"${SSH[@]}" "${PROD_USER}@${PROD_HOST}" \
  "cd '${PROD_DIR}' && APP_TAG='${APP_TAG}' docker compose --env-file .env.prod -f docker-compose.prod.yml up -d db" || true
"${SSH[@]}" "${PROD_USER}@${PROD_HOST}" '
  for i in $(seq 1 40); do
    if docker exec menu_prod_db pg_isready -U menu_user -d menu_stolovoy >/dev/null 2>&1; then
      exit 0
    fi
    sleep 1
  done
  echo "БД prod не готова" >&2
  exit 1
'

BACKUP_FILE="${REPO_ROOT}/prod_backup_$(date +%Y%m%d_%H%M%S).dump"
"${SSH[@]}" "${PROD_USER}@${PROD_HOST}" \
  "docker exec ${PROD_DB_CONTAINER} pg_dump -U ${POSTGRES_USER} -d ${POSTGRES_DB} -Fc" \
  > "${BACKUP_FILE}"

if [ ! -s "${BACKUP_FILE}" ]; then
  echo "ОШИБКА: резервная копия пуста" >&2
  exit 1
fi

echo "Резервная копия сохранена: ${BACKUP_FILE} ($(du -h "${BACKUP_FILE}" | cut -f1))"
