"use client";

import Link from "next/link";
import useSWR from "swr";
import { getDonors } from "@/app/lib/api";
import { DonorListResponse } from "@/app/lib/types";
import { useState } from "react";

const fetcher = ([_key, params]: any) => getDonors(params);

export default function DonorTable() {
  const [state, setState] = useState("CA");
  const [q, setQ] = useState("");
  const [limit] = useState(25);

  const { data, isLoading, error, mutate } = useSWR<DonorListResponse>(
    ["donors", { state, q, limit }],
    fetcher
  );

  return (
    <div className="space-y-4">
      <div className="flex gap-3 items-end">
        <div>
          <label className="block text-sm">State</label>
          <input value={state} onChange={e => setState(e.target.value)} className="border px-2 py-1 rounded w-24" />
        </div>
        <div className="flex-1">
          <label className="block text-sm">Search</label>
          <input value={q} onChange={e => setQ(e.target.value)} placeholder="keyword in name / mission"
                 className="border px-2 py-1 rounded w-full" />
        </div>
        <button onClick={() => mutate()} className="bg-black text-white px-3 py-2 rounded">Search</button>
      </div>

      {isLoading && <div>Loading…</div>}
      {error && <div className="text-red-600">Failed to load</div>}

      <table className="w-full border text-sm">
        <thead className="bg-gray-50">
          <tr>
            <th className="p-2 text-left">Name</th>
            <th className="p-2 text-left">Location</th>
            <th className="p-2 text-right">Assets</th>
            <th className="p-2">Website</th>
          </tr>
        </thead>
        <tbody>
          {data?.items?.map(d => (
            <tr key={d.id} className="border-t hover:bg-gray-50">
              <td className="p-2">
                <Link href={`/donors/${d.id}`} className="text-blue-600 underline">{d.name}</Link>
              </td>
              <td className="p-2">{[d.city, d.state].filter(Boolean).join(", ")}</td>
              <td className="p-2 text-right">{d.assets_total?.toLocaleString() ?? "—"}</td>
              <td className="p-2">
                {d.website ? <a className="text-blue-600 underline" href={`https://${d.website}`} target="_blank">{d.website}</a> : "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="text-sm text-gray-600">
        {data ? `${data.items.length} shown` : ""} {data?.total ? `• ${data.total} total` : ""}
      </div>
    </div>
  );
}
