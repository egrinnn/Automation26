#!/usr/bin/env bash
# Поиск учётных данных и секретов в git-истории (ЛР6).
# Любая находка trufflehog останавливает сборку.
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$APP_DIR"

TRUFFLEHOG_VERSION=3.99.8

if ! command -v trufflehog >/dev/null 2>&1; then
  echo "==> Установка trufflehog в агент"
  curl -sSfL "https://github.com/trufflesecurity/trufflehog/releases/download/v${TRUFFLEHOG_VERSION}/trufflehog_${TRUFFLEHOG_VERSION}_linux_amd64.tar.gz" \
    -o /tmp/trufflehog.tgz
  tar -xzf /tmp/trufflehog.tgz -C /usr/local/bin trufflehog
  rm -f /tmp/trufflehog.tgz
fi

echo "==> trufflehog: поиск секретов в git-истории"
set +e
trufflehog git "file://${APP_DIR}" --json --no-update --fail \
  > trufflehog-report.json 2> trufflehog-report.log
RC=$?
set -e

if [ "$RC" -eq 183 ]; then
  echo "Найдены секреты/учётные данные — сборка останавливается"
  python3 - <<'PY'
import json
from pathlib import Path

found = 0
for line in Path('trufflehog-report.json').read_text(encoding='utf-8').splitlines():
    line = line.strip()
    if not line:
        continue
    try:
        item = json.loads(line)
    except json.JSONDecodeError:
        continue
    found += 1
    detector = item.get('DetectorName') or item.get('detector_name') or 'unknown'
    git = item.get('SourceMetadata', {}).get('Data', {}).get('Git', {})
    path = git.get('file') or git.get('file_name') or '?'
    commit = git.get('commit') or '?'
    print(f'SECRET: detector={detector} file={path} commit={commit}')

print(f'Всего находок: {found}')
PY
  exit 1
fi

if [ "$RC" -ne 0 ]; then
  echo "trufflehog завершился с кодом $RC" >&2
  tail -20 trufflehog-report.log >&2 || true
  exit "$RC"
fi

echo "Секретов не найдено"
echo "Отчёт сохранён: trufflehog-report.json"
