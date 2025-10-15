#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

# Add all missing columns
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
    cur.execute('ALTER TABLE push_subscriptions ADD COLUMN IF NOT EXISTS batch_name VARCHAR(50);')
    cur.execute('ALTER TABLE push_subscriptions ADD COLUMN IF NOT EXISTS user_agent TEXT;')
    cur.execute('ALTER TABLE push_subscriptions ADD COLUMN IF NOT EXISTS ip_address VARCHAR(45);')
    cur.execute('ALTER TABLE push_subscriptions ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();')
    cur.execute('ALTER TABLE push_subscriptions ADD COLUMN IF NOT EXISTS last_notified TIMESTAMP;')
    cur.execute('ALTER TABLE push_subscriptions ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;')
    conn.commit()
    print('Added all missing columns')
except Exception as e:
    print(f'Error: {e}')
conn.close()
"

flask db stamp head
flask db upgrade