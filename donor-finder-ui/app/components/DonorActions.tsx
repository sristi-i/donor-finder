// app/components/DonorActions.tsx
"use client";

import { useTransition } from "react";
import { useRouter } from "next/navigation";

export default function DonorActions({ donorId }: { donorId: number }) {
  const [pending, start] = useTransition();
  const router = useRouter();
  const base = process.env.NEXT_PUBLIC_API_URL!;

  const run = (path: string, label: string) =>
    start(async () => {
      try {
        const res = await fetch(`${base}${path}`, { method: "POST" });
        if (!res.ok) {
          alert(`${label} failed`);
        } else {
          router.refresh(); // re-fetch server component data
        }
      } catch {
        alert(`${label} failed`);
      }
    });

  return (
    <div className="flex gap-3">
      <button
        onClick={() => run(`/donors/${donorId}/enrich`, "Enrich")}
        className="px-3 py-2 rounded bg-emerald-600 hover:bg-emerald-500 disabled:opacity-60"
        disabled={pending}
      >
        {pending ? "Working..." : "Enrich (Apollo)"}
      </button>
      <button
        onClick={() => run(`/donors/${donorId}/crawl`, "Crawl")}
        className="px-3 py-2 rounded bg-orange-600 hover:bg-orange-500 disabled:opacity-60"
        disabled={pending}
      >
        {pending ? "Working..." : "Crawl (Firecrawl)"}
      </button>
    </div>
  );
}
