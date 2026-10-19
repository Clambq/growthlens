.PHONY: test lint db-up db-down load-olist load-hillstrom dbt-build

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

dbt-build:
	python -m dbt.cli.main build --project-dir dbt --profiles-dir dbt --target $(DBT_TARGET)
