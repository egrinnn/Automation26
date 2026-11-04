# Актуальная схема базы данных

`schema.sql` — дамп схемы PostgreSQL, полученный штатной утилитой `pg_dump --schema-only`
с базы данных stage-стенда после применения миграций Alembic.

Обновление схемы:

```bash
docker exec menu_stage_db pg_dump -U menu_user -d menu_stolovoy \
  --schema-only --no-owner --no-privileges > db/schema/schema.sql
```

Файл коммитится вместе с миграцией и используется для сверки схем TEST/STAGE/PROD
в шагах деплоя TeamCity.
