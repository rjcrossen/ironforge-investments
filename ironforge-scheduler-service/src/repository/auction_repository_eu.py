from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from models.models import AuctionSnapshotEU


class AuctionRepositoryEU:
    def __init__(self, session: Session):
        self.session = session

    def batch_insert(self, model, values, chunk_size=5000):
        """Insert multiple records into the EU auction database in chunks."""
        if not values:
            return

        # Process in chunks to avoid database limits (increased from 1000 to 5000)
        for i in range(0, len(values), chunk_size):
            chunk = values[i : i + chunk_size]
            stmt = insert(AuctionSnapshotEU).values(chunk)
            stmt = stmt.on_conflict_do_nothing()
            self.session.execute(stmt)

    def get_snapshot(self, timestamp):
        """Get auction snapshot for specific timestamp."""
        try:
            # Query closest snapshot before timestamp
            snapshot_data = (
                self.session.query(AuctionSnapshotEU)
                .filter(AuctionSnapshotEU.snapshot_time <= timestamp)
                .order_by(AuctionSnapshotEU.snapshot_time.desc())
                .limit(1)
                .first()
            )

            if not snapshot_data:
                return {}

            # SQL-side grouping: Group by item_id and fetch only needed fields
            auctions = (
                self.session.query(
                    AuctionSnapshotEU.item_id,
                    func.array_agg(
                        func.jsonb_build_object(
                            "id",
                            AuctionSnapshotEU.auction_id,
                            "quantity",
                            AuctionSnapshotEU.quantity,
                            "unit_price",
                            AuctionSnapshotEU.unit_price,
                            "time_left",
                            AuctionSnapshotEU.time_left,
                        )
                    ).label("auctions"),
                )
                .filter(AuctionSnapshotEU.snapshot_time == snapshot_data.snapshot_time)
                .group_by(AuctionSnapshotEU.item_id)
                .all()
            )

            # Convert result to dictionary
            snapshot = {item_id: auctions for item_id, auctions in auctions}
            return snapshot
        except Exception as e:
            print(f"Error retrieving EU snapshot: {e}")
            return None
