from datetime import UTC, datetime, timedelta

from scraper.blizzard_api_utils import BlizzardAPI
from sqlalchemy.orm import Session

from models.models import CommoditySummaryEU, CommoditySummaryUS
from repository.auction_repository_eu import AuctionRepositoryEU
from repository.auction_repository_us import AuctionRepositoryUS
from utils.auction_utils import (
    calculate_median_price,
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
        # Region-specific tables are used directly, no need for generic snapshot tracking
        self.last_time_collected = None



    def collect_snapshot_for_region(self, auction_model):
        """Collect and store current auction house data for specific region model"""
        benchmark_manager = BenchmarkManager(self.session)
        
        # Get commodities data from API (check cache first to avoid double requests)
        commodities = self.api.get_cached_commodities_if_fresh()
        last_modified = None
        
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
        
        # Return the Last-Modified timestamp for logging
        return last_modified

    def get_snapshot(self, timestamp: datetime):
        """Get auction snapshot for specific timestamp"""
        return self.repository.get_snapshot(timestamp)

    def process_summary(self, current_time: datetime, summary_model):
        """Calculate summary statistics and estimate sales"""
        benchmark_manager = BenchmarkManager(self.session)
        
        with benchmark_manager.benchmark_operation(
            operation_type="summary",
            operation_name="summary_processing",
        ):
            # Get current and previous snapshot
            current = self.get_snapshot(current_time)
            previous = self.get_snapshot(current_time - timedelta(hours=1))

            assert isinstance(current, dict)
            assert isinstance(previous, dict)

            # Calculate statistics per item
            summaries = []
            for item_id in set(current.keys()) | set(previous.keys()):
                curr_auctions = current.get(item_id, [])
                prev_auctions = previous.get(item_id, [])

                # Calculate metrics
                minimum_price = (
                    min(a["unit_price"] for a in curr_auctions) if curr_auctions else None
                )
                median_price = (
                    calculate_median_price(curr_auctions) if curr_auctions else None
                )
                total_quantity = (
                    sum(a["quantity"] for a in curr_auctions) if curr_auctions else 0
                )
                new_listings = count_new_listings(curr_auctions, prev_auctions)
                estimated_sales = estimate_sales(curr_auctions, prev_auctions)

                summaries.append(
                    {
                        "item_id": item_id,
                        "minimum_price": minimum_price,
                        "median_price": median_price,
                        "total_quantity": total_quantity,
                        "new_listings": new_listings,
                        "estimated_sales": estimated_sales,
                        "summary_time": current_time,
                    }
                )

            # Summary database insertion
            self.repository.batch_insert(summary_model, summaries)
