#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# Run migrations
flask db upgrade

# Create admin user
python init_admin.py