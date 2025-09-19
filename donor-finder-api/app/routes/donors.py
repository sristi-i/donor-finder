# app/routes/donors.py
from __future__ import annotations
import json
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, Query, HTTPException, Body
from sqlalchemy import text, bindparam
from sqlalchemy.dialects.postgresql import JSONB

from app.db import get_session
from app import propublica
from app.embeddings import embed_texts, to_pgvector
from app.services.apollo import enrich_org_by_domain, search_org_by_name
from app.services.firecrawl import scrape_markdown, extract_structured


# --------------------------
# helpers
# --------------------------

def _to_domain(website: str | None) -> str | None:
    """Accepts 'ucla.edu' or 'https://ucla.edu/…' and returns bare domain like 'ucla.edu'."""
    if not website:
        return None
    w = website.strip()
    if "://" not in w:
        return w.lower()
    parsed = urlparse(w)
    host = (parsed.netloc or parsed.path).lower().strip("/")
    return host[4:] if host.startswith("www.") else host


def _normalize_site(website: str | None) -> str | None:
    """Return normalized https URL like 'https://ucla.edu' from bare or full input."""
    if not website:
        return None
    w = website.strip()
    if "://" not in w:
        w = f"https://{w}"
    parsed = urlparse(w)
    host = (parsed.netloc or parsed.path).lower().strip("/")
    if not host:
        return None
    return f"https://{host}"


def _candidate_pages_for(domain: str) -> list[str]:
    base = f"https://{domain}"
    return [
        base,
        f"{base}/about",
        f"{base}/about-us",
        f"{base}/mission",
        f"{base}/team",
        f"{base}/leadership",
        f"{base}/people",
        f"{base}/grants",
        f"{base}/grantmaking",
        f"{base}/apply",
        f"{base}/funding",
        f"{base}/contact",
    ]


router = APIRouter()


# --------------------------
# list & detail
# --------------------------

@router.get("")
def list_donors(
    state: str | None = None,
    q: str | None = None,
    min_assets: float | None = None,
    max_assets: float | None = None,
    min_grants: float | None = None,
    max_grants: float | None = None,
    limit: int = 25,
    offset: int = 0,
    session = Depends(get_session),
):
    """
    Filterable donors listing for the UI.
    """
    where = ["1=1"]
    params = {"limit": limit, "offset": offset}

    if state:
        where.append("state = :state")
        params["state"] = state

    if q:
        where.append("(name ILIKE :q OR mission ILIKE :q)")
        params["q"] = f"%{q}%"

    if min_assets is not None:
        where.append("assets_total >= :min_assets")
        params["min_assets"] = min_assets

    if max_assets is not None:
        where.append("assets_total <= :max_assets")
        params["max_assets"] = max_assets

    if min_grants is not None:
        where.append("grants_total >= :min_grants")
        params["min_grants"] = min_grants

    if max_grants is not None:
        where.append("grants_total <= :max_grants")
        params["max_grants"] = max_grants

    sql = text(f"""
      SELECT * FROM donors
      WHERE {' AND '.join(where)}
      ORDER BY assets_total DESC NULLS LAST, id
      LIMIT :limit OFFSET :offset
    """)
    items = session.execute(sql, params).mappings().all()
    total = session.execute(text(f"SELECT COUNT(*) FROM donors WHERE {' AND '.join(where)}"), params).scalar()
    return {"items": items, "total": total}


@router.get("/{id}")
def donor_detail(id: int, session=Depends(get_session)):
    """
    One donor + recent grants/contacts/enrichments for profile page.
    """
    donor = session.execute(text("SELECT * FROM donors WHERE id=:id"), {"id": id}).mappings().first()
    if not donor:
        raise HTTPException(404, "Donor not found")

    grants = session.execute(
        text("SELECT * FROM grants WHERE donor_id=:id ORDER BY year DESC NULLS LAST, id LIMIT 10"),
        {"id": id}
    ).mappings().all()

    contacts = session.execute(
        text("SELECT * FROM contacts WHERE donor_id=:id ORDER BY created_at DESC, id DESC LIMIT 20"),
        {"id": id}
    ).mappings().all()

    enrichments = session.execute(
        text("""
            SELECT id, donor_id, kind, source, url, created_at, raw
            FROM enrichments
            WHERE donor_id=:id
            ORDER BY created_at DESC, id DESC
            LIMIT 25
        """),
        {"id": id}
    ).mappings().all()

    return {"donor": donor, "grants": grants, "contacts": contacts, "enrichments": enrichments}


