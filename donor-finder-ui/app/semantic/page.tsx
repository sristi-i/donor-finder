"use client";

import { useState } from "react";
import { semanticSearch, Donor } from "@/app/lib/api";

type Row = Donor & { distance: number };

export default function SemanticPage() {
  const [query, setQuery] = useState("foundations supporting early childhood education in California");
  const [state, setState] = useState("CA");
  const [results, setResults] = useState<Row[] | null>(null);
  const [loading, setLoading] = useState(false);

  const runSearch = async () => {
    setLoading(true);
    try {
      const res = await semanticSearch({
        query,
        state: state || undefined,
        limit: 15,
      });
      setResults(res.items);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 space-y-4 max-w-6xl mx-auto">
      <h1 className="text-2xl font-semibold">Semantic Search (pgvector)</h1>

      <div className="grid md:grid-cols-8 gap-3 bg-white p-4 rounded-xl shadow">
        <input
          className="md:col-span-6 border rounded px-3 py-2"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder='e.g. "foundations supporting early childhood education in California"'
        />
        <input
          className="border rounded px-3 py-2"
          placeholder="State (optional)"
          value={state}
          onChange={(e) => setState(e.target.value.toUpperCase())}
          maxLength={2}
        />
        <button
          className="bg-blue-600 text-white rounded px-3 font-medium"
          onClick={runSearch}
          disabled={loading || !query.trim()}
        >
          {loading ? "Searching…" : "Search"}
        </button>
      </div>

      {results && (
        <div className="grid gap-3">
          {results.map((d) => (
            <a
              key={d.id}
              href={`/donors/${d.id}`}
              className="block rounded-xl border p-4 hover:shadow"
            >
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-lg font-medium">{d.name}</div>
                  <div className="text-sm text-gray-600">
                    {(d.city ? `${d.city}, ` : "") + (d.state || "")}
                    {d.mission ? ` • ${d.mission}` : ""}
                  </div>
                </div>
                <div className="text-right text-xs text-gray-500">
                  cosine distance: {d.distance.toFixed(3)}
                </div>
              </div>
            </a>
          ))}
        </div>
      )}
    </div>
  );
}
