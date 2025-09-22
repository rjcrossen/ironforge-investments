from typing import Any
from sqlalchemy import insert
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session
from sqlalchemy import DDL

from models.models import Item
from scraper.blizzard_api_utils import BlizzardAPI, BlizzardConfig
from seeding.seeder import Seeder

class ItemSeeder(Seeder):
    def seed(self, session: Session) -> None:
        """Seed item data using the repository pattern."""
        config = BlizzardConfig(
            client_id=self.client_id, client_secret=self.client_secret, region="eu"
        )
        api = BlizzardAPI(config)

        # Fetch items in chunks of 1000
        starting_id = 1
        while True:
            items = api.search_items_by_id(starting_id=starting_id)
            if not items:
                print(f"No more items found starting from ID {starting_id}.")
                break

            # Process and insert items into the database
            item_values = []
            for item in items:
                #print(item)  # Debugging line to see the item structure
                item = item["data"]
                try:
                    item_data = {
                        "id": item["id"],
                        "name": item["name"]["en_US"],  # Added ["en_US"]
                        "level": item["level"],
                        "class_": item["item_class"]["name"]["en_US"],
                        "subclass": item["item_subclass"]["name"]["en_US"],
                        "inventory_type": item["inventory_type"]["name"]["en_US"],
                        "is_equippable": item["is_equippable"],  # Changed from equippable
                        "is_stackable": item["is_stackable"],    # Changed from stackable
                        "quality": item["quality"]["name"]["en_US"]
                    }
                    item_values.append(item_data)
                except KeyError as e:
                    print(f"Skipping item due to missing field: {e}")
                    continue

            if not item_values:
                print("No valid items to insert")
                break

            stmt = pg_insert(Item).values(item_values)
            stmt = stmt.on_conflict_do_nothing()
            session.execute(stmt)
            session.commit()
            
            starting_id = item_values[-1]["id"] + 1
            
            print(f"Inserted {len(item_values)} items, next starting ID: {starting_id}")
        
        # Create a commodities view after seeding items
        try:
            # First drop the view if it exists
            ddl = DDL("DROP VIEW IF EXISTS commodities")
            session.execute(ddl)
            print("Hello world")
            
            # Then create the new view
            ddl = DDL("""
                CREATE OR REPLACE VIEW commodities AS
                SELECT id, name, level, "class" AS class_, subclass, inventory_type, quality
                FROM items
                WHERE is_stackable = true;
            """)
            session.execute(ddl)
            
            session.commit()
            print("Successfully created commodities view")
        except Exception as e:
            print(f"Error creating commodities view: {e}")
            session.rollback()