# --------------------------
# ingestion (ProPublica)
# --------------------------

@router.post("/ingest/propublica")
async def ingest(
    state: str = Query("CA", description="Two-letter state, e.g., CA"),
    ntee_major: int = Query(2, description="NTEE major group (2=Education)"),
    limit: int = Query(35, description="How many donors to ingest"),
    session=Depends(get_session)
):
    """
    Pull a small, real subset of donors from ProPublica and insert/update our DB.
    """
    page, added = 0, 0
    while added < limit:
        data = await propublica.search_orgs(state, ntee_major, page)
        orgs = data.get("organizations", [])
        if not orgs:
            break

        for o in orgs:
            ein = str(o.get("ein"))
            detail = await propublica.get_org(ein)

            org = detail.get("organization", {}) or {}
            filings = detail.get("filings_with_data", []) or []

            # pick a recent assets value if present
            tot_assets = None
            for f in filings[:3]:
                if "totassetsend" in f and f["totassetsend"] is not None:
                    tot_assets = f["totassetsend"]
                    break

            name = org.get("name") or o.get("organization_name")
            subseccd = org.get("subseccd")
            is_foundation = "foundation" in (name or "").lower()

            # keep to foundations/grantmakers roughly
            if not (is_foundation or subseccd in (3, 92)):
                continue

            stmt = text("""
                INSERT INTO donors (
                    ein, name, state, city, mission, ntee_code,
                    assets_total, irs_subsection, website, source
                )
                VALUES (
                    :ein, :name, :state, :city, :mission, :ntee,
                    :assets, :sub, :website, :source
                )
                ON CONFLICT (ein) DO UPDATE SET
                    name=EXCLUDED.name,
                    state=EXCLUDED.state,
                    city=EXCLUDED.city,
                    mission=EXCLUDED.mission,
                    ntee_code=EXCLUDED.ntee_code,
                    assets_total=EXCLUDED.assets_total,
                    irs_subsection=EXCLUDED.irs_subsection,
                    website=COALESCE(EXCLUDED.website, donors.website),
                    source=EXCLUDED.source,
                    updated_at=NOW()
            """).bindparams(bindparam("source", type_=JSONB))

            session.execute(stmt, {
                "ein": ein,
                "name": name,
                "state": org.get("state") or o.get("state"),
                "city": org.get("city"),
                "mission": org.get("ntee_code") or o.get("ntee_code"),
                "ntee": org.get("ntee_code") or o.get("ntee_code"),
                "assets": tot_assets,
                "sub": subseccd,
                "website": org.get("website") or None,
                "source": json.dumps(detail),
            })

            added += 1
            if added >= limit:
                break

        page += 1

    session.commit()
    return {"added": added, "state": state, "ntee_major": ntee_major}


# --------------------------
# embeddings & semantic search
# --------------------------

