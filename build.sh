#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

# Add missing column
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
    cur.execute('ALTER TABLE push_subscriptions ADD COLUMN IF NOT EXISTS subscription_json TEXT;')
    conn.commit()
    print('Added subscription_json column')
except Exception as e:
    print(f'Column may already exist: {e}')
conn.close()
"

flask db stamp head
flask db upgrade