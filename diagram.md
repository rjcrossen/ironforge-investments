# Ironforge Investments Architecture

```mermaid
graph LR
    API[Blizzard API] --> Scheduler[Scheduler Service]
    Scheduler --> DB[(PostgreSQL)]
    Scheduler --> Logs[Scraper Logs]
    
    subgraph "Database Tables"
        DB --> Auctions[auction_snapshots_eu/us]
        DB --> Recipes[recipes/reagents]
        DB --> Summaries[commodity_summaries_eu/us]
    end
    
    pgAdmin[pgAdmin UI] --> DB
    FutureAPI[API Service<br/>*Not Implemented*] -.-> DB
    
    style Scheduler fill:#90EE90
    style DB fill:#87CEEB
    style FutureAPI fill:#FFB6C1,stroke-dasharray: 5 5
```

## Components

- **Blizzard API**: External WoW game data source
- **Scheduler Service**: Python service that collects auction data hourly
- **PostgreSQL**: Time-partitioned database storing auction snapshots
- **pgAdmin**: Database management interface
- **API Service**: *Planned* - FastAPI endpoints for data access

## Data Flow

1. Scheduler polls Blizzard API every hour
2. Auction data stored in monthly partitioned tables
3. Recipe/reagent data seeded once on startup
4. Logs track collection status and performance
