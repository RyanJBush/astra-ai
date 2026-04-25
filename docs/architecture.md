# Astra AI MVP Architecture

- **Backend**: FastAPI service with JWT auth, RBAC-ready role field, SQLAlchemy models, and research pipeline.
- **AI flow**: planner -> search -> scrape -> validate -> summarize -> citations -> FAISS memory writes.
- **Frontend**: React + Vite + Tailwind pages for login, dashboard, query, results, source viewer, and settings.
- **Infra**: Dockerized backend/frontend with PostgreSQL in docker-compose and CI in GitHub Actions.

## Trust and report model
- Structured report includes:
  - `schema_version`
  - `provenance` (`generated_at`, `pipeline_version`, query metadata)
  - `findings`, `claims`, and `claim_evidence_links`
  - `evidence_coverage` with sufficiency threshold fields
  - contradiction entries with severity
- Confidence scoring is componentized:
  - base source credibility
  - corroboration bonus
  - recency bonus
  - contradiction penalty

## Demo-readiness notes
- Frontend surfaces confidence rationale, contradiction severity, and execution timeline latency.
- Source viewer exposes author/published/retrieved metadata for explainability.
- See `docs/runbook.md` for operator checks and `docs/demo-script.md` for live walkthrough.
