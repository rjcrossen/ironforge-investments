# Ironforge Investments 🏗️

A data collection and analysis platform for World of Warcraft auction house data. This project applies quantitative finance techniques to virtual marketplace data to identify market inefficiencies and trading opportunities.

## 🏗️ Architecture

The system consists of containerized services that collect, store, and analyze auction house data from EU and US regions:

- **Scheduler Service** - Handles data collection, recipe seeding, and database maintenance
- **PostgreSQL Database** - Time-partitioned storage for auction snapshots and commodity summaries
- **API Service** - _(Planned)_ FastAPI endpoints for data access and analysis

## 🚀 Development Setup

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)
- Blizzard API credentials

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
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
uv sync
uv run pytest  # Run tests
uv run ruff check .  # Lint code
```

## 📊 Database Schema

The database uses monthly partitioning for efficient time-series data storage:

- **auction_snapshots_eu/us**: Raw auction data partitioned by snapshot_time
- **commodity_summaries_eu/us**: Aggregated price data partitioned by summary_time
- **recipes/reagents**: Crafting recipe data
- **scraper_logs**: Collection status and error tracking
- **benchmarks**: Performance metrics

## 🛠️ Key Commands

- **Build & Start**: `docker-compose build && docker-compose up -d`
- **View Logs**: `docker-compose logs -f scheduler`
- **Stop Services**: `docker-compose down`
- **Database Shell**: `docker-compose exec db psql -U postgres -d DB`

## 🎯 Roadmap

### Priority 1

- [ ] Complete commodity summary processing pipeline
- [ ] Implement ironforge-api-service with FastAPI
- [ ] Add comprehensive test coverage
- [ ] Set up CI/CD pipeline

### Priority 2

- [ ] Add monitoring and alerting
- [ ] Implement data retention policies
- [ ] Add market analysis algorithms
- [ ] Create web dashboard for visualization

## 📝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
