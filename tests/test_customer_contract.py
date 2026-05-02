import pytest

from app.exceptions.custom_exceptions import ConflictException, NotFoundException
from app.services import order_service


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


def test_customer_contract_maps_required_fields(monkeypatch):
    calls = []

    def fake_get(url, auth_header):
        calls.append((url, auth_header))
        return FakeResponse(
            200,
            {"id": 42, "name": "Acme Buyer", "email": "buyer@example.com"},
        )

    monkeypatch.setattr(order_service, "authenticated_get", fake_get)

    customer = order_service.fetch_customer(42, "Bearer token")

    assert customer == {"name": "Acme Buyer", "email": "buyer@example.com"}
    assert calls == [
        ("http://customer-service:3000/api/v1/customers/42", "Bearer token")
    ]


def test_customer_contract_accepts_legacy_customer_name(monkeypatch):
    monkeypatch.setattr(
        order_service,
        "authenticated_get",
        lambda *_args: FakeResponse(
            200,
            {"id": 42, "customer_name": "Legacy Buyer", "email": "buyer@example.com"},
        ),
    )

    assert order_service.fetch_customer(42, "Bearer token") == {
        "name": "Legacy Buyer",
        "email": "buyer@example.com",
    }


def test_customer_contract_missing_customer_returns_not_found(monkeypatch):
    monkeypatch.setattr(
        order_service,
        "authenticated_get",
        lambda *_args: FakeResponse(404, {"error": {"code": "NOT_FOUND"}}),
    )

    with pytest.raises(NotFoundException):
        order_service.fetch_customer(42, "Bearer token")


def test_customer_contract_rejects_incomplete_success_payload(monkeypatch):
    monkeypatch.setattr(
        order_service,
        "authenticated_get",
        lambda *_args: FakeResponse(200, {"id": 42, "email": "buyer@example.com"}),
    )

    with pytest.raises(ConflictException):
        order_service.fetch_customer(42, "Bearer token")
