.PHONY: setup venv install run clean docker-build docker-run test lint

PYTHON := python3
VENV := .venv
BIN := $(VENV)/bin

setup: venv install

venv:
	$(PYTHON) -m venv $(VENV)

install: venv
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install uv
	$(BIN)/uv pip install -r requirements.txt

env:
	@echo "Run this command in your shell: source $(VENV)/bin/activate"

run: 
	$(BIN)/python3 main.py

serve: venv
	$(BIN)/uvicorn main:app --reload --host 0.0.0.0 --port 8000

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
