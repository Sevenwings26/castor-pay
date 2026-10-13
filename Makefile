.PHONY: help up down restart logs backend-shell worker-logs test test-unit test-integration test-chaos migrate seed clean

help:
	@echo "CastorPay Development Automation"
	@echo "---------------------------------"
	@echo "make up               - Start all containers in background"
	@echo "make down             - Stop all containers"
	@echo "make restart          - Restart all containers"
	@echo "make logs             - View live logs across all containers"
	@echo "make backend-shell    - Open interactive bash shell in backend container"
	@echo "make test             - Run entire backend test suite"
	@echo "make test-unit        - Run unit tests (ledger math, idempotency, quotes)"
	@echo "make test-integration - Run integration tests (payment, virtual accounts, recon)"
	@echo "make test-chaos       - Run chaos & DLQ failure tests"
	@echo "make migrate          - Run Alembic database migrations"
	@echo "make seed             - Seed database with demo accounts, merchants & rates"
	@echo "make clean            - Remove dangling containers and cache"

up:
	docker compose up -d --build

down:
	docker compose down

restart:
	docker compose restart

logs:
	docker compose logs -f

backend-shell:
	docker compose exec backend bash

test:
	docker compose exec backend pytest -v

test-unit:
	docker compose exec backend pytest tests/unit -v

test-integration:
	docker compose exec backend pytest tests/integration -v

test-chaos:
	docker compose exec backend pytest tests/chaos -v

migrate:
	docker compose exec backend alembic upgrade head

clean:
	docker compose down -v
	find . -type d -name "__pycache__" -exec rm -rf {} +
