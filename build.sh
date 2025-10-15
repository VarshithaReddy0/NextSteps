#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# Run migrations with fallback
flask db upgrade || (flask db stamp head && flask db upgrade)

# Create admin user
python init_admin.py