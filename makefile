# Ironforge Scheduler Service Makefile

.PHONY: help install dev test lint format type-check clean build run docker-build docker-run

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies using uv
	uv sync

dev: ## Run the scheduler service in development mode
	uv run python src/main.py

test: ## Run tests
	uv run pytest

lint: ## Run linting with ruff
	uv run ruff check src/

format: ## Format code with ruff
	uv run ruff format src/

type-check: ## Run type checking with pyright
	uv run pyright src/

clean: ## Clean up cache and temporary files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +

build: ## Build the Docker image
	docker build -t ironforge-scheduler-service .

run: ## Run the service locally
	uv run python src/main.py

docker-build: ## Build Docker image
	docker build -t ironforge-scheduler-service .

docker-run: ## Run Docker container
	docker run --rm -it \
		--env-file .env \
		--network host \
		ironforge-scheduler-service

# Quality checks
check: lint type-check ## Run all quality checks

# Development workflow
setup: install ## Setup development environment
	@echo "Development environment setup complete!"

# Integration test with database
test-integration: ## Run integration tests (requires database)
	uv run python test_integration.py
