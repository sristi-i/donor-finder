# 3) `donor-finder-ui/README.md` (frontend)

```markdown
# Donor Finder UI (Next.js + Tailwind)

## Env
Create `.env.local`:
NEXT_PUBLIC_API_URL=http://localhost:8000

shell
Copy code

## Install & run
```bash
npm install
npm run dev
# open http://localhost:3000/donors
If Tailwind/PostCSS errors appear:

bash
Copy code
npm i -D tailwindcss @tailwindcss/postcss postcss autoprefixer
Tailwind setup (already in repo)
tailwind.config.js scans ./app and ./components

postcss.config.js uses @tailwindcss/postcss + autoprefixer

app/globals.css imports tailwind layers and a few utility classes

Pages
/donors — filter bar (state, keyword, min/max assets) and semantic input.

If semantic query present → calls POST /donors/search/semantic.

Otherwise → GET /donors (with filters).

/donors/[id] — loads GET /donors/:id; shows:

donor summary (NTEE, assets, grants)

Website & company info (Firecrawl company_profile if available)

markup evidence cards (“open source”)

The profile page will best-effort trigger POST /donors/:id/crawl if the donor has a website but no Firecrawl profile yet.

First data load (backend calls)
bash
Copy code
curl -X POST "http://localhost:8000/donors/ingest/propublica?state=CA&ntee_major=2&limit=35"
curl -X POST "http://localhost:8000/donors/embeddings/build?batch_size=32&max_rows=500"
curl -X POST "http://localhost:8000/donors/websites/backfill_apollo?limit=12"
UX Notes
No raw “semantic score” shown — donors are just sorted by relevance.

External links open in a new tab.

Crawled profile is presented as About / Mission / Areas / How to apply / Contacts / Leadership when available.