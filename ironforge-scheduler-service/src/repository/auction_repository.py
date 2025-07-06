from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from models.models import AuctionSnapshot


class AuctionRepository:
    def __init__(self, session: Session):
        self.session = session

    def batch_insert(self, model, values, chunk_size=5000):
        """Insert multiple records into the database in chunks."""
        if not values:
            return

        # Process in chunks to avoid database limits (increased from 1000 to 5000)
        for i in range(0, len(values), chunk_size):
            chunk = values[i : i + chunk_size]
            stmt = insert(model).values(chunk)
            stmt = stmt.on_conflict_do_nothing()
            self.session.execute(stmt)

    def get_snapshot(self, timestamp):
        """Get auction snapshot for specific timestamp."""
        try:
            # Query closest snapshot before timestamp
            # NB: Snapshots usually come out close to half past
            snapshot_data = (
                self.session.query(AuctionSnapshot)
                .filter(AuctionSnapshot.snapshot_time <= timestamp)
                .order_by(AuctionSnapshot.snapshot_time.desc())
                .limit(1)
                .first()
            )

            if not snapshot_data:
                return {}

            # SQL-side grouping: Group by item_id and fetch only needed fields
            auctions = (
                self.session.query(
                    AuctionSnapshot.item_id,
                    func.array_agg(
                        func.jsonb_build_object(
                            "id",
                            AuctionSnapshot.auction_id,
                            "quantity",
                            AuctionSnapshot.quantity,
                            "unit_price",
                            AuctionSnapshot.unit_price,
                            "time_left",
                            AuctionSnapshot.time_left,
                        )
                    ).label("auctions"),
                )
                .filter(AuctionSnapshot.snapshot_time == snapshot_data.snapshot_time)
                .group_by(AuctionSnapshot.item_id)
                .all()
            )

            # Convert result to dictionary (similar to previous code)
            snapshot = {item_id: auctions for item_id, auctions in auctions}
            return snapshot
        except Exception as e:
            print(f"Error retrieving snapshot: {e}")
            return None
