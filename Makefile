.PHONY: setup dev-backend dev-frontend build test benchmarks-validate benchmarks-build benchmarks-check benchmarks-report benchmarks-fetch-boards

setup:
	pip install -r backend/requirements.txt
	cd frontend && npm install

dev-backend:
	cd backend && uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

build:
	cd frontend && npm run build

test:
	cd backend && python -m pytest tests/ -q

benchmarks-validate:
	cd backend && python -m pipeline.benchmarks validate

benchmarks-build:
	cd backend && python -m pipeline.benchmarks build

benchmarks-check:
	cd backend && python -m pipeline.benchmarks check-sources

benchmarks-report:
	cd backend && python -m pipeline.benchmarks report

benchmarks-fetch-boards:
	cd backend && python -m pipeline.boards
