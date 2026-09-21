"""Lightweight, dependency-free TF-IDF vectorisation and cosine similarity.

Content-based recommendation needs text features; these helpers avoid
pulling in scikit-learn purely for two functions.
"""

from __future__ import annotations

import math
import re
from typing import Iterable

STOPWORDS = frozenset(
    {
        "the", "a", "an", "and", "or", "of", "in", "on", "at", "to", "for",
        "with", "from", "by", "is", "are", "its", "this", "that", "as",
        "into", "their", "they", "be", "it", "offering", "tour", "guided",
    }
)

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    """Lower-case, alphanumeric tokens minus stopwords."""
    if not text:
        return []
    return [
        token
        for token in _TOKEN_RE.findall(text.lower())
        if token not in STOPWORDS and len(token) > 1
    ]


class TfidfVectorizer:
    """Plain-Python TF-IDF vectorizer producing sparse dict vectors.

    Each vector maps feature index -> smoothed TF-IDF weight. Feature
    indices follow :attr:`vocabulary_` insertion order.
    """

    def __init__(self) -> None:
        self.vocabulary_: dict[str, int] = {}
        self.idf_: dict[str, float] = {}

    def fit(self, raw_documents: Iterable[str]) -> "TfidfVectorizer":
        """Build the vocabulary and inverse document frequencies."""
        docs = [set(tokenize(doc)) for doc in raw_documents]
        doc_count = len(docs)
        df: dict[str, int] = {}
        vocabulary: dict[str, int] = {}
        for terms in docs:
            for term in terms:
                df[term] = df.get(term, 0) + 1
                if term not in vocabulary:
                    vocabulary[term] = len(vocabulary)
        self.vocabulary_ = vocabulary
        self.idf_ = {
            term: math.log((1 + doc_count) / (1 + df[term])) + 1.0
            for term in vocabulary
        }
        return self

    def transform(self, raw_documents: Iterable[str]) -> list[dict[int, float]]:
        """Return one sparse TF-IDF dict vector per input document."""
        vectors: list[dict[int, float]] = []
        for doc in raw_documents:
            tokens = tokenize(doc)
            if not tokens:
                vectors.append({})
                continue
            counts: dict[str, int] = {}
            for term in tokens:
                counts[term] = counts.get(term, 0) + 1
            vector: dict[int, float] = {}
            for term, count in counts.items():
                index = self.vocabulary_.get(term)
                if index is not None:
                    vector[index] = (count / len(tokens)) * self.idf_[term]
            vectors.append(vector)
        return vectors


def cosine_similarity(vector_a: dict[int, float], vector_b: dict[int, float]) -> float:
    """Cosine similarity between two sparse dict vectors, bounded to [0, 1]."""
    if not vector_a or not vector_b:
        return 0.0
    dot = sum(weight * vector_b.get(index, 0.0) for index, weight in vector_a.items())
    norm_a = math.sqrt(sum(weight * weight for weight in vector_a.values()))
    norm_b = math.sqrt(sum(weight * weight for weight in vector_b.values()))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return max(0.0, min(1.0, dot / (norm_a * norm_b)))