#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

# Check ALL columns and add what's missing
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

# Get existing columns
cur.execute(\"SELECT column_name, is_nullable FROM information_schema.columns WHERE table_name='push_subscriptions' ORDER BY column_name;\")
existing = cur.fetchall()
print('Current columns:', existing)

# Add ALL potentially missing columns
columns_to_add = [
    'ALTER TABLE push_subscriptions ADD COLUMN IF NOT EXISTS p256dh TEXT;',
    'ALTER TABLE push_subscriptions ADD COLUMN IF NOT EXISTS auth TEXT;',
    'ALTER TABLE push_subscriptions ADD COLUMN IF NOT EXISTS subscription_json TEXT;',
    'ALTER TABLE push_subscriptions ADD COLUMN IF NOT EXISTS batch_name VARCHAR(50);',
    'ALTER TABLE push_subscriptions ADD COLUMN IF NOT EXISTS user_agent TEXT;',
    'ALTER TABLE push_subscriptions ADD COLUMN IF NOT EXISTS ip_address VARCHAR(45);',
    'ALTER TABLE push_subscriptions ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();',
    'ALTER TABLE push_subscriptions ADD COLUMN IF NOT EXISTS last_notified TIMESTAMP;',
    'ALTER TABLE push_subscriptions ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;'
]

for sql in columns_to_add:
    try:
        cur.execute(sql)
    except Exception as e:
        print(f'Column may exist: {e}')

conn.commit()
print('All columns added/checked')
conn.close()
"

flask db stamp head
flask db upgrade