-- TODO: Add monthly partitioning to the auction_snapshots table and drop old partitions

-- Create recipes table
CREATE TABLE IF NOT EXISTS recipes (
    id INTEGER,
    name VARCHAR(255) NOT NULL,
    profession VARCHAR(255) NOT NULL,
    skill_tier VARCHAR(255) NOT NULL,
    crafted_item_id INTEGER,
    faction VARCHAR(8),
    data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, faction)
);

-- Create recipe ingredients table for fast lookups
CREATE TABLE IF NOT EXISTS reagents (
    recipe_id INTEGER,
    item_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    optional BOOLEAN NOT NULL,
    PRIMARY KEY (recipe_id, item_id)
);

-- Raw auction data
CREATE TABLE IF NOT EXISTS auction_snapshots (
    auction_id BIGINT,
    item_id INTEGER,
    unit_price BIGINT,
    quantity INTEGER,
    time_left VARCHAR(1),
    snapshot_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (auction_id, snapshot_time)
) PARTITION BY RANGE (snapshot_time);

-- January 2025 Partition
CREATE TABLE auction_snapshots_202501 PARTITION OF auction_snapshots
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

-- Processed commodity data
CREATE TABLE IF NOT EXISTS commodity_summaries (
    item_id INTEGER,
    minimum_price BIGINT,
    median_price BIGINT,
    total_quantity INTEGER,
    new_listings INTEGER,
    estimated_sales INTEGER,
    summary_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (item_id, summary_time)
) PARTITION BY RANGE (summary_time);

-- January 2025 Partition
CREATE TABLE commodity_summaries_202501 PARTITION OF commodity_summaries
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_recipe_ingredients_item_id ON reagents(item_id);
CREATE INDEX IF NOT EXISTS idx_recipes_profession ON recipes(profession);
CREATE INDEX IF NOT EXISTS idx_recipes_name ON recipes(name);
CREATE INDEX IF NOT EXISTS idx_recipes_crafted_item ON recipes(crafted_item_id);
CREATE INDEX IF NOT EXISTS idx_auction_snapshots_item ON auction_snapshots(item_id);
CREATE INDEX IF NOT EXISTS idx_auction_snapshots_item_price ON auction_snapshots(item_id, unit_price);
CREATE INDEX IF NOT EXISTS idx_commodity_summaries_item ON commodity_summaries(item_id);

-- Add timestamp trigger
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_recipes_timestamp
    BEFORE UPDATE ON recipes
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();