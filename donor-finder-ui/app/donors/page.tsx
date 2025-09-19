// app/donors/page.tsx
import { listDonors, semanticSearch, seedIfEmpty } from "@/app/lib/api";
import type { Donor, DonorListResponse } from "@/app/lib/types";

type SearchParams = Promise<{
  state?: string;
  q?: string;
  min_assets?: string;
  max_assets?: string;
  semantic?: string;
}>;

export const dynamic = "force-dynamic";

export default async function DonorIndex({ searchParams }: { searchParams: SearchParams }) {
  const sp = await searchParams;

  await seedIfEmpty();

  const state = String(sp?.state ?? "CA");
  const q = String(sp?.q ?? "");
  const min_assets = String(sp?.min_assets ?? "");
  const max_assets = String(sp?.max_assets ?? "");
  const semantic = String(sp?.semantic ?? "");

  let donors: Donor[] = [];
  let total = 0;
  let semanticCount = 0;

  if (semantic) {
    const res = await semanticSearch({ query: semantic, state, limit: 25 });
    donors = res.items;
    semanticCount = res.count;
  } else {
    const res: DonorListResponse = await listDonors({ state, q, min_assets, max_assets, limit: 25 });
    donors = res.items;
    total = res.total;
  }

  return (
    <>
      <h1 className="text-3xl font-semibold mb-6">Donor Finder</h1>

      {/* filter row */}
      <form action="/donors" method="get" className="flex flex-wrap gap-3 mb-4">
        <select name="state" defaultValue={state} className="input w-24">
          {["CA","NY","TX","WA","MA","FL","IL","PA","OH","MI"].map(s => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        <input name="q" defaultValue={q} placeholder="Keyword (name/mission)" className="input flex-1 min-w-64" />
        <input name="min_assets" defaultValue={min_assets} placeholder="Min assets" className="input w-36" />
        <input name="max_assets" defaultValue={max_assets} placeholder="Max assets" className="input w-36" />
        <button className="btn btn-primary">Filter</button>
      </form>

      {/* semantic row */}
      <form action="/donors" method="get" className="flex gap-3 mb-6">
        <input type="hidden" name="state" value={state} />
        <input name="semantic" defaultValue={semantic} placeholder="Natural language (e.g., early childhood in CA)" className="input flex-1" />
        <button className="btn bg-fuchsia-600 text-white hover:bg-fuchsia-700">Semantic</button>
      </form>

      <div className="text-sm text-gray-600 mb-3">
        {semantic ? `${semanticCount} semantic matches` : `${total} donors`}
      </div>

      <div className="space-y-4">
        {donors.map(d => {
          const donorHref = `/donors/${d.id}`;
          const siteHref = d.website ? `http://${d.website}` : null;

          return (
            <div key={d.id} className="card hover:border-blue-400">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <a href={donorHref} className="font-semibold text-lg text-blue-700 hover:underline break-words">
                    {d.name}
                  </a>
                  <div className="text-sm text-gray-600">{[d.city, d.state].filter(Boolean).join(", ") || "—"}</div>
                  <div className="text-sm text-gray-600">Assets: {d.assets_total?.toLocaleString() ?? "—"}</div>
                </div>

                <div className="shrink-0">
                  {siteHref && (
                    <a
                      href={siteHref}
                      target="_blank"
                      rel="noreferrer"
                      className="btn btn-secondary"
                    >
                      Visit site ↗
                    </a>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </>
  );
}
