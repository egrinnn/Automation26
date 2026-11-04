#!/usr/bin/env bash
set -euo pipefail

STAGE_HOST="${STAGE_HOST:-10.10.0.3}"
STAGE_USER="${STAGE_USER:-student}"
STAGE_KEY="${STAGE_KEY:-/data/teamcity_agent/conf/stage_key}"
STAGE_DIR="${STAGE_DIR:-/home/student/menu-stolovoy}"
APP_TAG="${APP_TAG:-dev}"
TEST_DB_CONTAINER="${TEST_DB_CONTAINER:-menu_test_db}"
STAGE_DB_CONTAINER="${STAGE_DB_CONTAINER:-menu_stage_db}"
POSTGRES_USER="${POSTGRES_USER:-menu_user}"
POSTGRES_DB="${POSTGRES_DB:-menu_stolovoy}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
COMPOSE_FILE="${REPO_ROOT}/docker-compose.stage.yml"

SSH_OPTS=(
  -i "${STAGE_KEY}"
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
  if ! docker ps --format '{{.Names}}' | grep -qx "${TEST_DB_CONTAINER}"; then
    echo "Контейнер TEST-БД ${TEST_DB_CONTAINER} не запущен, сверка пропущена"
    return 0
  fi

  local test_dump stage_dump
  test_dump="$(mktemp)"
  stage_dump="$(mktemp)"

  docker exec "${TEST_DB_CONTAINER}" \
    pg_dump -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" \
    --schema-only --no-owner --no-privileges > "${test_dump}"

  "${SSH[@]}" "${STAGE_USER}@${STAGE_HOST}" \
    "docker exec ${STAGE_DB_CONTAINER} pg_dump -U ${POSTGRES_USER} -d ${POSTGRES_DB} --schema-only --no-owner --no-privileges" \
    > "${stage_dump}"

  if diff -q <(normalize_schema "${test_dump}") <(normalize_schema "${stage_dump}") >/dev/null; then
    echo "Схемы TEST и STAGE идентичны"
    rm -f "${test_dump}" "${stage_dump}"
    return 0
  fi

  echo "Схемы TEST и STAGE различаются:"
  diff -u <(normalize_schema "${test_dump}") <(normalize_schema "${stage_dump}") || true
  rm -f "${test_dump}" "${stage_dump}"
  return 1
}

echo "==> Деплой образа denizkaderli/menu-stolovoy:${APP_TAG}"
echo "==> Целевой стенд: ${STAGE_USER}@${STAGE_HOST}:${STAGE_DIR}"

"${SSH[@]}" "${STAGE_USER}@${STAGE_HOST}" "mkdir -p '${STAGE_DIR}'"
"${SCP[@]}" "${COMPOSE_FILE}" \
  "${STAGE_USER}@${STAGE_HOST}:${STAGE_DIR}/docker-compose.stage.yml"

if ! "${SSH[@]}" "${STAGE_USER}@${STAGE_HOST}" "test -f '${STAGE_DIR}/.env.stage'"; then
  echo "ОШИБКА: на stage нет ${STAGE_DIR}/.env.stage" >&2
  echo "Создайте его из .env.stage.example и повторите деплой." >&2
  exit 1
fi

echo "==> Сверка схем TEST и STAGE до миграции"
compare_schemas || true

REMOTE_CMD="cd '${STAGE_DIR}' \
  && APP_TAG='${APP_TAG}' docker compose --env-file .env.stage -f docker-compose.stage.yml up -d db \
  && APP_TAG='${APP_TAG}' docker compose --env-file .env.stage -f docker-compose.stage.yml pull app \
  && APP_TAG='${APP_TAG}' docker compose --env-file .env.stage -f docker-compose.stage.yml run --rm --no-deps --entrypoint flask app db upgrade \
  && APP_TAG='${APP_TAG}' docker compose --env-file .env.stage -f docker-compose.stage.yml up -d --remove-orphans \
  && APP_TAG='${APP_TAG}' docker compose --env-file .env.stage -f docker-compose.stage.yml ps"

"${SSH[@]}" "${STAGE_USER}@${STAGE_HOST}" "${REMOTE_CMD}"

echo "==> Сверка схем TEST и STAGE после миграции"
compare_schemas

echo "==> Smoke-test: ждём ответ /menu"
"${SSH[@]}" "${STAGE_USER}@${STAGE_HOST}" '
  for i in $(seq 1 30); do
    if curl -fsS http://127.0.0.1:5000/menu >/dev/null 2>&1; then
      echo "stage отвечает (попытка $i)"
      exit 0
    fi
    sleep 2
  done
  echo "stage не поднялся за 60 секунд" >&2
  exit 1
'

echo "==> Деплой завершён успешно"
