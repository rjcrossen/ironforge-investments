# Codebase Analysis Summary

## Key Components

### 1. Database Models (src/models/models.py)

**Auction Data Models:**

- `EUCommodityPriceStats` / `USCommodityPriceStats`: Track commodity price statistics over time (min, max, mean, median prices, quantities, estimated sales, new listings)
- `AuctionSnapshotEU` / `AuctionSnapshotUS`: Store raw auction house snapshots with auction_id, item_id, unit_price, quantity, time_left, snapshot_time
- `EUTokenPrice` / `USTokenPrice`: Track WoW Token prices over time

**Crafting Data Models:**

- `Recipe`: Stores crafting recipes with profession, skill_tier, crafted_item_id, faction, JSON data
- `Reagent`: Stores recipe ingredients with recipe_id, faction, item_id, quantity, optional flag
- `Item`: Stores item metadata (name, level, class, subclass, inventory_type, equippable, stackable, quality)

**Operational Models:**

- `SeederStatus`: Tracks completion status of seeding operations (recipes, reagents, items)
- `ScraperLog`: Logs scraper attempts with region, status, last_modified, error_message, poll_attempts
- `Benchmark`: Tracks operation performance metrics (duration, record_count, status)

### 2. Data Access Layer (Repository Pattern)

**Auction Repositories:**

- `AuctionRepositoryEU` / `AuctionRepositoryUS`: Handle batch inserts and snapshot retrieval for each region
  - `batch_insert()`: Insert records in chunks (5000 records per chunk)
  - `get_snapshot()`: Retrieve auction data for specific timestamp

**Crafting Repositories:**

- `RecipeRepository`: Manage recipe data
  - `batch_insert()`: Insert recipes with conflict handling
  - `get_recipe_by_id_and_faction()`: Fetch specific recipe
  - `get_recipes_by_profession()`: Fetch all recipes for a profession
  - `recipe_exists()`: Check if recipe exists

- `ReagentRepository`: Manage reagent/ingredient data
  - `batch_insert()`: Insert reagents with validation against existing recipes
  - `_filter_valid_reagents()`: Ensure reagents reference valid recipes
  - `get_reagents_by_recipe()`: Fetch reagents for a recipe
  - `get_optional_reagents_by_recipe()` / `get_required_reagents_by_recipe()`: Filter by optionality

### 3. Blizzard API Client (src/scraper/blizzard_api_utils.py)

**Core Components:**

- `BlizzardConfig`: Dataclass for API configuration (client_id, client_secret, region, timeout, max_retries)
- `create_session()`: Creates requests session with retry strategy
- `get_access_token()`: OAuth authentication with Blizzard
- `BlizzardAPI`: Main API client class

**API Methods:**

- `get_commodities()`: Fetch auction house commodities
- `is_commodities_updated()`: Check if data changed using If-Modified-Since header (returns 304 if unchanged)
- `get_cached_commodities_if_fresh()`: Return cached data if < 60 seconds old
- `get_item()`: Fetch item details
- `get_professions()` / `get_profession_info()` / `get_skill_tier_details()` / `get_recipe_info()`: Crafting data
- `search_items_by_id()`: Search items by ID range
- `get_wow_token_price()`: Fetch WoW Token price

### 4. Auction Collection (src/scraper/auction_collector.py)

**AuctionCollector Class:**

- Manages auction data collection for a specific region
- `get_last_collection_time()`: Query last collection timestamp from database
- `collect_snapshot_for_region()`: Main collection logic
  1. Check for cached commodities or fetch fresh data
  2. Extract Last-Modified timestamp from headers
  3. Batch insert auction snapshots
  4. Calculate commodity statistics (min, max, mean, median prices)
  5. Compare with previous snapshot to estimate sales and new listings
  6. Insert commodity price statistics
  7. Collect and store WoW Token price

### 5. Scraper Orchestration (src/scraper/scraper.py)

**ScraperOrchestrator Class:**

- Manages continuous auction data collection for both EU and US regions
- `run_collection_cycle()`: Single collection cycle for both regions
  - Runs daily partition maintenance if needed
  - Collects EU data
  - Collects US data
  - Returns success status and new data flags

