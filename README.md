# Astra AI

Autonomous AI research agent monorepo with a FastAPI backend and React frontend.

## Repository structure
- `/backend` - FastAPI API, research pipeline, models, auth, and tests
- `/frontend` - React + Vite + Tailwind UI
- `/docs` - architecture notes, runbook, and demo script

## MVP capabilities
### Backend API
- `GET /health`
- `POST /api/auth/login`
- `POST /api/research`
- `GET /api/research`
- `GET /api/research/{id}`
- `GET /api/research/{id}/trace`
- `GET /api/research/{id}/metrics`
- `GET /api/research/{id}/agent-metrics`
- `GET /api/research/{id}/compliance`
- `POST /api/research/{id}/pause`
- `POST /api/research/{id}/resume`
- `POST /api/research/{id}/retry`
- `GET /api/research/{id}/export?format=markdown|json`
- `GET /api/research/{id}/replay`
- `GET /api/workspaces/current`
- `GET /api/audit-logs` (admin)
- `GET /api/sources/{research_id}`
- `GET /api/memory/{research_id}`

### Research pipeline
- Planner agent
- Sub-question decomposition + multi-query generation
- Search tool
- Scraping/extraction with `requests` + `BeautifulSoup`
- Validation layer with domain allow/deny filtering + duplicate source detection
- Prompt-injection signal filtering for scraped sources
- PII redaction before persistence and compliance reporting
- Source credibility scoring + contradiction detection
- Structured report synthesis with claim-to-source links
- Report export to Markdown / JSON with confidence + disclaimer sections
- Summarization agent
- Citation generation
- Research stage tracing + metrics
- Replay/debug timeline endpoint with error categories
- Agent-specific execution metrics and attempt tracking
- Workspace-scoped audit logging + daily research quota enforcement
- FAISS memory persistence

### Frontend pages
- Login
- Dashboard
- Research Query
- Research Results
- Source Viewer
- Settings

## Run locally
### Backend
```bash
cd backend
cp .env.example .env
PYENV_VERSION=3.11.14 python -m pip install -e .[dev]
PYENV_VERSION=3.11.14 python -m uvicorn app.main:app --reload
```

> Prefer Python 3.11+ for local development (CI runs on 3.11).

### Backend (without pyenv)
```bash
cd backend
cp .env.example .env
pip install -e .[dev]
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

### Full stack
```bash
docker-compose up --build
```

Once running:
- Frontend: http://localhost:5173
- Backend docs: http://localhost:8000/docs

## 15-minute demo flow
1. Open `http://localhost:5173`.
2. Sign in with any email/password (local demo auth auto-provisions a user).
3. Open **Research Query** and run one of the built-in demo prompts.
4. In **Research Results**, review:
   - Findings with confidence rationale
   - Evidence table filters and contradiction panel
   - Execution timeline (state + latency)
5. Open **Source Viewer** from citations and inspect source metadata.
6. Export Markdown and JSON reports for portfolio walkthrough material.

For a scriptable walkthrough, see `docs/demo-script.md`.
For troubleshooting and operational checks, see `docs/runbook.md`.

## Quality checks
```bash
make lint
make test
make smoke
```

## CI and delivery readiness
- GitHub Actions CI runs backend lint/tests and frontend lint/format/build.
- Docker Compose now includes health checks for postgres/backend and ordered startup.
- Report contract regression test guards structured-report trust fields.
