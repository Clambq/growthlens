.PHONY: test lint db-up db-down

test:
	python -m pytest

lint:
	python -m ruff check src tests

db-up:
	docker compose up -d --wait postgres

db-down:
	docker compose down
