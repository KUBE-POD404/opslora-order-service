from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.dependencies.auth import get_current_user
from app.main import app
from app.models.order import Order  # noqa: F401
from app.models.order_item import OrderItem  # noqa: F401
from app.security.jwt import TokenPayload


def test_order_api_create_list_confirm_and_cancel_rules(monkeypatch, no_op_celery):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    def override_current_user():
        return TokenPayload(
            user_id=10,
            org_id=20,
            permissions=[
                "order.create",
                "order.read",
                "order.update",
                "order.confirm",
                "order.cancel",
            ],
        )

    def fake_fetch_customer(customer_id, auth_header):
        return {
            "email": "buyer@example.com",
            "name": "Acme Buyer",
            "display_name": "Acme",
            "phone": "+91-9876543210",
            "customer_type": "BUSINESS",
            "gstin": "29ABCDE1234F1Z5",
            "place_of_supply": "Karnataka",
            "shipping_same_as_billing": True,
            "payment_terms_days": 30,
        }

    monkeypatch.setattr("app.services.order_service.fetch_customer", fake_fetch_customer)

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_current_user

    try:
        client = TestClient(app)

        create_response = client.post(
            "/api/v1/orders/create-order",
            json={
                "customer_id": 1,
                "items": [
                    {"product_name": "Steel Bolt", "quantity": 2, "unit_price": 12.5},
                    {"product_name": "Washer", "quantity": 4, "unit_price": 2.0},
                ],
            },
        )

        assert create_response.status_code == 201
        order = create_response.json()
        assert order["customer_email"] == "buyer@example.com"
        assert order["customer_display_name"] == "Acme"
        assert order["customer_gstin"] == "29ABCDE1234F1Z5"
        assert order["payment_terms_days"] == 30
        assert order["status"] == "CREATED"
        assert order["total"] == 33.0
        assert len(no_op_celery.tasks) == 1

        list_response = client.get("/api/v1/orders/")
        assert list_response.status_code == 200
        assert [item["id"] for item in list_response.json()] == [order["id"]]

        confirm_response = client.post(f"/api/v1/orders/{order['id']}/confirm")
        assert confirm_response.status_code == 200
        assert confirm_response.json()["status"] == "CONFIRMED"

        cancel_response = client.post(f"/api/v1/orders/{order['id']}/cancel")
        assert cancel_response.status_code == 409
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
