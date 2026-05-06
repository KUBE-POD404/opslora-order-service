from sqlalchemy import Column, Integer, String, Numeric, ForeignKey
from app.database import Base

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)

    order_id = Column(
        Integer,
        ForeignKey("orders.id"),
        nullable=False
    )

    product_id = Column(Integer, nullable=True)
    sku = Column(String(80), nullable=True)
    product_name = Column(String(100), nullable=False)
    hsn_sac_code = Column(String(20), nullable=True)
    unit_of_measure = Column(String(30), nullable=True)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    tax_rate = Column(Numeric(5, 2), nullable=True)
