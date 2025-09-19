from __future__ import annotations
import re
from typing import Dict, List, Tuple
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
HEADERS = {
    "User-Agent": "DonorFinderBot/0.1 (+https://example.org; polite crawl for MVP demo)"
}

def normalize_url(url: str) -> str | None:
    if not url:
        return None
    if not urlparse(url).scheme:
        url = "https://" + url
    return url

def looks_like_people_page(url: str, text: str) -> bool:
    lower = (url + " " + text[:200]).lower()
    return any(k in lower for k in ["team", "leadership", "board", "staff", "people"])

def looks_like_grants_page(url: str, text: str) -> bool:
    lower = (url + " " + text[:200]).lower()
    return any(k in lower for k in ["grant", "apply", "funding", "opportunit"])

def extract_emails(text: str) -> List[str]:
    return sorted(set(EMAIL_RE.findall(text)))

async def fetch(url: str, timeout: int = 20) -> Tuple[str, str]:
    async with httpx.AsyncClient(headers=HEADERS, timeout=timeout, follow_redirects=True) as client:
        r = await client.get(url)
        r.raise_for_status()
        return r.text, str(r.url)

def absolute_links(base_url: str, html: str, limit: int = 20) -> List[str]:
    soup = BeautifulSoup(html, "lxml")
    links: List[str] = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        url = urljoin(base_url, href)
        if url not in links and urlparse(url).netloc == urlparse(base_url).netloc:
            links.append(url)
        if len(links) >= limit:
            break
    return links

def extract_names_and_roles(html: str) -> List[Dict[str, str]]:
    soup = BeautifulSoup(html, "lxml")
    out: List[Dict[str, str]] = []
    for sel in ["h1", "h2", "h3", ".team-member", ".person", ".staff", "li"]:
        for el in soup.select(sel):
            text = " ".join(el.get_text(" ", strip=True).split())
            if 5 <= len(text) <= 80 and (" " in text):
                out.append({"name": text})
        if len(out) > 20:
            break
    seen = set()
    uniq: List[Dict[str, str]] = []
    for p in out:
        n = p["name"].lower()
        if n not in seen:
            uniq.append(p)
            seen.add(n)
    return uniq[:20]

async def crawl_site(base_url: str, max_pages: int = 6) -> Dict[str, object]:
    """
    Returns { emails, contacts, opportunities, pages_checked }
    """
    base_url = normalize_url(base_url)
    if not base_url:
        return {"emails": [], "contacts": [], "opportunities": [], "pages_checked": []}

    results = {"emails": set(), "contacts": [], "opportunities": [], "pages_checked": []}
    try:
        html, final_url = await fetch(base_url)
        results["pages_checked"].append(final_url)
    except Exception:
        return {"emails": [], "contacts": [], "opportunities": [], "pages_checked": []}

    queue = [final_url] + absolute_links(final_url, html, limit=15)

    for url in queue[:max_pages]:
        try:
            html, final_url = await fetch(url)
        except Exception:
            continue
        results["pages_checked"].append(final_url)

        soup = BeautifulSoup(html, "lxml")
        text = soup.get_text(" ", strip=True)

        for e in extract_emails(text):
            results["emails"].add(e)

        if looks_like_people_page(final_url, text):
            contacts = extract_names_and_roles(html)
            for c in contacts:
                c["source_url"] = final_url
            results["contacts"].extend(contacts)

        if looks_like_grants_page(final_url, text):
            snippet = text[:1000]
            results["opportunities"].append({"url": final_url, "snippet": snippet})

    results["emails"] = sorted(results["emails"])
    return results
