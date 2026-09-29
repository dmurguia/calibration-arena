.PHONY: setup seed dev-backend dev-frontend build test ratings benchmarks-validate benchmarks-build benchmarks-check benchmarks-report

setup:
	pip install -r backend/requirements.txt
	cd frontend && npm install

seed:
	cd backend && python -m pipeline.seed

dev-backend:
	cd backend && uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

build:
	cd frontend && npm run build

test:
	cd backend && python -m pytest tests/ -q

ratings:
	cd backend && python -m pipeline.compute_ratings

benchmarks-validate:
	cd backend && python -m pipeline.benchmarks validate

benchmarks-build:
	cd backend && python -m pipeline.benchmarks build

benchmarks-check:
	cd backend && python -m pipeline.benchmarks check-sources

benchmarks-report:
	cd backend && python -m pipeline.benchmarks report
