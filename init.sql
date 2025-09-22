-- Ironforge Database Initialization Script
-- This script creates all necessary tables and sets up initial partitioning

-- Create items table
CREATE TABLE IF NOT EXISTS items (
    id INTEGER NOT NULL PRIMARY KEY,
    item_name VARCHAR(255) NOT NULL,
    item_level SMALLINT NOT NULL,
    item_class VARCHAR(50) NOT NULL,
    item_subclass VARCHAR(50) NOT NULL,
    inventory_type VARCHAR(50) NOT NULL,
    is_equippable BOOLEAN NOT NULL DEFAULT FALSE,
    is_stackable BOOLEAN NOT NULL DEFAULT FALSE,
    quality VARCHAR(10) NOT NULL
);

-- Create EU commodity price stats table
CREATE TABLE IF NOT EXISTS eu_commodity_price_stats (
    item_id INTEGER NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    min_price BIGINT,
    max_price BIGINT,
    mean_price DOUBLE PRECISION,
    median_price DOUBLE PRECISION,
    total_quantity BIGINT,
    num_auctions INTEGER,
    estimated_sales INTEGER,
    new_listings INTEGER,
    PRIMARY KEY (item_id, timestamp)
) PARTITION BY RANGE (timestamp);

-- Create US commodity price stats table
CREATE TABLE IF NOT EXISTS us_commodity_price_stats (
    item_id INTEGER NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    min_price BIGINT,
    max_price BIGINT,
    mean_price DOUBLE PRECISION,
    median_price DOUBLE PRECISION,
    total_quantity BIGINT,
    num_auctions INTEGER,
    estimated_sales INTEGER,
    new_listings INTEGER,
    PRIMARY KEY (item_id, timestamp)
) PARTITION BY RANGE (timestamp);

-- Create EU token price table
CREATE TABLE IF NOT EXISTS eu_token_price (
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    price BIGINT NOT NULL,
    PRIMARY KEY (timestamp)
) PARTITION BY RANGE (timestamp);

-- Create US token price table
CREATE TABLE IF NOT EXISTS us_token_price (
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    price BIGINT NOT NULL,
    PRIMARY KEY (timestamp)
) PARTITION BY RANGE (timestamp);

-- Create recipes table
CREATE TABLE IF NOT EXISTS recipes (
    id INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    profession VARCHAR(255) NOT NULL,
    skill_tier VARCHAR(255) NOT NULL,
    crafted_item_id INTEGER,
    faction VARCHAR(8) NOT NULL,
    data JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, faction)
);

-- Create reagents table
CREATE TABLE IF NOT EXISTS reagents (
    recipe_id INTEGER NOT NULL,
    faction VARCHAR(8) NOT NULL,
    item_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    optional BOOLEAN NOT NULL,
    PRIMARY KEY (recipe_id, faction, item_id),
    FOREIGN KEY (recipe_id, faction) REFERENCES recipes(id, faction)
);

-- Create seeder_status table
CREATE TABLE IF NOT EXISTS seeder_status (
    seeder_type VARCHAR(50) PRIMARY KEY,
    completed BOOLEAN NOT NULL DEFAULT FALSE,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create scraper_logs table
CREATE TABLE IF NOT EXISTS scraper_logs (
    id SERIAL PRIMARY KEY,
    region VARCHAR(2) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL,
    last_modified TIMESTAMP,
    error_message VARCHAR(500),
    poll_attempts INTEGER NOT NULL DEFAULT 1
);

-- Create benchmarks table
CREATE TABLE IF NOT EXISTS benchmarks (
    id SERIAL PRIMARY KEY,
    operation_type VARCHAR(50) NOT NULL,
    operation_name VARCHAR(100) NOT NULL,
    region VARCHAR(2),
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    duration_seconds REAL NOT NULL,
    record_count INTEGER,
    status VARCHAR(20) NOT NULL,
    error_message VARCHAR(500),
    extra_data JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create partitioned auction_snapshots_eu table
CREATE TABLE IF NOT EXISTS auction_snapshots_eu (
    auction_id BIGINT NOT NULL,
    item_id INTEGER NOT NULL,
    unit_price BIGINT NOT NULL,
    quantity INTEGER NOT NULL,
    time_left VARCHAR(1) NOT NULL,
    snapshot_time TIMESTAMP NOT NULL,
    PRIMARY KEY (auction_id, snapshot_time)
) PARTITION BY RANGE (snapshot_time);

-- Create partitioned auction_snapshots_us table
CREATE TABLE IF NOT EXISTS auction_snapshots_us (
    auction_id BIGINT NOT NULL,
    item_id INTEGER NOT NULL,
    unit_price BIGINT NOT NULL,
    quantity INTEGER NOT NULL,
    time_left VARCHAR(1) NOT NULL,
    snapshot_time TIMESTAMP NOT NULL,
    PRIMARY KEY (auction_id, snapshot_time)
) PARTITION BY RANGE (snapshot_time);

-- Function to create partition for a given table and date range
CREATE OR REPLACE FUNCTION create_partition(
    parent_table TEXT,
    partition_name TEXT,
    start_date DATE,
    end_date DATE
) RETURNS VOID AS $$
BEGIN
    EXECUTE format('CREATE TABLE IF NOT EXISTS %I PARTITION OF %I FOR VALUES FROM (%L) TO (%L)',
                   partition_name, parent_table, start_date, end_date);
    
    -- Create indexes on the partition
    IF parent_table LIKE '%auction_snapshots%' THEN
        EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON %I (item_id, snapshot_time)', 
                       partition_name || '_item_time_idx', partition_name);
        EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON %I (snapshot_time)', 
                       partition_name || '_time_idx', partition_name);
    ELSIF parent_table LIKE '%commodity_price_stats%' THEN
        EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON %I (item_id, timestamp)', 
                       partition_name || '_item_time_idx', partition_name);
        EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON %I (timestamp)', 
                       partition_name || '_time_idx', partition_name);
    ELSIF parent_table LIKE '%token_price%' THEN
        EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON %I (timestamp)', 
                       partition_name || '_time_idx', partition_name);
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Function to create partitions for the next N months
CREATE OR REPLACE FUNCTION create_monthly_partitions(months_ahead INTEGER DEFAULT 6) RETURNS VOID AS $$
DECLARE
    current_month DATE;
    next_month DATE;
    partition_suffix TEXT;
    i INTEGER;
