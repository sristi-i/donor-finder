# app/services/firecrawl.py
from __future__ import annotations
import os
import json
import httpx

FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
BASE = "https://api.firecrawl.dev/v1"

if not FIRECRAWL_API_KEY:
    print("[WARN] FIRECRAWL_API_KEY is not set. Firecrawl calls will NO-OP.")

def _headers() -> dict:
    return {
        "Authorization": f"Bearer {FIRECRAWL_API_KEY or ''}",
        "Content-Type": "application/json",
    }

async def extract_structured(urls: list[str], prompt: str, schema: dict) -> dict | None:
    """
    Calls Firecrawl's /extract with a schema and prompt.
    Returns parsed JSON (dict) or None on error.
    """
    if not FIRECRAWL_API_KEY:
        return None

    payload = {
        "urls": urls,
        "schema": schema,
        "prompt": prompt,
    }

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(f"{BASE}/extract", headers=_headers(), json=payload)
            if r.status_code != 200:
                print(f"[Firecrawl] /extract non-200: {r.status_code} body={r.text[:500]}")
                return None
            data = r.json()
            # Firecrawl returns {"success":true, "id": "...", "data": {...}} OR {"success":true,"data":[...]}
            # Normalize to one dict for our UI:
            # Prefer "data" if present; else pass the whole body (so we can see it).
            return data.get("data") or data
    except httpx.HTTPError as e:
        print(f"[Firecrawl] /extract error: {e}")
        return None

async def scrape_markdown(url: str) -> dict | None:
    """
    Calls Firecrawl's /crawl or /scrape-like markdown API.
    Firecrawl's public API exposes /crawl for site capture; we’ll ask for markdown.
    If your plan only supports /extract, keep using extract on single URL
    and pull page text from the result.
    """
    if not FIRECRAWL_API_KEY:
        return None

    # Many folks use /crawl with options, but if your plan doesn’t support it,
    # we’ll fallback to /extract with a trivial schema to get markdown-ish content.
    # First try /crawl (if available):
    crawl_payload = {
        "url": url,
        "formats": ["markdown"],
        "maxDepth": 0,
        "limit": 1
    }

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(f"{BASE}/crawl", headers=_headers(), json=crawl_payload)
            if r.status_code == 200:
                data = r.json()
                # Normalize shape to {"data":{"markdown": "..."}}
                # Firecrawl Crawl can return an array of pages or a single doc—handle both:
                if isinstance(data, dict) and "data" in data:
                    d = data["data"]
                    if isinstance(d, list) and d:
                        first = d[0] or {}
                        md = first.get("markdown") or first.get("content") or ""
                        return {"data": {"markdown": md}}
                    if isinstance(d, dict):
                        md = d.get("markdown") or d.get("content") or ""
                        return {"data": {"markdown": md}}
                # If format unexpected, keep some evidence:
                return {"data": {"markdown": json.dumps(data)[:20000]}}
            else:
                print(f"[Firecrawl] /crawl non-200: {r.status_code} body={r.text[:400]}")
    except httpx.HTTPError as e:
        print(f"[Firecrawl] /crawl error: {e}")

    # Fallback: /extract with simple schema to pull page text
    try:
        payload = {
            "urls": [url],
            "schema": {
                "type": "object",
                "properties": {
                    "markdown": {"type": "string", "description": "Main page text content (markdown/plain)."}
                }
            },
            "prompt": "Return the primary page content as plain text/markdown in the 'markdown' field.",
        }
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(f"{BASE}/extract", headers=_headers(), json=payload)
            if r.status_code != 200:
                print(f"[Firecrawl] fallback /extract non-200: {r.status_code} body={r.text[:400]}")
                return None
            data = r.json()
            md = (data.get("data") or {}).get("markdown")
            if not md:
                # last resort: stash whole body so we see something
                return {"data": {"markdown": json.dumps(data)[:20000]}}
            return {"data": {"markdown": md}}
    except httpx.HTTPError as e:
        print(f"[Firecrawl] fallback /extract error: {e}")
        return None
