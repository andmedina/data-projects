PYTHON ?= python3
DSN ?= postgresql://healthcare_app:change-me@localhost:55432/healthcare_clinical_intelligence

.PHONY: help install-dev lint format format-check typecheck test coverage quality integration verify demo

help:
	@echo "Healthcare Clinical Intelligence developer commands"
	@echo "  make install-dev   Install all local development extras"
	@echo "  make quality       Run lint, formatting, typing, tests, and coverage"
	@echo "  make integration   Run the PostgreSQL end-to-end smoke test in a temporary database"
	@echo "  make verify        Run quality and PostgreSQL integration checks"
	@echo "  make demo          Run the dependency-free synthetic file demonstration"

install-dev:
	$(PYTHON) -m pip install -e '.[postgres,test,ml,dev]'

lint:
	$(PYTHON) -m ruff check src tests scripts

format:
	$(PYTHON) -m ruff format src tests scripts

format-check:
	$(PYTHON) -m ruff format --check src tests scripts

typecheck:
	$(PYTHON) -m mypy

test:
	$(PYTHON) -m pytest -q

coverage:
	$(PYTHON) -m pytest --cov --cov-report=term-missing --cov-report=xml -q

quality: lint format-check typecheck coverage

integration:
	$(PYTHON) scripts/run_postgres_smoke.py --dsn '$(DSN)' --ephemeral

verify: quality integration

demo:
	PYTHONPATH=src $(PYTHON) -m healthcare_clinical_intelligence.cli fhir-file data/samples/fhir_bundle.json --output output/demo
