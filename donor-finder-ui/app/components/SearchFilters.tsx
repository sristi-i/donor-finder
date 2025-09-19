"use client";
import { useRouter, useSearchParams } from "next/navigation";
import { useState, useMemo } from "react";

export default function SearchFilters() {
  const router = useRouter();
  const sp = useSearchParams();
  const [state, setState] = useState(sp.get("state") || "CA");
  const [q, setQ] = useState(sp.get("q") || "");
  const [minA, setMinA] = useState(sp.get("min_assets") || "");
  const [maxA, setMaxA] = useState(sp.get("max_assets") || "");
  const [semantic, setSemantic] = useState(sp.get("semantic") || "");

  const base = useMemo(() => "/donors", []);

  const applyFilters = () => {
    const usp = new URLSearchParams();
    if (state) usp.set("state", state);
    if (q) usp.set("q", q);
    if (minA) usp.set("min_assets", minA);
    if (maxA) usp.set("max_assets", maxA);
    router.push(`${base}?${usp.toString()}`);
  };

  const runSemantic = () => {
    const usp = new URLSearchParams();
    if (state) usp.set("state", state);
    usp.set("semantic", semantic);
    router.push(`${base}?${usp.toString()}`);
  };

  return (
    <div className="grid gap-3 md:grid-cols-[120px_1fr_160px_160px_auto] items-center">
      <select value={state} onChange={e => setState(e.target.value)} className="input">
        <option>CA</option>
        <option>NY</option>
        <option>TX</option>
        <option>IL</option>
        <option>WA</option>
      </select>

      <input className="input" placeholder="Keyword (name/mission)" value={q} onChange={e=>setQ(e.target.value)} />
      <input className="input" placeholder="Min assets" value={minA} onChange={e=>setMinA(e.target.value)} />
      <input className="input" placeholder="Max assets" value={maxA} onChange={e=>setMaxA(e.target.value)} />
      <button onClick={applyFilters} className="btn-primary">Filter</button>

      <input className="input md:col-span-4" placeholder="Natural language (e.g. “early childhood in CA”)" value={semantic} onChange={e=>setSemantic(e.target.value)} />
      <button onClick={runSemantic} className="btn bg-fuchsia-600 hover:bg-fuchsia-500 text-white">Semantic</button>
    </div>
  );
}
