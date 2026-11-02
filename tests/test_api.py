from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from bankops.api import create_app


def test_end_to_end_auth_and_metrics(settings):
    with TestClient(create_app(replace(settings, api_key="test-only"))) as client:
        assert client.get("/health").status_code == 200
        assert client.post("/v1/ask", json={"question": "Show liquidity"}).status_code == 401
        headers = {"X-API-Key": "test-only"}
        response = client.post(
            "/v1/ask", headers=headers, json={"question": "What if outflows increase by 20%?"}
        )
        assert response.status_code == 200
        assert response.json()["metrics"]["closing_cash_rub"] == 5_800_000
        assert (
            client.get("/v1/overview", headers=headers).json()["metrics"]["opening_cash_rub"]
            == 26_000_000
        )
        assert client.get("/v1/config", headers=headers).json()["read_only"] is True
        metrics = client.get("/metrics", headers=headers).text
        assert 'status="answered"} 2' in metrics


@pytest.mark.parametrize(
    "payload",
    [
        {"question": "Show liquidity", "horizon_days": 31},
        {"question": "Show liquidity", "stress_pct": -1},
        {"question": "Show liquidity", "sql": "SELECT * FROM secrets"},
        {"question": " " * 10},
        {"question": "x" * 2001},
    ],
)
def test_validation(settings, payload):
    with TestClient(create_app(settings)) as client:
        assert client.post("/v1/ask", json=payload).status_code == 422


def test_error_body_does_not_leak_exception(settings, monkeypatch):
    with TestClient(create_app(settings)) as client:

        def fail(*args):
            raise RuntimeError("sensitive-upstream-token")

        monkeypatch.setattr(client.app.state.agent, "ask", fail)
        response = client.post("/v1/ask", json={"question": "Show liquidity"})
        assert response.status_code == 503
        assert "sensitive" not in response.text
