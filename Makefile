.PHONY: help test test-backend test-fast test-cov migrations migrate

help:
	@echo "Available Project Commands:"
	@echo ""
	@echo "  Testing:"
	@echo "  make test           - Run full test suite with coverage"
	@echo "  make test-backend   - Run backend test suite (via backend/run_tests.sh)"
	@echo "  make test-fast      - Run backend tests quickly without coverage"
	@echo "  make test-cov       - Run backend tests with coverage report"
	@echo ""
	@echo "  Database & Migrations:"
	@echo "  make migrations     - Create new Django database migrations"
	@echo "  make migrate        - Apply pending Django database migrations"
	@echo ""

test: test-backend

test-backend:
	@cd backend && ./run_tests.sh

test-fast:
	@cd backend && .venv/bin/pytest -v

test-cov:
	@cd backend && .venv/bin/pytest --cov=. --cov-report=term-missing --cov-report=html

migrations:
	@cd backend && .venv/bin/python manage.py makemigrations

migrate:
	@cd backend && .venv/bin/python manage.py migrate

