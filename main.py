from sqlalchemy import create_engine
import time
from dotenv import load_dotenv
import os
from backend.db.auction.auction_collector import AuctionCollector
from backend.blizzard_api import BlizzardAPI
from sqlalchemy.orm import Session
import datetime

load_dotenv("./backend/.env")
client_id = os.getenv("BLIZZARD_API_CLIENT_ID")
client_secret = os.getenv("BLIZZARD_API_CLIENT_SECRET")

time.sleep(5)

engine = create_engine("postgresql+psycopg2://postgres:postgres@db:5432/DB")

#backend.db.seeders.populate_reagents.get_all_reagents()

api = BlizzardAPI(client_id, client_secret, region="eu")
session = Session(bind=engine)
collector = AuctionCollector(session, api)
collector.collect_snapshot()

##previous = collector.get_snapshot(datetime.datetime.now() - datetime.timedelta(hours=1))
#previous = previous.get(765, [])
#current = collector.get_snapshot(datetime.datetime.now())
#current = current.get(765, [])
#sales = AuctionCollector.estimate_sales(current, previous)
#print(sales)
#print(sum(x['quantity'] for x in snapshot[117]))

collector.process_summary(datetime.datetime.now())

# TODO: remove uniqueness constraint of auction_id in auction_snapshots table
# TODO: add a new 
