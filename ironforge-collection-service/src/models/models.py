from sqlalchemy import (JSON, Boolean, Column, DateTime, ForeignKey, Integer,
                        String)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class Recipe(Base):
    __tablename__ = 'recipes'
    
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
    __tablename__ = 'reagents'
    
    recipe_id = Column(Integer, primary_key=True)
    faction = Column(String(8), ForeignKey('recipes.faction'))
    item_id = Column(Integer, primary_key=True)
    quantity = Column(Integer, nullable=False)
    optional = Column(Boolean, nullable=False)
    
class AuctionSnapshot(Base):
    __tablename__ = 'auction_snapshots'
    
    auction_id = Column(Integer, primary_key=True)
    item_id = Column(Integer, nullable=False)
    unit_price = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False)
    time_left = Column(String(1), nullable=False)
    snapshot_time = Column(DateTime, primary_key=True)
        
class CommoditySummary(Base):
    __tablename__ = 'commodity_summaries'
    
    item_id = Column(Integer, primary_key=True)
    minimum_price = Column(Integer, nullable=False)
    median_price = Column(Integer, nullable=False)
    total_quantity = Column(Integer, nullable=False)
    new_listings = Column(Integer, nullable=False)
    estimated_sales = Column(Integer, nullable=False)
    summary_time = Column(DateTime, primary_key=True)
