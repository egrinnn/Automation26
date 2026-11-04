#!/usr/bin/env bash
set -euo pipefail

PROD_HOST="${PROD_HOST:-10.10.0.5}"
PROD_USER="${PROD_USER:-student}"
PROD_KEY="${PROD_KEY:-/data/teamcity_agent/conf/stage_key}"
PROD_DIR="${PROD_DIR:-/home/student/menu-stolovoy}"
APP_TAG="${APP_TAG:-prod}"

STAGE_HOST="${STAGE_HOST:-10.10.0.3}"
STAGE_USER="${STAGE_USER:-student}"
STAGE_KEY="${STAGE_KEY:-/data/teamcity_agent/conf/stage_key}"
STAGE_DB_CONTAINER="${STAGE_DB_CONTAINER:-menu_stage_db}"
PROD_DB_CONTAINER="${PROD_DB_CONTAINER:-menu_prod_db}"
POSTGRES_USER="${POSTGRES_USER:-menu_user}"
POSTGRES_DB="${POSTGRES_DB:-menu_stolovoy}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
COMPOSE_FILE="${REPO_ROOT}/docker-compose.prod.yml"

SSH_OPTS=(
  -i "${PROD_KEY}"
  -o StrictHostKeyChecking=no
  -o UserKnownHostsFile=/dev/null
  -o ConnectTimeout=10
)
SSH=(ssh "${SSH_OPTS[@]}")
SCP=(scp "${SSH_OPTS[@]}")

normalize_schema() {
  sed -e '/^--/d' -e '/^$/d' -e '/^\\restrict/d' -e '/^\\unrestrict/d' "$1"
}

compare_schemas() {
  local stage_dump prod_dump
  stage_dump="$(mktemp)"
  prod_dump="$(mktemp)"

  "${SSH[@]}" -i "${STAGE_KEY}" "${STAGE_USER}@${STAGE_HOST}" \
    "docker exec ${STAGE_DB_CONTAINER} pg_dump -U ${POSTGRES_USER} -d ${POSTGRES_DB} --schema-only --no-owner --no-privileges" \
    > "${stage_dump}"

  "${SSH[@]}" "${PROD_USER}@${PROD_HOST}" \
    "docker exec ${PROD_DB_CONTAINER} pg_dump -U ${POSTGRES_USER} -d ${POSTGRES_DB} --schema-only --no-owner --no-privileges" \
    > "${prod_dump}"

  if diff -q <(normalize_schema "${stage_dump}") <(normalize_schema "${prod_dump}") >/dev/null; then
    echo "Схемы STAGE и PROD идентичны"
    rm -f "${stage_dump}" "${prod_dump}"
    return 0
  fi

  echo "Схемы STAGE и PROD различаются:"
  diff -u <(normalize_schema "${stage_dump}") <(normalize_schema "${prod_dump}") || true
  rm -f "${stage_dump}" "${prod_dump}"
  return 1
}

echo "==> Деплой образа denizkaderli/menu-stolovoy:${APP_TAG} на prod"
echo "==> Целевой стенд: ${PROD_USER}@${PROD_HOST}:${PROD_DIR}"

"${SSH[@]}" "${PROD_USER}@${PROD_HOST}" "mkdir -p '${PROD_DIR}'"
"${SCP[@]}" "${COMPOSE_FILE}" \
  "${PROD_USER}@${PROD_HOST}:${PROD_DIR}/docker-compose.prod.yml"

if ! "${SSH[@]}" "${PROD_USER}@${PROD_HOST}" "test -f '${PROD_DIR}/.env.prod'"; then
  echo "ОШИБКА: на prod нет ${PROD_DIR}/.env.prod" >&2
  exit 1
fi

echo "==> Запуск БД prod"
"${SSH[@]}" "${PROD_USER}@${PROD_HOST}" "cd '${PROD_DIR}' && APP_TAG='${APP_TAG}' docker compose --env-file .env.prod -f docker-compose.prod.yml up -d db"
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

echo "==> Сверка схем STAGE и PROD до миграции"
compare_schemas || true

REMOTE_CMD="cd '${PROD_DIR}' \
  && APP_TAG='${APP_TAG}' docker compose --env-file .env.prod -f docker-compose.prod.yml pull app \
  && APP_TAG='${APP_TAG}' docker compose --env-file .env.prod -f docker-compose.prod.yml run --rm --no-deps --entrypoint flask app db upgrade \
  && APP_TAG='${APP_TAG}' docker compose --env-file .env.prod -f docker-compose.prod.yml up -d --remove-orphans \
  && APP_TAG='${APP_TAG}' docker compose --env-file .env.prod -f docker-compose.prod.yml ps"

"${SSH[@]}" "${PROD_USER}@${PROD_HOST}" "${REMOTE_CMD}"

echo "==> Сверка схем STAGE и PROD после миграции"
compare_schemas

echo "==> Smoke-test: ждём ответ /menu"
"${SSH[@]}" "${PROD_USER}@${PROD_HOST}" '
  for i in $(seq 1 30); do
    if curl -fsS http://127.0.0.1:5000/menu >/dev/null 2>&1; then
      echo "prod отвечает (попытка $i)"
      exit 0
    fi
    sleep 2
  done
  echo "prod не поднялся за 60 секунд" >&2
  exit 1
'

echo "==> Деплой на prod завершён успешно"
