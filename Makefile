.PHONY: dev prod lint test build clean

dev:
	docker compose -f infra/docker-compose.dev.yml up --build

prod:
	docker compose -f infra/docker-compose.yml up --build

lint:
	cd apps/web && npm run lint
	cd apps/api && python -m flake8 . --max-line-length=100 --exclude=__pycache__,venv

test:
	cd apps/web && npm run test
	cd apps/api && python -m pytest

build:
	docker compose -f infra/docker-compose.yml build

clean:
	docker compose -f infra/docker-compose.yml down -v
	docker compose -f infra/docker-compose.dev.yml down -v
	rm -rf apps/web/.next
	rm -rf apps/api/__pycache__
	rm -rf apps/api/artifacts/*
