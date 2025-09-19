"use client";

import { postCrawl, postEnrich } from "@/app/lib/api";
import { useState } from "react";

export default function EnrichButtons({ id, onDone }: { id: number; onDone?: () => void }) {
  const [busy, setBusy] = useState<"enrich"|"crawl"|null>(null);
  const run = async (which: "enrich"|"crawl") => {
    try {
      setBusy(which);
      if (which === "enrich") await postEnrich(id);
      else await postCrawl(id);
      onDone?.();
    } catch (e) {
      alert((e as Error).message);
    } finally {
      setBusy(null);
    }
  };

  return (
    <div className="flex gap-2">
      <button disabled={busy!==null} onClick={() => run("enrich")}
        className="px-3 py-2 rounded bg-black text-white disabled:opacity-50">
        {busy==="enrich" ? "Enriching…" : "Enrich (Apollo)"}
      </button>
      <button disabled={busy!==null} onClick={() => run("crawl")}
        className="px-3 py-2 rounded border">
        {busy==="crawl" ? "Crawling…" : "Crawl (Firecrawl)"}
      </button>
    </div>
  );
}
