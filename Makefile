.PHONY: help test lint format type-check check install-dev clean

# Default target
help:
	@echo "Available commands:"
	@echo "  test         - Run pytest tests"
	@echo "  lint         - Run ruff linter"
	@echo "  type-check   - Run mypy type checking"
	@echo "  check        - Run all checks (lint, type-check, test)"

# Install development dependencies
install-dev:
	pip install pytest pytest-django ruff mypy

# Run pytest tests
test:
	pytest .

# Run ruff linter
lint:
	ruff check .

# Run mypy type checking
type-check:
	mypy .

# Run all quality checks
check: lint type-check test
