"""
Commodity-related API routes
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_
from sqlalchemy.orm import Session

from api.schemas import CommodityStatsResponse
from models.models import EUCommodityPriceStats, USCommodityPriceStats
from api.dependencies import get_db

router = APIRouter(prefix="/commodities", tags=["commodities"])


@router.get("/eu/{item_id}", response_model=List[CommodityStatsResponse])
def get_eu_commodity_stats(
    item_id: int,
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
):
    """Get EU commodity price statistics for an item"""
    query = db.query(EUCommodityPriceStats).filter(
        EUCommodityPriceStats.item_id == item_id
    )

    if from_date:
        query = query.filter(EUCommodityPriceStats.timestamp >= from_date)
    if to_date:
        query = query.filter(EUCommodityPriceStats.timestamp <= to_date)

    stats = query.order_by(EUCommodityPriceStats.timestamp.desc()).all()
    if not stats:
        raise HTTPException(status_code=404, detail="No data found for item")
    return stats


@router.get("/us/{item_id}", response_model=List[CommodityStatsResponse])
def get_us_commodity_stats(
    item_id: int,
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
):
    """Get US commodity price statistics for an item"""
    query = db.query(USCommodityPriceStats).filter(
        USCommodityPriceStats.item_id == item_id
    )

    if from_date:
        query = query.filter(USCommodityPriceStats.timestamp >= from_date)
    if to_date:
        query = query.filter(USCommodityPriceStats.timestamp <= to_date)

    stats = query.order_by(USCommodityPriceStats.timestamp.desc()).all()
    if not stats:
        raise HTTPException(status_code=404, detail="No data found for item")
    return stats