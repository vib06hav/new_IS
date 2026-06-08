from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable
from uuid import UUID

from sqlalchemy.orm import Session

from app.config import settings
from app.rag.qdrant_store import qdrant_enabled, search_question_points

LexicalFallback = Callable[[], list[dict[str, Any]]]


@dataclass(frozen=True)
class QuestionRetrievalResult:
    examples: list[dict[str, Any]]
    snapshot: dict[str, Any]


def build_regeneration_query_text(
    *,
    theme_title: str,
    theme_direction: str,
    question_role: str,
    question_text: str,
) -> str:
    return "\n".join(
        part
        for part in [
            f"Theme: {theme_title}" if theme_title else "",
            f"Line of inquiry: {theme_direction}" if theme_direction else "",
            f"Question role: {question_role}" if question_role else "",
            f"Current question: {question_text}" if question_text else "",
        ]
        if part
    ).strip()


def retrieve_question_regeneration_examples(
    *,
    db: Session,
    application_id: UUID,
    focus_area_id: str,
    theme_title: str,
    theme_direction: str,
    question_role: str,
    question_text: str,
    lexical_fallback: LexicalFallback,
) -> QuestionRetrievalResult:
    query_text = build_regeneration_query_text(
        theme_title=theme_title,
        theme_direction=theme_direction,
        question_role=question_role,
        question_text=question_text,
    )
    base_snapshot = {
        "strategy_version": "qdrant_regeneration_v1",
        "provider": "qdrant" if qdrant_enabled() else "lexical_fallback",
        "collection": settings.QDRANT_COLLECTION,
        "embedding_model": settings.RAG_EMBEDDING_MODEL,
        "query_text": query_text,
        "filters": {
            "exclude_application_id": str(application_id),
            "prefer_focus_area_id": focus_area_id,
            "prefer_question_role": question_role,
        },
        "candidate_limit": settings.RAG_CANDIDATE_LIMIT,
        "limit": settings.RAG_RETRIEVAL_LIMIT,
    }

    if not qdrant_enabled():
        examples = lexical_fallback()
        return QuestionRetrievalResult(
            examples=examples,
            snapshot={
                **base_snapshot,
                "provider": "lexical_fallback",
                "fallback_reason": "qdrant_disabled",
                "retrieved_examples": examples,
            },
        )

    try:
        candidates = search_question_points(query_text=query_text, limit=settings.RAG_CANDIDATE_LIMIT)
        examples, selected = _select_examples(
            candidates=candidates,
            application_id=application_id,
            focus_area_id=focus_area_id,
            question_role=question_role,
            limit=settings.RAG_RETRIEVAL_LIMIT,
        )
        if examples:
            return QuestionRetrievalResult(
                examples=examples,
                snapshot={
                    **base_snapshot,
                    "provider": "qdrant",
                    "fallback_reason": None,
                    "selected_points": selected,
                    "retrieved_examples": examples,
                },
            )

        fallback_examples = lexical_fallback()
        return QuestionRetrievalResult(
            examples=fallback_examples,
            snapshot={
                **base_snapshot,
                "provider": "lexical_fallback",
                "fallback_reason": "qdrant_empty_after_filtering",
                "selected_points": [],
                "retrieved_examples": fallback_examples,
            },
        )
    except Exception as exc:
        fallback_examples = lexical_fallback()
        return QuestionRetrievalResult(
            examples=fallback_examples,
            snapshot={
                **base_snapshot,
                "provider": "lexical_fallback",
                "fallback_reason": f"qdrant_error:{type(exc).__name__}",
                "retrieved_examples": fallback_examples,
            },
        )


def retrieve_question_generation_context(
    *,
    application_id: UUID,
    question_bundle: dict[str, Any],
) -> dict[str, Any]:
    focus_area_contexts: list[dict[str, Any]] = []
    base_snapshot = {
        "strategy_version": "qdrant_generation_v1",
        "provider": "qdrant" if qdrant_enabled() else "disabled",
        "collection": settings.QDRANT_COLLECTION,
        "embedding_model": settings.RAG_EMBEDDING_MODEL,
        "candidate_limit": settings.RAG_CANDIDATE_LIMIT,
        "limit_per_focus_area": settings.RAG_RETRIEVAL_LIMIT,
    }

    if not qdrant_enabled():
        return {
            **base_snapshot,
            "fallback_reason": "qdrant_disabled",
            "focus_area_examples": [],
        }

    try:
        for item in question_bundle.get("focus_areas", []) or []:
            focus_area = item.get("focus_area") if isinstance(item, dict) else None
            if not isinstance(focus_area, dict):
                continue
            focus_area_id = str(focus_area.get("focus_area_id") or "").strip()
            if not focus_area_id:
                continue
            query_text = build_generation_query_text(focus_area_item=item)
            if not query_text:
                continue

            candidates = search_question_points(query_text=query_text, limit=settings.RAG_CANDIDATE_LIMIT)
            examples, selected = _select_examples(
                candidates=candidates,
                application_id=application_id,
                focus_area_id=focus_area_id,
                question_role="",
                limit=settings.RAG_RETRIEVAL_LIMIT,
            )
            focus_area_contexts.append(
                {
                    "focus_area_id": focus_area_id,
                    "focus_area_title": focus_area.get("title"),
                    "query_text": query_text,
                    "selected_points": selected,
                    "examples": examples,
                }
            )

        return {
            **base_snapshot,
            "provider": "qdrant",
            "fallback_reason": None,
            "focus_area_examples": focus_area_contexts,
        }
    except Exception as exc:
        return {
            **base_snapshot,
            "provider": "disabled",
            "fallback_reason": f"qdrant_error:{type(exc).__name__}",
            "focus_area_examples": [],
        }


