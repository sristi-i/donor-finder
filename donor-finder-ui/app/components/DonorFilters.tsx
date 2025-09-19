"use client";

import { useState } from "react";

type Props = {
  onSearch: (filters: {
    state?: string;
    q?: string;
    min_assets?: string;
    max_assets?: string;
    semantic?: string;
  }) => Promise<void>;
};

export default function DonorFilters({ onSearch }: Props) {
  const [state, setState] = useState("CA");
  const [q, setQ] = useState("");
  const [minAssets, setMinAssets] = useState("");
  const [maxAssets, setMaxAssets] = useState("");
  const [semantic, setSemantic] = useState("");

  return (
    <div className="space-y-3">
      <div className="flex gap-3 max-sm:flex-col">
        <select
          value={state}
          onChange={(e) => setState(e.target.value)}
          className="w-36 rounded-md bg-zinc-900 border border-zinc-800 px-3 py-2"
        >
          {["", "CA", "NY", "TX", "WA", "MA", "IL"].map((s) => (
            <option key={s} value={s}>{s || "Any state"}</option>
          ))}
        </select>

        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Keyword (name/mission)"
          className="flex-1 rounded-md bg-zinc-900 border border-zinc-800 px-3 py-2"
        />
        <input
          value={minAssets}
          onChange={(e) => setMinAssets(e.target.value)}
          placeholder="Min assets"
          className="w-40 rounded-md bg-zinc-900 border border-zinc-800 px-3 py-2"
        />
        <input
          value={maxAssets}
          onChange={(e) => setMaxAssets(e.target.value)}
          placeholder="Max assets"
          className="w-40 rounded-md bg-zinc-900 border border-zinc-800 px-3 py-2"
        />

        <button
          onClick={() => onSearch({ state, q, min_assets: minAssets, max_assets: maxAssets })}
          className="rounded-md bg-blue-600 hover:bg-blue-500 px-4 py-2 font-medium"
        >
          Filter
        </button>
      </div>

      <div className="flex gap-3 max-sm:flex-col">
        <input
          value={semantic}
          onChange={(e) => setSemantic(e.target.value)}
          placeholder='Natural language (e.g. "early childhood in California")'
          className="flex-1 rounded-md bg-zinc-900 border border-zinc-800 px-3 py-2"
        />
        <button
          onClick={() => onSearch({ state, semantic })}
          className="rounded-md bg-fuchsia-600 hover:bg-fuchsia-500 px-4 py-2 font-medium"
        >
          Semantic
        </button>
      </div>
    </div>
  );
}
