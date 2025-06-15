
from datetime import datetime, timedelta, timezone
from typing import Dict, List

from backend.blizzard_api import BlizzardAPI
from backend.db.auction.auction_utils import (calculate_median_price,
                                              count_new_listings,
                                              estimate_sales)
from backend.db.models import AuctionSnapshot, CommoditySummary
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session


class AuctionCollector:
    def __init__(self, session: Session, api: BlizzardAPI):
        self.session = session
        self.api = api
        self.TIME_LEFT_CODES = {
            'SHORT': 1,    # <0.5 hours
            'MEDIUM': 2,   # 0.5 - 2 hours
            'LONG': 3,     # 2 - 12 hours
            'VERY_LONG': 4 # 12 - 48 hours
        }
        time = self.session.query(AuctionSnapshot.snapshot_time).order_by(AuctionSnapshot.snapshot_time.desc()).first()
        if time is None:
            self.last_time_collected = None
        else:
            self.last_time_collected = time[0]
    
    def collect_snapshot(self):
        """Collect and store current auction house data"""
        commodities = self.api.get_commodities()
        snapshot_time = datetime.now(timezone.utc)
        
        # Prepare batch insert
        values = [{
            'auction_id': auction['id'],
            'item_id': auction['item']['id'],
            'unit_price': auction['unit_price'],
            'quantity': auction['quantity'],
            'time_left': self.TIME_LEFT_CODES[auction['time_left']],
            'snapshot_time': snapshot_time
        } for auction in commodities['auctions']]
        
        # Efficient batch insert
        stmt = insert(AuctionSnapshot).values(values)
        stmt.on_conflict_do_nothing()
        
        # Handle conflicts (in case of duplicate auction_ids)
        #stmt = stmt.on_conflict_do_nothing(index_elements=['auction_id'])
        
        # Execute and commit
        self.session.execute(stmt)
        self.session.commit()
        
        self.last_time_collected = snapshot_time
        
    def get_snapshot(self, timestamp: datetime) -> Dict[int, List[Dict]]:
        """Get auction snapshot for specific timestamp"""
        try:
            # Query closest snapshot before timestamp
            # NB: Snapshots usually come out close to half past
            snapshot_data = (
                self.session.query(AuctionSnapshot)
                .filter(
                    AuctionSnapshot.snapshot_time <= timestamp
                )
                .order_by(AuctionSnapshot.snapshot_time.desc())
                .limit(1)
                .first()
            )
            
            print(snapshot_data.snapshot_time)
            
            if not snapshot_data:
               return {}
            
            # SQL-side grouping: Group by item_id and fetch only needed fields
            auctions = (
                self.session.query(
                    AuctionSnapshot.item_id,
                    func.array_agg(
                        func.jsonb_build_object(
                            'id', AuctionSnapshot.auction_id,
                            'quantity', AuctionSnapshot.quantity,
                            'unit_price', AuctionSnapshot.unit_price,
                            'time_left', AuctionSnapshot.time_left
                        )
                    ).label('auctions')
                )
                .filter(AuctionSnapshot.snapshot_time == snapshot_data.snapshot_time)
                .group_by(AuctionSnapshot.item_id)
                .all()
            )
            
            # Convert result to dictionary (similar to previous code)
            snapshot = {item_id: auctions for item_id, auctions in auctions}
                
            return snapshot
            
        except Exception as e:
            print(f"Error getting snapshot: {e}")
            return {}    
        
    
    def process_summary(self, current_time: datetime):
        """Calculate summary statistics and estimate sales"""
        # Get current and previous snapshot
        current = self.get_snapshot(current_time)
        previous = self.get_snapshot(current_time - timedelta(hours=1))
        
        # Calculate statistics per item
        summaries = []
        for item_id in set(current.keys()) | set(previous.keys()):
            curr_auctions = current.get(item_id, [])
            prev_auctions = previous.get(item_id, [])
            print(item_id)
            
            # Calculate metrics
            minimum_price = min(a['unit_price'] for a in curr_auctions) if curr_auctions else None
            median_price = calculate_median_price(curr_auctions) if curr_auctions else None
            total_quantity = sum(a['quantity'] for a in curr_auctions) if curr_auctions else 0
            new_listings = count_new_listings(curr_auctions, prev_auctions) 
            estimated_sales = estimate_sales(curr_auctions, prev_auctions)
            
            #TODO: Convert this from ORM insert to batch insert
            summaries.append(CommoditySummary(
                item_id=item_id,
                minimum_price=minimum_price,
                median_price=median_price,
                total_quantity=total_quantity,
                new_listings=new_listings,
                estimated_sales=estimated_sales,
                summary_time=current_time
            ))
        
        self.session.bulk_save_objects(summaries)
        self.session.commit()

