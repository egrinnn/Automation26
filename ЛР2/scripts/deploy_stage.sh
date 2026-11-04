#!/usr/bin/env bash
# Деплой образа из Docker Hub на stage-стенд.
# Запускается TeamCity-агентом (контейнер) в шаге "Deploy to stage".
#
# Обязательные переменные окружения:
#   STAGE_HOST  — IP stage-ВМ (по умолчанию 10.10.0.3)
#   STAGE_USER  — пользователь SSH (по умолчанию student)
#   STAGE_KEY   — путь к приватному ключу внутри агента
#   APP_TAG     — тег образа (dev)
set -euo pipefail

STAGE_HOST="${STAGE_HOST:-10.10.0.3}"
STAGE_USER="${STAGE_USER:-student}"
STAGE_KEY="${STAGE_KEY:-/data/teamcity_agent/conf/stage_key}"
STAGE_DIR="${STAGE_DIR:-/home/student/menu-stolovoy}"
APP_TAG="${APP_TAG:-dev}"

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

REMOTE_CMD="cd '${STAGE_DIR}' \
  && APP_TAG='${APP_TAG}' docker compose --env-file .env.stage -f docker-compose.stage.yml pull \
  && APP_TAG='${APP_TAG}' docker compose --env-file .env.stage -f docker-compose.stage.yml up -d --remove-orphans \
  && APP_TAG='${APP_TAG}' docker compose --env-file .env.stage -f docker-compose.stage.yml ps"

"${SSH[@]}" "${STAGE_USER}@${STAGE_HOST}" "${REMOTE_CMD}"

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
