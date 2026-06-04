.PHONY: run mms migrate test

run:
	@python manage.py runserver

mms:
	@python manage.py makemigrations

migrate:
	@python manage.py migrate

test:
	@.venv/bin/pytest || pytest