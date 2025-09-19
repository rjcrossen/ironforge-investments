import json
from typing import Any

from sqlalchemy.orm import Session

from repository.recipe_repository import RecipeRepository
from scraper.blizzard_api_utils import BlizzardAPI, BlizzardConfig
from seeding.seeder import Seeder


class RecipeSeeder(Seeder):
    def _process_recipe(
        self, recipe_info: dict, profession_name: str, tier_name: str
    ) -> list[dict[str, Any]]:
        """Process recipe info and return list of recipe dictionaries."""
        recipes = []

        if "crafted_item" in recipe_info:
            recipes.append(
                {
                    "id": recipe_info["id"],
                    "name": recipe_info["name"],
                    "profession": profession_name,
                    "skill_tier": tier_name,
                    "crafted_item_id": recipe_info["crafted_item"]["id"],
                    "faction": "Neutral",
                    "data": json.dumps(recipe_info),
                }
            )
        elif (
            "alliance_crafted_item" in recipe_info
            and "horde_crafted_item" in recipe_info
        ):
            recipes.extend(
                [
                    {
                        "id": recipe_info["id"],
                        "name": recipe_info["name"],
                        "profession": profession_name,
                        "skill_tier": tier_name,
                        "crafted_item_id": recipe_info["alliance_crafted_item"]["id"],
                        "faction": "Alliance",
                        "data": json.dumps(recipe_info),
                    },
                    {
                        "id": recipe_info["id"],
                        "name": recipe_info["name"],
                        "profession": profession_name,
                        "skill_tier": tier_name,
                        "crafted_item_id": recipe_info["horde_crafted_item"]["id"],
                        "faction": "Horde",
                        "data": json.dumps(recipe_info),
                    },
                ]
            )
        else:
            recipes.append(
                {
                    "id": recipe_info["id"],
                    "name": recipe_info["name"],
                    "profession": profession_name,
                    "skill_tier": tier_name,
                    "crafted_item_id": None,
                    "faction": "Neutral",
                    "data": json.dumps(recipe_info),
                }
            )

        return recipes

    def seed(self, session: Session) -> None:
        """Seed recipes data using the repository pattern."""
        config = BlizzardConfig(
            client_id=self.client_id, client_secret=self.client_secret, region="eu"
        )
        api = BlizzardAPI(config)
        recipe_repo = RecipeRepository(session)

        professions = api.get_professions()

        for profession in professions:
            print(f"Processing profession: {profession['name']}")

            profession_info = api.get_profession_info(profession["key"]["href"])

            if (
                not isinstance(profession_info, dict)
                or "skill_tiers" not in profession_info
            ):
                continue

            recipe_batch = []

            for tier in profession_info["skill_tiers"]:
                print(f"  Processing tier: {tier['name']}")

                tier_data = api.get_skill_tier_details(tier["key"]["href"])

                if not isinstance(tier_data, dict) or "categories" not in tier_data:
                    continue

                for category in tier_data["categories"]:
                    print(f"    Processing category: {category['name']}")

                    for recipe in category["recipes"]:
                        recipe_info = api.get_recipe_info(recipe["key"]["href"])

                        if not isinstance(recipe_info, dict):
                            continue

                        recipes = self._process_recipe(
                            recipe_info, profession["name"], tier["name"]
                        )
                        recipe_batch.extend(recipes)

                        for recipe_data in recipes:
                            print(
                                f"      Recipe: {recipe_data['name']} "
                                f"(ID: {recipe_data['crafted_item_id']}, "
                                f"Faction: {recipe_data['faction']})"
                            )

            if recipe_batch:
                recipe_repo.batch_insert(recipe_batch)
                session.commit()
                print(f"Inserted {len(recipe_batch)} recipes for {profession['name']}")
