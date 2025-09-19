// app/lib/api.ts
import { Donor, DonorDetail } from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/* --------------------------
 * Core fetch helpers
 * -------------------------- */
async function json<T>(url: string, init?: RequestInit): Promise<T> {
  const r = await fetch(url, { cache: "no-store", ...init });
  if (!r.ok) {
    const msg = await r.text().catch(() => r.statusText);
    throw new Error(`${r.status} ${r.statusText}: ${msg}`);
  }
  return r.json();
}

/* --------------------------
 * Public API used by pages
 * -------------------------- */

// List donors with simple filters (state/q/min/max)
export async function listDonors(params: {
  state?: string;
  q?: string;
  min_assets?: string | number;
  max_assets?: string | number;
  limit?: number;
  offset?: number;
}): Promise<{ items: Donor[]; total: number }> {
  const usp = new URLSearchParams();
  if (params.state) usp.set("state", params.state);
  if (params.q) usp.set("q", params.q);
  if (params.min_assets) usp.set("min_assets", String(params.min_assets));
  if (params.max_assets) usp.set("max_assets", String(params.max_assets));
  usp.set("limit", String(params.limit ?? 25));
  if (params.offset) usp.set("offset", String(params.offset));

  return json<{ items: Donor[]; total: number }>(`${BASE}/donors?${usp.toString()}`);
}

// Semantic search (LLM/pgvector)
export async function semanticSearch(params: {
  query: string;
  state?: string;
  min_assets?: number;
  max_assets?: number;
  limit?: number;
}): Promise<{ items: Donor[]; count: number }> {
  return json<{ items: Donor[]; count: number }>(`${BASE}/donors/search/semantic`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      query: params.query,
      state: params.state,
      min_assets: params.min_assets,
      max_assets: params.max_assets,
      limit: params.limit ?? 10,
    }),
  });
}

// Donor detail (includes enrichments + contacts + grants)
export async function fetchDonorDetail(id: number): Promise<DonorDetail> {
  return json<DonorDetail>(`${BASE}/donors/${id}`);
}

/* --------------------------
 * “Seed” convenience for local dev
 * -------------------------- */

// Seed a small dataset locally if DB is empty
export async function seedIfEmpty(): Promise<void> {
  // Is there at least 1 CA donor?
  const check = await listDonors({ state: "CA", limit: 1, offset: 0 }).catch(() => ({ total: 0 }));
  if ((check?.total ?? 0) > 0) return;

  // 1) Ingest a small set from ProPublica
  await json(`${BASE}/donors/ingest/propublica?state=CA&ntee_major=2&limit=35`, { method: "POST" });

  // 2) Build embeddings for semantic search
  await json(`${BASE}/donors/embeddings/build?batch_size=32&max_rows=500`, { method: "POST" });

  // 3) Try to backfill missing websites via Apollo (best-effort)
  // ok if it fails silently — it’s just enrichment
  await fetch(`${BASE}/donors/websites/backfill_apollo?limit=12`, { method: "POST" }).catch(() => {});
}

/* --------------------------
 * Optional helpers (if you call them)
 * -------------------------- */

// Opportunistically enrich (Apollo) or crawl (Firecrawl) for one donor
export async function autoEnrichIfNeeded(donorId: number): Promise<void> {
  // Apollo enrich (company profile & top people)
  await fetch(`${BASE}/donors/${donorId}/enrich`, { method: "POST" }).catch(() => {});
  // Crawl website for structured profile + evidence pages
  await fetch(`${BASE}/donors/${donorId}/crawl`, { method: "POST" }).catch(() => {});
}
