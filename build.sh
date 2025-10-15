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
cur.execute('DROP TABLE IF EXISTS alembic_version;')
conn.commit()
conn.close()
print('Reset migration tracking')
"

flask db stamp head
flask db upgrade