@router.post("/embeddings/build")
def build_embeddings(
    batch_size: int = Query(32, ge=1, le=256),
    max_rows: int = Query(200, ge=1),
    session = Depends(get_session),
):
    """
    Create embeddings for donors missing them using a small doc (name+mission+location+website).
    """
    rows = session.execute(text("""
        SELECT d.id, d.name, COALESCE(d.mission,'' ) AS mission,
               COALESCE(d.city,'') AS city, COALESCE(d.state,'') AS state,
               COALESCE(d.website,'') AS website
        FROM donors d
        LEFT JOIN donor_embeddings de ON de.donor_id = d.id
        WHERE de.donor_id IS NULL
        ORDER BY d.id
        LIMIT :max_rows
    """), {"max_rows": max_rows}).mappings().all()

    if not rows:
        return {"created": 0, "note": "No missing embeddings"}

    docs, ids = [], []
    for r in rows:
        parts = [r["name"]]
        if r["mission"]:
            parts.append(r["mission"])
        loc = f'{r["city"]}, {r["state"]}'.strip(", ")
        if loc:
            parts.append(loc)
        if r["website"]:
            parts.append(r["website"])
        doc = " | ".join(p for p in parts if p)
        docs.append(doc)
        ids.append(r["id"])

    created = 0
    for i in range(0, len(docs), batch_size):
        batch_docs = docs[i:i+batch_size]
        batch_ids = ids[i:i+batch_size]
        vecs = embed_texts(batch_docs)

        for donor_id, doc, vec in zip(batch_ids, batch_docs, vecs):
            stmt = text("""
                INSERT INTO donor_embeddings (donor_id, embedding, doc)
                VALUES (:donor_id, CAST(:embedding AS vector), :doc)
                ON CONFLICT (donor_id) DO UPDATE SET
                    embedding = EXCLUDED.embedding,
                    doc = EXCLUDED.doc
            """)
            session.execute(stmt, {
                "donor_id": donor_id,
                "embedding": to_pgvector(vec),
                "doc": doc
            })
            created += 1

    session.commit()
    return {"created": created}


@router.post("/search/semantic")
def semantic_search(
    payload: dict = Body(..., example={
        "query": "foundations supporting early childhood education in California",
        "state": "CA",
        "limit": 10
    }),
    session = Depends(get_session),
):
    """
    Semantic search donors using pgvector cosine distance. Optional filters: state, min/max assets.
    """
    query = (payload.get("query") or "").strip()
    if not query:
        raise HTTPException(400, "Missing 'query'")

    state = payload.get("state")
    min_assets = payload.get("min_assets")
    max_assets = payload.get("max_assets")
    limit = int(payload.get("limit") or 10)

    qvec = embed_texts([query])[0]

    where = ["1=1"]
    params = {"qvec": to_pgvector(qvec), "limit": limit}

    if state:
        where.append("d.state = :state")
        params["state"] = state
    if min_assets is not None:
        where.append("d.assets_total >= :min_assets")
        params["min_assets"] = min_assets
    if max_assets is not None:
        where.append("d.assets_total <= :max_assets")
        params["max_assets"] = max_assets

    sql = text(f"""
        SELECT d.id, d.name, d.state, d.city, d.mission,
               d.assets_total, d.grants_total,
               (de.embedding <=> CAST(:qvec AS vector)) AS distance,
               d.website
        FROM donor_embeddings de
        JOIN donors d ON d.id = de.donor_id
        WHERE {' AND '.join(where)}
        ORDER BY distance ASC
        LIMIT :limit
    """)
    rows = session.execute(sql, params).mappings().all()
    return {"items": rows, "count": len(rows)}


# --------------------------
# apollo enrichment (domain + profile)
# --------------------------

@router.post("/{id}/enrich")
async def enrich_donor(id: int, session=Depends(get_session)):
    donor = session.execute(text("SELECT * FROM donors WHERE id=:id"), {"id": id}).mappings().first()
    if not donor:
        raise HTTPException(404, "Donor not found")

    domain = _to_domain(donor.get("website"))
    if not domain:
        return {"id": id, "enriched": False, "reason": "no website/domain on record"}

    org = await enrich_org_by_domain(domain)
    if not org:
        return {"id": id, "enriched": False, "reason": "Apollo: no data / credits / invalid domain"}

    stmt_apollo = text("""
        INSERT INTO enrichments (donor_id, kind, source, url, raw)
        VALUES (:donor_id, :kind, :source, :url, :raw)
    """).bindparams(bindparam("raw", type_=JSONB))

    session.execute(stmt_apollo, {
        "donor_id": id,
        "kind": "company_profile",
        "source": "apollo",
        "url": "https://api.apollo.io/v1/organizations/enrich",
        "raw": json.dumps(org),
    })

    apollo_site = org.get("website_url") or org.get("domain")
    if apollo_site and (donor.get("website") or "").lower() != apollo_site.lower():
        session.execute(
            text("UPDATE donors SET website=:w, updated_at=NOW() WHERE id=:id"),
            {"w": apollo_site, "id": id}
        )

    top_people = (org.get("top_people") or [])[:5]
    for p in top_people:
        session.execute(text("""
            INSERT INTO contacts (donor_id, name, title, email, linkedin_url, source)
            VALUES (:donor_id, :name, :title, :email, :linkedin, :source)
            ON CONFLICT DO NOTHING
        """), {
            "donor_id": id,
            "name": p.get("name"),
            "title": p.get("title"),
            "email": p.get("email"),
            "linkedin": p.get("linkedin_url"),
            "source": "apollo",
        })

    session.commit()
    return {"id": id, "enriched": True, "contacts_added": len(top_people), "domain": domain}


