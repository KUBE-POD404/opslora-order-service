from app.database import engine, Base
from app.models.order import Order
from app.models.order_item import OrderItem

def create_tables():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    create_tables()