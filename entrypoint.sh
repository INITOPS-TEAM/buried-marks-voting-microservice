#!/bin/bash

set -euo pipefail

cp /tmp/jwt_public_key/ec_public.key /app/public.pem

echo "Running pre-start check..."
python app/backend_pre_start.py

echo "Running alembic migrations..."
alembic upgrade head

echo "Starting Uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8900 --reload
