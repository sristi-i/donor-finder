import Link from "next/link";
import { Donor } from "@/lib/types";

function money(n?: number | null) {
  if (!n && n !== 0) return "—";
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(n);
}

export default function DonorList({ donors }: { donors: Donor[] }) {
  if (!donors?.length) return <p className="text-sm text-zinc-400">No donors found.</p>;
  return (
    <ul className="divide-y divide-zinc-800">
      {donors.map(d => (
        <li key={d.id} className="py-4">
          <div className="flex items-center justify-between">
            <Link href={`/donors/${d.id}`} className="no-underline">
              <h3 className="text-lg font-semibold text-zinc-100 hover:text-white">{d.name}</h3>
            </Link>
            {d.website ? (
              <a href={`http://${d.website}`} target="_blank" className="text-xs text-blue-400 hover:text-blue-300 underline">
                Visit site ↗
              </a>
            ) : null}
          </div>
          <div className="text-sm text-zinc-400">
            {(d.city || d.state) ? <div>{[d.city, d.state].filter(Boolean).join(", ")}</div> : null}
            <div>Assets: ${money(d.assets_total)}</div>
          </div>
        </li>
      ))}
    </ul>
  );
}
