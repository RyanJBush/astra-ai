# Astra AI MVP Architecture

- **Backend**: FastAPI service with JWT auth, RBAC-ready role field, SQLAlchemy models, and research pipeline.
- **AI flow**: planner -> search -> scrape -> validate -> summarize -> citations -> FAISS memory writes.
- **Frontend**: React + Vite + Tailwind pages for login, dashboard, query, results, source viewer, and settings.
- **Infra**: Dockerized backend/frontend with PostgreSQL in docker-compose and CI in GitHub Actions.
