#!/usr/bin/env bash
set -euo pipefail

# DB
docker run -d --name donor-pg \
  -e POSTGRES_PASSWORD=postgres \
  -p 5433:5432 \
  ankane/pgvector || true

sleep 2
docker exec donor-pg psql -U postgres -d postgres -c "CREATE EXTENSION IF NOT EXISTS vector" || true

# Backend
cd donor-finder-api
python -m venv .venv || true
source .venv/bin/activate
pip install -r requirements.txt

export DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5433/postgres"
uvicorn app.main:app --reload --port 8000 --host 0.0.0.0
