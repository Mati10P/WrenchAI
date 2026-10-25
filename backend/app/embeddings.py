"""Bounded Gemini embedding adapter. No vehicle context is sent here."""

import json
import math
import os
from functools import lru_cache
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

MODEL = "gemini-embedding-001"
DIMENSIONS = 768


class EmbeddingError(Exception):
    pass


def unit_vector(values):
    if not isinstance(values, list) or len(values) != DIMENSIONS:
        raise ValueError("Invalid embedding dimensions")
    if any(
        isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)
        for v in values
    ):
        raise ValueError("Invalid embedding values")
    norm = math.sqrt(sum(v * v for v in values))
    if not math.isfinite(norm) or norm == 0:
        raise ValueError("Invalid embedding norm")
    return [v / norm for v in values]


def embed(texts, task, timeout=30):
    if (
        task not in {"RETRIEVAL_DOCUMENT", "RETRIEVAL_QUERY"}
        or not 1 <= len(texts) <= 32
    ):
        raise ValueError("Invalid embedding batch")
    if any(not isinstance(t, str) or not t.strip() or len(t) > 3000 for t in texts):
        raise ValueError("Invalid embedding input")
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        raise EmbeddingError("embedding_key_missing")
    requests = [
        {
            "model": f"models/{MODEL}",
            "content": {"parts": [{"text": t}]},
            "taskType": task,
            "outputDimensionality": DIMENSIONS,
        }
        for t in texts
    ]
    req = Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:batchEmbedContents",
        data=json.dumps({"requests": requests}).encode(),
        headers={"Content-Type": "application/json", "x-goog-api-key": key},
        method="POST",
    )
    try:
        with urlopen(req, timeout=timeout) as response:
            raw = response.read(2_000_001)
        if len(raw) > 2_000_000:
            raise ValueError("Oversized embedding response")
        entries = json.loads(raw)["embeddings"]
        if len(entries) != len(texts):
            raise ValueError("Incomplete embedding batch")
        return [unit_vector(e["values"]) for e in entries]
    except HTTPError as exc:
        raise EmbeddingError(f"embedding_http_{exc.code}") from None
    except (URLError, TimeoutError, OSError):
        raise EmbeddingError("embedding_unavailable") from None
    except (ValueError, KeyError, TypeError):
        raise EmbeddingError("embedding_invalid_response") from None


@lru_cache(maxsize=128)
def query_vector(query):
    return embed([query], "RETRIEVAL_QUERY", timeout=8)[0]
