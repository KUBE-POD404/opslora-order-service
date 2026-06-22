import requests
import pytest

from app.core.logging_config import request_id_ctx
from app.utils import service_client


class FakeResponse:
    status_code = 200


def test_authenticated_get_adds_auth_and_request_id(monkeypatch):
    captured = {}
    request_id_ctx.set("req-123")

    def fake_get(url, headers, timeout):
        captured.update(url=url, headers=headers, timeout=timeout)
        return FakeResponse()

    monkeypatch.setattr(service_client.requests, "get", fake_get)

    response = service_client.authenticated_get("http://service/items", "Bearer token", timeout=7)

    assert response.status_code == 200
    assert captured == {
        "url": "http://service/items",
        "headers": {"Authorization": "Bearer token", "X-Request-ID": "req-123"},
        "timeout": 7,
    }


def test_authenticated_get_reraises_request_errors(monkeypatch):
    request_id_ctx.set(None)

    def fake_get(*args, **kwargs):
        raise requests.Timeout("boom")

    monkeypatch.setattr(service_client.requests, "get", fake_get)

    with pytest.raises(requests.Timeout):
        service_client.authenticated_get("http://service/items", "Bearer token")


def test_authenticated_post_adds_json_payload_and_headers(monkeypatch):
    captured = {}
    request_id_ctx.set("req-456")

    def fake_post(url, json, headers, timeout):
        captured.update(url=url, json=json, headers=headers, timeout=timeout)
        return FakeResponse()

    monkeypatch.setattr(service_client.requests, "post", fake_post)

    payload = {"items": [{"product_id": 7, "quantity": 2}]}
    response = service_client.authenticated_post(
        "http://service/stock/deduct",
        "Bearer token",
        payload,
        timeout=9,
    )

    assert response.status_code == 200
    assert captured == {
        "url": "http://service/stock/deduct",
        "json": payload,
        "headers": {"Authorization": "Bearer token", "X-Request-ID": "req-456"},
        "timeout": 9,
    }


def test_authenticated_post_reraises_request_errors(monkeypatch):
    request_id_ctx.set(None)

    def fake_post(*args, **kwargs):
        raise requests.ConnectionError("boom")

    monkeypatch.setattr(service_client.requests, "post", fake_post)

    with pytest.raises(requests.ConnectionError):
        service_client.authenticated_post("http://service/items", "Bearer token", {"x": 1})
