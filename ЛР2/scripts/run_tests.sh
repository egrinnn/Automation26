#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$APP_DIR"

if [ ! -x /opt/testsvenv/bin/pytest ]; then
  apt-get update -qq
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq python3-venv >/dev/null
  python3 -m venv /opt/testsvenv
  /opt/testsvenv/bin/pip install -q -r requirements.txt pytest-cov
fi

DB=menu_test_db_ci
docker rm -f "$DB" >/dev/null 2>&1 || true
cleanup() {
  docker rm -f "$DB" >/dev/null 2>&1 || true
}
trap cleanup EXIT

docker run -d --name "$DB" \
  -e POSTGRES_DB=menu_stolovoy_test \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -p 55432:5432 postgres:16 >/dev/null

for _ in $(seq 1 40); do
  if docker exec "$DB" pg_isready -U postgres -d menu_stolovoy_test >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

docker exec "$DB" psql -U postgres -d postgres -c "DROP DATABASE IF EXISTS menu_stolovoy_test;" >/dev/null
docker exec "$DB" psql -U postgres -d postgres -c "CREATE DATABASE menu_stolovoy_test;" >/dev/null

export TEST_DATABASE_URL="postgresql+psycopg2://postgres:postgres@172.17.0.1:55432/menu_stolovoy_test"

/opt/testsvenv/bin/python -m pytest -q \
  --cov=app --cov-report=term --cov-report=xml:coverage.xml \
  --junitxml=pytest-report.xml | tee pytest-report.txt
