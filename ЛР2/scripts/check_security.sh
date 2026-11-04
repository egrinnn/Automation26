#!/usr/bin/env bash
# Анализатор безопасности кода (ЛР6).
# Падает, если bandit находит проблему уровня HIGH (в терминах задания — CRITICAL).
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$APP_DIR"

if ! command -v bandit >/dev/null 2>&1; then
  echo "==> Установка bandit в агент"
  apt-get update -qq
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq python3-pip >/dev/null
  pip3 install --break-system-packages --quiet bandit==1.8.6
fi

echo "==> bandit: статический анализ безопасности"
# bandit возвращает 1 при любых находках, поэтому код возврата обрабатываем сами:
# сборку останавливают только проблемы HIGH (CRITICAL).
set +e
bandit -r app config.py run.py -x tests,migrations -f json -o bandit-report.json
set -e
bandit -r app config.py run.py -x tests,migrations -f txt -o bandit-report.txt || true

python3 - <<'PY'
import json
from pathlib import Path

report = Path('bandit-report.json')
if not report.exists():
    raise SystemExit('bandit не создал отчёт')

data = json.loads(report.read_text(encoding='utf-8'))
high = [r for r in data.get('results', []) if r.get('issue_severity') == 'HIGH']

for item in high:
    print(
        "HIGH/CRITICAL: {test_id} {filename}:{line} — {text}".format(
            test_id=item.get('test_id'),
            filename=item.get('filename'),
            line=item.get('line_number'),
            text=item.get('issue_text'),
        )
    )

if high:
    print(f'Найдено {len(high)} проблем уровня HIGH (CRITICAL) — сборка останавливается')
    raise SystemExit(1)

print('Проблем уровня HIGH/CRITICAL не найдено')
PY

echo "Отчёты сохранены: bandit-report.json, bandit-report.txt"
