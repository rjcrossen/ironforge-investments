import time
from typing import List
from sqlalchemy import create_engine
from backend.blizzard_api import BlizzardAPI
from backend.db.models import Recipe, Base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
import json

load_dotenv("./backend/.env")
client_id = os.getenv("BLIZZARD_API_CLIENT_ID")
client_secret = os.getenv("BLIZZARD_API_CLIENT_SECRET")

#TODO: Store DB entries as a list of dicts instead of tuples to cut out the transcription process later on
def _process_recipe(info: dict) -> List[tuple]:
    """Returns list of (recipe_id, name, crafted_item_id, faction) tuples"""
    if 'crafted_item' in info:
        return [(info['id'], info['name'], info['crafted_item']['id'], "Neutral")]
    elif 'alliance_crafted_item' in info and 'horde_crafted_item' in info:
        return [
            (info['id'], info['name'], info['alliance_crafted_item']['id'], 'Alliance'),
            (info['id'], info['name'], info['horde_crafted_item']['id'], 'Horde')
        ]
    return [(info['id'], info['name'], None, "Neutral")]


def get_all_recipes():
    api = BlizzardAPI(client_id=client_id, client_secret=client_secret, region='eu')
    professions = api.get_professions()
    
    # Setup SQLAlchemy
    engine = create_engine("postgresql+psycopg2://postgres:postgres@db:5432/DB")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Batching by profession
    recipe_batch = []
    ingredient_batch = []
    
    try:
        for profession in professions:
            print(profession['name'])
            
            profession_info = api.get_profession_info(profession)
            
            # Skip if there are no skill tiers
            if 'skill_tiers' not in profession_info:
                continue
            
            for tier in profession_info['skill_tiers']:
                print(tier['name'])

                tier_data = api.get_skill_tier_details(tier)
                
                # Skip if there are no recipes in the tier
                if 'categories' not in tier_data:
                    continue
                
                for category in tier_data['categories']:
                    print(category['name'])
                    for recipe in category['recipes']:
                        info = api.get_recipe_info(recipe)
                        
                        # Not storing recipes with no (optional) reagents
                        #if not info['reagents'] and not info['optional_reagents']:
                        #    continue
                        
                        for recipe_entry in _process_recipe(info):
                            recipe_id, name, crafted_id, faction = recipe_entry
                            print(f"Crafted Item ID: {crafted_id}, Name: {name}, Faction: {faction}")
                            #print(f"Reagents: {info['reagents']}") 
                            
                            recipe_batch.append((recipe_id, name, profession['name'],
                                                tier['name'], crafted_id, faction,
                                                json.dumps(recipe)))
            
            # Commit the profession's data and clear buffer
            # TODO: Add recipe_batch to recipes and ingredient_batch to recipe_ingredients
            
            # Convert tuples to dictionaries for ORM
            recipe_dicts = [
                {
                    'id': r[0],
                    'name': r[1],
                    'profession': r[2],
                    'skill_tier': r[3],
                    'crafted_item_id': r[4],
                    'faction': r[5],
                    'data': r[6]
                }
                for r in recipe_batch
            ]
            
            session.bulk_insert_mappings(Recipe, recipe_dicts)
            session.commit()
            recipe_batch = []
            
    except Exception as e:
        session.rollback()
        raise e
    finally :
        session.close()

get_all_recipes()

