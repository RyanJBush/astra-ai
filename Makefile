.PHONY: install-backend install-frontend dev-backend dev-frontend up down ci

install-backend:
	cd backend && pip install -r requirements.txt

install-frontend:
	cd frontend && npm install

dev-backend:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	cd frontend && npm run dev

up:
	docker compose up --build

down:
	docker compose down -v

ci:
	cd backend && python -m compileall app
	cd frontend && npm run build
