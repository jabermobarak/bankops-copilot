"""Version-aware retrieval with reciprocal-rank fusion.

Default: BM25 + character TF-IDF cosine, entirely local and lexical.
Optional: BM25 + multilingual E5 dense vectors searched in local Qdrant.
Temporal filtering happens BEFORE ranking, including in the vector store.
"""

import json
import math
import re
from collections import Counter
from datetime import date
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from bankops.models import Source

STOP = set(
    "the a an is are of in on to and for what how our do does at as we with can i it "
    "какой какая как что и в на по для у нас ли это из с при".split()
)


def tokens(text: str) -> list[str]:
    return [
        t
        for t in re.findall(r"[a-zа-яё0-9]+", text.lower())
        if t not in STOP and (len(t) > 1 or t.isdigit())
    ]


class PolicyIndex:
    def __init__(self, root: Path, mode: str = "lexical"):
        self.mode = mode
        metadata = json.loads((root / "data/policies/index.json").read_text(encoding="utf-8"))
        self.documents = []
        self.rules = {}
        for item in metadata:
            self.rules[item["id"]] = item.pop("rules", {})
            body = (root / "data/policies" / item.pop("file")).read_text(encoding="utf-8")
            self.documents.append(Source(**item, text=body))
        self.vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5))
        self.matrix = self.vectorizer.fit_transform([d.text for d in self.documents])
        if mode == "semantic":
            self._init_semantic()

    def _init_semantic(self):
        import os

        from qdrant_client import QdrantClient, models
        from sentence_transformers import SentenceTransformer

        self.encoder = SentenceTransformer(
            os.getenv("BANKOPS_EMBED_MODEL", "intfloat/multilingual-e5-small")
        )
        vectors = self.encoder.encode(
            ["passage: " + d.text for d in self.documents], normalize_embeddings=True
        )
        self.qdrant = QdrantClient(":memory:")
        self.qdrant.create_collection(
            "policies",
            vectors_config=models.VectorParams(
                size=vectors.shape[1], distance=models.Distance.COSINE
            ),
        )
        self.qdrant.upsert(
            "policies",
            points=[
                models.PointStruct(id=i, vector=v.tolist(), payload={"index": i})
                for i, v in enumerate(vectors)
            ],
        )

    def search(self, query: str, as_of: date, k: int = 3, method: str = "hybrid") -> list[Source]:
        eligible = [
            i
            for i, d in enumerate(self.documents)
            if d.effective_from <= as_of and (d.effective_to is None or as_of <= d.effective_to)
        ]
        if not eligible:
            return []
        words = [tokens(self.documents[i].text) for i in eligible]
        terms = set(tokens(query))
        if not terms:
            return []
        avg = sum(map(len, words)) / len(words)
        scores = []
        for doc in words:
            counts = Counter(doc)
            score = 0.0
            for term in terms:
                freq = counts[term]
                df = sum(term in other for other in words)
                idf = math.log(1 + (len(words) - df + 0.5) / (df + 0.5))
                score += idf * freq * 2.5 / (freq + 1.5 * (0.25 + 0.75 * len(doc) / avg))
            scores.append(score)
        bm25 = {i: score for i, score in zip(eligible, scores, strict=True)}
        lexical_rank = sorted((i for i in eligible if bm25[i] > 0), key=lambda i: (-bm25[i], i))
        if method == "bm25":
            return [
                self.documents[i].model_copy(update={"score": round(bm25[i], 6)})
                for i in lexical_rank[:k]
            ]
        if self.mode == "semantic":
            from qdrant_client import models

            vector = self.encoder.encode("query: " + query, normalize_embeddings=True)
            hits = self.qdrant.query_points(
                "policies",
                query=vector.tolist(),
                limit=len(eligible),
                query_filter=models.Filter(must=[models.HasIdCondition(has_id=eligible)]),
            ).points
            other_rank = [int(h.id) for h in hits if h.score > 0.72]
        else:
            similarities = self.matrix[eligible] @ self.vectorizer.transform([query]).T
            cosine = dict(zip(eligible, np.asarray(similarities.toarray()).ravel(), strict=True))
            # A lexical-overlap gate avoids accepting accidental character matches.
            other_rank = sorted(
                (i for i in eligible if cosine[i] > 0.08 and bm25[i] > 0),
                key=lambda i: (-cosine[i], i),
            )
        fused = {}
        for ranking in (lexical_rank, other_rank):
            for rank, idx in enumerate(ranking, 1):
                fused[idx] = fused.get(idx, 0) + 1 / (60 + rank)
        best = sorted(fused, key=lambda i: (-fused[i], i))[:k]
        return [self.documents[i].model_copy(update={"score": round(fused[i], 6)}) for i in best]
