from sqlalchemy.orm import Session
import neo4j
from repository.item_repository import ItemRepository
from repository.recipe_repository import RecipeRepository
from repository.reagent_repository import ReagentRepository
from seeding.seeder import Seeder
from scraper.blizzard_api_utils import BlizzardAPI, BlizzardConfig

class GraphSeeder(Seeder):
    BATCH_SIZE = 1000

    def seed(self, pg_session: Session) -> None:
        """Seed graph data using Neo4j."""
        # Get all repositories and data
        item_repo = ItemRepository(pg_session)
        recipe_repo = RecipeRepository(pg_session)
        reagent_repo = ReagentRepository(pg_session)
        
        items = item_repo.get_all_items()
        recipes = recipe_repo.get_all_recipes()
        reagents = reagent_repo.get_all_reagents()
        
        # Initialize Blizzard API
        config = BlizzardConfig(
            client_id=self.client_id,
            client_secret=self.client_secret,
            region="eu"
        )
        api = BlizzardAPI(config)
        
        # Get profession data from Blizzard API
        professions = api.get_professions()
        profession_data = []
        
        for profession in professions:
            print(f"Processing profession: {profession['name']}")
            try:
                profession_info = api.get_profession_info(profession["key"]["href"])
                
                if not isinstance(profession_info, dict) or "skill_tiers" not in profession_info:
                    print(f"Skipping profession {profession['name']}: Invalid profession info")
                    continue
                
                skill_tiers = []
                for tier in profession_info["skill_tiers"]:
                    tier_data = api.get_skill_tier_details(tier["key"]["href"])
                    if isinstance(tier_data, dict):
                        skill_tiers.append({
                            'name': tier['name'],
                            'min_skill': tier_data.get('minimum_skill', 0),
                            'max_skill': tier_data.get('maximum_skill', 300)
                        })

                profession_data.append({
                    'id': profession['id'],
                    'name': profession['name'],
                    'skill_tiers': skill_tiers
                })
                
            except Exception as e:
                print(f"Error processing profession {profession.get('name', 'Unknown')}: {str(e)}")
                continue
        
        total_items = len(items)
        total_recipes = len(recipes)
        
        # Connect to Neo4j database
        driver = neo4j.GraphDatabase.driver("bolt://neo4j:7687", auth=("neo4j", "test1234"))
        
        with driver.session() as session:
            # Clear existing Recipe, Profession, and SkillTier nodes
            session.run("""
                MATCH (n) 
                WHERE n:Recipe OR n:Profession OR n:SkillTier
                DETACH DELETE n
            """)
            print("Cleared existing Recipe, Profession, and SkillTier nodes from database")
            
            # Create Profession and SkillTier nodes
            session.run("""
                UNWIND $professions AS prof
                MERGE (p:Profession {id: prof.id})
                SET p.name = prof.name
                WITH p, prof
                UNWIND prof.skill_tiers AS tier
                MERGE (t:SkillTier {
                    profession_id: prof.id,
                    profession_name: prof.name,
                    name: tier.name
                })
                SET t.min_skill = tier.min_skill,
                    t.max_skill = tier.max_skill
                MERGE (p)-[:HAS_TIER]->(t)
            """, professions=profession_data)
            print("Created Profession and SkillTier nodes")
            
            ''' 
            # Create Item nodes in batches
            for i in range(0, total_items, self.BATCH_SIZE):
                batch_items = items[i:i + self.BATCH_SIZE]
                batch_data = [{
                    'id': item.id,
                    'name': item.name,
                    'level': item.level,
                    'item_class': getattr(item, 'class_'),
                    'subclass': item.subclass,
                    'inventory_type': item.inventory_type,
                    'is_equippable': item.is_equippable,
                    'is_stackable': item.is_stackable,
                    'quality': item.quality
                } for item in batch_items]
                
                session.run("""
                    UNWIND $items AS item
                    MERGE (i:Item {id: item.id})
                    SET i.name = item.name,
                        i.level = item.level,
                        i.class = item.item_class,
                        i.subclass = item.subclass,
                        i.inventory_type = item.inventory_type,
                        i.is_equippable = item.is_equippable,
                        i.is_stackable = item.is_stackable,
                        i.quality = item.quality
                """, items=batch_data)
                
                items_processed = min(i + self.BATCH_SIZE, total_items)
                print(f"Items Progress: {(items_processed / total_items) * 100:.1f}% ({items_processed}/{total_items})")
                '''

            # Create Recipe nodes and relationships in batches
            for i in range(0, total_recipes, self.BATCH_SIZE):
                batch_recipes = recipes[i:i + self.BATCH_SIZE]
                recipe_data = [{
                    'recipe_id': recipe.id,
                    'name': recipe.name,
                    'crafted_item_id': recipe.crafted_item_id,
                    'profession': recipe.profession,
                    'skill_tier': recipe.skill_tier,
                    'faction': recipe.faction,
                    'reagents': [
                        {
                            'item_id': reagent.item_id,
                            'quantity': reagent.quantity
                        }
                        for reagent in reagents 
                        if reagent.recipe_id == recipe.id and reagent.faction == recipe.faction
                    ]
                } for recipe in batch_recipes]

                session.run("""
                    UNWIND $recipes AS recipe
                    // Create Recipe node
                    MERGE (r:Recipe {id: recipe.recipe_id})
                    SET r.name = recipe.name,
                        r.profession = recipe.profession,
                        r.skill_tier = recipe.skill_tier,
                        r.faction = recipe.faction
                    
                    // Connect Recipe to Profession
                    WITH r, recipe
                    MATCH (p:Profession)
                    WHERE p.name = recipe.profession
                    MERGE (p)-[:CONTAINS_RECIPE]->(r)
                    
                    // Connect Recipe to SkillTier
                    WITH r, recipe, p
                    MATCH (t:SkillTier)
                    WHERE t.profession_name = recipe.profession
                      AND t.name = recipe.skill_tier
                    MERGE (t)-[:INCLUDES_RECIPE]->(r)
                    
                    // Connect Recipe to crafted Item
                    WITH r, recipe
                    MATCH (crafted:Item {id: recipe.crafted_item_id})
                    MERGE (r)-[:CRAFTS]->(crafted)
                    
                    // Connect Recipe to reagent Items
                    WITH r, recipe
                    UNWIND recipe.reagents AS reagent
                    MATCH (reagent_item:Item {id: reagent.item_id})
                    MERGE (reagent_item)-[rel:USED_IN]->(r)
                    SET rel.quantity = reagent.quantity
                """, recipes=recipe_data)
                
                recipes_processed = min(i + self.BATCH_SIZE, total_recipes)
                print(f"Recipes Progress: {(recipes_processed / total_recipes) * 100:.1f}% ({recipes_processed}/{total_recipes})")
                
            print("Graph seeding completed successfully.")

        driver.close()