import logging
import os
from abc import ABC, abstractmethod
from datetime import UTC, datetime

from dotenv import load_dotenv
from sqlalchemy.orm import Session

from models.models import SeederStatus
from repository.database import db_session
from utils.benchmark import BenchmarkManager


class Seeder(ABC):
    def __init__(self, session: Session | None = None):
        self.session = session
        self._load_env()

    def _load_env(self):
        """Load environment variables for API credentials."""
        load_dotenv()
        client_id = os.getenv("BLIZZARD_API_CLIENT_ID")
        client_secret = os.getenv("BLIZZARD_API_CLIENT_SECRET")

        if not client_id or not client_secret:
            raise ValueError(
                "Missing Blizzard API credentials in environment variables"
            )

        self.client_id: str = client_id
        self.client_secret: str = client_secret

    @abstractmethod
    def seed(self, session: Session) -> None:
        """Implement seeding logic in subclasses."""
        pass

    def run(self) -> None:
        """Run the seeder with proper session management."""
        if self.session:
            self.seed(self.session)
        else:
            with db_session() as session:
                self.seed(session)


class SeederOrchestrator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def should_run_seeders(self, session: Session) -> bool:
        """Check if seeders need to run based on completion status."""
        recipes_status = (
            session.query(SeederStatus).filter_by(seeder_type="recipes").first()
        )
        reagents_status = (
            session.query(SeederStatus).filter_by(seeder_type="reagents").first()
        )

        recipes_completed = recipes_status is not None and bool(
            recipes_status.completed
        )
        reagents_completed = reagents_status is not None and bool(
            reagents_status.completed
        )

        return not (recipes_completed and reagents_completed)

    def mark_seeder_complete(self, session: Session, seeder_type: str) -> None:
        """Mark a seeder as completed in the database."""
        status = session.query(SeederStatus).filter_by(seeder_type=seeder_type).first()

        if status:
            status.completed = True  # type: ignore
            status.completed_at = datetime.now(UTC)  # type: ignore
        else:
            status = SeederStatus(
                seeder_type=seeder_type,
                completed=True,
                completed_at=datetime.now(UTC),
            )
            session.add(status)

        session.commit()

    def run_initial_seeding(self) -> None:
        """Run all seeders sequentially if they haven't been completed."""
        with db_session() as session:
            if not self.should_run_seeders(session):
                self.logger.info(
                    "All seeders have already been completed. Skipping seeding."
                )
                return

            self.logger.info("Starting initial seeding process...")

            # Check individual seeder status
            recipes_status = (
                session.query(SeederStatus).filter_by(seeder_type="recipes").first()
            )
            reagents_status = (
                session.query(SeederStatus).filter_by(seeder_type="reagents").first()
            )

            recipes_completed = recipes_status is not None and bool(
                recipes_status.completed
            )
            reagents_completed = reagents_status is not None and bool(
                reagents_status.completed
            )

            # Run recipes seeder if not completed
            if not recipes_completed:
                benchmark_manager = BenchmarkManager(session)
                with benchmark_manager.benchmark_operation(
                    operation_type="seeding",
                    operation_name="recipes_seeding",
                ):
                    try:
                        self.logger.info("Running recipes seeder...")
                        from seeding.recipes import RecipeSeeder

                        recipe_seeder = RecipeSeeder(session)
                        recipe_seeder.seed(session)
                        self.mark_seeder_complete(session, "recipes")
                        self.logger.info("Recipes seeding completed successfully.")
                    except Exception as e:
                        self.logger.error(f"Recipes seeding failed: {e}")
                        raise
            else:
                self.logger.info("Recipes seeding already completed. Skipping.")

            # Run reagents seeder if not completed
            if not reagents_completed:
                benchmark_manager = BenchmarkManager(session)
                with benchmark_manager.benchmark_operation(
                    operation_type="seeding",
                    operation_name="reagents_seeding",
                ):
                    try:
                        self.logger.info("Running reagents seeder...")
                        from seeding.reagents import ReagentSeeder

                        reagent_seeder = ReagentSeeder(session)
                        reagent_seeder.seed(session)
                        self.mark_seeder_complete(session, "reagents")
                        self.logger.info("Reagents seeding completed successfully.")
                    except Exception as e:
                        self.logger.error(f"Reagents seeding failed: {e}")
                        raise
            else:
                self.logger.info("Reagents seeding already completed. Skipping.")

            self.logger.info("Initial seeding process completed.")
