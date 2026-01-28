# Ironforge Investments - System Architecture

## Table of Contents

- [Overview](#overview)
- [High-Level System Architecture](#high-level-system-architecture)
- [Component Descriptions](#component-descriptions)
- [Data Collection Schedule](#data-collection-schedule)
- [Data Flow Diagram](#data-flow-diagram)
- [Component Interactions](#component-interactions)
- [Data Model](#data-model)
- [Sequence Diagrams](#sequence-diagrams)
- [Component Inventory](#component-inventory)
- [Technology Stack](#technology-stack)
- [Repository Pattern](#repository-pattern)
- [Next Steps](#next-steps)

## Overview

Ironforge Investments is a data collection and analysis platform for World of Warcraft auction house data. The system collects auction data from both EU and US regions, stores it in a time-partitioned PostgreSQL database, and provides analysis capabilities for identifying market opportunities.

## High-Level System Architecture

```mermaid
flowchart TB
    subgraph External["External Services"]
        BlizzardAPI["Blizzard API\n(World of Warcraft)"]
    end

    subgraph Scheduler["Scheduler Service"]
        direction TB
        Main["SchedulerService\n(main.py)"]

        subgraph Seeding["Seeding System"]
            SeederOrch["SeederOrchestrator"]
            RecipeSeeder["RecipeSeeder"]
            ReagentSeeder["ReagentSeeder"]
            ItemSeeder["ItemSeeder"]
        end

        subgraph Scraping["Data Collection"]
            ScraperOrch["ScraperOrchestrator"]
            AuctionCollector["AuctionCollector"]
            BlizzardAPIClient["BlizzardAPI Client"]
        end

        PartitionManager["PartitionManagerService"]
    end

    subgraph Database["PostgreSQL Database"]
        direction TB

        subgraph AuctionTables["Auction Data"]
            AuctionSnapshotEU["AuctionSnapshotEU"]
            AuctionSnapshotUS["AuctionSnapshotUS"]
            EUStats["EUCommodityPriceStats"]
            USStats["USCommodityPriceStats"]
            EUToken["EUTokenPrice"]
            USToken["USTokenPrice"]
        end

        subgraph CraftingTables["Crafting Data"]
            Recipe["Recipe"]
            Reagent["Reagent"]
            Item["Item"]
        end

        subgraph OperationalTables["Operational Data"]
            SeederStatus["SeederStatus"]
            ScraperLog["ScraperLog"]
            Benchmark["Benchmark"]
        end
    end

    subgraph Future["Future Services"]
        APIService["API Service\n(Planned)"]
    end

    %% Connections
    BlizzardAPI -->|"OAuth + API Calls"| BlizzardAPIClient
    BlizzardAPIClient -->|"Fetch Recipes/Items"| SeederOrch
    BlizzardAPIClient -->|"Fetch Auctions"| ScraperOrch

    Main -->|"Initialize"| PartitionManager
    Main -->|"Run Once"| SeederOrch
    Main -->|"Continuous"| ScraperOrch

    SeederOrch --> RecipeSeeder
    SeederOrch --> ReagentSeeder
    SeederOrch --> ItemSeeder

    ScraperOrch --> AuctionCollector
    AuctionCollector -->|"Batch Insert"| AuctionTables

    RecipeSeeder -->|"Insert"| Recipe
    ReagentSeeder -->|"Insert"| Reagent
    ItemSeeder -->|"Insert"| Item

    SeederOrch -->|"Track Status"| SeederStatus
    ScraperOrch -->|"Log Attempts"| ScraperLog
    Main -->|"Performance Metrics"| Benchmark

    Database -->|"Query"| APIService

    %% Styling with dark text for readability
    classDef external fill:#ff9999,stroke:#333,stroke-width:2px,color:#000
    classDef service fill:#99ccff,stroke:#333,stroke-width:2px,color:#000
    classDef database fill:#99ff99,stroke:#333,stroke-width:2px,color:#000
    classDef future fill:#ffcc99,stroke:#333,stroke-width:2px,stroke-dasharray: 5 5,color:#000

    class BlizzardAPI external
    class Main,SeederOrch,ScraperOrch,RecipeSeeder,ReagentSeeder,ItemSeeder,AuctionCollector,BlizzardAPIClient,PartitionManager service
    class AuctionSnapshotEU,AuctionSnapshotUS,EUStats,USStats,EUToken,USToken,Recipe,Reagent,Item,SeederStatus,ScraperLog,Benchmark database
    class APIService future
```

## Component Descriptions

### Scheduler Service

The main application service that orchestrates all data collection and processing activities.

**Key Components:**

- **SchedulerService** (`main.py`): Entry point that initializes partitions, runs seeding, and starts continuous scraping
- **Signal Handling**: Graceful shutdown on SIGINT/SIGTERM signals

### Seeding System

One-time data population from Blizzard API for crafting-related data.

**Components:**

- **SeederOrchestrator**: Manages seeding workflow and tracks completion status
- **RecipeSeeder**: Fetches all professions, skill tiers, and recipes from Blizzard API
- **ReagentSeeder**: Extracts ingredients/reagents for each recipe
- **ItemSeeder**: Populates item metadata (names, levels, types)

**Data Flow:**

```
Blizzard API → Seeder → Repository → PostgreSQL
```

### Data Collection System

Continuous auction house data collection with intelligent polling.

**Components:**

- **ScraperOrchestrator**: Manages polling schedule (:30 past each hour) and retry logic
- **AuctionCollector**: Collects and processes auction data for a specific region
- **BlizzardAPI Client**: Handles OAuth, API requests, caching, and change detection

**Key Features:**

- **Change Detection**: Uses HTTP If-Modified-Since headers to skip unchanged data (304 responses)
- **Caching**: 60-second in-memory cache to avoid redundant API calls
- **Batch Processing**: Inserts data in 5000-record chunks
- **Dual Region Support**: Separate collection for EU and US

**Data Flow:**

```
Blizzard API → BlizzardAPI Client → AuctionCollector → Repository → PostgreSQL
```

### PostgreSQL Database

Time-partitioned storage for auction data and crafting information.

**Auction Data Tables:**

- **AuctionSnapshotEU/US**: Raw auction snapshots (auction_id, item_id, price, quantity, time_left)
- **EU/USCommodityPriceStats**: Aggregated statistics (min/max/mean/median prices, sales estimates)
- **EU/USTokenPrice**: WoW Token price tracking

**Crafting Data Tables:**

- **Recipe**: Crafting recipes with profession, skill tier, crafted item
- **Reagent**: Recipe ingredients with quantities and optionality
- **Item**: Item metadata and properties

**Operational Tables:**

- **SeederStatus**: Tracks which seeders have completed
- **ScraperLog**: Logs all scraper attempts with status and errors
- **Benchmark**: Performance metrics for operations

**Partitioning Strategy:**

- Auction tables are time-partitioned by snapshot_time for efficient querying
- Daily partition maintenance runs automatically

### Future Services

**API Service (Planned)**

- FastAPI-based service for querying auction data
- Will provide endpoints for price history, market analysis, and crafting profitability

## Sequence Diagrams

### Auction Data Collection Sequence

```mermaid
sequenceDiagram
    autonumber
    participant Main as SchedulerService
    participant Scraper as ScraperOrchestrator
    participant Partition as PartitionManagerService
    participant API as BlizzardAPI
    participant Collector as AuctionCollector
    participant Repo as AuctionRepositoryEU/US
    participant DB as PostgreSQL

    Note over Main,DB: Collection Cycle
    Main->>Scraper: start_polling_collection()
    Scraper->>Scraper: Run initial collection

    loop Every Hour at :30
        Scraper->>Scraper: Calculate wait time
        Scraper->>Scraper: sleep(seconds_to_wait)
        
        Note over Scraper: Collection Window (30 min)
        loop Polling Every 30s
            Scraper->>Scraper: run_collection_cycle()
            
            Note over Scraper,Partition: Daily Maintenance
            alt Daily Maintenance Needed
                Scraper->>Partition: run_daily_maintenance()
                Partition->>DB: CREATE PARTITION
                DB-->>Partition: OK
                Partition-->>Scraper: Complete
            end
            
            Note over Scraper,DB: EU Region Collection
            Scraper->>Scraper: _collect_region_data("eu")
            Scraper->>API: _create_api_for_region("eu")
            API-->>Scraper: api_instance
            
            Scraper->>DB: _get_last_modified_from_db("eu")
            DB-->>Scraper: last_modified
            
            Scraper->>API: is_commodities_updated(last_modified)
            API->>API: Check If-Modified-Since
            
            alt Data Unchanged (304)
                API-->>Scraper: false
                Scraper->>DB: _log_scraper_attempt("eu", "no_change")
            else Data Changed
                API-->>Scraper: true
                Scraper->>Collector: create(session, api, repository)
                Collector-->>Scraper: collector
                
                Scraper->>Collector: collect_snapshot_for_region(AuctionSnapshotEU)
                
                Collector->>API: get_cached_commodities_if_fresh()
                
                alt Cache Hit
                    API-->>Collector: cached_data
                else Cache Miss
                    Collector->>API: get_commodities(return_headers=True)
                    API->>API: OAuth + API Request
                    API-->>Collector: (commodities, headers)
                    Collector->>Collector: Extract Last-Modified
                end
                
                Collector->>Collector: Prepare batch values
                Note right of Collector: 5000 records per batch
                
                Collector->>Repo: batch_insert(AuctionSnapshotEU, values)
                loop Batch Insert
                    Repo->>DB: INSERT INTO auction_snapshots_eu
                    DB-->>Repo: OK
                end
                Repo-->>Collector: Complete
                
                Collector->>DB: get_last_collection_time("eu")
                DB-->>Collector: previous_timestamp
                
                Collector->>Repo: get_snapshot(previous_timestamp)
                Repo->>DB: SELECT * FROM auction_snapshots_eu
                DB-->>Repo: previous_data
                Repo-->>Collector: previous_snapshot
                
                Collector->>Collector: calculate_commodity_stats()
                Collector->>Collector: estimate_sales()
                Collector->>Collector: count_new_listings()
                
                Collector->>DB: INSERT INTO eu_commodity_price_stats
                DB-->>Collector: OK
                
                Collector->>API: get_wow_token_price()
                API-->>Collector: token_data
                Collector->>DB: INSERT INTO eu_token_price
                DB-->>Collector: OK
                
                Collector->>DB: session.commit()
                Collector-->>Scraper: last_modified
                
                Scraper->>DB: _log_scraper_attempt("eu", "success")
            end
            
            Note over Scraper,DB: US Region Collection (Same Flow)
            Scraper->>Scraper: _collect_region_data("us")
            
            alt Both Regions Collected
                Scraper->>Scraper: break
            else Window Timeout
                Scraper->>Scraper: break
            end
        end
    end
```

### Recipe Seeding Sequence

```mermaid
sequenceDiagram
    autonumber
    participant Main as SchedulerService
    participant SeederOrch as SeederOrchestrator
    participant Seeder as RecipeSeeder
    participant API as BlizzardAPI
    participant Repo as RecipeRepository
    participant DB as PostgreSQL

    Note over Main,DB: Initial Seeding
    Main->>SeederOrch: run_initial_seeding()
    
    SeederOrch->>DB: Check SeederStatus
    DB-->>SeederOrch: seeder_status
    
    alt Recipe Seeder Not Complete
        SeederOrch->>Seeder: seed(session)
        Seeder->>API: Create BlizzardAPI(config)
        API-->>Seeder: api
        
        Seeder->>API: get_professions()
        API->>API: OAuth + API Request
        API-->>Seeder: professions_list
        
        loop For Each Profession
            Seeder->>API: get_profession_info(href)
            API-->>Seeder: profession_info
            
            alt Has Skill Tiers
                loop For Each Skill Tier
                    Seeder->>API: get_skill_tier_details(href)
                    API-->>Seeder: tier_data
                    
                    loop For Each Category
                        loop For Each Recipe
                            Seeder->>API: get_recipe_info(href)
                            API-->>Seeder: recipe_info
                            
                            alt Has Crafted Item
                                Seeder->>Seeder: _process_recipe()
                                Seeder->>Seeder: Add to batch (Neutral)
                            else Has Alliance/Horde Items
                                Seeder->>Seeder: _process_recipe()
                                Seeder->>Seeder: Add to batch (Alliance)
                                Seeder->>Seeder: Add to batch (Horde)
                            else No Crafted Item
                                Seeder->>Seeder: Add to batch (Neutral, null)
                            end
                        end
                    end
                end
                
                Seeder->>Repo: batch_insert(recipe_batch)
                Repo->>DB: INSERT INTO recipes
                DB-->>Repo: OK
                Repo-->>Seeder: Complete
                Seeder->>DB: session.commit()
            end
        end
        
        SeederOrch->>SeederOrch: mark_seeder_complete("recipe")
        SeederOrch->>DB: UPDATE SeederStatus
        DB-->>SeederOrch: OK
    end
```

### Reagent Seeding Sequence

```mermaid
sequenceDiagram
    autonumber
    participant SeederOrch as SeederOrchestrator
    participant Seeder as ReagentSeeder
    participant API as BlizzardAPI
    participant Repo as ReagentRepository
    participant DB as PostgreSQL

    Note over SeederOrch,DB: Reagent Seeding (After Recipe Seeding)
    SeederOrch->>DB: Check SeederStatus
    DB-->>SeederOrch: seeder_status
    
    alt Reagent Seeder Not Complete
        SeederOrch->>Seeder: seed(session)
        Seeder->>API: Create BlizzardAPI(config)
        API-->>Seeder: api
        
        Seeder->>API: get_professions()
        API-->>Seeder: professions_list
        
        loop For Each Profession
            Seeder->>API: get_profession_info(href)
            API-->>Seeder: profession_info
            
            alt Has Skill Tiers
                loop For Each Skill Tier
                    Seeder->>API: get_skill_tier_details(href)
                    API-->>Seeder: tier_data
                    
                    loop For Each Category
                        loop For Each Recipe
                            Seeder->>API: get_recipe_info(href)
                            API-->>Seeder: recipe_info
                            
                            Seeder->>Seeder: _process_reagents()
                            
                            alt Has Crafted Item
                                Seeder->>Seeder: Add reagents (Neutral)
                            else Has Alliance/Horde Items
                                Seeder->>Seeder: Add reagents (Alliance)
                                Seeder->>Seeder: Add reagents (Horde)
                            else No Crafted Item
                                Seeder->>Seeder: Add reagents (Neutral)
                            end
                            
                            alt Has Required Reagents
                                loop For Each Reagent
                                    Seeder->>Seeder: Add to batch<br/>(recipe_id, item_id, quantity, optional=False)
                                end
                            end
                            
                            alt Has Optional Reagents
                                loop For Each Optional Reagent
                                    Seeder->>Seeder: Add to batch<br/>(recipe_id, item_id, quantity, optional=True)
                                end
                            end
                        end
                    end
                end
                
                Seeder->>Repo: batch_insert(reagent_batch)
                Repo->>Repo: _filter_valid_reagents()
                Repo->>DB: Validate recipe_id exists
                DB-->>Repo: valid_reagents
                Repo->>DB: INSERT INTO reagents
                DB-->>Repo: OK
                Repo-->>Seeder: Complete
                Seeder->>DB: session.commit()
            end
        end
        
        SeederOrch->>SeederOrch: mark_seeder_complete("reagent")
        SeederOrch->>DB: UPDATE SeederStatus
        DB-->>SeederOrch: OK
    end
```

### Error Handling in Sequences

**Auction Collection Errors:**

```mermaid
sequenceDiagram
    participant Scraper as ScraperOrchestrator
    participant API as BlizzardAPI
    participant Collector as AuctionCollector
    participant DB as PostgreSQL

    Note over Scraper,DB: Error Scenarios
    
    alt API Authentication Error
        Scraper->>API: _create_api_for_region()
        API->>API: Missing credentials
        API--xScraper: ValueError
        Scraper->>DB: _log_scraper_attempt("failed", error)
    else API Request Timeout
        Scraper->>API: is_commodities_updated()
        API->>API: Request timeout
        API--xScraper: Exception
        Scraper->>Scraper: Proceed with collection (safe fallback)
    else Database Connection Error
        Collector->>DB: batch_insert()
        DB--xCollector: ConnectionError
        Collector->>DB: session.rollback()
        Collector--xScraper: Exception
        Scraper->>DB: _log_scraper_attempt("failed", error)
    else Data Validation Error
        Collector->>Collector: Process auction data
        Collector->>Collector: Invalid time_left code
        Collector--xCollector: KeyError
        Collector->>DB: session.rollback()
    end
```

**Seeding Errors:**

```mermaid
sequenceDiagram
    participant Seeder as RecipeSeeder/ReagentSeeder
    participant API as BlizzardAPI
    participant Repo as Repository
    participant DB as PostgreSQL

    Note over Seeder,DB: Seeding Error Scenarios
    
    alt API Rate Limit
        Seeder->>API: get_profession_info()
        API--xSeeder: RateLimitError
        Seeder->>Seeder: Retry with backoff
    else Invalid API Response
        Seeder->>API: get_recipe_info()
        API-->>Seeder: Invalid JSON
        Seeder->>Seeder: Skip recipe, continue
    else Foreign Key Violation
        Seeder->>Repo: batch_insert(reagents)
        Repo->>DB: INSERT
        DB--xRepo: ForeignKeyViolation
        Repo->>Repo: _filter_valid_reagents()
        Repo->>DB: Retry with valid only
    else Database Error
        Seeder->>Repo: batch_insert()
        Repo->>DB: INSERT
        DB--xRepo: DatabaseError
        Repo--xSeeder: Exception
        Seeder->>DB: session.rollback()
        Seeder--xSeederOrch: Raise error
    end
```

## Data Collection Schedule

- **Initial Seeding**: Runs once on startup (if not completed)
- **Auction Collection**: Every hour at :30 past the hour
- **Polling Window**: 30-minute window with 30-second intervals
- **Partition Maintenance**: Daily (automatic)

## Data Flow Diagram

This diagram illustrates the complete data flow from the Blizzard API through the system to the PostgreSQL database.

```mermaid
flowchart TB
    subgraph External["Blizzard API"]
        BlizzardAPI["/data/wow/auctions/commodities"]
        TokenAPI["/data/wow/token/index"]
    end

    subgraph DataCollection["Data Collection Layer"]
        direction TB
        ScraperOrch["ScraperOrchestrator<br/>(scraper.py)"]

        subgraph PerRegion["Per-Region Processing"]
            direction TB
            APIClientEU["BlizzardAPI<br/>(EU)"]
            APIClientUS["BlizzardAPI<br/>(US)"]
            CollectorEU["AuctionCollector<br/>(EU)"]
            CollectorUS["AuctionCollector<br/>(US)"]
        end

        subgraph ChangeDetection["Change Detection"]
            CheckModified["Check If-Modified-Since"]
            Cache["60s In-Memory Cache"]
        end
    end

    subgraph DataTransformation["Data Transformation"]
        direction TB
        ExtractRaw["Extract Raw Auction Data<br/>(id, item_id, unit_price, quantity, time_left)"]
        CalculateStats["Calculate Commodity Statistics<br/>(min, max, mean, median)"]
        EstimateSales["Estimate Sales & New Listings<br/>(Compare with previous snapshot)"]
        ExtractToken["Extract Token Price"]
    end

    subgraph DataStorage["PostgreSQL Database"]
        direction TB

        subgraph AuctionData["Auction Snapshots"]
            AuctionEU["AuctionSnapshotEU"]
            AuctionUS["AuctionSnapshotUS"]
        end

        subgraph StatsData["Commodity Statistics"]
            StatsEU["EUCommodityPriceStats"]
            StatsUS["USCommodityPriceStats"]
        end

        subgraph TokenData["Token Prices"]
            TokenEU["EUTokenPrice"]
            TokenUS["USTokenPrice"]
        end

        subgraph Operational["Operational Logs"]
            ScraperLog["ScraperLog<br/>(attempts, status, errors)"]
        end
    end

    %% Data Flow Connections
    BlizzardAPI -->|"OAuth + API Call"| APIClientEU
    BlizzardAPI -->|"OAuth + API Call"| APIClientUS
    TokenAPI -->|"Fetch Token Price"| APIClientEU
    TokenAPI -->|"Fetch Token Price"| APIClientUS

    ScraperOrch -->|"Trigger Collection"| CollectorEU
    ScraperOrch -->|"Trigger Collection"| CollectorUS

    APIClientEU -->|"Use or Fetch"| Cache
    APIClientUS -->|"Use or Fetch"| Cache
    Cache -->|"Return Data"| APIClientEU
    Cache -->|"Return Data"| APIClientUS

    APIClientEU -->|"Check 304 Status"| CheckModified
    APIClientUS -->|"Check 304 Status"| CheckModified
    CheckModified -->|"Skip if unchanged"| ScraperOrch

    APIClientEU -->|"Raw JSON Response"| ExtractRaw
    APIClientUS -->|"Raw JSON Response"| ExtractRaw

    ExtractRaw -->|"Batch Insert 5000"| AuctionEU
    ExtractRaw -->|"Batch Insert 5000"| AuctionUS

    ExtractRaw -->|"Group by item_id"| CalculateStats
    CalculateStats -->|"Compare with previous"| EstimateSales
    EstimateSales -->|"Insert Stats"| StatsEU
    EstimateSales -->|"Insert Stats"| StatsUS

    ExtractToken -->|"Insert Token Price"| TokenEU
    ExtractToken -->|"Insert Token Price"| TokenUS

    ScraperOrch -->|"Log Attempt"| ScraperLog

    %% Styling
    classDef external fill:#ff9999,stroke:#333,stroke-width:2px,color:#000
    classDef service fill:#99ccff,stroke:#333,stroke-width:2px,color:#000
    classDef transform fill:#ffcc99,stroke:#333,stroke-width:2px,color:#000
    classDef database fill:#99ff99,stroke:#333,stroke-width:2px,color:#000

    class BlizzardAPI,TokenAPI external
    class ScraperOrch,APIClientEU,APIClientUS,CollectorEU,CollectorUS,CheckModified,Cache service
    class ExtractRaw,CalculateStats,EstimateSales,ExtractToken transform
    class AuctionEU,AuctionUS,StatsEU,StatsUS,TokenEU,TokenUS,ScraperLog database
```

### Data Flow Description

**1. API Request Phase**
- ScraperOrchestrator triggers collection at :30 past each hour
- BlizzardAPI client checks 60-second in-memory cache first
- If cache miss, makes OAuth-authenticated request to Blizzard API
- Uses `If-Modified-Since` header to detect changes (304 response if unchanged)

**2. Data Extraction Phase**
- Raw auction data extracted: `id`, `item_id`, `unit_price`, `quantity`, `time_left`
- Time-left codes converted: SHORT(1), MEDIUM(2), LONG(3), VERY_LONG(4)
- WoW Token price fetched from separate endpoint

**3. Data Transformation Phase**
- Auctions grouped by `item_id` for statistical analysis
- Statistics calculated per commodity:
  - Min/Max prices
  - Mean and median prices
  - Total quantity available
- Sales estimation by comparing with previous snapshot:
  - Items no longer present = estimated sales
  - New auction IDs = new listings

**4. Data Storage Phase**
- **Auction Snapshots**: Batch inserted in 5000-record chunks
- **Commodity Statistics**: Aggregated data with sales estimates
- **Token Prices**: Timestamp and price stored
- **Operational Logs**: Every attempt logged with status and errors

**5. Dual Region Support**
- Parallel processing for EU and US regions
- Separate API clients, collectors, and database tables per region
- Independent change detection and caching
- Collection continues even if one region fails

## Component Interactions

### Auction Collection Flow

```mermaid
sequenceDiagram
    participant Scraper as ScraperOrchestrator
    participant Collector as AuctionCollector
    participant API as BlizzardAPI
    participant Cache as In-Memory Cache
    participant Repo as AuctionRepository
    participant DB as PostgreSQL

    Scraper->>Scraper: run_collection_cycle()
    Scraper->>Scraper: _run_daily_maintenance_if_needed()
    
    loop For Each Region (EU, US)
        Scraper->>Scraper: _collect_region_data(region)
        Scraper->>API: _create_api_for_region(region)
        Scraper->>API: is_commodities_updated(last_modified)
        
        alt Data Unchanged (304)
            API-->>Scraper: false
            Scraper->>DB: _log_scraper_attempt(region, "no_change")
        else Data Changed or Error
            API-->>Scraper: true
            Scraper->>Collector: create AuctionCollector(session, api, repository)
            Scraper->>Collector: collect_snapshot_for_region(auction_model)
            
            Collector->>API: get_cached_commodities_if_fresh()
            
            alt Cache Hit
                Cache-->>Collector: cached_data
            else Cache Miss
                Collector->>API: get_commodities(return_headers=True)
                API-->>Collector: commodities + headers
                Collector->>Collector: Extract Last-Modified
            end
            
            Collector->>Collector: Prepare batch values (5000 chunks)
            Collector->>Repo: batch_insert(auction_model, values)
            Repo->>DB: INSERT INTO auction_snapshots
            
            Collector->>Collector: Calculate commodity stats
            Collector->>Collector: Compare with previous snapshot
            Collector->>Collector: Estimate sales & new listings
            Collector->>DB: INSERT INTO commodity_price_stats
            
            Collector->>API: get_wow_token_price()
            API-->>Collector: token_data
            Collector->>DB: INSERT INTO token_price
            
            Collector-->>Scraper: last_modified
            Scraper->>DB: _log_scraper_attempt(region, "success")
        end
    end
```

### Seeding Flow

```mermaid
sequenceDiagram
    participant Main as SchedulerService
    participant SeederOrch as SeederOrchestrator
    participant Seeder as RecipeSeeder/ReagentSeeder
    participant API as BlizzardAPI
    participant Repo as RecipeRepository/ReagentRepository
    participant DB as PostgreSQL

    Main->>Main: run_initial_seeding()
    Main->>SeederOrch: should_run_seeders()
    SeederOrch->>DB: Check SeederStatus
    
    alt Seeders Not Complete
        SeederOrch-->>Main: true
        Main->>SeederOrch: run_initial_seeding()
        
        loop For Each Seeder (Recipe, Reagent, Item)
            SeederOrch->>Seeder: seed(session)
            Seeder->>API: Create BlizzardAPI(config)
            Seeder->>API: get_professions()
            API-->>Seeder: professions_list
            
            loop For Each Profession
                Seeder->>API: get_profession_info(href)
                API-->>Seeder: profession_info
                
                loop For Each Skill Tier
                    Seeder->>API: get_skill_tier_details(href)
                    API-->>Seeder: tier_data
                    
                    loop For Each Category
                        loop For Each Recipe
                            Seeder->>API: get_recipe_info(href)
                            API-->>Seeder: recipe_info
                            Seeder->>Seeder: _process_recipe() / _process_reagents()
                            Seeder->>Seeder: Build batch list
                        end
                    end
                end
            end
            
            Seeder->>Repo: batch_insert(batch_list)
            Repo->>DB: INSERT INTO recipes/reagents
            Seeder->>DB: session.commit()
        end
        
        SeederOrch->>SeederOrch: mark_seeder_complete()
        SeederOrch->>DB: UPDATE SeederStatus
    else All Seeders Complete
        SeederOrch-->>Main: false
        Main->>Main: Skip seeding
    end
```

### Error Handling Flow

```mermaid
flowchart TB
    subgraph Collection["Auction Collection"]
        Start["Start Collection"]
        CheckAPI["Create API Client"]
        CheckChange["Check If-Modified-Since"]
        Collect["Collect Data"]
        LogSuccess["Log Success"]
        LogError["Log Error"]
        
        Start --> CheckAPI
        CheckAPI -->|"API Error"| LogError
        CheckAPI --> CheckChange
        CheckChange -->|"304 Not Modified"| LogNoChange["Log No Change"]
        CheckChange -->|"API Error"| LogError
        CheckChange --> Collect
        Collect -->|"Success"| LogSuccess
        Collect -->|"Exception"| LogError
    end

    subgraph Seeding["Seeding Process"]
        SeedStart["Start Seeding"]
        FetchProf["Fetch Professions"]
        ProcessTier["Process Skill Tier"]
        InsertBatch["Batch Insert"]
        SeedSuccess["Mark Complete"]
        SeedError["Rollback & Error"]
        
        SeedStart --> FetchProf
        FetchProf -->|"API Error"| SeedError
        FetchProf --> ProcessTier
        ProcessTier -->|"API Error"| SeedError
        ProcessTier --> InsertBatch
        InsertBatch -->|"Success"| SeedSuccess
        InsertBatch -->|"Exception"| SeedError
    end

    subgraph Recovery["Recovery Strategies"]
        Retry["Retry with Backoff"]
        Skip["Skip & Continue"]
        Abort["Abort Operation"]
        
        LogError --> Retry
        Retry -->|"Max Retries"| Skip
        SeedError --> Abort
    end

    style Start fill:#99ccff,stroke:#333,color:#000
    style SeedStart fill:#99ccff,stroke:#333,color:#000
    style LogSuccess fill:#99ff99,stroke:#333,color:#000
    style SeedSuccess fill:#99ff99,stroke:#333,color:#000
    style LogError fill:#ff9999,stroke:#333,color:#000
    style SeedError fill:#ff9999,stroke:#333,color:#000
```

### Component Interaction Summary

**Auction Collection Flow:**
1. **ScraperOrchestrator** manages the collection cycle and polling schedule
2. **AuctionCollector** handles data extraction and transformation per region
3. **BlizzardAPI** provides OAuth authentication and API access with caching
4. **AuctionRepository** abstracts database operations with batch inserts
5. **PostgreSQL** stores snapshots, statistics, and operational logs

**Seeding Flow:**
1. **SeederOrchestrator** checks completion status and runs seeders sequentially
2. **RecipeSeeder/ReagentSeeder** fetch crafting data from Blizzard API
3. **RecipeRepository/ReagentRepository** handle database insertions
4. **SeederStatus** tracks which seeders have completed

**Error Handling:**
- **API Errors**: Logged to ScraperLog with error message
- **Database Errors**: Session rollback, error logged
- **Change Detection**: 304 responses skip unnecessary collection
- **Retry Logic**: Built into BlizzardAPI with urllib3 retry strategy

## Technology Stack

- **Language**: Python 3.11+
- **Database**: PostgreSQL with time-based partitioning
- **ORM**: SQLAlchemy 2.0
- **API Client**: Requests with urllib3 retry strategy
- **Type Checking**: BasedPyright (strict mode)
- **Formatting**: Ruff (PEP 8)
- **Package Manager**: UV

## Repository Pattern

All database access follows the repository pattern:

```
Models (SQLAlchemy) ← Repositories ← Services/Seeders/Collectors
```

**Repositories:**

- `AuctionRepositoryEU/US`: Auction data access
- `RecipeRepository`: Recipe management
- `ReagentRepository`: Reagent/ingredient management

## Data Model

### Entity Relationship Diagram - Auction Data

```mermaid
erDiagram
    EUCommodityPriceStats {
        int item_id PK
        datetime timestamp PK
        bigint min_price
        bigint max_price
        float mean_price
        float median_price
        bigint total_quantity
        int num_auctions
        int estimated_sales
        int new_listings
    }

    USCommodityPriceStats {
        int item_id PK
        datetime timestamp PK
        bigint min_price
        bigint max_price
        float mean_price
        float median_price
        bigint total_quantity
        int num_auctions
        int estimated_sales
        int new_listings
    }

    AuctionSnapshotEU {
        bigint auction_id PK
        int item_id
        bigint unit_price
        int quantity
        string time_left
        datetime snapshot_time PK
    }

    AuctionSnapshotUS {
        bigint auction_id PK
        int item_id
        bigint unit_price
        int quantity
        string time_left
        datetime snapshot_time PK
    }

    EUTokenPrice {
        datetime timestamp PK
        bigint price
    }

    USTokenPrice {
        datetime timestamp PK
        bigint price
    }

    EUCommodityPriceStats ||--o{ AuctionSnapshotEU : "aggregates"
    USCommodityPriceStats ||--o{ AuctionSnapshotUS : "aggregates"
```

### Entity Relationship Diagram - Crafting Data

```mermaid
erDiagram
    Recipe {
        int id PK
        string name
        string profession
        string skill_tier
        int crafted_item_id
        string faction PK
        json data
        datetime created_at
        datetime updated_at
    }

    Reagent {
        int recipe_id PK, FK
        string faction PK, FK
        int item_id PK
        int quantity
        boolean optional
    }

    Item {
        int id PK
        string item_name
        int item_level
        string item_class
        string item_subclass
        string inventory_type
        boolean is_equippable
        boolean is_stackable
        string quality
    }

    Recipe ||--o{ Reagent : "requires"
    Item ||--o{ Reagent : "is ingredient in"
    Item ||--o{ Recipe : "is crafted by"
```

### Entity Relationship Diagram - Operational Data

```mermaid
erDiagram
    SeederStatus {
        string seeder_type PK
        boolean completed
        datetime completed_at
        datetime created_at
        datetime updated_at
    }

    ScraperLog {
        int id PK
        string region
        datetime timestamp
        string status
        datetime last_modified
        string error_message
        int poll_attempts
    }

    Benchmark {
        int id PK
        string operation_type
        string operation_name
        string region
        datetime start_time
        datetime end_time
        float duration_seconds
        int record_count
        string status
        string error_message
        json extra_data
        datetime created_at
    }
```

### Table Descriptions

**Auction Data Tables:**

| Table | Description | Primary Key | Partitioned |
|-------|-------------|-------------|-------------|
| `AuctionSnapshotEU/US` | Raw auction snapshots | (auction_id, snapshot_time) | Yes |
| `EU/USCommodityPriceStats` | Aggregated commodity statistics | (item_id, timestamp) | No |
| `EU/USTokenPrice` | WoW Token price history | timestamp | No |

**Crafting Data Tables:**

| Table | Description | Primary Key | Relationships |
|-------|-------------|-------------|---------------|
| `Recipe` | Crafting recipes | (id, faction) | - |
| `Reagent` | Recipe ingredients | (recipe_id, faction, item_id) | FK → Recipe |
| `Item` | Item metadata | id | Referenced by Reagent |

**Operational Tables:**

| Table | Description | Primary Key |
|-------|-------------|-------------|
| `SeederStatus` | Tracks seeding completion | seeder_type |
| `ScraperLog` | Logs all scraper attempts | id |
| `Benchmark` | Performance metrics | id |

### Partitioning Strategy

**Time-Based Partitioning:**

- **AuctionSnapshotEU/US** tables are partitioned by `snapshot_time`
- Daily partitions created automatically
- Partitions named: `auction_snapshots_eu_2024_01_15`, etc.
- Old partitions can be archived or dropped for data retention

**Benefits:**
- Efficient querying by date range
- Fast data deletion (drop partition vs DELETE)
- Parallel processing capabilities
- Better index performance

**Partition Maintenance:**
- Runs daily during collection cycle
- Creates partitions for upcoming days
- Managed by `PartitionManagerService`

## Component Inventory

### Service Layer Components

| Component | File Path | Description | Key Methods |
|-----------|-----------|-------------|-------------|
| **SchedulerService** | `src/main.py` | Main entry point orchestrating all services | `run_initial_seeding()`, `start_services()`, `stop_services()` |
| **ScraperOrchestrator** | `src/scraper/scraper.py` | Manages auction data collection and polling | `run_collection_cycle()`, `start_polling_collection()`, `_collect_region_data()` |
| **AuctionCollector** | `src/scraper/auction_collector.py` | Collects and processes auction data per region | `collect_snapshot_for_region()`, `get_last_collection_time()`, `get_snapshot()` |
| **SeederOrchestrator** | `src/seeding/seeder.py` | Manages seeding workflow and completion status | `should_run_seeders()`, `run_initial_seeding()`, `mark_seeder_complete()` |
| **RecipeSeeder** | `src/seeding/recipes.py` | Fetches and stores crafting recipes | `seed()`, `_process_recipe()` |
| **ReagentSeeder** | `src/seeding/reagents.py` | Extracts and stores recipe ingredients | `seed()`, `_process_reagents()` |
| **ItemSeeder** | `src/seeding/items.py` | Populates item metadata | `seed()` |
| **PartitionManagerService** | `src/utils/partition_manager.py` | Manages database partition creation | `run_daily_maintenance()`, `create_partitions()` |

### Data Access Layer (Repositories)

| Component | File Path | Description | Key Methods |
|-----------|-----------|-------------|-------------|
| **AuctionRepositoryEU** | `src/repository/auction_repository_eu.py` | EU auction data access | `batch_insert()`, `get_snapshot()` |
| **AuctionRepositoryUS** | `src/repository/auction_repository_us.py` | US auction data access | `batch_insert()`, `get_snapshot()` |
| **RecipeRepository** | `src/repository/recipe_repository.py` | Recipe management | `batch_insert()`, `get_recipe_by_id_and_faction()`, `get_recipes_by_profession()` |
| **ReagentRepository** | `src/repository/reagent_repository.py` | Reagent/ingredient management | `batch_insert()`, `get_reagents_by_recipe()`, `_filter_valid_reagents()` |

### External API Integration

| Component | File Path | Description | Key Methods |
|-----------|-----------|-------------|-------------|
| **BlizzardAPI** | `src/scraper/blizzard_api_utils.py` | OAuth-authenticated API client | `get_commodities()`, `is_commodities_updated()`, `get_wow_token_price()`, `get_professions()`, `get_recipe_info()` |
| **BlizzardConfig** | `src/scraper/blizzard_api_utils.py` | API configuration dataclass | Configuration for client_id, client_secret, region, timeout |

### Database Models

| Model | File Path | Description | Primary Key |
|-------|-----------|-------------|-------------|
| **EUCommodityPriceStats** | `src/models/models.py` | EU commodity price statistics | (item_id, timestamp) |
| **USCommodityPriceStats** | `src/models/models.py` | US commodity price statistics | (item_id, timestamp) |
| **AuctionSnapshotEU** | `src/models/models.py` | EU raw auction snapshots | (auction_id, snapshot_time) |
| **AuctionSnapshotUS** | `src/models/models.py` | US raw auction snapshots | (auction_id, snapshot_time) |
| **EUTokenPrice** | `src/models/models.py` | EU WoW Token prices | timestamp |
| **USTokenPrice** | `src/models/models.py` | US WoW Token prices | timestamp |
| **Recipe** | `src/models/models.py` | Crafting recipes | (id, faction) |
| **Reagent** | `src/models/models.py` | Recipe ingredients | (recipe_id, faction, item_id) |
| **Item** | `src/models/models.py` | Item metadata | id |
| **SeederStatus** | `src/models/models.py` | Seeding completion tracking | seeder_type |
| **ScraperLog** | `src/models/models.py` | Scraper attempt logs | id |
| **Benchmark** | `src/models/models.py` | Performance metrics | id |

### Utility Components

| Component | File Path | Description | Key Functions |
|-----------|-----------|-------------|---------------|
| **Database Connection** | `src/repository/database.py` | SQLAlchemy session management | `get_engine()`, `get_session()`, `db_session()` |
| **Auction Utilities** | `src/utils/auction_utils.py` | Auction data calculations | `calculate_commodity_stats()`, `estimate_sales()`, `count_new_listings()` |
| **Benchmark Manager** | `src/utils/benchmark.py` | Performance tracking | `start_benchmark()`, `end_benchmark()` |
| **Polling Config** | `src/scraper/polling_config.py` | Collection scheduling | `SimplePollingConfig` |

### Key Design Patterns

1. **Repository Pattern**: All database access through repository classes
2. **Orchestrator Pattern**: High-level service coordination
3. **Context Manager**: Database session management with automatic cleanup
4. **Batch Processing**: Chunked inserts (5000 records per batch)
5. **Caching**: 60-second in-memory cache for API responses
6. **Change Detection**: HTTP 304 Not Modified handling
7. **Partitioning**: Time-based table partitioning for auction data

### Component Dependencies

```
SchedulerService
├── SeederOrchestrator
│   ├── RecipeSeeder → RecipeRepository → Recipe
│   ├── ReagentSeeder → ReagentRepository → Reagent
│   └── ItemSeeder → ItemRepository → Item
├── ScraperOrchestrator
│   ├── AuctionCollector → AuctionRepositoryEU/US → AuctionSnapshotEU/US
│   └── BlizzardAPI (OAuth client)
└── PartitionManagerService
```

## Next Steps

See the following sections for detailed diagrams:

- [Data Flow Diagram](#data-flow-diagram)
- [Component Interactions](#component-interactions)
- [Data Model](#data-model)
- [Sequence Diagrams](#sequence-diagrams)
