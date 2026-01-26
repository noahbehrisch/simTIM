# Makefile for simTIM

# Use bash for shell commands (required for 'source' command)
SHELL := /bin/bash

.PHONY: help install install-dev test test-cov lint format security clean build docker run profile docs

# Default Python version
PYTHON ?= python3
VENV := venv
ACTIVATE := source $(VENV)/bin/activate

help:  ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ==================== Installation ====================

install:  ## Install production dependencies
	$(PYTHON) -m venv $(VENV)
	$(ACTIVATE) && pip install --upgrade pip
	$(ACTIVATE) && pip install -r requirements.txt

install-dev:  ## Install development dependencies
	$(PYTHON) -m venv $(VENV)
	$(ACTIVATE) && pip install --upgrade pip
	$(ACTIVATE) && pip install -r requirements-dev.txt
	$(ACTIVATE) && pre-commit install

# ==================== Testing ====================

test:  ## Run tests
	$(ACTIVATE) && python -m pytest tests/ -v

test-cov:  ## Run tests with coverage report
	$(ACTIVATE) && python -m pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html

# ==================== Code Quality ====================

lint:  ## Run linting checks
	$(ACTIVATE) && ruff check src/ tests/
	$(ACTIVATE) && mypy src/ --ignore-missing-imports

format:  ## Format code with ruff
	$(ACTIVATE) && ruff format src/ tests/
	$(ACTIVATE) && ruff check --fix src/ tests/

type-check:  ## Run type checking with mypy
	$(ACTIVATE) && mypy src/ --ignore-missing-imports

# ==================== Security ====================

security:  ## Run security scans
	$(ACTIVATE) && pip-audit
	$(ACTIVATE) && bandit -r src/ -ll -f json -o reports/bandit-report.json

# ==================== Build & Docker ====================

build:  ## Build Python package
	$(ACTIVATE) && python -m build

docker:  ## Build Docker image
	docker build -t simtim:latest .

docker-dev:  ## Build Docker development image
	docker build --target development -t simtim:dev .

docker-run:  ## Run Docker container (headless)
	docker run --rm simtim:latest python main.py --demo

# ==================== Application ====================

run:  ## Run the GUI application
	$(ACTIVATE) && python main.py

demo:  ## Run demo simulation
	$(ACTIVATE) && python main.py --demo

# ==================== Profiling ====================

profile:  ## Run profiling on simulation
	$(ACTIVATE) && python profile/profile_simulation.py

profile-view:  ## Visualize profiling results with snakeviz
	$(ACTIVATE) && snakeviz profile/simulation_profile.prof

# ==================== Cleanup ====================

clean:  ## Clean build artifacts and caches
	rm -rf build/ dist/ *.egg-info/
	rm -rf .pytest_cache/ .mypy_cache/ .ruff_cache/
	rm -rf htmlcov/ coverage.xml .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

clean-all: clean  ## Clean everything including venv
	rm -rf $(VENV)/

# ==================== Release ====================

version:  ## Show current version
	@grep "^version" pyproject.toml | head -1

release-check:  ## Pre-release checks
	$(ACTIVATE) && ruff check src/ tests/
	$(ACTIVATE) && python -m pytest tests/ -v --cov=src --cov-fail-under=40
	$(ACTIVATE) && pip-audit
	@echo "✅ All pre-release checks passed"