- `start_polling_collection()`: Continuous polling at :30 past each hour
  - Runs initial collection on startup
  - Waits until :30 past each hour
  - Polls every 30 seconds for up to 30 minutes
  - Tracks which regions have been collected
  - Stops polling once both regions have new data

- `_collect_region_data()`: Single region collection with change detection
  - Checks if data has been updated since last collection
  - Skips collection if data unchanged (304 response)
  - Creates AuctionCollector and collects data
  - Logs scraper attempts to database

### 6. Seeding System (src/seeding/)

**Base Seeder Class (src/seeding/seeder.py):**

- `Seeder`: Abstract base class for all seeders
  - Loads Blizzard API credentials from environment
  - `run()`: Execute seeding with session management
  - `seed()`: Abstract method implemented by subclasses

**SeederOrchestrator:**

- `should_run_seeders()`: Check if any seeders need to run based on SeederStatus
- `mark_seeder_complete()`: Update seeder completion status
- `run_initial_seeding()`: Run all seeders sequentially
  - Recipes seeder
  - Reagents seeder
  - Items seeder
  - Uses BenchmarkManager for performance tracking

**RecipeSeeder (src/seeding/recipes.py):**

- Fetches all professions from Blizzard API
- Iterates through skill tiers and categories
- Processes each recipe with faction handling:
  - Neutral: Single entry
  - Alliance/Horde: Separate entries for each faction
- Batch inserts recipes using RecipeRepository

**ReagentSeeder (src/seeding/reagents.py):**

- Processes recipes to extract reagents
- Handles required and optional reagents
- Creates faction-specific entries
- Validates reagents against existing recipes before insertion
- Batch inserts using ReagentRepository

**ItemSeeder (src/seeding/items.py):**

- Searches items by ID in batches of 1000
- Processes item metadata
- Batch inserts items

### 7. Main Service Entry Point (src/main.py)

**SchedulerService:**

- Orchestrates all system components
- `run_initial_seeding()`: Run seeding in separate thread
- `start_services()`: Main service startup
  1. Initialize database partitions
  2. Run initial seeding
  3. Start continuous scraping
- `stop_services()`: Graceful shutdown

**Signal Handling:**

- SIGINT and SIGTERM handlers for graceful shutdown
- Logs signal reception location

### 8. Database Connection (src/repository/database.py)

- `get_engine()`: Returns SQLAlchemy engine
- `get_session()`: Creates new database session
- `db_session()`: Context manager for automatic commit/rollback

## Component Relationships

### Data Flow - Auction Collection:

```
Blizzard API → BlizzardAPI.get_commodities() → AuctionCollector.collect_snapshot_for_region()
  ↓
AuctionRepository.batch_insert() → AuctionSnapshotEU/US table
  ↓
Commodity statistics calculation → EUCommodityPriceStats/USCommodityPriceStats table
  ↓
WoW Token price → EUTokenPrice/USTokenPrice table
```

### Data Flow - Seeding:

```
Blizzard API → RecipeSeeder/ReagentSeeder/ItemSeeder
  ↓
RecipeRepository/ReagentRepository/ItemRepository
  ↓
Recipe/Reagent/Item tables
  ↓
SeederStatus table (completion tracking)
```

### Service Orchestration:

```
SchedulerService (main.py)
  ├── SeederOrchestrator
  │   ├── RecipeSeeder
  │   ├── ReagentSeeder
  │   └── ItemSeeder
  ├── ScraperOrchestrator
  │   ├── AuctionCollector (EU)
  │   └── AuctionCollector (US)
  └── PartitionManagerService
```

### Repository Pattern:

```
Models (SQLAlchemy) ← Repositories ← Services/Seeders/Collectors
  ↓
PostgreSQL Database
```

## Key Design Patterns

1. **Repository Pattern**: Data access abstraction through repository classes
2. **Orchestrator Pattern**: High-level service coordination
3. **Context Manager**: Database session management with automatic cleanup
4. **Batch Processing**: Chunked inserts to avoid database limits
5. **Caching**: In-memory caching of API responses to avoid redundant requests
6. **Change Detection**: HTTP 304 Not Modified handling for efficient polling
7. **Partitioning**: Time-based table partitioning for auction data
8. **Benchmarking**: Performance tracking for all major operations
