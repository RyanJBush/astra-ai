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
- `GET /api/sources/{research_id}`
- `GET /api/memory/{research_id}`

### Research pipeline
- Planner agent
- Search tool
- Scraping/extraction with `requests` + `BeautifulSoup`
- Validation layer
- Summarization agent
- Citation generation
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
