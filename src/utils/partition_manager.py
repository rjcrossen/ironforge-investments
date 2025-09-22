"""
Partition Manager for Ironforge Database

This module handles automatic creation and management of database partitions
for auction snapshots and commodity price statistics tables.
"""

import logging
import os
from datetime import datetime, timedelta

from sqlalchemy import text
from sqlalchemy.orm import Session

from repository.database import db_session


class PartitionManager:
    """Manages database partitions for time-series data tables."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.partitioned_tables = [
            "auction_snapshots_eu",
            "auction_snapshots_us",
            "eu_commodity_price_stats",
            "us_commodity_price_stats",
            "eu_token_price",
            "us_token_price",
        ]

    def ensure_future_partitions(self, session: Session, months_ahead: int = 6) -> None:
        """
        Ensure partitions exist for the specified number of months ahead.

        Args:
            session: Database session
            months_ahead: Number of months to create partitions for
        """
        try:
            self.logger.info(
                f"Checking partition requirements for {months_ahead} months ahead..."
            )

            # Call the PostgreSQL function to ensure future partitions
            session.execute(text("SELECT ensure_future_partitions()"))
            session.commit()

            self.logger.info("Partition check completed successfully")

        except Exception as e:
            self.logger.error(f"Failed to ensure future partitions: {e}")
            session.rollback()
            raise

    def create_monthly_partitions(
        self, session: Session, months_ahead: int = 6
    ) -> None:
        """
        Create monthly partitions for all partitioned tables.

        Args:
            session: Database session
            months_ahead: Number of months to create partitions for
        """
        try:
            self.logger.info(
                f"Creating monthly partitions for {months_ahead} months ahead..."
            )

            # Call the PostgreSQL function to create monthly partitions
            session.execute(text(f"SELECT create_monthly_partitions({months_ahead})"))
            session.commit()

            self.logger.info(
                f"Successfully created partitions for {months_ahead} months"
            )

        except Exception as e:
            self.logger.error(f"Failed to create monthly partitions: {e}")
            session.rollback()
            raise

    def get_partition_info(self, session: Session) -> list[dict]:
        """
        Get information about existing partitions.

        Args:
            session: Database session

        Returns:
            List of partition information dictionaries
        """
        try:
            # Get partition info for both auction and commodity price stats tables
            result = session.execute(
                text("""
                SELECT 
                    schemaname,
                    tablename as partition_name,
                    'time_partition' as partition_type
                FROM pg_tables pt
                WHERE (pt.tablename LIKE '%auction_snapshots_eu_%' 
                       OR pt.tablename LIKE '%auction_snapshots_us_%'
                       OR pt.tablename LIKE '%eu_commodity_price_stats_%'
                       OR pt.tablename LIKE '%us_commodity_price_stats_%'
                       OR pt.tablename LIKE '%eu_token_price_%'
                       OR pt.tablename LIKE '%us_token_price_%')
                  AND pt.tablename ~ '_[0-9]{4}_[0-9]{2}$'
                ORDER BY schemaname, tablename
            """)
            )

            partitions = []
            for row in result:
                partitions.append(
                    {
                        "schema": row.schemaname,
                        "partition_name": row.partition_name,
                        "partition_type": row.partition_type,
                    }
                )

            return partitions

        except Exception as e:
            self.logger.error(f"Failed to get partition info: {e}")
            raise

    def cleanup_old_partitions(
        self, session: Session, months_to_keep: int = 12
    ) -> None:
        """
        Clean up old partitions beyond the retention period.

        Args:
            session: Database session
            months_to_keep: Number of months of data to retain
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=months_to_keep * 30)
            cutoff_str = cutoff_date.strftime("%Y_%m")

            self.logger.info(
                f"Checking for partitions older than {cutoff_str} to cleanup..."
            )

            # Get list of old partitions for both auction and commodity price stats tables
            result = session.execute(
                text(f"""
                SELECT tablename
                FROM pg_tables
                WHERE (tablename LIKE '%auction_snapshots_%'
                   OR tablename LIKE '%eu_commodity_price_stats_%'
                   OR tablename LIKE '%us_commodity_price_stats_%'
                   OR tablename LIKE '%eu_token_price_%'
                   OR tablename LIKE '%us_token_price_%')
                   AND tablename ~ '\\d{{4}}_\\d{{2}}$'
                   AND substring(tablename from '(\\d{{4}}_\\d{{2}})$') < '{cutoff_str}'
            """)
            )

            old_partitions = [row.tablename for row in result]

            if not old_partitions:
                self.logger.info("No old partitions found for cleanup")
                return

            # Drop old partitions
            for partition in old_partitions:
                self.logger.info(f"Dropping old partition: {partition}")
                session.execute(text(f"DROP TABLE IF EXISTS {partition}"))

            session.commit()
            self.logger.info(
                f"Successfully cleaned up {len(old_partitions)} old partitions"
            )

        except Exception as e:
            self.logger.error(f"Failed to cleanup old partitions: {e}")
            session.rollback()
            raise

    def check_partition_health(self, session: Session) -> dict:
        """
        Check the health of partition setup and return status information.

        Args:
            session: Database session

        Returns:
            Dictionary with partition health information
        """
        try:
            health_info = {
                "status": "healthy",
                "issues": [],
                "partition_count": 0,
                "future_coverage_months": 0,
            }

            # Get partition information
            partitions = self.get_partition_info(session)
            health_info["partition_count"] = len(partitions)
            
            self.logger.info(f"Found {len(partitions)} partitions")
            for partition in partitions:
                self.logger.debug(f"Partition: {partition['partition_name']}")

            if not partitions:
                health_info["status"] = "unhealthy"
                health_info["issues"].append("No partitions found")
                return health_info

            # Check future coverage
            current_date = datetime.now()
            max_future_date = current_date

            for partition in partitions:
                partition_name = partition["partition_name"]
                try:
                    # Extract year and month from partition name
                    parts = partition_name.split("_")
                    if len(parts) >= 2:
                        year_str = parts[-2]
                        month_str = parts[-1]
                        # Create end date as the first day of the next month
                        partition_date = datetime.strptime(f"{year_str}-{month_str}-01", "%Y-%m-%d")
                        # Calculate the end of the month
                        if partition_date.month == 12:
                            end_date = datetime(partition_date.year + 1, 1, 1)
                        else:
                            end_date = datetime(partition_date.year, partition_date.month + 1, 1)
                        
                        if end_date > max_future_date:
                            max_future_date = end_date
                except (IndexError, ValueError):
                    continue

            # Calculate months of future coverage
            months_diff = (max_future_date.year - current_date.year) * 12 + (
                max_future_date.month - current_date.month
            )
            health_info["future_coverage_months"] = months_diff

            # Check if we have adequate future coverage
            if months_diff < 3:
                health_info["status"] = "warning"
                health_info["issues"].append(
                    f"Low future partition coverage: {months_diff} months"
                )

            return health_info

        except Exception as e:
            self.logger.error(f"Failed to check partition health: {e}")
            return {
                "status": "error",
                "issues": [f"Health check failed: {str(e)}"],
                "partition_count": 0,
                "future_coverage_months": 0,
            }

    def run_maintenance(self, session: Session) -> None:
        """
        Run routine partition maintenance tasks.

        Args:
            session: Database session
        """
        try:
            self.logger.info("Starting partition maintenance...")

            # Check partition health
            health = self.check_partition_health(session)
            self.logger.info(f"Partition health status: {health['status']}")

            if health["issues"]:
                for issue in health["issues"]:
                    self.logger.warning(f"Partition issue: {issue}")

            # Ensure future partitions if coverage is low
            if health["future_coverage_months"] < 6:
                self.logger.info("Creating additional future partitions...")
                self.ensure_future_partitions(session, months_ahead=6)

            # Cleanup old partitions - configurable via environment
            cleanup_enabled = os.getenv("PARTITION_CLEANUP_ENABLED", "false").lower() == "true"
            if cleanup_enabled:
                months_to_keep = int(os.getenv("PARTITION_CLEANUP_MONTHS", "12"))
                self.cleanup_old_partitions(session, months_to_keep=months_to_keep)
            else:
                self.logger.info("Partition cleanup disabled - preserving historical data")

            self.logger.info("Partition maintenance completed successfully")

        except Exception as e:
            self.logger.error(f"Partition maintenance failed: {e}")
            raise


