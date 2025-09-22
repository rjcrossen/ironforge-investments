from datetime import UTC, datetime, timedelta

from scraper.blizzard_api_utils import BlizzardAPI
from sqlalchemy.orm import Session

from models.models import EUTokenPrice, USTokenPrice
from repository.auction_repository_eu import AuctionRepositoryEU
from repository.auction_repository_us import AuctionRepositoryUS
from utils.auction_utils import (
    count_new_listings,
    estimate_sales,
)
from utils.benchmark import BenchmarkManager


class AuctionCollector:
    def __init__(
        self,
        session: Session,
        api: BlizzardAPI,
        repository: AuctionRepositoryEU | AuctionRepositoryUS,
    ):
        self.repository = repository
        self.session = session
        self.api = api
        self.TIME_LEFT_CODES = {
            "SHORT": 1,  # <0.5 hours
            "MEDIUM": 2,  # 0.5 - 2 hours
            "LONG": 3,  # 2 - 12 hours
            "VERY_LONG": 4,  # 12 - 48 hours
        }
        
    def get_last_collection_time(self, region: str) -> datetime | None:
        """Get the timestamp of the last commodity price stats collection for the region"""
        from sqlalchemy import func, text
        table = "eu_commodity_price_stats" if region == "eu" else "us_commodity_price_stats"
        result = self.session.execute(
            text(f"SELECT MAX(timestamp AT TIME ZONE 'UTC') FROM {table}")
        ).scalar()
        if result:
            # Ensure the timestamp is UTC-aware
            return datetime.fromisoformat(str(result)).replace(tzinfo=UTC)
        return None



    def collect_snapshot_for_region(self, auction_model):
        """Collect and store current auction house data for specific region model"""
        benchmark_manager = BenchmarkManager(self.session)
        
        # Get commodities data from API (check cache first to avoid double requests)
        commodities = self.api.get_cached_commodities_if_fresh()
        last_modified = None
        
        # Determine region from repository type
        region = 'eu' if isinstance(self.repository, AuctionRepositoryEU) else 'us'
        
        if commodities is None:
            # Get fresh data with headers to capture Last-Modified
            commodities, headers = self.api.get_commodities(return_headers=True)
            
            # Extract Last-Modified timestamp
            last_modified_str = headers.get("Last-Modified")
            if last_modified_str:
                try:
                    last_modified = datetime.strptime(
                        last_modified_str, "%a, %d %b %Y %H:%M:%S %Z"
                    ).replace(tzinfo=UTC)
                except Exception:
                    last_modified = datetime.now(UTC)
            else:
                last_modified = datetime.now(UTC)
        else:
            # Using cached data, return current time as best estimate
            last_modified = datetime.now(UTC)
            
        snapshot_time = datetime.now(UTC)

        # Prepare batch insert
        values = [
            {
                "auction_id": auction["id"],
                "item_id": auction["item"]["id"],
                "unit_price": auction["unit_price"],
                "quantity": auction["quantity"],
                "time_left": self.TIME_LEFT_CODES[auction["time_left"]],
                "snapshot_time": snapshot_time,
            }
            for auction in commodities["auctions"]
        ]

        # Database insertion
        self.repository.batch_insert(auction_model, values)
        
        # Process commodity statistics
        from models.models import EUCommodityPriceStats, USCommodityPriceStats
        from utils.auction_utils import calculate_commodity_stats
        
        # Get previous snapshot for comparison
        region = 'eu' if isinstance(self.repository, AuctionRepositoryEU) else 'us'
        last_collection_time = self.get_last_collection_time(region)
        previous_snapshot = self.get_snapshot(last_collection_time) if last_collection_time else None
        
        # Group previous snapshot data by item_id
        previous_by_item = {}
        if previous_snapshot:
            for prev_auction in previous_snapshot:  # previous_snapshot is now a list of dicts
                item_id = prev_auction["item_id"]
                if item_id not in previous_by_item:
                    previous_by_item[item_id] = []
                previous_by_item[item_id].append({
                    "id": prev_auction["id"],
                    "quantity": prev_auction["quantity"],
                    "time_left": prev_auction["time_left"]
                })
        
        # Group current auctions by item_id
        item_auctions = {}
        current_by_item = {}
        for auction in commodities["auctions"]:
            item_id = auction["item"]["id"]
            if item_id not in item_auctions:
                item_auctions[item_id] = []
                current_by_item[item_id] = []
            
            auction_data = {
                "unit_price": auction["unit_price"],
                "quantity": auction["quantity"]
            }
            item_auctions[item_id].append(auction_data)
            
            current_by_item[item_id].append({
                "id": auction["id"],
                "quantity": auction["quantity"],
                "time_left": self.TIME_LEFT_CODES[auction["time_left"]]
            })
        
        # Calculate statistics for each commodity
        stats_values = []
        for item_id, auctions in item_auctions.items():
            stats = calculate_commodity_stats(auctions)
            
            # Calculate estimated sales and new listings
            previous_auctions = previous_by_item.get(item_id, [])
            current_auctions = current_by_item[item_id]
            
            estimated_sales = estimate_sales(current_auctions, previous_auctions) if previous_auctions else 0
            new_listings = count_new_listings(current_auctions, previous_auctions) if previous_auctions else 0
            
            stats_values.append({
                "item_id": item_id,
                "timestamp": snapshot_time,
                "estimated_sales": estimated_sales,
                "new_listings": new_listings,
                **stats  # Unpack the calculated statistics
            })
        
        # Batch insert the commodity statistics into the appropriate regional table
        if stats_values:
            model = EUCommodityPriceStats if region == 'eu' else USCommodityPriceStats
            self.session.execute(
                model.__table__.insert(),
                stats_values
            )
            
        # Collect and store token price
        token_data = self.api.get_wow_token_price()
        token_price = {
            "timestamp": snapshot_time,
            "price": token_data["price"]
        }
        
        # Store token price in the appropriate regional table
        token_model = EUTokenPrice if region == 'eu' else USTokenPrice
        self.session.execute(
            token_model.__table__.insert(),
            [token_price]
        )
        
        self.session.commit()
        
        # Return the Last-Modified timestamp for logging
        return last_modified

    def get_snapshot(self, timestamp: datetime):
        """Get auction snapshot for specific timestamp"""
        return self.repository.get_snapshot(timestamp)
