from typing import Any

from sqlalchemy.orm import Session

from repository.reagent_repository import ReagentRepository
from scraper.blizzard_api_utils import BlizzardAPI, BlizzardConfig
from seeding.seeder import Seeder


class ReagentSeeder(Seeder):
    def _process_reagents(self, recipe_info: dict) -> list[dict[str, Any]]:
        """Process recipe info and return list of reagent dictionaries."""
        reagents_list = []

        # Determine faction(s) for this recipe
        factions = []
        if "crafted_item" in recipe_info:
            factions = ["Neutral"]
        elif (
            "alliance_crafted_item" in recipe_info
            and "horde_crafted_item" in recipe_info
        ):
            factions = ["Alliance", "Horde"]
        else:
            factions = ["Neutral"]

        # Create reagents for each faction
        for faction in factions:
            if "reagents" in recipe_info:
                for reagent in recipe_info["reagents"]:
                    reagents_list.append(
                        {
                            "recipe_id": recipe_info["id"],
                            "faction": faction,
                            "item_id": reagent["reagent"]["id"],
                            "quantity": reagent["quantity"],
                            "optional": False,
                        }
                    )

            if "optional_reagents" in recipe_info:
                for reagent in recipe_info["optional_reagents"]:
                    reagents_list.append(
                        {
                            "recipe_id": recipe_info["id"],
                            "faction": faction,
                            "item_id": reagent["reagent"]["id"],
                            "quantity": reagent["quantity"],
                            "optional": True,
                        }
                    )

        return reagents_list

    def seed(self, session: Session) -> None:
        """Seed reagents data using the repository pattern."""
        config = BlizzardConfig(
            client_id=self.client_id, client_secret=self.client_secret, region="eu"
        )
        api = BlizzardAPI(config)
        reagent_repo = ReagentRepository(session)

        professions = api.get_professions()

        for profession in professions:
            print(f"Processing profession: {profession['name']}")

            profession_info = api.get_profession_info(profession["key"]["href"])

            if (
                not isinstance(profession_info, dict)
                or "skill_tiers" not in profession_info
            ):
                continue

            reagent_batch = []

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

                        reagents = self._process_reagents(recipe_info)
                        if reagents:
                            print(
                                f"      Recipe {recipe_info['id']}: {len(reagents)} reagents"
                            )
                        reagent_batch.extend(reagents)

            if reagent_batch:
                try:
                    reagent_repo.batch_insert(reagent_batch)
                    session.commit()
                    print(
                        f"Inserted reagents for {profession['name']} (processed {len(reagent_batch)} reagents)"
                    )
                except Exception as e:
                    session.rollback()
                    print(f"Error inserting reagents for {profession['name']}: {e}")
                    raise


def get_all_reagents():
    """Legacy function for backward compatibility."""
    seeder = ReagentSeeder()
    seeder.run()
