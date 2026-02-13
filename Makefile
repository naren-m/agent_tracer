.PHONY: help clean setup install install-dev test lint format all venv check-venv

# Python command (use python3 on macOS)
PYTHON := python3
PIP := pip3

# Virtual environment directory
VENV := venv
VENV_BIN := $(VENV)/bin
VENV_PYTHON := $(VENV_BIN)/python
VENV_PIP := $(VENV_BIN)/pip

# Default target
help:
	@echo "Available targets:"
	@echo "  make venv        - Create virtual environment"
	@echo "  make setup       - Set up virtual environment and install dependencies"
	@echo "  make install     - Install package in editable mode (requires active venv)"
	@echo "  make install-dev - Install package with dev dependencies (requires active venv)"
	@echo "  make clean       - Remove build artifacts and cache files"
	@echo "  make clean-all   - Remove build artifacts AND virtual environment"
	@echo "  make test        - Run tests"
	@echo "  make lint        - Run code quality checks (if ruff/pylint installed)"
	@echo "  make format      - Format code (if black/ruff installed)"
	@echo "  make all         - Clean, setup, and install"
	@echo ""
	@echo "Quick start:"
	@echo "  1. make setup    - Creates venv and installs everything"
	@echo "  2. source venv/bin/activate - Activate the virtual environment"
	@echo "  3. make test     - Run tests"

# Check if we're in a virtual environment
check-venv:
	@if [ -z "$$VIRTUAL_ENV" ] && [ ! -f "$(VENV_PYTHON)" ]; then \
		echo "⚠️  No virtual environment detected!"; \
		echo "Run 'make venv' to create one, then 'source venv/bin/activate'"; \
		echo "Or run 'make setup' to create venv and install automatically"; \
		exit 1; \
	fi

# Clean build artifacts, cache files, and temporary files
clean:
	@echo "Cleaning build artifacts and cache files..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete
	find . -type f -name '*.pyo' -delete
	find . -type f -name '*.egg' -delete
	@echo "✅ Clean complete!"

# Clean everything including virtual environment
clean-all: clean
	@echo "Removing virtual environment..."
	rm -rf $(VENV)
	@echo "✅ All clean!"

# Create virtual environment
venv:
	@if [ -d "$(VENV)" ]; then \
		echo "Virtual environment already exists at $(VENV)"; \
	else \
		echo "Creating virtual environment at $(VENV)..."; \
		$(PYTHON) -m venv $(VENV); \
		echo "✅ Virtual environment created!"; \
		echo "Activate with: source $(VENV_BIN)/activate"; \
	fi

# Install dependencies from requirements.txt (in venv)
install-deps:
	@if [ -f "$(VENV_PIP)" ]; then \
		echo "Installing dependencies in virtual environment..."; \
		$(VENV_PIP) install --upgrade pip; \
		$(VENV_PIP) install -r requirements.txt; \
	elif [ -n "$$VIRTUAL_ENV" ]; then \
		echo "Installing dependencies in active virtual environment..."; \
		$(PIP) install --upgrade pip; \
		$(PIP) install -r requirements.txt; \
	else \
		echo "❌ No virtual environment found. Run 'make venv' first."; \
		exit 1; \
	fi

# Install package in editable mode (development mode)
install:
	@if [ -f "$(VENV_PIP)" ]; then \
		echo "Installing package in virtual environment (editable mode)..."; \
		$(VENV_PIP) install --upgrade pip; \
		$(VENV_PIP) install -e .; \
	elif [ -n "$$VIRTUAL_ENV" ]; then \
		echo "Installing package in active virtual environment (editable mode)..."; \
		$(PIP) install --upgrade pip; \
		$(PIP) install -e .; \
	else \
		echo "❌ No virtual environment found. Run 'make venv' first."; \
		exit 1; \
	fi

# Install package with development dependencies
install-dev:
	@if [ -f "$(VENV_PIP)" ]; then \
		echo "Installing package with dev dependencies in virtual environment..."; \
		$(VENV_PIP) install --upgrade pip; \
		$(VENV_PIP) install -e ".[dev]"; \
	elif [ -n "$$VIRTUAL_ENV" ]; then \
		echo "Installing package with dev dependencies in active virtual environment..."; \
		$(PIP) install --upgrade pip; \
		$(PIP) install -e ".[dev]"; \
	else \
		echo "❌ No virtual environment found. Run 'make venv' first."; \
		exit 1; \
	fi

# Full setup: create venv, clean, and install
setup: venv clean install-deps install
	@echo ""
	@echo "✅ Setup complete!"
	@echo "To activate the virtual environment, run:"
	@echo "  source $(VENV_BIN)/activate"

# Run tests
test:
	@echo "Running tests..."
	@if [ -f "$(VENV_BIN)/pytest" ]; then \
		$(VENV_BIN)/pytest -v; \
	elif [ -n "$$VIRTUAL_ENV" ]; then \
		pytest -v; \
	else \
		echo "⚠️  No virtual environment active. Run 'source venv/bin/activate' first."; \
		exit 1; \
	fi

# Run linting (requires ruff or pylint)
lint:
	@echo "Running code quality checks..."
	@command -v ruff >/dev/null 2>&1 && ruff check . || echo "ruff not installed, skipping..."
	@command -v pylint >/dev/null 2>&1 && pylint agent_tracer || echo "pylint not installed, skipping..."

# Format code (requires black or ruff)
format:
	@echo "Formatting code..."
	@command -v ruff >/dev/null 2>&1 && ruff format . || echo "ruff not installed, skipping..."
	@command -v black >/dev/null 2>&1 && black . || echo "black not installed, skipping..."

# Complete workflow: clean, setup, and run tests
all: clean setup test
	@echo "All tasks complete!"