BEGIN
    -- Start from the beginning of current month
    current_month := date_trunc('month', CURRENT_DATE);
    
    FOR i IN 0..months_ahead LOOP
        next_month := current_month + INTERVAL '1 month';
        partition_suffix := to_char(current_month, 'YYYY_MM');
        
        -- Create partitions for regional auction snapshot tables
        PERFORM create_partition('auction_snapshots_eu', 'auction_snapshots_eu_' || partition_suffix, current_month, next_month);
        PERFORM create_partition('auction_snapshots_us', 'auction_snapshots_us_' || partition_suffix, current_month, next_month);
        
        -- Create partitions for regional commodity price stats tables
        PERFORM create_partition('eu_commodity_price_stats', 'eu_commodity_price_stats_' || partition_suffix, current_month, next_month);
        PERFORM create_partition('us_commodity_price_stats', 'us_commodity_price_stats_' || partition_suffix, current_month, next_month);
        
        -- Create partitions for regional token price tables
        PERFORM create_partition('eu_token_price', 'eu_token_price_' || partition_suffix, current_month, next_month);
        PERFORM create_partition('us_token_price', 'us_token_price_' || partition_suffix, current_month, next_month);
        
        current_month := next_month;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Function to check and create future partitions if needed
CREATE OR REPLACE FUNCTION ensure_future_partitions() RETURNS VOID AS $$
DECLARE
    max_partition_date DATE;
    months_to_create INTEGER;
BEGIN
    -- Find the latest partition end date by checking partition constraints
    SELECT MAX(matches[1]::DATE) INTO max_partition_date
    FROM pg_constraint c
    JOIN pg_class t ON c.conrelid = t.oid
    LEFT JOIN LATERAL regexp_matches(pg_get_expr(c.conbin, c.conrelid), 'TO \(''([^'']+)''.*\)') AS matches ON true
    WHERE (t.relname LIKE '%auction_snapshots_eu%' 
           OR t.relname LIKE '%auction_snapshots_us%'
           OR t.relname LIKE '%eu_commodity_price_stats%'
           OR t.relname LIKE '%us_commodity_price_stats%'
           OR t.relname LIKE '%eu_token_price%'
           OR t.relname LIKE '%us_token_price%')
    AND c.contype = 'c'
    AND pg_get_expr(c.conbin, c.conrelid) LIKE '%FOR VALUES FROM%'
    AND matches IS NOT NULL;
    
    -- If no partitions exist or we need more, create them
    IF max_partition_date IS NULL OR max_partition_date < (CURRENT_DATE + INTERVAL '3 months') THEN
        PERFORM create_monthly_partitions(6);
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Create initial partitions for the next 6 months
SELECT create_monthly_partitions(6);

-- Create indexes on non-partitioned tables
CREATE INDEX IF NOT EXISTS idx_recipes_profession ON recipes(profession);
CREATE INDEX IF NOT EXISTS idx_recipes_faction ON recipes(faction);
CREATE INDEX IF NOT EXISTS idx_recipes_crafted_item_id ON recipes(crafted_item_id);

CREATE INDEX IF NOT EXISTS idx_reagents_recipe_faction ON reagents(recipe_id, faction);
CREATE INDEX IF NOT EXISTS idx_reagents_item_id ON reagents(item_id);

CREATE INDEX IF NOT EXISTS idx_scraper_logs_region_timestamp ON scraper_logs(region, timestamp);
CREATE INDEX IF NOT EXISTS idx_scraper_logs_status ON scraper_logs(status);

-- Create a view to easily check partition information
CREATE OR REPLACE VIEW partition_info AS
SELECT 
    schemaname,
    tablename as partition_name,
    pg_get_expr(c.conbin, c.conrelid) as partition_constraint
FROM pg_tables pt
JOIN pg_class t ON t.relname = pt.tablename
JOIN pg_constraint c ON c.conrelid = t.oid
WHERE pt.tablename LIKE '%auction_snapshots_%' 
   OR pt.tablename LIKE '%commodity_summaries_%'
   AND c.contype = 'c'
   AND pg_get_expr(c.conbin, c.conrelid) LIKE '%FOR VALUES FROM%'
ORDER BY schemaname, tablename;

-- Grant necessary permissions (adjust as needed for your setup)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_app_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_app_user;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO your_app_user;