@router.post("/enrich/batch")
async def enrich_batch(limit: int = Query(5, ge=1, le=25), session=Depends(get_session)):
    to_enrich = session.execute(text("""
        SELECT d.id, d.website
        FROM donors d
        WHERE d.website IS NOT NULL
          AND NOT EXISTS (
            SELECT 1 FROM enrichments e
            WHERE e.donor_id = d.id AND e.kind = 'company_profile'
          )
        ORDER BY d.id
        LIMIT :limit
    """), {"limit": limit}).mappings().all()

    results = []
    stmt_batch = text("""
        INSERT INTO enrichments (donor_id, kind, source, url, raw)
        VALUES (:donor_id, :kind, :source, :url, :raw)
    """).bindparams(bindparam("raw", type_=JSONB))

    for row in to_enrich:
        donor_id = row["id"]
        domain = _to_domain(row["website"])
        if not domain:
            results.append({"id": donor_id, "enriched": False, "reason": "bad website"})
            continue

        org = await enrich_org_by_domain(domain)
        if not org:
            results.append({"id": donor_id, "enriched": False, "reason": "apollo: no data/credits"})
            continue

        session.execute(stmt_batch, {
            "donor_id": donor_id,
            "kind": "company_profile",
            "source": "apollo",
            "url": "https://api.apollo.io/v1/organizations/enrich",
            "raw": json.dumps(org),
        })

        apollo_site = org.get("website_url") or org.get("domain")
        if apollo_site:
            session.execute(
                text("UPDATE donors SET website=:w, updated_at=NOW() WHERE id=:id"),
                {"w": apollo_site, "id": donor_id}
            )

        results.append({"id": donor_id, "enriched": True, "domain": domain})

    session.commit()
    return {"count": len(results), "enriched": results}


# --------------------------
# crawling (Firecrawl)
# --------------------------

