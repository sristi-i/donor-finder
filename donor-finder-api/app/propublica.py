"""
Thin async wrapper around ProPublica Nonprofit Explorer API (public).
This is the same public dataset we already used for seeding.
"""
from __future__ import annotations
import httpx

BASE = "https://projects.propublica.org/nonprofits/api/v2"

async def search_orgs(state: str, ntee_major: int, page: int = 0) -> dict:
    url = f"{BASE}/search.json?state%5Bid%5D={state}&ntee%5Bmajor%5D={ntee_major}&page={page}"
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url)
        r.raise_for_status()
        return r.json()

async def get_org(ein: str) -> dict:
    url = f"{BASE}/organizations/{ein}.json"
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url)
        r.raise_for_status()
        return r.json()
