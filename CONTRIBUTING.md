# Contributing

## Local setup
- Backend: `cd backend && pip install -e .[dev]`
- Frontend: `cd frontend && npm install`
- Full stack: `docker-compose up --build`

## Quality checks
- Backend lint: `cd backend && ruff check app tests`
- Backend tests: `cd backend && pytest`
- Frontend lint: `cd frontend && npm run lint`
- Frontend format check: `cd frontend && npm run format:check`