@router.post("/{id}/crawl")
async def crawl_donor_site(id: int, session=Depends(get_session)):
    """
    Crawl donor website (if present) and store:
      - a structured 'company_profile' enrichment (Firecrawl extract)
      - a few markdown snapshots as 'page_markdown'
      - (light) contacts from structured payload
    """
    donor = session.execute(text("SELECT * FROM donors WHERE id=:id"), {"id": id}).mappings().first()
    if not donor:
        raise HTTPException(404, "Donor not found")

    website_raw = donor.get("website")
    norm = _normalize_site(website_raw)
    if not norm:
        return {"id": id, "crawled": False, "reason": "no website/domain on donor"}

    parsed = urlparse(norm)
    domain = (parsed.netloc or parsed.path).lower()
    if not domain:
        return {"id": id, "crawled": False, "reason": "invalid domain"}

    pages = _candidate_pages_for(domain)[:6]

    schema = {
        "type": "object",
        "properties": {
            "org_name": {"type": "string"},
            "about": {"type": "string"},
            "mission": {"type": "string"},
            "program_areas": {"type": "array", "items": {"type": "string"}},
            "grantmaking": {"type": "string"},
            "apply_instructions": {"type": "string"},
            "contacts": {
                "type": "object",
                "properties": {
                    "emails": {"type": "array", "items": {"type": "string"}},
                    "phones": {"type": "array", "items": {"type": "string"}},
                    "address": {"type": "string"},
                }
            },
            "leadership": {
                "type": "array",
                "items": {"type": "object", "properties": {
                    "name": {"type": "string"}, "title": {"type": "string"}
                }}
            }
        },
        "additionalProperties": True
    }

    prompt = (
        "From these pages, extract a compact profile for a grantmaking foundation: "
        "org_name, 1–2 paragraph about, mission in 1 sentence, up to 6 program_areas, "
        "grantmaking summary, apply_instructions (deadlines/eligibility), contacts (emails/phones/address), "
        "and leadership list with name/title when obvious."
    )

    structured = await extract_structured(pages, prompt=prompt, schema=schema)

    # Insert structured profile (as JSONB)
    if structured:
        stmt_struct = text("""
            INSERT INTO enrichments (donor_id, kind, source, url, raw)
            VALUES (:donor_id, :kind, :source, :url, :raw)
        """).bindparams(bindparam("raw", type_=JSONB))

        session.execute(stmt_struct, {
            "donor_id": id,
            "kind": "company_profile",
            "source": "firecrawl",
            "url": ", ".join(pages),
            "raw": json.dumps(structured),
        })

        # light contacts from leadership
        leadership = (structured.get("leadership") or []) if isinstance(structured, dict) else []
        seen = set()
        for p in leadership:
            name = (p or {}).get("name")
            title = (p or {}).get("title")
            if not name:
                continue
            key = (name or "", title or "")
            if key in seen:
                continue
            seen.add(key)
            session.execute(text("""
                INSERT INTO contacts (donor_id, name, title, source)
                VALUES (:donor_id, :name, :title, :source)
                ON CONFLICT DO NOTHING
            """), {"donor_id": id, "name": name, "title": title, "source": "firecrawl"})

    # Snapshot up to 3 pages of markdown
    saved_pages: list[str] = []
    stmt_md = text("""
        INSERT INTO enrichments (donor_id, kind, source, url, raw)
        VALUES (:donor_id, :kind, :source, :url, :raw)
    """).bindparams(bindparam("raw", type_=JSONB))

    for url in pages[:3]:
        page = await scrape_markdown(url)
        if page and page.get("data", {}).get("markdown"):
            md = page["data"]["markdown"][:20000]
            session.execute(stmt_md, {
                "donor_id": id,
                "kind": "page_markdown",
                "source": "firecrawl",
                "url": url,
                "raw": json.dumps({"url": url, "markdown": md}),
            })
            saved_pages.append(url)

    session.commit()
    return {
        "id": id,
        "crawled": True,
        "domain": domain,
        "structured": bool(structured),
        "pages_saved": saved_pages,
    }


# --------------------------
# website backfill via apollo search
# --------------------------

@router.post("/websites/backfill_apollo")
async def backfill_websites_apollo(
    limit: int = Query(12, ge=1, le=50),
    session = Depends(get_session),
):
    """
    For donors missing website, try Apollo organizations search by name and set website/domain.
    """
    rows = session.execute(text("""
        SELECT id, name, state
        FROM donors
        WHERE website IS NULL
        ORDER BY assets_total DESC NULLS LAST, id
        LIMIT :limit
    """), {"limit": limit}).mappings().all()

    updated: list[dict] = []
    stmt_websrc = text("""
        INSERT INTO enrichments (donor_id, kind, source, url, raw)
        VALUES (:id, :kind, :source, :url, :raw)
    """).bindparams(bindparam("raw", type_=JSONB))

    for r in rows:
        donor_id = r["id"]
        name = r["name"]
        state = r["state"]

        org = await search_org_by_name(name, state)
        if not org:
            updated.append({"id": donor_id, "updated": False, "reason": "apollo: no match"})
            continue

        # Apollo may give 'website_url' or 'domain'
        site = (org.get("website_url") or org.get("domain") or "").strip()
        if site.startswith("http://") or site.startswith("https://"):
            site = site.split("://", 1)[1]
        site = site.rstrip("/")

        if site:
            session.execute(
                text("UPDATE donors SET website=:w, updated_at=NOW() WHERE id=:id"),
                {"w": site, "id": donor_id}
            )

        session.execute(stmt_websrc, {
            "id": donor_id,
            "kind": "website_source",
            "source": "apollo",
            "url": "https://api.apollo.io/v1/organizations/search",
            "raw": json.dumps({"query": {"name": name, "state": state}, "org": org}),
        })

        updated.append({"id": donor_id, "updated": bool(site), "website": site or None})

    session.commit()
    return {"backfilled": len(updated), "items": updated}
