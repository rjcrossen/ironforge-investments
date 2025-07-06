# Ironforge Investments Root Makefile

.PHONY: help up down logs build clean scheduler-dev scheduler-logs

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

up: ## Start all services with docker-compose
	docker-compose up -d

down: ## Stop all services
	docker-compose down

logs: ## Show logs for all services
	docker-compose logs -f

build: ## Build all Docker images
	docker-compose build

clean: ## Clean up Docker containers, images, and volumes
	docker-compose down -v
	docker system prune -f

scheduler-dev: ## Run scheduler service in development mode
	cd ironforge-scheduler-service && make dev

scheduler-logs: ## Show scheduler service logs
	docker-compose logs -f scheduler

# Database operations
db-up: ## Start only the database
	docker-compose up -d db

db-logs: ## Show database logs
	docker-compose logs -f db

# Development setup
setup: ## Setup development environment
	@echo "Setting up development environment..."
	@echo "1. Copy .env.example to .env and configure your API credentials"
	@echo "2. Run 'make up' to start services"
	@echo "3. Run 'make scheduler-dev' for local development"