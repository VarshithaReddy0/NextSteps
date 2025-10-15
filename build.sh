#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python -c "
import os
import psycopg2
from urllib.parse import urlparse

url = urlparse(os.environ['DATABASE_URL'])
conn = psycopg2.connect(
    database=url.path[1:],
    user=url.username,
    password=url.password,
    host=url.hostname,
    port=url.port
)
cur = conn.cursor()
try:
    cur.execute('ALTER TABLE push_subscriptions DROP COLUMN IF EXISTS p256dh;')
    cur.execute('ALTER TABLE push_subscriptions DROP COLUMN IF EXISTS auth;')
    conn.commit()
    print('Cleaned up unwanted columns')
except Exception as e:
    print(f'Error: {e}')
conn.close()
"

flask db stamp head
flask db upgrade