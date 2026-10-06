PYTHON ?= python

.PHONY: install test lint verify verify-phase1 verify-phase2 verify-phase3 verify-phase4 run docker-up docker-down

install:
	$(PYTHON) -m pip install -e ".[dev]"

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check .

verify:
	$(PYTHON) scripts/verify_phase1.py
	$(PYTHON) scripts/verify_phase2.py
	$(PYTHON) scripts/verify_phase3.py
	$(PYTHON) scripts/verify_phase4.py

verify-phase1:
	$(PYTHON) scripts/verify_phase1.py

verify-phase2:
	$(PYTHON) scripts/verify_phase2.py

verify-phase3:
	$(PYTHON) scripts/verify_phase3.py

verify-phase4:
	$(PYTHON) scripts/verify_phase4.py

run:
	$(PYTHON) -m forestwatch

docker-up:
	docker compose up --build

docker-down:
	docker compose down
