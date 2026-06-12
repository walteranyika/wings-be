#!/bin/sh
set -e

python <<'PY'
import os
import socket
import time

host = os.environ.get("DB_HOST", "db")
port = int(os.environ.get("DB_PORT", "3306"))

for attempt in range(60):
    try:
        with socket.create_connection((host, port), timeout=2):
            break
    except OSError:
        time.sleep(1)
else:
    raise SystemExit(f"Database {host}:{port} was not reachable.")
PY

python manage.py migrate

exec "$@"
