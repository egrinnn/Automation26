#!/bin/bash
set -e

echo "==> Ожидание готовности PostgreSQL..."
python wait_for_db.py

echo "==> Применение миграций (flask db upgrade)..."
flask db upgrade

echo "==> Проверка справочника ролей..."
flask seed-roles

echo "==> Запуск приложения (gunicorn)..."
exec gunicorn --bind 0.0.0.0:5000 --workers 3 --access-logfile - run:app
