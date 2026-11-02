import json

import httpx
import pytest

from bankops.providers import generate, validate_narrative


def test_provider_http_contract_and_fallback(agent, monkeypatch):
    sources = agent.index.search("liquidity buffer", __import__("datetime").date(2026, 10, 30))
    observed = []
    raw = json.dumps(
        {"summary": "Review the buffer [liquidity-v2].", "citations": ["liquidity-v2"]}
    )

    def handler(req):
        observed.append(json.loads(req.content))
        return httpx.Response(200, json={"choices": [{"message": {"content": raw}}]})

    original = httpx.Client
    monkeypatch.setattr(
        httpx, "Client", lambda **kwargs: original(transport=httpx.MockTransport(handler))
    )
    summary, warnings = generate("openai_compatible", "Explain", "buffer 10000000", sources, "en")
    assert summary and not warnings
    assert observed[0]["messages"][0]["role"] == "system"
    assert observed[0]["max_tokens"] == 600
    raw = '{"summary":"Invented 999999 [liquidity-v2]", "citations":["liquidity-v2"]}'
    summary, warnings = generate("openai_compatible", "Explain", "buffer 10000000", sources, "en")
    assert summary is None and warnings


@pytest.mark.parametrize(
    "raw",
    [
        "not json",
        '{"summary":"A claim [made-up]", "citations":["made-up"]}',
        '{"summary":"A claim without inline citation", "citations":["liquidity-v2"]}',
        '{"summary":"A claim [liquidity-v2]", "citations":["liquidity-v2"], "extra":"x"}',
    ],
)
def test_invalid_narratives_rejected(agent, raw):
    sources = agent.index.search("liquidity", __import__("datetime").date(2026, 10, 30))
    with pytest.raises(ValueError):
        validate_narrative(raw, "test", sources)


def test_missing_gigachat_credentials_fails_safely(agent, monkeypatch):
    monkeypatch.delenv("GIGACHAT_CREDENTIALS", raising=False)
    summary, warnings = generate("gigachat", "Explain", "facts", [], "en")
    assert summary is None and warnings
