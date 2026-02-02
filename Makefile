.PHONY: help setup dev build test clean migrate

help:
	@echo "UAI Engine - Makefile Commands"
	@echo ""
	@echo "  make setup     - Initial setup (install deps, start infra, run migrations)"
	@echo "  make dev        - Start all services in development mode"
	@echo "  make build      - Build all services"
	@echo "  make test       - Run all tests"
	@echo "  make clean      - Clean build artifacts"
	@echo "  make migrate    - Run database migrations"
	@echo "  make up         - Start Docker Compose services"
	@echo "  make down       - Stop Docker Compose services"
	@echo "  make logs       - View Docker Compose logs"

setup:
	@./scripts/setup.sh

dev:
	@./scripts/dev.sh

build:
	@pnpm build

test:
	@pnpm test

clean:
	@pnpm clean

migrate:
	@cd apps/api && alembic upgrade head

up:
	@cd infra && docker-compose up -d

down:
	@cd infra && docker-compose down

logs:
	@cd infra && docker-compose logs -f
