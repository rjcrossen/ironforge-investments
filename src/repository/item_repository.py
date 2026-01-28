from models.models import Item
from sqlalchemy.orm import Session


class ItemRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_item_by_id(self, item_id: int) -> Item:
        return self.session.query(Item).filter(Item.id == item_id).first()

    def get_item_by_name(self, item_name: str) -> Item:
        return self.session.query(Item).filter(Item.item_name == item_name).first()

    def get_all_items(self) -> list[Item]:
        return self.session.query(Item).all()
