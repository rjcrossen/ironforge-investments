# Product Features

## Architecture

The system consists of containerized services that collect, store, and analyze auction house data from EU and US regions:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Scheduler      │────▶│  PostgreSQL     │◄────│  API Service    │
│  Service        │     │  Database       │     │  (Planned)      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │
        ▼
┌─────────────────┐
│  Blizzard API   │
│  (EU & US)      │
└─────────────────┘
```

### Services

- **Scheduler Service** - Handles data collection, recipe seeding, and database maintenance
- **PostgreSQL Database** - Time-partitioned storage for auction snapshots and commodity summaries
- **API Service** - _(Planned)_ FastAPI endpoints for data access and analysis

## Features

### Data Collection

- Automated auction house data collection from EU and US regions
- Time-partitioned storage for efficient querying
- Recipe and reagent seeding for crafting analysis
- Commodity market tracking

### Database

- PostgreSQL with time-based partitioning
- Optimized schema for auction snapshots
- Support for historical data analysis

### Development Tools

- Docker Compose for local development
- pgAdmin for database management
- Ruff for code formatting and linting (PEP 8)
- MyPy and Pyright for type checking

## Development Setup

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)
- Blizzard API credentials
- UV

### Quick Start

1. **Clone and configure**:

   ```bash
   git clone https://github.com/rjcrossen/ironforge-investments.git
   cd ironforge-investments
   cp ironforge-scheduler-service/.env.example ironforge-scheduler-service/.env
   # Edit .env with your Blizzard API credentials
   ```

2. **Start services**:

   ```bash
   docker-compose build && docker-compose up -d
   ```

3. **Access services**:
   - pgAdmin: http://localhost:8080 (admin@ironforge.com / admin)
   - Database: localhost:5432 (postgres / [see docker-compose.yml])

### Local Development

For scheduler service development:

```bash
cd ironforge-scheduler-service
uv venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
uv sync
uv run pytest  # Run tests
uv run ruff check .  # Lint code
```

## Key Commands

- **Build & Start**: `docker-compose build && docker-compose up -d`
- **View Logs**: `docker-compose logs -f scheduler`
- **Stop Services**: `docker-compose down`
- **Database Shell**: `docker-compose exec db psql -U postgres -d DB`
