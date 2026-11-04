#!/usr/bin/env bash
# Анализатор качества кода (ЛР6).
# Падает, если flake8 находит ошибки уровня BLOCKER: E9*, F63, F7, F82
# (синтаксические ошибки, неопределённые имена, ошибки импортов).
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$APP_DIR"

if ! command -v flake8 >/dev/null 2>&1; then
  echo "==> Установка flake8 в агент"
  apt-get update -qq
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq python3-pip >/dev/null
  pip3 install --break-system-packages --quiet flake8==7.3.0
fi

echo "==> flake8: проверка критических ошибок (BLOCKER)"
flake8 --select=E9,F63,F7,F82 --show-source --statistics \
  --exclude=.git,__pycache__,venv,.venv,migrations,tests .

echo "==> flake8: полный отчёт по стилю (не влияет на статус сборки)"
flake8 --exit-zero --statistics --output-file=flake8-report.txt \
  --exclude=.git,__pycache__,venv,.venv,migrations,tests . || true
echo "Отчёт сохранён: flake8-report.txt"
