import os
import sys
import time

import psycopg2

RAW_URL = os.environ.get('DATABASE_URL', '')
PG_URL = RAW_URL.replace('postgresql+psycopg2://', 'postgresql://', 1)

if not PG_URL:
    print('DATABASE_URL не задан — нечего ждать.', file=sys.stderr)
    sys.exit(1)

MAX_ATTEMPTS = 30

for attempt in range(1, MAX_ATTEMPTS + 1):
    try:
        conn = psycopg2.connect(PG_URL, connect_timeout=3)
        conn.close()
        print('PostgreSQL готов принимать подключения.')
        sys.exit(0)
    except psycopg2.OperationalError as exc:
        print(f'[{attempt}/{MAX_ATTEMPTS}] PostgreSQL ещё не готов: {exc}'.strip())
        time.sleep(2)

print('PostgreSQL не ответил за отведённое время.', file=sys.stderr)
sys.exit(1)
