from __future__ import annotations

from functools import lru_cache

from app.config import settings


@lru_cache(maxsize=1)
def _embedding_model():
    from fastembed import TextEmbedding

    return TextEmbedding(model_name=settings.RAG_EMBEDDING_MODEL)


def embed_text(text: str) -> list[float]:
    cleaned = " ".join(str(text or "").split()).strip()
    if not cleaned:
        return []
    embeddings = list(_embedding_model().embed([cleaned]))
    if not embeddings:
        return []
    vector = embeddings[0]
    if hasattr(vector, "tolist"):
        return [float(item) for item in vector.tolist()]
    return [float(item) for item in vector]
