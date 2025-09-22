#!/usr/bin/env python3
"""
Entry Point for the Ironforge Scheduler Service

This service handles:
1. Initial seeding of recipes and reagents (run once on startup)
2. Continuous hourly auction data collection for EU and US regions
"""

import logging
import signal
import sys

from scraper.scraper import ScraperOrchestrator
from seeding.seeder import SeederOrchestrator
from utils.partition_manager import PartitionManagerService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler("scheduler.log")],
)

logger = logging.getLogger(__name__)


class SchedulerService:
    def __init__(self):
        self.seeder_orchestrator = SeederOrchestrator()
        self.scraper_orchestrator = ScraperOrchestrator()
        self.partition_manager = PartitionManagerService()
        self.running = False

    def run_initial_seeding(self):
        """Run initial seeding in a separate thread."""
        try:
            logger.info("Starting initial seeding process...")
            self.seeder_orchestrator.run_initial_seeding()
            logger.info("Initial seeding completed successfully")
        except Exception as e:
            logger.error(f"Initial seeding failed: {e}")
            raise

    def start_services(self):
        """Start all services: partition management, seeding, then continuous scraping."""
        self.running = True

        # Initialize partition management first
        logger.info("Initializing database partitions...")
        try:
            self.partition_manager.initialize_partitions()
        except Exception as e:
            logger.warning(f"Partition initialization failed: {e}. Continuing without partitions...")

        # Run initial seeding
        self.run_initial_seeding()

        # Start continuous scraping
        logger.info("Starting continuous auction data collection...")
        self.scraper_orchestrator.start_polling_collection()

    def stop_services(self):
        """Stop all services gracefully."""
        logger.info("Stopping scheduler services...")
        self.running = False
        self.scraper_orchestrator.stop()


def create_signal_handler(service):
    """Create a signal handler for the given service."""

    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        logger.info(
            f"Signal received at {frame.f_code.co_filename}:{frame.f_lineno} in function '{frame.f_code.co_name}'"
        )
        service.stop_services()
        sys.exit(0)

    return signal_handler


def start_scheduler():
    """Start the scheduler service."""
    service = SchedulerService()

    # Set up signal handlers for graceful shutdown
    handler = create_signal_handler(service)
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)

    try:
        service.start_services()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
        service.stop_services()
    except Exception as e:
        logger.error(f"Scheduler service failed: {e}")
        sys.exit(1)


def main():
    """Main entry point."""
    logger.info("Starting Ironforge Scheduler Service...")
    start_scheduler()

if __name__ == "__main__":
    main()
