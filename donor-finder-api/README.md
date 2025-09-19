# 2) `donor-finder-api/README.md` (backend)

```markdown
# Donor Finder API (FastAPI)

## Stack
- FastAPI / Uvicorn
- Postgres (Docker) + **pgvector**
- SQLAlchemy Core
- External APIs:
  - ProPublica (seed)
  - Apollo (enrichment)
  - Firecrawl (structured extraction + markdown snapshots)

## Env vars
- `DATABASE_URL` (required) e.g. `postgresql+psycopg://postgres:postgres@localhost:5433/postgres`
- `APOLLO_API_KEY` (optional)
- `FIRECRAWL_API_KEY` (optional)

Quick check:
```bash
python - <<'PY'
import os
print("DATABASE_URL:", bool(os.getenv("DATABASE_URL")))
print("APOLLO_API_KEY:", bool(os.getenv("APOLLO_API_KEY")))
print("FIRECRAWL_API_KEY:", bool(os.getenv("FIRECRAWL_API_KEY")))
PY
Run
bash
Copy code
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000 --host 0.0.0.0
Database
Start Postgres
bash
Copy code
docker run -d --name donor-pg \
  -e POSTGRES_PASSWORD=postgres \
  -p 5433:5432 \
  ankane/pgvector
Create extension + schema
Open psql:

bash
Copy code
docker exec -it donor-pg psql -U postgres -d postgres
Paste:

sql
Copy code
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS donors (
  id BIGSERIAL PRIMARY KEY,
  ein TEXT UNIQUE,
  name TEXT NOT NULL,
  state TEXT,
  city TEXT,
  mission TEXT,
  ntee_code TEXT,
  assets_total NUMERIC,
  grants_total NUMERIC,
  irs_subsection INTEGER,
  website TEXT,
  source JSONB,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS donor_embeddings (
  donor_id BIGINT PRIMARY KEY REFERENCES donors(id) ON DELETE CASCADE,
  embedding VECTOR,
  doc TEXT
);

CREATE TABLE IF NOT EXISTS enrichments (
  id BIGSERIAL PRIMARY KEY,
  donor_id BIGINT REFERENCES donors(id) ON DELETE CASCADE,
  kind TEXT,   -- company_profile | page_markdown | website_source | site_extract
  source TEXT, -- propublica | apollo | firecrawl | scraper
  url TEXT,
  raw JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS contacts (
  id BIGSERIAL PRIMARY KEY,
  donor_id BIGINT REFERENCES donors(id) ON DELETE CASCADE,
  name TEXT,
  title TEXT,
  email TEXT,
  linkedin_url TEXT,
  source TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS grants (
  id BIGSERIAL PRIMARY KEY,
  donor_id BIGINT REFERENCES donors(id) ON DELETE CASCADE,
  year INT,
  amount NUMERIC,
  recipient_name TEXT,
  recipient_ein TEXT
);
Useful DB commands
bash
Copy code
docker exec donor-pg psql -U postgres -d postgres -c "\dt"
docker exec donor-pg psql -U postgres -d postgres -c "\d+ donors"
docker exec -it donor-pg psql -U postgres -d postgres
API
Base: http://localhost:8000

GET /donors?state=CA&q=K&min_assets=&max_assets=&limit=25&offset=0 → {items,total}

GET /donors/{id} → { donor, grants, contacts, enrichments }

POST /donors/ingest/propublica?state=CA&ntee_major=2&limit=35

POST /donors/embeddings/build?batch_size=32&max_rows=500

POST /donors/search/semantic
Body:

json
Copy code
{ "query": "foundations supporting early childhood education in California", "state": "CA", "limit": 10 }
POST /donors/{id}/enrich (Apollo; adds company profile + contacts)

POST /donors/enrich/batch?limit=5

POST /donors/{id}/crawl (Firecrawl; structured profile + page markdown)

POST /donors/websites/backfill_apollo?limit=12

Bootstrap sequence
bash
Copy code
curl -X POST "http://localhost:8000/donors/ingest/propublica?state=CA&ntee_major=2&limit=35"
curl -X POST "http://localhost:8000/donors/embeddings/build?batch_size=32&max_rows=500"
curl -X POST "http://localhost:8000/donors/websites/backfill_apollo?limit=12"
curl -X POST "http://localhost:8000/donors/2/enrich"
curl -X POST "http://localhost:8000/donors/2/crawl"
Troubleshooting
ECONNREFUSED from UI → run backend with --host 0.0.0.0 and NEXT_PUBLIC_API_URL=http://localhost:8000.

SQL placeholders → don’t mix $1 with :name in a single statement.

Firecrawl shows no activity → verify the key with:

bash
Copy code
curl -s https://api.firecrawl.dev/v1/extract \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $FIRECRAWL_API_KEY" \
  -d '{"urls":["https://www.uclafoundation.org"],"schema":{"type":"object","properties":{"ok":{"type":"boolean"}}}}'