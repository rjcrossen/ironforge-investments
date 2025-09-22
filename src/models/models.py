from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKeyConstraint,
    Integer,
    String,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class EUCommodityPriceStats(Base):
    """Tracks price statistics for EU commodities over time"""
    __tablename__ = "eu_commodity_price_stats"

    item_id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, primary_key=True, nullable=False, server_default=func.now())
    
    # Price statistics
    min_price = Column(BigInteger)
    max_price = Column(BigInteger)
    mean_price = Column(Float)
    median_price = Column(Float)
    
    # Quantity statistics
    total_quantity = Column(BigInteger)
    num_auctions = Column(Integer)  # Number of distinct auctions for this item
    estimated_sales = Column(Integer)  # Estimated number of items sold since last snapshot
    new_listings = Column(Integer)  # Number of new items listed since last snapshot

class USCommodityPriceStats(Base):
    """Tracks price statistics for US commodities over time"""
    __tablename__ = "us_commodity_price_stats"

    item_id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, primary_key=True, nullable=False, server_default=func.now())
    
    # Price statistics
    min_price = Column(BigInteger)
    max_price = Column(BigInteger)
    mean_price = Column(Float)
    median_price = Column(Float)
    
    # Quantity statistics
    total_quantity = Column(BigInteger)
    num_auctions = Column(Integer)  # Number of distinct auctions for this item
    estimated_sales = Column(Integer)  # Estimated number of items sold since last snapshot
    new_listings = Column(Integer)  # Number of new items listed since last snapshot


class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    profession = Column(String(255), nullable=False)
    skill_tier = Column(String(255), nullable=False)
    crafted_item_id = Column(Integer)
    faction = Column(String(8), primary_key=True)
    data = Column(JSON, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Reagent(Base):
    __tablename__ = "reagents"

    recipe_id = Column(Integer, primary_key=True)
    faction = Column(String(8), primary_key=True)
    item_id = Column(Integer, primary_key=True)
    quantity = Column(Integer, nullable=False)
    optional = Column(Boolean, nullable=False)

    # Composite foreign key to reference the recipe's composite primary key
    __table_args__ = (
        ForeignKeyConstraint(
            ["recipe_id", "faction"], ["recipes.id", "recipes.faction"]
        ),
    )


class AuctionSnapshotEU(Base):
    __tablename__ = "auction_snapshots_eu"

    auction_id = Column(BigInteger, primary_key=True)
    item_id = Column(Integer, nullable=False)
    unit_price = Column(BigInteger, nullable=False)
    quantity = Column(Integer, nullable=False)
    time_left = Column(String(1), nullable=False)
    snapshot_time = Column(DateTime, primary_key=True)


class AuctionSnapshotUS(Base):
    __tablename__ = "auction_snapshots_us"

    auction_id = Column(BigInteger, primary_key=True)
    item_id = Column(Integer, nullable=False)
    unit_price = Column(BigInteger, nullable=False)
    quantity = Column(Integer, nullable=False)
    time_left = Column(String(1), nullable=False)
    snapshot_time = Column(DateTime, primary_key=True)


class SeederStatus(Base):
    __tablename__ = "seeder_status"

    seeder_type = Column(String(50), primary_key=True)
    completed = Column(Boolean, nullable=False, default=False)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class ScraperLog(Base):
    __tablename__ = "scraper_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    region = Column(String(2), nullable=False)  # 'eu' or 'us'
    timestamp = Column(DateTime, nullable=False, server_default=func.now())
    status = Column(String(20), nullable=False)  # 'success', 'failed', 'no_change'
    last_modified = Column(DateTime, nullable=True)
    error_message = Column(String(500), nullable=True)
    poll_attempts = Column(Integer, nullable=False, default=1)


class Benchmark(Base):
    __tablename__ = "benchmarks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    operation_type = Column(
        String(50), nullable=False
    )  # 'snapshot', 'seeding', 'summary'
    operation_name = Column(
        String(100), nullable=False
    )  # 'eu_snapshot', 'recipe_seeding', etc.
    region = Column(
        String(2), nullable=True
    )  # 'eu', 'us' (null for non-regional operations)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    duration_seconds = Column(Float, nullable=False)
    record_count = Column(Integer, nullable=True)  # Number of records processed
    status = Column(String(20), nullable=False)  # 'success', 'failed', 'partial'
    error_message = Column(String(500), nullable=True)
    extra_data = Column(
        JSON, nullable=True
    )  # Additional context like API response times
    created_at = Column(DateTime, server_default=func.now())


class EUTokenPrice(Base):
    """Tracks WoW Token prices in the EU region over time"""
    __tablename__ = "eu_token_price"

    timestamp = Column(DateTime, primary_key=True, nullable=False, server_default=func.now())
    price = Column(BigInteger, nullable=False)


class USTokenPrice(Base):
    """Tracks WoW Token prices in the US region over time"""
    __tablename__ = "us_token_price"

    timestamp = Column(DateTime, primary_key=True, nullable=False, server_default=func.now())
    price = Column(BigInteger, nullable=False)


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    level = Column(Integer, nullable=False)
    class_ = Column(String(50), name="class", nullable=False)
    subclass = Column(String(50), nullable=False)
    inventory_type = Column(String(50), nullable=False)
    is_equippable = Column(Boolean, nullable=False, default=False)
    is_stackable = Column(Boolean, nullable=False, default=False)
    quality = Column(String(10), nullable=False)
