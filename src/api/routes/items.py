"""
Item-rfrom api.dependencies import get_db

router = APIRouter(prefix="/items", tags=["items"])outes
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from repository.database import db_session
from repository.item_repository import ItemRepository
from api.schemas import ItemResponse

router = APIRouter(prefix="/items", tags=["items"])


def get_db():
    """Dependency for database session."""
    session = db_session().__enter__()
    try:
        yield session
    finally:
        session.__exit__(None, None, None)


@router.get("/{item_id}", response_model=ItemResponse)
def get_item(item_id: int, db: Session = Depends(get_db)):
    """Get item by ID"""
    repo = ItemRepository(db)
    item = repo.get_item_by_id(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.get("/", response_model=List[ItemResponse])
def get_items(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """Get all items with pagination"""
    repo = ItemRepository(db)
    return repo.get_all_items()[skip : skip + limit]