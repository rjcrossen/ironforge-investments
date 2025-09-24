"""
Token price-related API routes
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.schemas import TokenPriceResponse
from models.models import EUTokenPrice, USTokenPrice
from api.dependencies import get_db

router = APIRouter(prefix="/token", tags=["token"])


@router.get("/eu", response_model=List[TokenPriceResponse])
def get_eu_token_prices(
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
):
    """Get EU token price history"""
    query = db.query(EUTokenPrice)

    if from_date:
        query = query.filter(EUTokenPrice.timestamp >= from_date)
    if to_date:
        query = query.filter(EUTokenPrice.timestamp <= to_date)

    prices = query.order_by(EUTokenPrice.timestamp.desc()).all()
    if not prices:
        raise HTTPException(status_code=404, detail="No token price data found")
    return prices


@router.get("/us", response_model=List[TokenPriceResponse])
def get_us_token_prices(
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
):
    """Get US token price history"""
    query = db.query(USTokenPrice)

    if from_date:
        query = query.filter(USTokenPrice.timestamp >= from_date)
    if to_date:
        query = query.filter(USTokenPrice.timestamp <= to_date)

    prices = query.order_by(USTokenPrice.timestamp.desc()).all()
    if not prices:
        raise HTTPException(status_code=404, detail="No token price data found")
    return prices