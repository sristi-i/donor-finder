# donor-finder
# Donor Finder — MVP

A tiny full-stack app that helps nonprofits discover and research potential grantmakers.

- **Backend**: FastAPI + Postgres (Docker) + pgvector  
- **Data**: ProPublica Nonprofit Explorer (seed), Apollo (org enrichment), Firecrawl (site extraction)  
- **Search**: Keyword filters + semantic search with pgvector  
- **Frontend**: Next.js (App Router) + Tailwind CSS

## Repo layout

/donor-finder-api # FastAPI backend
/donor-finder-ui # Next.js frontend

markdown
Copy code

## Quick start (local)

### 0) Prereqs
- Docker, Python 3.11+, Node 18+
- (Optional) API keys:
  - `APOLLO_API_KEY` (enrichment)
  - `FIRECRAWL_API_KEY` (site extraction and snapshots)

### 1) Start Postgres (with pgvector)
```bash
docker run -d --name donor-pg \
  -e POSTGRES_PASSWORD=postgres \
  -p 5433:5432 \
  ankane/pgvector
2) Create schema
Open a psql shell:

bash
Copy code
docker exec -it donor-pg psql -U postgres -d postgres
Paste the schema from donor-finder-api/README.md (“Create extension + schema”) and run it.

3) Run backend
bash
Copy code
cd donor-finder-api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# env
export DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5433/postgres"
export APOLLO_API_KEY="<optional>"
export FIRECRAWL_API_KEY="<optional>"

uvicorn app.main:app --reload --port 8000 --host 0.0.0.0
4) Run frontend
bash
Copy code
cd ../donor-finder-ui
cp .env.local.example .env.local   # edit if needed
npm install
npm run dev
# open http://localhost:3000/donors
Bootstrap data (first run)
bash
Copy code
# Seed ~35 CA foundations (education-ish)
curl -X POST "http://localhost:8000/donors/ingest/propublica?state=CA&ntee_major=2&limit=35"

# Build embeddings for semantic search
curl -X POST "http://localhost:8000/donors/embeddings/build?batch_size=32&max_rows=500"

# Optional: backfill websites via Apollo (needs APOLLO_API_KEY)
curl -X POST "http://localhost:8000/donors/websites/backfill_apollo?limit=12"

# Optional: enrich + crawl one donor (replace :id)
curl -X POST "http://localhost:8000/donors/2/enrich"
curl -X POST "http://localhost:8000/donors/2/crawl"
What this delivers
Filtering by state, keyword, asset range

Semantic search (“foundations supporting early childhood education in California”)

Donor profile page with:

summary (location, NTEE, assets)

crawled website profile (About, Mission, Areas, Apply, Contacts, Leadership) when available

evidence cards: links + captured page markdown

What I’d build next
See NEXT_STEPS.md.
