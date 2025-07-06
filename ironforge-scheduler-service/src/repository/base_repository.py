from typing import Any, Protocol

from sqlalchemy.orm import Session


class AuctionRepositoryProtocol(Protocol):
    """Protocol for auction repositories to ensure type compatibility."""

    def __init__(self, session: Session) -> None: ...

    def batch_insert(
        self, model_or_values: Any, values: list[Any] = None, chunk_size: int = 1000
    ) -> None:
        """Insert multiple records into the database in chunks."""
        ...

    def get_snapshot(self, timestamp: Any) -> Any:
        """Get auction snapshot for specific timestamp."""
        ...
