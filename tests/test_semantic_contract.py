"""Real Qdrant search/filter contract with a fake encoder, no model downloads."""

import sys
from datetime import date
from types import SimpleNamespace

import numpy as np
import pytest

from bankops.config import ROOT
from bankops.retrieval import PolicyIndex


def test_qdrant_filter_excludes_expired_versions(monkeypatch):
    pytest.importorskip("qdrant_client")

    class FakeEncoder:
        def __init__(self, *args, **kwargs):
            pass

        def encode(self, text, **kwargs):
            if isinstance(text, str):
                return np.array([1.0, 0.0])
            return np.array([[1.0, 0.0] for _ in text])

    monkeypatch.setitem(
        sys.modules, "sentence_transformers", SimpleNamespace(SentenceTransformer=FakeEncoder)
    )
    index = PolicyIndex(ROOT, "semantic")
    old = index.search("liquidity buffer", date(2026, 9, 30), k=8)
    current = index.search("liquidity buffer", date(2026, 10, 30), k=8)
    assert "liquidity-v2" not in [s.id for s in old]
    assert "liquidity-v1" not in [s.id for s in current]
    assert "liquidity-v2" in [s.id for s in current]
    index.qdrant.close()
