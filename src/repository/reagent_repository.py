from typing import Any

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from models.models import Reagent, Recipe


class ReagentRepository:
    def __init__(self, session: Session):
        self.session = session

    def batch_insert(
        self, reagents: list[dict[str, Any]], chunk_size: int = 1000
    ) -> None:
        """Insert multiple reagent records into the database in chunks."""
        if not reagents:
            return

        # Filter out reagents that don't have corresponding recipes
        valid_reagents = self._filter_valid_reagents(reagents)

        for i in range(0, len(valid_reagents), chunk_size):
            chunk = valid_reagents[i : i + chunk_size]
            stmt = insert(Reagent).values(chunk)
            stmt = stmt.on_conflict_do_nothing()
            self.session.execute(stmt)

    def _filter_valid_reagents(
        self, reagents: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Filter reagents to only include those with valid recipe references."""
        if not reagents:
            return []

        # Get all unique (recipe_id, faction) combinations from reagents
        recipe_keys = {(r["recipe_id"], r["faction"]) for r in reagents}

        # Query existing recipes
        existing_recipes = set()
        for recipe_id, faction in recipe_keys:
            exists = (
                self.session.query(Recipe)
                .filter(Recipe.id == recipe_id, Recipe.faction == faction)
                .first()
            )
            if exists:
                existing_recipes.add((recipe_id, faction))

        # Filter reagents to only include those with existing recipes
        valid_reagents = [
            r for r in reagents if (r["recipe_id"], r["faction"]) in existing_recipes
        ]

        # Log filtered out reagents for debugging
        filtered_count = len(reagents) - len(valid_reagents)
        if filtered_count > 0:
            print(
                f"Filtered out {filtered_count} reagents with missing recipe references"
            )

        return valid_reagents

    def get_reagents_by_recipe(self, recipe_id: int) -> list[Reagent]:
        """Get all reagents for a specific recipe."""
        return self.session.query(Reagent).filter(Reagent.recipe_id == recipe_id).all()

    def get_optional_reagents_by_recipe(self, recipe_id: int) -> list[Reagent]:
        """Get all optional reagents for a specific recipe."""
        return (
            self.session.query(Reagent)
            .filter(Reagent.recipe_id == recipe_id, Reagent.optional.is_(True))
            .all()
        )

    def get_required_reagents_by_recipe(self, recipe_id: int) -> list[Reagent]:
        """Get all required reagents for a specific recipe."""
        return (
            self.session.query(Reagent)
            .filter(Reagent.recipe_id == recipe_id, Reagent.optional.is_(False))
            .all()
        )
