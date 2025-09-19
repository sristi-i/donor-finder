# 4) `NEXT_STEPS.md`

```markdown
# Next steps (if I had more time)

1) **Background jobs**
   - Move enrichment/crawl to a queue (Celery/RQ) to keep the UI instant.
   - Retry with exponential backoff; dedupe per-domain.

2) **Deeper data model**
   - Normalize “program areas” and “geographies”.
   - Track grant rounds, deadlines, eligibility.
   - Track historical filings & year-over-year assets/grants.

3) **Better extraction**
   - A second pass LLM prompt to produce consistent, compact profiles.
   - Use site maps + robots-aware crawling; fall back to page ranking by heuristics.

4) **User accounts**
   - Saved searches, notes, star/follow donors, CSV export.
   - Org-level sharing & permissioning.

5) **Integrations**
   - Airtable/Sheets export.
   - CRM sync (HubSpot/Salesforce) for contacts.

6) **Production hardening**
   - Helm chart and managed Postgres (pgvector).
   - Observability: request logs, job metrics, extract success rate.

7) **Quality loop**
   - Relevance feedback for semantic search (RRF or small reranker).
   - Active learning to improve extraction fields over time.
