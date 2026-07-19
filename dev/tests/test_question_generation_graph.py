import uuid
from unittest.mock import patch

from app.agents.question_generation_graph import (
    QUESTION_GENERATION_GRAPH_VERSION,
    run_question_generation_graph,
)
from app.llm.client import LLMClientError


def test_question_generation_graph_success_routes_through_rag_llm_and_validation():
    application_id = str(uuid.uuid4())
    question_bundle = {"focus_areas": [{"focus_area": {"focus_area_id": "FA-001", "title": "Builder"}}]}
    entity_id_map = [{"entity_id": "SIG-001"}]
    rag_context = {"provider": "disabled", "focus_area_examples": []}
    validation_result = {
        "passed": True,
        "sanitized_output": {"question_groups": [{"focus_area_id": "FA-001", "questions": []}]},
        "violations_log": [],
    }

    with patch(
        "app.agents.question_generation_graph.retrieve_question_generation_context",
        return_value=rag_context,
    ) as retrieve_mock, patch(
        "app.agents.question_generation_graph.generate_interview",
        return_value='{"question_groups":[]}',
    ) as generate_mock, patch(
        "app.agents.question_generation_graph.validate_question_groups",
        return_value=validation_result,
    ) as validate_mock:
        result = run_question_generation_graph(
            application_id=application_id,
            question_bundle=question_bundle,
            entity_id_map=entity_id_map,
        )

    assert result.route == "success"
    assert result.passed is True
    assert result.rag_context == rag_context
    assert result.raw_output == '{"question_groups":[]}'
    assert result.validation_result == validation_result
    assert result.graph_metadata["orchestrator"] == "langgraph"
    assert result.graph_metadata["graph_version"] == QUESTION_GENERATION_GRAPH_VERSION
    retrieve_mock.assert_called_once()
    generate_mock.assert_called_once_with(question_bundle, entity_id_map, rag_context=rag_context)
    validate_mock.assert_called_once_with('{"question_groups":[]}', entity_id_map, question_bundle)


def test_question_generation_graph_returns_transport_error_without_validation():
    application_id = str(uuid.uuid4())
    rag_context = {"provider": "disabled", "fallback_reason": "qdrant_disabled", "focus_area_examples": []}

    with patch(
        "app.agents.question_generation_graph.retrieve_question_generation_context",
        return_value=rag_context,
    ), patch(
        "app.agents.question_generation_graph.generate_interview",
        side_effect=LLMClientError("capacity exhausted"),
    ), patch("app.agents.question_generation_graph.validate_question_groups") as validate_mock:
        result = run_question_generation_graph(
            application_id=application_id,
            question_bundle={"focus_areas": []},
            entity_id_map=[],
        )

    assert result.route == "transport_error"
    assert result.passed is False
    assert result.error_message == "capacity exhausted"
    assert result.validation_result is None
    assert result.rag_context == rag_context
    validate_mock.assert_not_called()


def test_question_generation_graph_exposes_validation_failure_route():
    application_id = str(uuid.uuid4())
    validation_result = {
        "passed": False,
        "violations_log": [{"field": "question_groups", "type": "missing"}],
    }

    with patch(
        "app.agents.question_generation_graph.retrieve_question_generation_context",
        return_value={"provider": "disabled", "focus_area_examples": []},
    ), patch(
        "app.agents.question_generation_graph.generate_interview",
        return_value="{}",
    ), patch(
        "app.agents.question_generation_graph.validate_question_groups",
        return_value=validation_result,
    ):
        result = run_question_generation_graph(
            application_id=application_id,
            question_bundle={"focus_areas": []},
            entity_id_map=[],
        )

    assert result.route == "validation_failed"
    assert result.passed is False
    assert result.validation_result == validation_result