class PartitionManagerService:
    """Service wrapper for partition management operations."""

    def __init__(self):
        self.partition_manager = PartitionManager()
        self.logger = logging.getLogger(__name__)

    def initialize_partitions(self) -> None:
        """Initialize partitions on service startup."""
        try:
            with db_session() as session:
                self.logger.info("Initializing partition management...")
                self.partition_manager.ensure_future_partitions(session, months_ahead=6)
                self.logger.info("Partition initialization completed")
        except Exception as e:
            self.logger.error(f"Failed to initialize partitions: {e}")
            raise

    def run_daily_maintenance(self) -> None:
        """Run daily partition maintenance tasks."""
        try:
            with db_session() as session:
                self.logger.info("Running daily partition maintenance...")
                self.partition_manager.run_maintenance(session)
                self.logger.info("Daily partition maintenance completed")
        except Exception as e:
            self.logger.error(f"Daily partition maintenance failed: {e}")
            raise

    def get_status(self) -> dict:
        """Get current partition status."""
        try:
            with db_session() as session:
                return self.partition_manager.check_partition_health(session)
        except Exception as e:
            self.logger.error(f"Failed to get partition status: {e}")
            return {
                "status": "error",
                "issues": [f"Status check failed: {str(e)}"],
                "partition_count": 0,
                "future_coverage_months": 0,
            }