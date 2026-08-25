PY = .venv/bin/python

.DEFAULT_GOAL := run

# Usage: make run ARGS="https://x.com -s 'h1::text' --fetcher http"
run:
	@test -f .env || cp .env.example .env
	source .venv/bin/activate && python main.py $(ARGS)

install:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt

env:
	@test -f .env || cp .env.example .env

clean:
	rm -rf __pycache__ output/*.json

help:
	@echo "make run ARGS=\"<url> [flags]\"   scrape one URL"
	@echo "make install                      create venv + install deps"
	@echo "make env                          create .env from .env.example"
	@echo "make clean                        remove cache/output"
