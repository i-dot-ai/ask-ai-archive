lint:
	ruff .


.PHONY: reset-db
reset-db:
	docker-compose down db --volumes
	docker-compose up -d db

.PHONY: check-python-code
check-python-code:
	poetry run ruff .
	poetry run bandit -ll -r ./ask_ai
	poetry run mypy ./ask_ai --ignore-missing-imports

.PHONY: check-migrations
check-migrations:
	docker-compose build web
	docker-compose run --env ENVIRONMENT="TEST" web poetry run python manage.py migrate
	docker-compose run --env ENVIRONMENT="TEST" web poetry run python manage.py makemigrations --check

.PHONY: test
test:
	docker-compose up -d db
	docker-compose run --env ENVIRONMENT="TEST" web poetry run pytest tests -v --cov=ask_ai --cov-fail-under 92
