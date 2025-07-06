import logging
import time
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from models.models import AuctionSnapshotEU, AuctionSnapshotUS, ScraperLog
from repository.auction_repository_eu import AuctionRepositoryEU
from repository.auction_repository_us import AuctionRepositoryUS
from repository.database import db_session
from scraper.auction_collector import AuctionCollector
from scraper.blizzard_api_utils import BlizzardAPI, BlizzardConfig
from scraper.polling_config import SimplePollingConfig
from utils.benchmark import BenchmarkManager
from utils.partition_manager import PartitionManagerService


class ScraperOrchestrator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.running = False
        self.polling_config = SimplePollingConfig()
        self.partition_manager = PartitionManagerService()
        self.last_maintenance_date = None

    def _create_api_for_region(self, region: str) -> BlizzardAPI:
        """Create BlizzardAPI instance for specific region."""
        import os

        from dotenv import load_dotenv

        load_dotenv()
        client_id = os.getenv("BLIZZARD_API_CLIENT_ID")
        client_secret = os.getenv("BLIZZARD_API_CLIENT_SECRET")

        if not client_id or not client_secret:
            raise ValueError(
                "Missing Blizzard API credentials in environment variables"
            )

        config = BlizzardConfig(
            client_id=client_id, client_secret=client_secret, region=region
        )
        return BlizzardAPI(config)

    def _log_scraper_attempt(
        self,
        session: Session,
        region: str,
        status: str,
        last_modified: datetime | None = None,
        error_message: str | None = None,
        poll_attempts: int = 1,
    ) -> None:
        """Log scraper attempt to database."""
        log_entry = ScraperLog(
            region=region,
            status=status,
            last_modified=last_modified,
            error_message=error_message,
            poll_attempts=poll_attempts,
        )
        session.add(log_entry)
        session.commit()

    def _get_last_modified_from_db(
        self, session: Session, region: str
    ) -> datetime | None:
        """Get the last successful collection timestamp for a region."""
        last_log = (
            session.query(ScraperLog)
            .filter_by(region=region, status="success")
            .order_by(ScraperLog.timestamp.desc())
            .first()
        )
        if last_log and last_log.last_modified:
            # Cast to datetime to satisfy type checker
            return last_log.last_modified  # type: ignore
        return None



    def _collect_region_data_with_retries(self, region: str, session: Session) -> bool:
        """Collect auction data for a specific region with retries until end of hour."""
        attempt = 1
        
        while True:
            try:
                api = self._create_api_for_region(region)
                
                # Check if data has been updated since last collection
                last_modified = self._get_last_modified_from_db(session, region)
                last_modified_str = last_modified.strftime("%Y-%m-%d %H:%M:%S UTC") if last_modified else "never"
                
                try:
                    data_updated = api.is_commodities_updated(last_modified)
                    if not data_updated:
                        self.logger.info(f"{region.upper()} auction data unchanged since {last_modified_str} - skipping collection")
                        self._log_scraper_attempt(session, region, "no_change", last_modified, poll_attempts=attempt)
                        return True  # No error, just no new data
                except Exception as e:
                    # If change detection fails, proceed with collection to be safe
                    self.logger.debug(f"Change detection failed for {region.upper()}, proceeding with collection: {e}")
                    data_updated = True

                # Data has changed, proceed with collection
                self.logger.info(f"{region.upper()} auction data updated since {last_modified_str} - polling for new data")
                if region == "eu":
                    auction_model = AuctionSnapshotEU
                    repository = AuctionRepositoryEU(session)
                else:
                    auction_model = AuctionSnapshotUS
                    repository = AuctionRepositoryUS(session)

                collector = AuctionCollector(session, api, repository)
                
                # Data collection and insertion
                last_modified_from_api = collector.collect_snapshot_for_region(auction_model)

                self._log_scraper_attempt(session, region, "success", last_modified_from_api, poll_attempts=attempt)
                new_last_modified_str = last_modified_from_api.strftime("%Y-%m-%d %H:%M:%S UTC") if last_modified_from_api else "unknown"
                self.logger.info(f"Successfully collected {region.upper()} auction data (attempt {attempt}) - new last_modified: {new_last_modified_str}")
                return True

            except Exception as e:
                self.logger.warning(f"Attempt {attempt} failed for {region.upper()}: {e}")
                
                # Check if we've reached the end of the hour
                now = datetime.now()
                minutes_until_next_hour = (60 - now.minute) % 60
                
                if minutes_until_next_hour == 0 or minutes_until_next_hour >= 30:
                    # We're at the end of the hour or past the retry window
                    self.logger.error(f"Failed to collect {region.upper()} data after {attempt} attempts (end of hour reached)")
                    self._log_scraper_attempt(session, region, "failed", error_message=str(e), poll_attempts=attempt)
                    return False
                
                # Wait before retrying
                self.logger.info(f"Retrying {region.upper()} collection in {self.polling_config.retry_delay_seconds} seconds...")
                time.sleep(self.polling_config.retry_delay_seconds)
                attempt += 1

    def _run_daily_maintenance_if_needed(self) -> None:
        """Run daily partition maintenance if it hasn't been run today."""
        today = datetime.now().date()

        if self.last_maintenance_date != today:
            try:
                self.logger.info("Running daily partition maintenance...")
                self.partition_manager.run_daily_maintenance()
                self.last_maintenance_date = today
                self.logger.info("Daily partition maintenance completed")
            except Exception as e:
                self.logger.warning(f"Daily partition maintenance failed: {e}. Continuing without maintenance...")

    def run_collection_cycle(self) -> None:
        """Run a single collection cycle for both regions."""
        with db_session() as session:
            self.logger.info("Starting auction collection cycle...")

            # Run daily maintenance if needed (once per day)
            self._run_daily_maintenance_if_needed()

            # Collect EU data
            eu_success = self._collect_region_data_with_retries("eu", session)

            # Collect US data
            us_success = self._collect_region_data_with_retries("us", session)

            if eu_success and us_success:
                self.logger.info(
                    "Collection cycle completed successfully for both regions"
                )
            elif eu_success or us_success:
                self.logger.warning("Collection cycle completed with partial success")
            else:
                self.logger.error("Collection cycle failed for both regions")

    def start_polling_collection(self) -> None:
        """Start continuous polling collection at :30 past each hour with retries."""
        self.running = True
        self.logger.info(f"Starting intelligent polling collection at :{self.polling_config.collection_minute:02d} past each hour...")

        # Run collection immediately on startup
        self.logger.info("Running initial collection on startup...")
        try:
            self.run_collection_cycle()
        except Exception as e:
            self.logger.error(f"Error in startup collection: {e}")

        while self.running:
            try:
                # Calculate time until next :30 minute mark
                now = datetime.now()
                target_minute = self.polling_config.collection_minute
                
                # Calculate minutes until target minute
                minutes_until_target = (target_minute - now.minute) % 60
                if minutes_until_target == 0 and now.second > 0:
                    # We're at the target minute but not at the start, wait for next hour
                    minutes_until_target = 60

                seconds_to_wait = (minutes_until_target * 60) - now.second

                self.logger.info(f"Waiting {seconds_to_wait} seconds until next collection at :{target_minute:02d}")
                time.sleep(seconds_to_wait)

                # Run collection cycle with retries until end of hour
                self.run_collection_cycle()

            except Exception as e:
                self.logger.error(f"Error in polling collection loop: {e}")
                time.sleep(60)  # Wait 1 minute before retrying

    def stop(self) -> None:
        """Stop the polling collection."""
        self.running = False
        self.logger.info("Stopping intelligent polling collection...")


class Scraper:
    def __init__(self):
        """Initialize the scraper with necessary configurations."""
        self.orchestrator = ScraperOrchestrator()

    def run(self):
        """Run the scraper orchestrator."""
        self.orchestrator.start_polling_collection()
