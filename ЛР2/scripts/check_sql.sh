#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$APP_DIR"

if ! command -v sqlcheck >/dev/null 2>&1; then
  curl -sSfL https://github.com/jarulraj/sqlcheck/releases/download/v1.3/sqlcheck-x86_64.tar.gz \
    -o /tmp/sqlcheck.tgz
  rm -rf /tmp/sqlcheck
  mkdir -p /tmp/sqlcheck
  tar -xzf /tmp/sqlcheck.tgz -C /tmp/sqlcheck
  find /tmp/sqlcheck -type f -name sqlcheck -exec cp {} /usr/local/bin/sqlcheck \;
  chmod +x /usr/local/bin/sqlcheck
fi

mkdir -p sqlcheck-reports
fail=0

while IFS= read -r -d '' file; do
  report="sqlcheck-reports/$(basename "$file").log"
  echo "==> SQLCheck: $file"
  set +e
  sqlcheck -f "$file" -v > "$report" 2>&1
  rc=$?
  set -e
  cat "$report"
  if [ "$rc" -ne 0 ] && grep -qE "High Risk   :: [1-9]" "$report"; then
    fail=1
  fi
done < <(find db -type f -name '*.sql' -print0)

if [ "$fail" -ne 0 ]; then
  echo "Найдены SQL-антипаттерны HIGH RISK — сборка останавливается"
  exit 1
fi

echo "SQL-файлы проверены, HIGH RISK не найдено"
