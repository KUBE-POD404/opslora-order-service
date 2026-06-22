from sqlalchemy import Boolean, Column, Integer, String, DateTime, CheckConstraint
from datetime import datetime, timezone
from app.database import Base

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)

    organization_id = Column(Integer, nullable=False, index=True)

    customer_id = Column(Integer, nullable=False)

    customer_email = Column(String(255), nullable=False)
    customer_name = Column(String(255), nullable=False)
    customer_display_name = Column(String(255), nullable=True)
    customer_phone = Column(String(50), nullable=True)
    customer_type = Column(String(30), nullable=True)
    customer_tax_id = Column(String(50), nullable=True)
    customer_gstin = Column(String(20), nullable=True)
    customer_tax_registration_type = Column(String(50), nullable=True)
    customer_place_of_supply = Column(String(100), nullable=True)
    billing_address_line1 = Column(String(255), nullable=True)
    billing_address_line2 = Column(String(255), nullable=True)
    billing_city = Column(String(100), nullable=True)
    billing_state = Column(String(100), nullable=True)
    billing_postal_code = Column(String(30), nullable=True)
    billing_country = Column(String(100), nullable=True)
    shipping_same_as_billing = Column(Boolean, nullable=True)
    shipping_address_line1 = Column(String(255), nullable=True)
    shipping_address_line2 = Column(String(255), nullable=True)
    shipping_city = Column(String(100), nullable=True)
    shipping_state = Column(String(100), nullable=True)
    shipping_postal_code = Column(String(30), nullable=True)
    shipping_country = Column(String(100), nullable=True)
    payment_terms_days = Column(Integer, nullable=True)

    status = Column(
        String(20),
        nullable=False,
        default="CREATED"
    )

    created_by_user_id = Column(Integer, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('CREATED','CONFIRMED','CANCELLED')",
            name="check_order_status"
        ),
    )
