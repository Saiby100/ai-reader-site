VENV := .venv/bin

.PHONY: install dev start test debug clean

# Create the venv and install the package with dev extras
install:
	python3.11 -m venv .venv
	$(VENV)/pip install -e ".[dev]"

# Run the parser service with auto-reload for local development
dev:
	$(VENV)/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Run the parser service without reload (production-style)
start:
	$(VENV)/uvicorn app.main:app --host 0.0.0.0 --port 8000

# Run the test suite
test:
	$(VENV)/pytest

# Parse FILE and write out/<name>.json plus out/<name>.html, so the structured tree
# and the way it renders in a browser can be checked side by side.
# Usage: make debug FILE=path/to/document.pdf
debug:
	@test -n "$(FILE)" || { echo "FILE is required, e.g. make debug FILE=path/to/doc.pdf"; exit 1; }
	$(VENV)/python scripts/parse_file.py "$(FILE)"

# Drop the debug output
clean:
	rm -rf out
