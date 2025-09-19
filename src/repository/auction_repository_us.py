from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from models.models import AuctionSnapshotUS


class AuctionRepositoryUS:
    def __init__(self, session: Session):
        self.session = session

    def batch_insert(self, model, values, chunk_size=5000):
        """Insert multiple records into the US auction database in chunks."""
        if not values:
            return

        # Process in chunks to avoid database limits (increased from 1000 to 5000)
        for i in range(0, len(values), chunk_size):
            chunk = values[i : i + chunk_size]
            stmt = insert(AuctionSnapshotUS).values(chunk)
            stmt = stmt.on_conflict_do_nothing()
            self.session.execute(stmt)

    def get_snapshot(self, timestamp):
        """Get auction snapshot for specific timestamp."""
        try:
            # Query closest snapshot before timestamp
            snapshot_data = (
                self.session.query(AuctionSnapshotUS)
                .filter(AuctionSnapshotUS.snapshot_time <= timestamp)
                .order_by(AuctionSnapshotUS.snapshot_time.desc())
                .limit(1)
                .first()
            )

            if not snapshot_data:
                return {}

            # SQL-side grouping: Group by item_id and fetch only needed fields
            auctions = (
                self.session.query(
                    AuctionSnapshotUS.item_id,
                    func.array_agg(
                        func.jsonb_build_object(
                            "id",
                            AuctionSnapshotUS.auction_id,
                            "quantity",
                            AuctionSnapshotUS.quantity,
                            "unit_price",
                            AuctionSnapshotUS.unit_price,
                            "time_left",
                            AuctionSnapshotUS.time_left,
                        )
                    ).label("auctions"),
                )
                .filter(AuctionSnapshotUS.snapshot_time == snapshot_data.snapshot_time)
                .group_by(AuctionSnapshotUS.item_id)
                .all()
            )

            # Convert result to dictionary
            snapshot = {item_id: auctions for item_id, auctions in auctions}
            return snapshot
        except Exception as e:
            print(f"Error retrieving US snapshot: {e}")
            return None
