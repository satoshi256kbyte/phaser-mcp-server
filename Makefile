# Phaser MCP Server Makefile

.PHONY: help install install-dev test test-cov lint format format-md check clean build docker-build docker-run health-check

# Default target
help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Installation
install: ## Install the package
	uv sync

install-dev: ## Install with development dependencies
	uv sync --dev
	uv run pre-commit install

# Testing
test: ## Run tests
	uv run pytest

test-cov: ## Run tests with coverage report
	uv run pytest --cov=phaser_mcp_server --cov-report=html --cov-report=term-missing

test-live: ## Run tests including live tests (requires internet)
	uv run pytest -m live

# Code quality
lint: ## Run linting checks
	uv run ruff check
	uv run pyright

format: ## Format Python code
	uv run ruff format
	uv run ruff check --fix

format-md: ## Format Markdown files
	uv run mdformat README.md docs/ --wrap 88

format-md-check: ## Check Markdown formatting without making changes
	uv run mdformat --check README.md docs/ --wrap 88

format-md-diff: ## Show what changes mdformat would make
	uv run mdformat --diff README.md docs/ --wrap 88

format-all: format format-md ## Format all code and documentation

check: ## Run all quality checks
	uv run ruff check
	uv run pyright
	uv run pytest --tb=short

pre-commit: ## Run pre-commit hooks on all files
	uv run pre-commit run --all-files

# Build and package
clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean ## Build the package
	uv build

# Docker
docker-build: ## Build Docker image
	docker build -t phaser-mcp-server:latest .

docker-run: ## Run Docker container
	docker run --rm -it -e FASTMCP_LOG_LEVEL=DEBUG phaser-mcp-server:latest

docker-compose-up: ## Start with docker-compose
	docker-compose up -d

docker-compose-down: ## Stop docker-compose services
	docker-compose down

# Health and info
health-check: ## Run health check
	uv run phaser-mcp-server --health-check

info: ## Show server info
	uv run phaser-mcp-server --info

version: ## Show version
	uv run phaser-mcp-server --version

# Development
dev-server: ## Run server in development mode
	FASTMCP_LOG_LEVEL=DEBUG uv run phaser-mcp-server

dev-install: install-dev ## Alias for install-dev

# CI/CD helpers
ci-test: ## Run tests for CI
	uv run pytest --cov=phaser_mcp_server --cov-report=xml --cov-fail-under=90

ci-lint: ## Run linting for CI
	uv run ruff check --output-format=github
	uv run pyright --outputjson

ci-format-check: ## Check if code is properly formatted (for CI)
	uv run ruff format --check
	uv run mdformat --check README.md docs/

# Documentation
docs-format: format-md ## Format documentation files

docs-check: ## Check documentation formatting
	uv run mdformat --check README.md docs/
