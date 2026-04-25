.PHONY: backend-install frontend-install lint test smoke

backend-install:
	cd backend && pip install -e .[dev]

frontend-install:
	cd frontend && npm install

lint:
	cd backend && ruff check app tests
	cd frontend && npm run lint
	cd frontend && npm run format:check

test:
	cd backend && pytest
	cd frontend && npm run build

smoke:
	cd backend && ruff check app tests
	cd backend && pytest -q
	cd frontend && npm run lint
	cd frontend && npm run format:check
	cd frontend && npm run build
