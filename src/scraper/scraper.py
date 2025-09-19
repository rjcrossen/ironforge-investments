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

    def _collect_region_data(self, region: str, session: Session) -> tuple[bool, bool]:
        """Collect auction data for a specific region (single attempt).

        Returns:
            tuple[bool, bool]: (success, new_data_collected)
        """
        try:
            api = self._create_api_for_region(region)

            # Check if data has been updated since last collection
            last_modified = self._get_last_modified_from_db(session, region)
            last_modified_str = (
                last_modified.strftime("%Y-%m-%d %H:%M:%S UTC")
                if last_modified
                else "never"
            )

            try:
                data_updated = api.is_commodities_updated(last_modified)
                if not data_updated:
                    self.logger.info(
                        f"{region.upper()} auction data unchanged since {last_modified_str} - skipping collection"
                    )
                    self._log_scraper_attempt(
                        session, region, "no_change", last_modified, poll_attempts=1
                    )
                    return True, False  # No error, but no new data
            except Exception as e:
                # If change detection fails, proceed with collection to be safe
                self.logger.debug(
                    f"Change detection failed for {region.upper()}, proceeding with collection: {e}"
                )
                data_updated = True

            # Data has changed, proceed with collection
            self.logger.info(
                f"{region.upper()} auction data updated since {last_modified_str} - polling for new data"
            )
            if region == "eu":
                auction_model = AuctionSnapshotEU
                repository = AuctionRepositoryEU(session)
            else:
                auction_model = AuctionSnapshotUS
                repository = AuctionRepositoryUS(session)

            collector = AuctionCollector(session, api, repository)

            # Data collection and insertion
            last_modified_from_api = collector.collect_snapshot_for_region(
                auction_model
            )

            self._log_scraper_attempt(
                session, region, "success", last_modified_from_api, poll_attempts=1
            )
            new_last_modified_str = (
                last_modified_from_api.strftime("%Y-%m-%d %H:%M:%S UTC")
                if last_modified_from_api
                else "unknown"
            )
            self.logger.info(
                f"Successfully collected {region.upper()} auction data - new last_modified: {new_last_modified_str}"
            )
            return True, True  # Success and new data collected

        except Exception as e:
            self.logger.warning(f"Failed to collect {region.upper()} data: {e}")
            self._log_scraper_attempt(
                session, region, "failed", error_message=str(e), poll_attempts=1
            )
            return False, False  # Failed and no new data

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
                self.logger.warning(
                    f"Daily partition maintenance failed: {e}. Continuing without maintenance..."
                )

    def run_collection_cycle(self) -> tuple[bool, bool, dict[str, bool]]:
        """Run a single collection cycle for both regions.

        Returns:
            tuple[bool, bool, dict[str, bool]]: (success, new_data_collected, region_new_data_status)
        """
        with db_session() as session:
            self.logger.info("Starting auction collection cycle...")

            # Run daily maintenance if needed (once per day)
            self._run_daily_maintenance_if_needed()

            # Collect EU data
            eu_success, eu_new_data = self._collect_region_data("eu", session)

            # Collect US data
            us_success, us_new_data = self._collect_region_data("us", session)

            # Determine overall success and if new data was collected
            overall_success = eu_success and us_success
            any_new_data = eu_new_data or us_new_data
            region_new_data_status = {"eu": eu_new_data, "us": us_new_data}

            if overall_success:
                self.logger.info(
                    "Collection cycle completed successfully for both regions"
                )
                return True, any_new_data, region_new_data_status
            elif eu_success or us_success:
                self.logger.warning("Collection cycle completed with partial success")
                return False, any_new_data, region_new_data_status
            else:
                self.logger.error("Collection cycle failed for both regions")
                return False, False, region_new_data_status

    def start_polling_collection(self) -> None:
        """Start continuous polling collection at :30 past each hour with retries."""
        self.running = True
        self.logger.info(
            f"Starting intelligent polling collection at :{self.polling_config.collection_minute:02d} past each hour..."
        )

        # Run collection immediately on startup
        self.logger.info("Running initial collection on startup...")
        try:
            success, _, _ = self.run_collection_cycle()
            if not success:
                self.logger.warning("Startup collection had errors")
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

                # Wait until the scheduled collection time
                self.logger.info(
                    f"Waiting {seconds_to_wait} seconds until collection window at {target_minute} minutes past the hour"
                )
                time.sleep(seconds_to_wait)

                # Start polling every 30 seconds for up to 30 minutes
                self.logger.info(
                    f"Collection window started at {target_minute} minutes past the hour. Polling every 30 seconds for up to 30 minutes..."
                )

                window_start = datetime.now()
                window_duration_minutes = 30
                polling_attempt = 1
                regions_collected = {"eu": False, "us": False}

                while self.running:
                    self.logger.info(f"Polling attempt #{polling_attempt}")

                    # Check if we've exceeded the 30-minute window
                    elapsed_minutes = (
                        datetime.now() - window_start
                    ).total_seconds() / 60
                    if elapsed_minutes >= window_duration_minutes:
                        self.logger.info(
                            f"Collection window ended after {window_duration_minutes} minutes. Waiting until next hour."
                        )
                        break

                    # Try to collect data
                    try:
                        success, new_data_collected, region_new_data_status = (
                            self.run_collection_cycle()
                        )

                        # Update regions_collected status - once a region has new data, mark it as collected
                        for region, has_new_data in region_new_data_status.items():
                            if has_new_data:
                                regions_collected[region] = True

                        # Check if both regions have been collected
                        both_regions_collected = all(regions_collected.values())

                        if success and new_data_collected:
                            if both_regions_collected:
                                self.logger.info(
                                    "New data collected successfully for both regions! Collection window complete - waiting until next hour."
                                )
                                break
                            else:
                                uncollected_regions = [
                                    region
                                    for region, collected in regions_collected.items()
                                    if not collected
                                ]
                                self.logger.info(
                                    f"New data collected successfully! Still waiting for: {', '.join(uncollected_regions).upper()}. Continuing to poll..."
                                )
                        elif success and not new_data_collected:
                            if both_regions_collected:
                                self.logger.info(
                                    "Both regions already collected in this window. Waiting until next hour."
                                )
                                break
                            else:
                                uncollected_regions = [
                                    region
                                    for region, collected in regions_collected.items()
                                    if not collected
                                ]
                                self.logger.info(
                                    f"No new data available yet. Still waiting for: {', '.join(uncollected_regions).upper()}. Continuing to poll..."
                                )
                        else:
                            self.logger.warning(
                                f"Collection attempt #{polling_attempt} had errors. Continuing to poll..."
                            )

                        polling_attempt += 1

                        # Wait 30 seconds before next attempt (unless window is about to end or both regions collected)
                        if both_regions_collected:
                            break

                        remaining_minutes = window_duration_minutes - elapsed_minutes
                        if remaining_minutes > 0.5:  # More than 30 seconds left
                            self.logger.info(
                                "Waiting 30 seconds before next polling attempt..."
                            )
                            time.sleep(30)
                        else:
                            self.logger.info(
                                "Collection window ending soon, making final attempt..."
                            )

                    except Exception as e:
                        self.logger.error(
                            f"Collection attempt #{polling_attempt} failed with exception: {e}"
                        )
                        polling_attempt += 1

                        # Wait 30 seconds before next attempt (unless window is about to end)
                        elapsed_minutes = (
                            datetime.now() - window_start
                        ).total_seconds() / 60
                        remaining_minutes = window_duration_minutes - elapsed_minutes
                        if remaining_minutes > 0.5:
                            self.logger.info(
                                "Waiting 30 seconds before next polling attempt..."
                            )
                            time.sleep(30)
                        else:
                            break

            except Exception as e:
                self.logger.error(f"Error in polling collection loop: {e}")
                time.sleep(60)  # Wait 1 minute before retrying

    def stop(self) -> None:
        """Stop the polling collection."""
        self.running = False
        self.logger.info("Stopping intelligent polling collection...")