def build_generation_query_text(*, focus_area_item: dict[str, Any]) -> str:
    focus_area = focus_area_item.get("focus_area") if isinstance(focus_area_item, dict) else {}
    focus_area = focus_area if isinstance(focus_area, dict) else {}
    themes = focus_area_item.get("themes") if isinstance(focus_area_item, dict) else []
    signals = focus_area_item.get("signals") if isinstance(focus_area_item, dict) else []

    parts = [
        f"Focus area: {focus_area.get('title')}" if focus_area.get("title") else "",
        f"Territory: {focus_area.get('territory')}" if focus_area.get("territory") else "",
        (
            f"Why this is worth time: {focus_area.get('what_makes_it_worth_time')}"
            if focus_area.get("what_makes_it_worth_time")
            else ""
        ),
        f"Interview direction: {focus_area.get('interview_direction')}" if focus_area.get("interview_direction") else "",
    ]
    for theme in themes or []:
        if not isinstance(theme, dict):
            continue
        parts.extend(
            [
                f"Theme: {theme.get('title')}" if theme.get("title") else "",
                f"Theme axis: {theme.get('unifying_axis')}" if theme.get("unifying_axis") else "",
                f"Theme direction: {theme.get('interview_direction')}" if theme.get("interview_direction") else "",
            ]
        )
    for signal_pair in signals or []:
        if not isinstance(signal_pair, dict):
            continue
        signal = signal_pair.get("signal") if isinstance(signal_pair.get("signal"), dict) else {}
        parts.extend(
            [
                f"Signal: {signal.get('title')}" if signal.get("title") else "",
                f"Observation: {signal.get('core_observation')}" if signal.get("core_observation") else "",
                f"Opening: {signal.get('interview_opening')}" if signal.get("interview_opening") else "",
            ]
        )
    return "\n".join(part for part in parts if part).strip()


def _select_examples(
    *,
    candidates: list[dict[str, Any]],
    application_id: UUID,
    focus_area_id: str,
    question_role: str,
    limit: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    scored: list[tuple[float, dict[str, Any]]] = []
    for candidate in candidates:
        payload = candidate.get("payload") if isinstance(candidate.get("payload"), dict) else {}
        if str(payload.get("application_id")) == str(application_id):
            continue
        score = float(candidate.get("score") or 0.0)
        rating_avg = _coerce_float(payload.get("rating_avg"))
        if rating_avg is not None:
            score += rating_avg / 10.0
        if str(payload.get("focus_area_id") or "") == focus_area_id:
            score += 0.05
        if question_role and str(payload.get("question_role") or "") == question_role:
            score += 0.05
        scored.append((score, candidate))

    scored.sort(key=lambda item: item[0], reverse=True)

    examples: list[dict[str, Any]] = []
    selected: list[dict[str, Any]] = []
    for reranked_score, candidate in scored[:limit]:
        payload = candidate.get("payload") if isinstance(candidate.get("payload"), dict) else {}
        examples.append(
            {
                "question_text": payload.get("question_text"),
                "theme_title": payload.get("theme_title"),
                "theme_direction": payload.get("theme_direction"),
                "question_role": payload.get("question_role"),
                "why_this": payload.get("why_this"),
                "rating_avg": payload.get("rating_avg"),
                "rating_count": payload.get("rating_count"),
                "retrieval_score": round(reranked_score, 4),
            }
        )
        selected.append(
            {
                "point_id": candidate.get("point_id"),
                "score": candidate.get("score"),
                "reranked_score": round(reranked_score, 4),
                "application_id": payload.get("application_id"),
                "focus_area_id": payload.get("focus_area_id"),
                "rating_avg": payload.get("rating_avg"),
            }
        )
    return examples, selected


def _coerce_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None
