// app/lib/types.ts

// Basic donor row returned by /donors
export type Donor = {
  id: number;
  ein?: string | null;
  name: string;
  state?: string | null;
  city?: string | null;
  mission?: string | null;
  ntee_code?: string | null;
  assets_total?: number | null;
  grants_total?: number | null;
  irs_subsection?: number | null;
  website?: string | null;
  source?: any; // raw JSON from ProPublica seed
  updated_at?: string;
  created_at?: string;
};

// Individual grant (if you end up showing them)
export type Grant = {
  id?: number;
  donor_id?: number;
  year?: number | null;
  amount?: number | null;
  recipient_name?: string | null;
  recipient_ein?: string | null;
};

// Contact captured from Apollo/Firecrawl
export type Contact = {
  id?: number;
  donor_id?: number;
  name?: string | null;
  title?: string | null;
  email?: string | null;
  linkedin_url?: string | null;
  source?: string | null; // "apollo" | "firecrawl"
  created_at?: string;
};

// Enrichment rows (evidence + structured info)
export type Enrichment = {
  id: number;
  donor_id: number;
  kind: string;          // "company_profile" | "page_markdown" | "website_source" | "site_extract" ...
  source: string;        // "propublica" | "apollo" | "firecrawl" | "scraper"
  url?: string | null;   // source/evidence URL(s)
  raw?: any;             // JSON payload (structured profile or markdown snapshot)
  created_at?: string;
};

// Full detail payload from GET /donors/:id
export type DonorDetail = {
  donor: Donor;
  grants: Grant[];
  contacts: Contact[];
  enrichments: Enrichment[];
};

// List response from GET /donors
export type DonorListResponse = {
  items: Donor[];
  total: number;
};

// Semantic search response from POST /donors/search/semantic
export type SemanticSearchResponse = {
  items: (Donor & { distance?: number; doc?: string })[];
  count: number;
};
