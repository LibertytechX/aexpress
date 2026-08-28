.PHONY: help run mms migrations migrate test test-fast test-cov test-unit test-integration test-api test-isolate

help:
	@echo "Available Backend Commands:"
	@echo "  make test             - Run complete backend test suite with coverage (via run_tests.sh)"
	@echo "  make test-fast        - Run backend tests quickly without coverage"
	@echo "  make test-cov         - Run tests with HTML and terminal coverage report"
	@echo "  make test-unit        - Run unit test suite (pure Python / no DB)"
	@echo "  make test-integration - Run integration test suite (requires DB)"
	@echo "  make test-api         - Run DRF API view tests"
	@echo "  make test-isolate     - Run tests inside isolated Docker test container"
	@echo "  make run              - Start Django development server"
	@echo "  make migrations / mms - Create new Django migrations"
	@echo "  make migrate          - Apply Django migrations"

run:
	@python manage.py runserver

mms:
	@python manage.py makemigrations

migrations:
	@python manage.py makemigrations

migrate:
	@python manage.py migrate

test:
	@./run_tests.sh

test-fast:
	@pytest -v

test-cov:
	@pytest --cov=. --cov-report=term-missing --cov-report=html

test-unit:
	@pytest -m unit

test-integration:
	@pytest -m integration

test-api:
	@pytest -m api

test-isolate:
	@./test.sh