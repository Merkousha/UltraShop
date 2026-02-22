#!/bin/bash
set -e

# Ensure data dir exists when using persistent volume (e.g. DJANGO_DB_PATH=/app/data/db.sqlite3)
if [ -n "$DJANGO_DB_PATH" ]; then
  DATA_DIR="$(dirname "$DJANGO_DB_PATH")"
  if [ -n "$DATA_DIR" ] && [ "$DATA_DIR" != "." ]; then
    mkdir -p "$DATA_DIR"
  fi
fi

echo "Running migrations..."
python manage.py migrate

echo "Seeding platform data and theme presets (idempotent)..."
python manage.py seed_platform 2>/dev/null || true

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Gunicorn..."
exec gunicorn ultrashop.wsgi:application --bind 0.0.0.0:8080 --workers 3
