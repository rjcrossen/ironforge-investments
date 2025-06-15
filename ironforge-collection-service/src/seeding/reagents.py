
import os
import time
from typing import List

from backend.blizzard_api import BlizzardAPI
from backend.db.models import Base, Reagent
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv("./backend/.env")
client_id = os.getenv("BLIZZARD_API_CLIENT_ID")
client_secret = os.getenv("BLIZZARD_API_CLIENT_SECRET")

#TODO: Store DB entries as a list of dicts instead of tuples to cut out the transcription process later on
def _process_reagents(info: dict) -> List[tuple]:
    """Returns list of (recipe_id, faction, item_id, quantity, optional) tuples"""
    
    reagents_list = []
    
    if 'reagents' in info:
        reagents = info['reagents']
        for reagent in reagents:
            reagents_list.append((info['id'], reagent['reagent']['id'], reagent['quantity'], False))
        
    if 'optional_reagents' in info:
        optional_reagents = info['optional_reagents']
        for reagent in optional_reagents:
            reagents_list.append((info['id'], reagent['reagent']['id'], reagent['quantity'], True))
    
    return reagents_list
        


def get_all_reagents():
    api = BlizzardAPI(client_id=client_id, client_secret=client_secret, region='eu')
    professions = api.get_professions()
    
    # Setup SQLAlchemy
    engine = create_engine("postgresql+psycopg2://postgres:postgres@db:5432/DB")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Batching by profession
    reagent_batch = []
    
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
                        for reagent_entry in _process_reagents(info):
                            reagent_batch.append(reagent_entry)
            
            # Commit ingredient data and clear buffer
            
            # Convert tuples to dictionaries for ORM
            reagent_dicts = [
                {
                    'recipe_id': r[0],
                    'item_id': r[1],
                    'quantity': r[2],
                    'optional': r[3]
                }
                for r in reagent_batch
            ]
            
            session.bulk_insert_mappings(Reagent, reagent_dicts)
            session.commit()
            reagent_batch = []
            
    except Exception as e:
        session.rollback()
        raise e
    finally :
        session.close()
