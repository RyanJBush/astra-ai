# Astra AI Runbook

## Goal
Provide a reliable operator checklist for local demos and portfolio presentations.

## Preconditions
- Python 3.11+
- Node 22+
- Docker + Docker Compose (optional but recommended for full-stack startup)

## Local startup options

### Option A: Docker Compose (recommended)
```bash
docker-compose up --build
```

Health checks gate service startup:
- `postgres` must be healthy before backend starts.
- `backend` must respond on `/health` before frontend starts.

### Option B: Manual dev startup
Backend:
```bash
cd backend
cp .env.example .env
pip install -e .[dev]
uvicorn app.main:app --reload
```

Frontend:
```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

## Verification checklist
1. `GET /health` returns `{"status":"ok"}`.
2. UI loads at `http://localhost:5173`.
3. Login succeeds with demo credentials (any email/password in local mode).
4. Query run creates a results page with:
   - findings
   - evidence table
   - contradictions panel
   - timeline events
5. Source viewer shows source metadata and content.
6. Markdown/JSON export downloads succeed.

## Quality gates before demo
```bash
make smoke
```

This runs:
- backend lint (`ruff`)
- backend tests (`pytest -q`)
- frontend lint + format check + build

## Common issues
- **Backend import errors**: ensure install was done from `backend` with `pip install -e .[dev]`.
- **Auth failures**: clear browser local storage key `astra_token` and re-login.
- **No results on query**: check outbound network connectivity for search/scrape steps.
- **Frontend API mismatch**: confirm `VITE_API_BASE` points to backend URL.

## Demo stability tips
- Use one of the built-in demo prompts to reduce prep time.
- Keep a pre-run session in Dashboard for fast fallback during live demos.
- Export one Markdown and one JSON report ahead of time as backup artifacts.
