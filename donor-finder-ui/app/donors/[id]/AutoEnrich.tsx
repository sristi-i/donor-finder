"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { autoEnrichIfNeeded } from "@/lib/api";

export default function AutoEnrich({ id, enrichmentCount }: { id: number; enrichmentCount: number }) {
  const router = useRouter();
  useEffect(() => {
    let done = false;
    (async () => {
      if (enrichmentCount === 0) {
        await autoEnrichIfNeeded(id, enrichmentCount);
        done = true;
        router.refresh(); // fetch latest details
      }
    })();
    return () => { done = true; };
  }, [id, enrichmentCount, router]);
  return null;
}
