# Astra AI Architecture

## Monorepo Layout
- `backend/`: FastAPI API layer, domain services, and persistence models.
- `frontend/`: React app for interacting with research, sources, and memory workflows.
- `docs/`: Architecture and API notes.

## Core Components
- **Research workflow**: intended to run as a LangGraph orchestration service.
- **Source registry**: tracks citations and credibility metadata.
- **Memory subsystem**: PostgreSQL persistence + FAISS vector indexing hook points.

## Infrastructure
- Docker Compose for local orchestration.
- GitHub Actions CI for backend checks and frontend build.
