PYTHON ?= python

.PHONY: install test lint verify build report pipeline db-up db-down load-olist load-hillstrom dbt-build notebooks

install:
	$(PYTHON) -m pip install -e ".[dev,analytics]"

test:
	$(PYTHON) -m pytest -q

lint:
	$(PYTHON) -m ruff check src scripts tests

verify:
	$(PYTHON) scripts/run_pipeline.py verify

build:
	$(PYTHON) scripts/run_pipeline.py build

report:
	$(PYTHON) scripts/run_pipeline.py report

pipeline:
	$(PYTHON) scripts/run_pipeline.py all

db-up:
	docker compose up -d --wait postgres

db-down:
	docker compose down

load-olist:
	$(PYTHON) scripts/load_raw.py olist

load-hillstrom:
	$(PYTHON) scripts/load_raw.py hillstrom

dbt-build:
	$(PYTHON) -m dbt.cli.main build --project-dir dbt --profiles-dir dbt

notebooks:
	$(PYTHON) scripts/execute_notebooks.py
