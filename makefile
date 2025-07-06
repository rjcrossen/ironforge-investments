dev:
	uv run uvicorn ironforge.api.app:app --reload --host 0.0.0.0 --port 8000

test:
	uv run pytest

test-coverage:
	uv run pytest --cov=ironforge --cov-report=html

lint:
	uv run ruff check .

format:
	uv run ruff format .

install:
	uv sync

# Docker commands
docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-reset:
	docker-compose down -v && docker-compose up -d

# Database commands
db-connect:
	docker exec -it db psql -U postgres -d DB

db-logs:
	docker-compose logs db
