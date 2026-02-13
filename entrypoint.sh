#!/bin/sh
set -e
# When DATA_DIR is set (Docker volume), ensure appuser can write (volume may be root-owned)
if [ -n "$DATA_DIR" ]; then
  mkdir -p "$DATA_DIR/media"
  chown -R appuser:appuser "$DATA_DIR" 2>/dev/null || true
fi
# Run migrate as appuser so db file is owned correctly
gosu appuser python manage.py migrate --noinput
# Run the main command as appuser (e.g. gunicorn)
exec gosu appuser "$@"
