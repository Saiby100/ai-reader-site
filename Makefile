PARSER_DIR := services/parser

.PHONY: debug parse render

# Parse FILE through the parser package -> services/parser/.parse-out/<name>.json
# Usage: make parse FILE=path/to/document.pdf
parse:
	@test -n "$(FILE)" || { echo "FILE is required, e.g. make parse FILE=path/to/doc.pdf"; exit 1; }
	cd $(PARSER_DIR) && .venv/bin/python scripts/parse_file.py "$(abspath $(FILE))"

# Render an already-parsed tree to the client's HTML -> services/parser/.parse-out/<name>.html
# NAME is the filename stem of a .json already in .parse-out/ (e.g. NAME=document).
# Usage: make render NAME=document
render:
	@test -n "$(NAME)" || { echo "NAME is required, e.g. make render NAME=document"; exit 1; }
	npx tsx scripts/render-tree.tsx "$(NAME)"

# Run both for the same FILE: parse, then render the same tree, so the JSON and HTML
# can be compared side by side.
# Usage: make debug FILE=path/to/document.pdf
debug:
	@test -n "$(FILE)" || { echo "FILE is required, e.g. make debug FILE=path/to/doc.pdf"; exit 1; }
	$(MAKE) parse FILE="$(FILE)"
	$(MAKE) render NAME="$(basename $(notdir $(FILE)))"
