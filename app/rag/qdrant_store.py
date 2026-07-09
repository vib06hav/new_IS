from __future__ import annotations

from functools import lru_cache
import time
from typing import Any

from app.config import settings
from app.rag.embeddings import embed_text
from app.telemetry.observability import increment_counter, record_histogram, start_span


class QdrantUnavailableError(RuntimeError):
    pass


def qdrant_enabled() -> bool:
    return bool(settings.QDRANT_URL) and not bool(settings.QDRANT_DISABLE)


@lru_cache(maxsize=1)
def get_qdrant_client():
    if not qdrant_enabled():
        raise QdrantUnavailableError("Qdrant is disabled or QDRANT_URL is not configured")

    from qdrant_client import QdrantClient

    kwargs: dict[str, Any] = {
        "url": settings.QDRANT_URL,
        "timeout": settings.QDRANT_TIMEOUT_SECONDS,
    }
    if settings.QDRANT_API_KEY:
        kwargs["api_key"] = settings.QDRANT_API_KEY
    return QdrantClient(**kwargs)


def ensure_question_collection() -> None:
    client = get_qdrant_client()
    try:
        client.get_collection(settings.QDRANT_COLLECTION)
        return
    except Exception:
        pass

    from qdrant_client.models import Distance, VectorParams

    client.create_collection(
        collection_name=settings.QDRANT_COLLECTION,
        vectors_config=VectorParams(size=settings.RAG_EMBEDDING_DIMENSION, distance=Distance.COSINE),
    )


def upsert_question_point(*, point_id: str, text: str, payload: dict[str, Any]) -> dict[str, Any]:
    started_at = time.perf_counter()
    status = "skipped"
    if not qdrant_enabled():
        return {"status": "skipped", "reason": "qdrant_disabled"}

    with start_span(
        "rag.index",
        {
            "rag.provider": "qdrant",
            "rag.collection": settings.QDRANT_COLLECTION,
            "rag.entity_type": "question_version",
        },
    ):
        try:
            vector = embed_text(text)
            if not vector:
                return {"status": "skipped", "reason": "empty_embedding"}
            if len(vector) != settings.RAG_EMBEDDING_DIMENSION:
                status = "failed"
                return {
                    "status": "failed",
                    "reason": "embedding_dimension_mismatch",
                    "expected_dimension": settings.RAG_EMBEDDING_DIMENSION,
                    "actual_dimension": len(vector),
                }

            ensure_question_collection()

            from qdrant_client.models import PointStruct

            get_qdrant_client().upsert(
                collection_name=settings.QDRANT_COLLECTION,
                points=[
                    PointStruct(
                        id=point_id,
                        vector=vector,
                        payload=payload,
                    )
                ],
            )
            status = "indexed"
            return {"status": "indexed", "point_id": point_id, "collection": settings.QDRANT_COLLECTION}
        finally:
            attributes = {"provider": "qdrant", "collection": settings.QDRANT_COLLECTION, "status": status}
            increment_counter("agis_rag_index_total", attributes=attributes)
            record_histogram("agis_rag_index_duration_seconds", time.perf_counter() - started_at, attributes=attributes)


def search_question_points(*, query_text: str, limit: int) -> list[dict[str, Any]]:
    if not qdrant_enabled():
        raise QdrantUnavailableError("Qdrant is disabled or QDRANT_URL is not configured")

    started_at = time.perf_counter()
    status = "error"
    with start_span(
        "rag.retrieval",
        {
            "rag.provider": "qdrant",
            "rag.collection": settings.QDRANT_COLLECTION,
            "rag.limit": limit,
        },
    ):
        try:
            vector = embed_text(query_text)
            if not vector:
                status = "empty_embedding"
                return []

            ensure_question_collection()
            client = get_qdrant_client()

            try:
                points = client.search(
                    collection_name=settings.QDRANT_COLLECTION,
                    query_vector=vector,
                    limit=limit,
                    with_payload=True,
                )
            except AttributeError:
                response = client.query_points(
                    collection_name=settings.QDRANT_COLLECTION,
                    query=vector,
                    limit=limit,
                    with_payload=True,
                )
                points = response.points

            results: list[dict[str, Any]] = []
            for point in points:
                payload = point.payload if isinstance(point.payload, dict) else {}
                results.append(
                    {
                        "point_id": str(point.id),
                        "score": float(getattr(point, "score", 0.0) or 0.0),
                        "payload": payload,
                    }
                )
            status = "success"
            return results
        finally:
            attributes = {"provider": "qdrant", "collection": settings.QDRANT_COLLECTION, "status": status}
            increment_counter("agis_rag_retrievals_total", attributes=attributes)
            record_histogram("agis_rag_retrieval_duration_seconds", time.perf_counter() - started_at, attributes=attributes)
