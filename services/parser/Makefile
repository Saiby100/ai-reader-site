VENV := .venv/bin

.PHONY: dev start test install

# Run the parser with auto-reload for local development
dev:
	$(VENV)/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Run the parser without reload (production-style)
start:
	$(VENV)/uvicorn app.main:app --host 0.0.0.0 --port 8000

# Run the test suite
test:
	$(VENV)/pytest

# Create the venv and install the package with dev extras
install:
	python3.11 -m venv .venv
	$(VENV)/pip install -e ".[dev]"
