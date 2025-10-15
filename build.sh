#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

# Force reset migration state
python -c "
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from your_app import app, db
with app.app_context():
    db.engine.execute('DELETE FROM alembic_version;')
    print('Cleared migration history')
"

# Get current head and stamp
HEAD=$(flask db heads | head -n1 | awk '{print $1}')
flask db stamp $HEAD

# Run migrations
flask db upgrade

# Create admin user
python init_admin.py