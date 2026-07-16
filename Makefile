.PHONY: install dev test lint seed benchmark docker-up docker-down
install:
	pip install -r apps/api/requirements.txt
	cd apps/web && npm install

dev:
	uvicorn apps.api.app.main:app --reload --port 8000

test:
	pytest -q
	cd apps/web && npm test -- --run

lint:
	ruff check apps packages scripts tests
	cd apps/web && npm run lint

seed:
	python scripts/seed_demo.py

benchmark:
	python benchmarks/run_benchmark.py

docker-up:
	docker compose up --build

docker-down:
	docker compose down
