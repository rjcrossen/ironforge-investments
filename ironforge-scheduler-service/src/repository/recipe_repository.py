from typing import Any
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session
from models.models import Recipe


class RecipeRepository:
    def __init__(self, session: Session):
        self.session = session

    def batch_insert(self, recipes: list[dict[str, Any]], chunk_size: int = 1000) -> None:
        """Insert multiple recipe records into the database in chunks."""
        if not recipes:
            return

        for i in range(0, len(recipes), chunk_size):
            chunk = recipes[i : i + chunk_size]
            stmt = insert(Recipe).values(chunk)
            stmt = stmt.on_conflict_do_nothing()
            self.session.execute(stmt)

    def get_recipe_by_id_and_faction(self, recipe_id: int, faction: str) -> Recipe | None:
        """Get a specific recipe by ID and faction."""
        return self.session.query(Recipe).filter(Recipe.id == recipe_id, Recipe.faction == faction).first()

    def get_all_recipes(self) -> list[Recipe]:
        """Get all recipes from the database."""
        return self.session.query(Recipe).all()
