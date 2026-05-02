import pytest

from app.exceptions.custom_exceptions import ConflictException, NotFoundException
from app.services import order_service


def test_create_order_fetches_customer_and_calculates_total(db_session, monkeypatch, no_op_celery):
    monkeypatch.setattr(
        order_service,
        "fetch_customer",
        lambda customer_id, auth_header: {"email": "buyer@example.com", "name": "Buyer"},
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
    assert order.total == 200.0
    assert len(order.items) == 1
    assert no_op_celery.tasks[0][0][0] == "notification.send_order_created_email"


def test_confirm_order_changes_status_and_publishes_event(db_session, monkeypatch, no_op_celery):
    monkeypatch.setattr(
        order_service,
        "fetch_customer",
        lambda customer_id, auth_header: {"email": "buyer@example.com", "name": "Buyer"},
    )
    order = order_service.create_order(
        db_session,
        42,
        [{"product_name": "Item A", "quantity": 1, "unit_price": 50.0}],
        1,
        10,
        "Bearer token",
    )

    confirmed = order_service.confirm_order(db_session, order.id, organization_id=1)

    assert confirmed.status == "CONFIRMED"
    assert no_op_celery.tasks[-1][0][0] == "notification.send_order_confirmed_email"


def test_confirming_cancelled_order_is_rejected(db_session, monkeypatch, no_op_celery):
    monkeypatch.setattr(
        order_service,
        "fetch_customer",
        lambda customer_id, auth_header: {"email": "buyer@example.com", "name": "Buyer"},
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
        order_service.confirm_order(db_session, order.id, organization_id=1)


def test_order_reads_are_tenant_scoped(db_session, monkeypatch, no_op_celery):
    monkeypatch.setattr(
        order_service,
        "fetch_customer",
        lambda customer_id, auth_header: {"email": "buyer@example.com", "name": "Buyer"},
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
