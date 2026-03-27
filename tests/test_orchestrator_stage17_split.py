from contextlib import ExitStack
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
import uuid

from app.agents.orchestrator import run_pipeline


def test_run_pipeline_splits_theme_generation_into_call_1():
    application_id = str(uuid.uuid4())
    dummy_app = SimpleNamespace(pipeline_status="processing", pipeline_confidence=None)

    db = MagicMock()
    canonical_query = MagicMock()
    application_query = MagicMock()
    canonical_query.filter.return_value.first.return_value = None
    application_query.filter.return_value.first.return_value = dummy_app

    def query_side_effect(model):
        if model.__name__ == "CanonicalRecord":
            return canonical_query
        if model.__name__ == "Application":
            return application_query
        raise AssertionError(f"Unexpected model queried: {model}")

    db.query.side_effect = query_side_effect

    canonical_data = {
        "identifiers": {"application_id": application_id},
        "extraction_confidence": {"aggregate_confidence": 0.91},
    }
    entity_id_map = [{"entity_id": "ACA-001", "collection": "academic_entries", "descriptor": "10TH"}]
    call_1_validated = {
        "signals": [
            {
                "signal_id": "SIG-001",
                "theme_id": "THEME-001",
                "title": "Signal title",
                "evidence_anchor": "Evidence anchor",
                "direct_read": "Direct read",
                "what_remains_open": "What remains open",
                "why_it_matters": "Why it matters",
                "referenced_entity_ids": ["ACA-001"],
                "supporting_det_signal_ids": ["DET-001"],
                "supporting_fragment_ids": [],
            }
        ],
        "themes": [
            {
                "theme_id": "THEME-001",
                "title": "Theme title",
                "framing": "Theme framing",
                "what_this_theme_must_resolve": "Theme resolution",
                "supporting_signal_ids": ["SIG-001"],
                "referenced_entity_ids": ["ACA-001"],
            }
        ],
    }
    theme_first_bundle = {
        "application_id": application_id,
        "themes": call_1_validated["themes"],
        "theme_signal_evidence_groups": [
            {
                "theme": call_1_validated["themes"][0],
                "signal_evidence_pairs": [
                    {
                        "signal": call_1_validated["signals"][0],
                        "evidence": [{"entity_id": "ACA-001", "collection": "academic_entries", "content": {}}],
                    }
                ],
            }
        ],
    }
    question_groups_validated = {
        "question_groups": [
            {
                "theme_id": "THEME-001",
                "group_title": "Question group",
                "questions": ["Why did this applicant choose that path?"],
            }
        ]
    }
    ros_document = {
        "report_metadata": {"report_version": "ROS_v1"},
        "page_1_background_profile": {"identity": {}},
        "page_2_academic_and_engagement": {"academic_records": []},
        "page_3_essays": {"essays": []},
        "page_4_focus_areas": {"themes": call_1_validated["themes"], "signals": call_1_validated["signals"]},
        "page_5_question_groups": {"question_groups": question_groups_validated["question_groups"]},
    }

    with ExitStack() as stack:
        stack.enter_context(patch("app.utils.layout_normalizer.normalize_layout", return_value=[]))
        stack.enter_context(patch("app.agents.orchestrator.extract_layout_blocks", return_value={"blocks": [{"text": "dummy"}], "page_count": 1}))
        stack.enter_context(patch("app.agents.orchestrator.detect_sections", return_value={}))
        stack.enter_context(
            patch(
                "app.agents.orchestrator.resolve_section_scopes",
                return_value={
                    "section_map": {},
                    "section_slices": {},
                    "academic_rows": [],
                    "test_rows": [],
                },
            )
        )
        stack.enter_context(patch("app.agents.orchestrator.extract_personal_info", return_value={"identifiers": {}, "confidence_score": 0.8}))
        stack.enter_context(patch("app.agents.orchestrator.extract_family_background", return_value={"family_background": {}, "confidence_score": 0.7}))
        stack.enter_context(patch("app.agents.orchestrator.extract_geographic_context", return_value={}))
        stack.enter_context(patch("app.agents.orchestrator.extract_academic_records", return_value={"academic_entries": [], "confidence_score": 0.8}))
        stack.enter_context(patch("app.agents.orchestrator.extract_test_records", return_value={"test_entries": [], "confidence_score": 0.8}))
        stack.enter_context(patch("app.agents.orchestrator.extract_essays", return_value={"essay_entries": [], "confidence_score": 0.8}))
        stack.enter_context(patch("app.agents.orchestrator.extract_activities", return_value={"activity_entries": [], "confidence_score": 0.8}))
        stack.enter_context(patch("app.agents.orchestrator.detect_cross_sections", return_value={"confidence_score": 0.8}))
        stack.enter_context(patch("app.agents.orchestrator.analyze_integrity", return_value={"confidence_score": 0.8}))
        stack.enter_context(patch("app.agents.orchestrator.assemble_canonical", return_value=canonical_data))
        stack.enter_context(
            patch(
                "app.agents.orchestrator.project_ros",
                return_value=({"identity": {}}, {"academic_records": []}, {"essays": []}, canonical_data, entity_id_map),
            )
        )
        stack.enter_context(patch("app.agents.orchestrator.detect_signals", return_value=[{"signal_id": "DET-001", "referenced_entity_ids": ["ACA-001"]}]))
        stack.enter_context(patch("app.agents.orchestrator.build_projection", return_value={"projection": True}))
        stack.enter_context(patch("app.agents.orchestrator.interpret_signals", return_value="{}"))
        stack.enter_context(
            patch(
                "app.agents.orchestrator.validate_signals",
                return_value={"passed": True, "sanitized_output": call_1_validated, "violations_log": []},
            )
        )
        construct_bundle_mock = stack.enter_context(
            patch("app.agents.orchestrator.construct_bundle", return_value=theme_first_bundle)
        )
        stack.enter_context(patch("app.agents.orchestrator.generate_interview", return_value="{}"))
        stack.enter_context(
            patch(
                "app.agents.orchestrator.validate_question_groups",
                return_value={"passed": True, "sanitized_output": question_groups_validated, "violations_log": []},
            )
        )
        assemble_ros_mock = stack.enter_context(
            patch("app.agents.orchestrator.assemble_ros_v1", return_value=ros_document)
        )
        result = run_pipeline(application_id, "dummy.pdf", db)

    assert construct_bundle_mock.call_args.args[0] == call_1_validated
    assert assemble_ros_mock.call_args.kwargs["themes"] == call_1_validated["themes"]
    assert assemble_ros_mock.call_args.kwargs["question_groups"] == question_groups_validated["question_groups"]
    assert result["ros_v1"]["page_4_focus_areas"]["themes"] == call_1_validated["themes"]
    assert result["ros_v1"]["page_4_focus_areas"]["signals"] == call_1_validated["signals"]
    assert result["ros_v1"]["page_5_question_groups"]["question_groups"] == question_groups_validated["question_groups"]
    assert result["ros_v1"]["signal_data"]["themes"] == call_1_validated["themes"]
    assert result["ros_v1"]["signal_data"]["signals"] == call_1_validated["signals"]
    assert result["ros_v1"]["signal_data"]["annotations"] == {
        "page_1_entities": {},
        "page_2_entities": {"ACA-001": {"signal_ids": ["SIG-001"], "theme_ids": ["THEME-001"]}},
        "page_3_fragments": {},
    }
