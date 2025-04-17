.PHONY: setup venv install run clean docker-build docker-run test lint export-requirements

PYTHON := python3
VENV := .venv
BIN := $(VENV)/bin

setup: venv install

venv:
	$(PYTHON) -m venv $(VENV)

# Export requirements.txt from Poetry
export-requirements:
	poetry export --without-hashes --format=requirements.txt --output=requirements.txt 

install: venv export-requirements
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install uv
	$(BIN)/uv pip install -r requirements.txt

env:
	@echo "Run this command in your shell: source $(VENV)/bin/activate"

serve: venv
	$(BIN)/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

clean:
	rm -rf $(VENV)
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

docker-build:
	docker build -t magic-mirror:latest .

docker-run:
	docker run -p 8000:8000 --name magic-mirror --rm magic-mirror:latest

dev-up:
	docker-compose up -d

dev-down:
	docker-compose down

test: venv
	$(BIN)/pytest

lint: venv
	$(BIN)/flake8 .
