import os
import httpx

APOLLO_API_KEY = os.getenv("APOLLO_API_KEY")
BASE_URL = "https://api.apollo.io/v1"

if not APOLLO_API_KEY:
    print("[WARN] APOLLO_API_KEY is not set. Apollo enrichment will no-op.")

HEADERS = {
    "Authorization": f"Bearer {APOLLO_API_KEY}" if APOLLO_API_KEY else "",
    "Content-Type": "application/json",
}

async def enrich_org_by_domain(domain: str) -> dict | None:
    """Apollo org enrichment by domain."""
    if not APOLLO_API_KEY:
        return None
    url = f"{BASE_URL}/organizations/enrich"
    payload = {"domain": domain}
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            r = await client.post(url, headers=HEADERS, json=payload)
            if r.status_code != 200:
                return None
            data = r.json()
            return data.get("organization")
        except httpx.HTTPError:
            return None

async def search_org_by_name(name: str, state: str | None = None) -> dict | None:
    """
    Search Apollo organizations by name (optionally hint by state).
    Returns best hit or None.
    """
    if not APOLLO_API_KEY:
        return None
    url = f"{BASE_URL}/organizations/search"
    payload = {
        "q_organization_name": name,
        "page": 1,
        "per_page": 1,
    }
    if state:
        payload["person_locations"] = [state]  # weak heuristic

    async with httpx.AsyncClient(timeout=20) as client:
        try:
            r = await client.post(url, headers=HEADERS, json=payload)
            if r.status_code != 200:
                return None
            data = r.json()
            orgs = (data.get("organizations") or []) \
                or (data.get("organizations_page") or {}).get("organizations", [])
            if not orgs:
                return None
            return orgs[0]
        except httpx.HTTPError:
            return None
