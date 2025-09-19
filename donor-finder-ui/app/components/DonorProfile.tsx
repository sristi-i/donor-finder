// components/DonorProfile.tsx
import { DonorDetail, Enrichment } from "@/app/lib/types";

function latest<T extends Enrichment>(
  items: T[],
  pred: (e: T) => boolean
): T | undefined {
  return [...items].filter(pred).sort((a,b) =>
    new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  )[0];
}

function ensureHttps(hostOrUrl?: string | null) {
  if (!hostOrUrl) return null;
  const s = hostOrUrl.trim();
  if (s.startsWith("http://") || s.startsWith("https://")) return s;
  return `https://${s}`;
}

export default function DonorProfile({ data }: { data: DonorDetail }) {
  const { donor, grants, contacts, enrichments } = data;

  // Firecrawl structured profile
  const fcProfile = latest(enrichments, e => e.kind === "company_profile" && e.source === "firecrawl");
  const profile = fcProfile?.raw || null;

  // Evidence markdown pages
  const evidence = enrichments
    .filter(e => e.kind === "page_markdown" && e.source === "firecrawl")
    .slice(0, 5);

  const websiteUrl = ensureHttps(donor.website);

  return (
    <div className="space-y-8">
      {/* Header */}
      <section className="rounded-xl border p-6 shadow-sm bg-white">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold">{donor.name}</h1>
            <p className="text-sm text-gray-600">
              {donor.city ? `${donor.city}, ` : ""}{donor.state || ""}
            </p>
            {websiteUrl && (
              <p className="mt-2">
                <a
                  href={websiteUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 underline"
                >
                  {websiteUrl}
                </a>
              </p>
            )}
          </div>
          <div className="text-right text-sm">
            {donor.assets_total != null && (
              <p><span className="font-medium">Assets:</span> ${donor.assets_total.toLocaleString()}</p>
            )}
            {donor.grants_total != null && (
              <p><span className="font-medium">Grants:</span> ${donor.grants_total.toLocaleString()}</p>
            )}
          </div>
        </div>
      </section>

      {/* Firecrawl profile if available */}
      {profile ? (
        <section className="rounded-xl border p-6 shadow-sm bg-white space-y-6">
          <h2 className="text-xl font-semibold">Organization Profile (from website)</h2>

          {profile.about && (
            <div>
              <h3 className="font-medium mb-1">About</h3>
              <p className="text-gray-700 whitespace-pre-wrap">{profile.about}</p>
            </div>
          )}

          {profile.mission && (
            <div>
              <h3 className="font-medium mb-1">Mission</h3>
              <p className="text-gray-700">{profile.mission}</p>
            </div>
          )}

          {Array.isArray(profile.program_areas) && profile.program_areas.length > 0 && (
            <div>
              <h3 className="font-medium mb-1">Program Areas</h3>
              <ul className="list-disc pl-6 text-gray-700">
                {profile.program_areas.slice(0,8).map((p: string, i: number) => (
                  <li key={i}>{p}</li>
                ))}
              </ul>
            </div>
          )}

          {profile.grantmaking && (
            <div>
              <h3 className="font-medium mb-1">Grantmaking Focus</h3>
              <p className="text-gray-700 whitespace-pre-wrap">{profile.grantmaking}</p>
            </div>
          )}

          {profile.apply_instructions && (
            <div>
              <h3 className="font-medium mb-1">How to Apply</h3>
              <p className="text-gray-700 whitespace-pre-wrap">{profile.apply_instructions}</p>
            </div>
          )}

          {(profile.contacts?.emails?.length || profile.contacts?.phones?.length || profile.contacts?.address) && (
            <div className="grid md:grid-cols-3 gap-4">
              <div>
                <h3 className="font-medium mb-1">Emails</h3>
                <ul className="text-gray-700 space-y-1">
                  {(profile.contacts.emails || []).map((e: string, i: number) => (
                    <li key={i}><a href={`mailto:${e}`} className="text-blue-600 underline">{e}</a></li>
                  ))}
                </ul>
              </div>
              <div>
                <h3 className="font-medium mb-1">Phones</h3>
                <ul className="text-gray-700 space-y-1">
                  {(profile.contacts.phones || []).map((p: string, i: number) => <li key={i}>{p}</li>)}
                </ul>
              </div>
              <div>
                <h3 className="font-medium mb-1">Address</h3>
                <p className="text-gray-700 whitespace-pre-wrap">{profile.contacts.address}</p>
              </div>
            </div>
          )}

          {Array.isArray(profile.leadership) && profile.leadership.length > 0 && (
            <div>
              <h3 className="font-medium mb-2">Leadership</h3>
              <ul className="divide-y rounded-md border">
                {profile.leadership.slice(0,10).map((p: any, i: number) => (
                  <li key={i} className="p-3 text-gray-800">
                    <span className="font-medium">{p.name}</span>
                    {p.title ? <span className="text-gray-600"> — {p.title}</span> : null}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {evidence.length > 0 && (
            <div>
              <h3 className="font-medium mb-1">Evidence (pages we parsed)</h3>
              <ul className="list-disc pl-6">
                {evidence.map(e => (
                  <li key={e.id}>
                    <a href={e.url || "#"} target="_blank" rel="noopener noreferrer" className="text-blue-600 underline">
                      {e.url}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <p className="text-xs text-gray-500">
            Source: Firecrawl • Saved {new Date(fcProfile!.created_at).toLocaleString()}
          </p>
        </section>
      ) : (
        <section className="rounded-xl border p-6 shadow-sm bg-white">
          <h2 className="text-lg font-semibold mb-1">Organization Profile</h2>
          <p className="text-gray-600">
            No website profile captured yet. Visit the donor’s website above, or run the crawl endpoint:
            <code className="ml-1 bg-gray-100 px-1 py-0.5 rounded">POST /donors/{donor.id}/crawl</code>
          </p>
        </section>
      )}

      {/* Basic data (mission, contacts, grants) */}
      <section className="rounded-xl border p-6 shadow-sm bg-white space-y-4">
        <h2 className="text-xl font-semibold">Additional Details</h2>

        {donor.mission && (
          <div>
            <h3 className="font-medium mb-1">IRS/NTEE Mission Code</h3>
            <p className="text-gray-700">{donor.mission}</p>
          </div>
        )}

        {contacts.length > 0 && (
          <div>
            <h3 className="font-medium mb-2">Contacts (from enrichments)</h3>
            <ul className="divide-y rounded-md border">
              {contacts.map(c => (
                <li key={c.id} className="p-3">
                  <div className="font-medium">{c.name}</div>
                  <div className="text-sm text-gray-600">{c.title}</div>
                </li>
              ))}
            </ul>
          </div>
        )}

        {grants.length > 0 && (
          <div>
            <h3 className="font-medium mb-2">Recent Grants (sample)</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="text-left text-gray-600">
                    <th className="py-2 pr-4">Year</th>
                    <th className="py-2 pr-4">Recipient</th>
                    <th className="py-2 pr-4">Amount</th>
                    <th className="py-2">Purpose</th>
                  </tr>
                </thead>
                <tbody>
                  {grants.map(g => (
                    <tr key={g.id} className="border-t">
                      <td className="py-2 pr-4">{g.year ?? "-"}</td>
                      <td className="py-2 pr-4">{g.recipient ?? "-"}</td>
                      <td className="py-2 pr-4">{g.amount != null ? `$${g.amount.toLocaleString()}` : "-"}</td>
                      <td className="py-2">{g.purpose ?? "-"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
