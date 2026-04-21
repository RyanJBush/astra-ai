# Astra AI

Autonomous AI research agent monorepo with a FastAPI backend and React frontend.

## Repository structure
- `/backend` - FastAPI API, research pipeline, models, auth, and tests
- `/frontend` - React + Vite + Tailwind UI
- `/docs` - architecture notes

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
pip install -e .[dev]
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Full stack
```bash
docker-compose up --build
```

## Quality checks
```bash
make lint
make test
```
