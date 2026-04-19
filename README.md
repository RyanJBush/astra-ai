# Astra AI Monorepo Scaffold

Production-style starter scaffold for an autonomous research agent.

## Stack
- FastAPI backend
- React frontend (Vite)
- PostgreSQL
- LangChain / LangGraph integration seams
- FAISS dependency and memory integration hooks
- Docker Compose + GitHub Actions CI

## Repository Layout
```
backend/        # FastAPI app (agents/tools/validators/routers/services/models)
frontend/       # React UI (layout + pages)
docs/           # Architecture/API docs
.github/        # CI workflow
```

## Implemented Research Pipeline
1. Query submission via `POST /api/v1/research`
2. Planner agent generates search facets
3. Web search tool gathers candidate sources
4. Scraper extracts page content
5. Validation layer scores credibility and relevance
6. Summarizer agent synthesizes cited output
7. Citation linker maps ranked sources to `[n]` references

## API Endpoints
- `GET /health`
- `POST /api/v1/research`
- `GET /api/v1/research`
- `GET /api/v1/research/{run_id}`
- `GET /api/v1/sources`
- `POST /api/v1/memory`
- `GET /api/v1/memory`

## Local Development
### 1) Install dependencies
```bash
make install-backend
make install-frontend
```

### 2) Run services locally
```bash
make dev-backend
make dev-frontend
```

### 3) Run with Docker
```bash
make up
```

### 4) Run CI-equivalent checks
```bash
make ci
```

## Testing
```bash
cd backend && python -m pytest
```

## Next Build Steps
- Integrate LangGraph stateful planning/execution graph and LLM summarization calls.
- Add vector embeddings and FAISS-backed memory retrieval flow.
- Introduce Alembic migrations and repository interfaces for all entities.
- Build frontend result visualization with inline citation drill-down.
