from datetime import date

import pytest


@pytest.mark.parametrize(
    "when,expected,excluded",
    [
        (date(2026, 9, 30), "liquidity-v1", "liquidity-v2"),
        (date(2026, 10, 1), "liquidity-v2", "liquidity-v1"),
        (date(2026, 10, 30), "liquidity-v2", "liquidity-v1"),
    ],
)
def test_temporal_filter(agent, when, expected, excluded):
    hits = agent.index.search("minimum liquidity buffer", when, k=8)
    ids = [h.id for h in hits]
    assert expected in ids
    assert excluded not in ids


def test_old_policy_not_used_for_current_decision(agent):
    from bankops.models import AskRequest

    result = agent.ask(AskRequest(question="Show liquidity"))
    assert result.metrics["buffer_rub"] == 10_000_000
    assert "liquidity-v1" not in [s.id for s in result.sources]


def test_metadata_and_human_policy_agree(agent):
    for source in agent.index.documents:
        for value in agent.index.rules[source.id].values():
            assert str(value) in source.text.replace(",", "").replace(" ", "")


def test_before_any_policy(agent):
    assert not agent.index.search("liquidity", date(2025, 12, 31))
