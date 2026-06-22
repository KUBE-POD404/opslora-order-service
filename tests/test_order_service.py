from decimal import Decimal

import pytest

from app.exceptions.custom_exceptions import ConflictException, NotFoundException
from app.services import order_service


def customer_snapshot():
    return {
        "email": "buyer@example.com",
        "name": "Buyer",
        "display_name": "Buyer Co",
        "phone": "+91-9876543210",
        "customer_type": "BUSINESS",
        "gstin": "29ABCDE1234F1Z5",
        "place_of_supply": "Karnataka",
        "billing_city": "Bengaluru",
        "billing_country": "India",
        "shipping_same_as_billing": True,
        "payment_terms_days": 30,
    }


def product_snapshot():
    return {
        "id": 7,
        "name": "Steel Bolt",
        "sku": "BOLT-001",
        "hsn_sac_code": "7318",
        "unit_of_measure": "PCS",
        "sale_price": "12.50",
        "tax_rate": "18.00",
    }


def test_create_order_fetches_customer_and_calculates_total(db_session, monkeypatch, no_op_celery):
    monkeypatch.setattr(
        order_service,
        "fetch_customer",
        lambda customer_id, auth_header: customer_snapshot(),
    )

    order = order_service.create_order(
        db=db_session,
        customer_id=42,
        items=[{"product_name": "Item A", "quantity": 2, "unit_price": 100.0}],
        organization_id=1,
        created_by_user_id=10,
        auth_header="Bearer token",
    )

    assert order.customer_id == 42
    assert order.customer_email == "buyer@example.com"
    assert order.customer_display_name == "Buyer Co"
    assert order.customer_gstin == "29ABCDE1234F1Z5"
    assert order.payment_terms_days == 30
    assert order.total == 200.0
    assert len(order.items) == 1
    assert no_op_celery.tasks[0][0][0] == "notification.send_order_created_email"


def test_product_order_item_snapshots_inventory_product_and_deducts_on_confirm(
    db_session,
    monkeypatch,
    no_op_celery,
):
    deductions = []
    monkeypatch.setattr(
        order_service,
        "fetch_customer",
        lambda customer_id, auth_header: customer_snapshot(),
    )
    monkeypatch.setattr(
        order_service,
        "fetch_product_snapshot",
        lambda product_id, auth_header: product_snapshot(),
    )
    monkeypatch.setattr(
        order_service,
        "deduct_inventory_stock",
        lambda order, items, auth_header: deductions.append(
            [(item.product_id, item.quantity) for item in items if item.product_id]
        ),
    )

    order = order_service.create_order(
        db=db_session,
        customer_id=42,
        items=[{"product_id": 7, "quantity": 3}],
        organization_id=1,
        created_by_user_id=10,
        auth_header="Bearer token",
    )

    assert order.items[0].product_id == 7
    assert order.items[0].sku == "BOLT-001"
    assert order.items[0].product_name == "Steel Bolt"
    assert order.items[0].unit_price == Decimal("12.50")
    assert order.total == Decimal("37.50")

    order_service.confirm_order(db_session, order.id, organization_id=1, auth_header="Bearer token")

    assert deductions == [[(7, 3)]]


def test_confirm_order_changes_status_and_publishes_event(db_session, monkeypatch, no_op_celery):
    monkeypatch.setattr(
        order_service,
        "fetch_customer",
        lambda customer_id, auth_header: customer_snapshot(),
    )
    order = order_service.create_order(
        db_session,
        42,
        [{"product_name": "Item A", "quantity": 1, "unit_price": 50.0}],
        1,
        10,
        "Bearer token",
    )

    confirmed = order_service.confirm_order(db_session, order.id, organization_id=1, auth_header="Bearer token")

    assert confirmed.status == "CONFIRMED"
    assert no_op_celery.tasks[-1][0][0] == "notification.send_order_confirmed_email"


def test_confirming_cancelled_order_is_rejected(db_session, monkeypatch, no_op_celery):
    monkeypatch.setattr(
        order_service,
        "fetch_customer",
        lambda customer_id, auth_header: customer_snapshot(),
    )
    order = order_service.create_order(
        db_session,
        42,
        [{"product_name": "Item A", "quantity": 1, "unit_price": 50.0}],
        1,
        10,
        "Bearer token",
    )
    order_service.cancel_order(db_session, order.id, organization_id=1)

    with pytest.raises(ConflictException):
        order_service.confirm_order(db_session, order.id, organization_id=1, auth_header="Bearer token")


def test_order_reads_are_tenant_scoped(db_session, monkeypatch, no_op_celery):
    monkeypatch.setattr(
        order_service,
        "fetch_customer",
        lambda customer_id, auth_header: customer_snapshot(),
    )
    order = order_service.create_order(
        db_session,
        42,
        [{"product_name": "Item A", "quantity": 1, "unit_price": 50.0}],
        1,
        10,
        "Bearer token",
    )

    with pytest.raises(NotFoundException):
        order_service.get_order(db_session, order.id, organization_id=2)
