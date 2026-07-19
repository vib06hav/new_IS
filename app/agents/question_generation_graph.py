from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Literal, TypedDict
from uuid import UUID

from langgraph.graph import END, START, StateGraph

from app.agents.interview_generator import generate_interview
from app.llm.client import LLMClientError
from app.policy.guard import validate_question_groups
from app.rag.question_retrieval import retrieve_question_generation_context

logger = logging.getLogger(__name__)

QUESTION_GENERATION_GRAPH_VERSION = "question_generation_graph_v1"

QuestionGenerationRoute = Literal["success", "validation_failed", "transport_error"]


class QuestionGenerationState(TypedDict, total=False):
    application_id: str
    question_bundle: dict[str, Any]
    entity_id_map: list[dict[str, Any]]
    rag_context: dict[str, Any]
    raw_output: str
    validation_result: dict[str, Any]
    route: QuestionGenerationRoute
    error_message: str
    graph_metadata: dict[str, Any]


@dataclass(frozen=True)
class QuestionGenerationGraphResult:
    route: QuestionGenerationRoute
    rag_context: dict[str, Any]
    raw_output: str | None
    validation_result: dict[str, Any] | None
    error_message: str | None
    graph_metadata: dict[str, Any]

    @property
    def passed(self) -> bool:
        return self.route == "success" and bool((self.validation_result or {}).get("passed"))


def run_question_generation_graph(
    *,
    application_id: str,
    question_bundle: dict[str, Any],
    entity_id_map: list[dict[str, Any]],
) -> QuestionGenerationGraphResult:
    graph = _compiled_question_generation_graph()
    final_state = graph.invoke(
        {
            "application_id": application_id,
            "question_bundle": question_bundle,
            "entity_id_map": entity_id_map,
            "graph_metadata": {
                "orchestrator": "langgraph",
                "graph_version": QUESTION_GENERATION_GRAPH_VERSION,
                "nodes": ["retrieve_rag_context", "generate_questions", "validate_questions"],
            },
        }
    )
    route = final_state.get("route") or "validation_failed"
    metadata = {
        **(final_state.get("graph_metadata") or {}),
        "route": route,
    }
    return QuestionGenerationGraphResult(
        route=route,
        rag_context=final_state.get("rag_context") or {},
        raw_output=final_state.get("raw_output"),
        validation_result=final_state.get("validation_result"),
        error_message=final_state.get("error_message"),
        graph_metadata=metadata,
    )


@lru_cache(maxsize=1)
def _compiled_question_generation_graph():
    graph = StateGraph(QuestionGenerationState)
    graph.add_node("retrieve_rag_context", _retrieve_rag_context)
    graph.add_node("generate_questions", _generate_questions)
    graph.add_node("validate_questions", _validate_questions)

    graph.add_edge(START, "retrieve_rag_context")
    graph.add_edge("retrieve_rag_context", "generate_questions")
    graph.add_conditional_edges(
        "generate_questions",
        _route_after_generation,
        {
            "validate": "validate_questions",
            "end": END,
        },
    )
    graph.add_conditional_edges(
        "validate_questions",
        _route_after_validation,
        {
            "success": END,
            "validation_failed": END,
        },
    )
    return graph.compile()


def _retrieve_rag_context(state: QuestionGenerationState) -> dict[str, Any]:
    rag_context = retrieve_question_generation_context(
        application_id=UUID(state["application_id"]),
        question_bundle=state["question_bundle"],
    )
    if rag_context.get("fallback_reason"):
        logger.info(
            "question_generation_rag_context_fallback application_id=%s reason=%s",
            state["application_id"],
            rag_context.get("fallback_reason"),
        )
    else:
        logger.info(
            "question_generation_rag_context_ready application_id=%s focus_area_count=%s",
            state["application_id"],
            len(rag_context.get("focus_area_examples") or []),
        )
    return {"rag_context": rag_context}


def _generate_questions(state: QuestionGenerationState) -> dict[str, Any]:
    try:
        raw_output = generate_interview(
            state["question_bundle"],
            state["entity_id_map"],
            rag_context=state.get("rag_context"),
        )
        return {"raw_output": raw_output}
    except LLMClientError as exc:
        logger.error("LLM Call 3 Transport/Load Failure: %s", str(exc))
        return {
            "route": "transport_error",
            "error_message": str(exc),
        }


def _route_after_generation(state: QuestionGenerationState) -> Literal["validate", "end"]:
    if state.get("route") == "transport_error":
        return "end"
    return "validate"


def _validate_questions(state: QuestionGenerationState) -> dict[str, Any]:
    validation_result = validate_question_groups(
        state.get("raw_output") or "",
        state["entity_id_map"],
        state["question_bundle"],
    )
    route: QuestionGenerationRoute = "success" if validation_result.get("passed") else "validation_failed"
    return {
        "validation_result": validation_result,
        "route": route,
    }


def _route_after_validation(state: QuestionGenerationState) -> QuestionGenerationRoute:
    return state.get("route") or "validation_failed"
