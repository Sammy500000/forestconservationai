PYTHON ?= python

.PHONY: install test lint verify run docker-up docker-down

install:
	$(PYTHON) -m pip install -e ".[dev]"

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check .

verify:
	$(PYTHON) scripts/verify_phase1.py

run:
	$(PYTHON) -m forestwatch

docker-up:
	docker compose up --build

docker-down:
	docker compose down
