.PHONY: test lint db-up db-down load-olist load-hillstrom

test:
	python -m pytest

lint:
	python -m ruff check src tests

db-up:
	docker compose up -d --wait postgres

db-down:
	docker compose down

load-olist:
	python scripts/load_raw.py olist

load-hillstrom:
	python scripts/load_raw.py hillstrom
