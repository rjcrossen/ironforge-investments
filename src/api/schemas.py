"""
Pydantic models for API request/response validation.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ItemResponse(BaseModel):
    id: int
    item_name: str
    item_level: int
    item_class: str
    item_subclass: str
    inventory_type: str
    quality: str
    is_stackable: bool

    class Config:   
        from_attributes = True


class CommodityStatsResponse(BaseModel):
    item_id: int
    timestamp: datetime
    min_price: int
    max_price: int
    mean_price: float
    median_price: float
    total_quantity: int
    num_auctions: int
    estimated_sales: Optional[int]
    new_listings: Optional[int]

    class Config:
        from_attributes = True


class TokenPriceResponse(BaseModel):
    timestamp: datetime
    price: int

    class Config:
        from_attributes = True