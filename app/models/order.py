from sqlalchemy import Column, Integer, String, DateTime, CheckConstraint
from datetime import datetime, timezone
from app.database import Base

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)

    organization_id = Column(Integer, nullable=False, index=True)

    customer_id = Column(Integer, nullable=False)

    customer_email = Column(String(255), nullable=False)
    customer_name = Column(String(255), nullable=False)

    status = Column(
        String(20),
        nullable=False,
        default="CREATED"
    )

    created_by_user_id = Column(Integer, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        default=datetime.now(timezone.utc)
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('CREATED','CONFIRMED','CANCELLED')",
            name="check_order_status"
        ),
    )