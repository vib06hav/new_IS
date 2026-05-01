import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agents.bundle_constructor import construct_bundle
from app.agents.projection_builder import build_projection
from app.agents.report_annotations import build_report_annotations
from app.agents.signal_detector import detect_signals
from app.agents.interview_generator import build_interview_messages
from app.agents.signal_interpreter import build_signal_interpreter_messages
from app.policy.guard import validate_question_groups, validate_signals
from app.projection.ros_projector import project_ros
from app.ros.assembler import assemble_ros_v1

FIXTURE_DIR = ROOT / "tests" / "pipeline_stages"
OUTPUT_DIR = ROOT / "tests" / "stage17_fake_llm_output"


def _write_json(path: Path, payload) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    canonical_fixture = FIXTURE_DIR / "11_canonical_assembled.json"
    entity_map_fixture = FIXTURE_DIR / "12_entity_id_map.json"

    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    canonical = json.loads(canonical_fixture.read_text(encoding="utf-8"))
    expected_entity_id_map = json.loads(entity_map_fixture.read_text(encoding="utf-8"))

    page_1, page_2, page_3, _, projected_entity_map = project_ros(canonical)
    if projected_entity_map != expected_entity_id_map:
        raise RuntimeError("Projected entity_id_map does not match the fixture expected by Stage 1.7.")

    deterministic_signals = detect_signals(canonical, expected_entity_id_map)
    projection = build_projection(canonical, expected_entity_id_map, deterministic_signals)
    _write_json(OUTPUT_DIR / "01_call_1_projection_input.json", projection)

    essay_fragments = projection.get("essay_fragments", [])
    fragments_by_entity = {}
    for fragment in essay_fragments:
        fragments_by_entity.setdefault(fragment["entity_id"], []).append(fragment["fragment_id"])

    call_1_messages = build_signal_interpreter_messages(projection)
    _write_json(OUTPUT_DIR / "02_call_1_prompt_messages.json", call_1_messages)

    fake_call_1_response = {
        "signals": [
            {
                "signal_id": "SIG-001",
                "title": "Tech Identity Without Visible Practice",
                "evidence_anchor": "The engineering essay makes technology central to the applicant's identity and future direction.",
                "direct_read": "The record contains strong technology-facing language but little visible self-directed technical building work in activities.",
                "what_remains_open": "Whether the applicant's technology-facing identity is already grounded in lived practice or still mostly aspirational.",
                "why_it_matters": "Resolving this changes how the applicant's entire technology-facing self-presentation should be understood.",
                "referenced_entity_ids": ["ESS-001", "ACT-001", "ACT-002", "ACT-003", "ACT-004"],
                "supporting_det_signal_ids": ["DET-003", "DET-004"],
                "supporting_fragment_ids": fragments_by_entity.get("ESS-001", [])[:2],
            },
            {
                "signal_id": "SIG-002",
                "title": "Strong Scores, Real Reasoning Unknown",
                "evidence_anchor": "The academic and test record shows very high performance, especially in mathematics.",
                "direct_read": "The applicant performs strongly in structured academic problem-solving across school and JEE Mains.",
                "what_remains_open": "How the applicant reasons when the problem is open-ended, ambiguous, or not exam-shaped.",
                "why_it_matters": "This determines whether the applicant's evident capability extends beyond structured performance settings.",
                "referenced_entity_ids": ["ACA-002", "ACA-003", "ACA-004", "TEST-001"],
                "supporting_det_signal_ids": ["DET-001"],
                "supporting_fragment_ids": [],
            },
            {
                "signal_id": "SIG-003",
                "title": "Community Action and Actual Ownership",
                "evidence_anchor": "The community essay describes initiating a stray-dog support effort with classmates and responding to neighborhood resistance.",
                "direct_read": "The applicant can narrate a socially grounded initiative involving persistence, persuasion, and coordination.",
                "what_remains_open": "How much of the decision-making and adaptation in that effort was personally owned by the applicant in practice.",
                "why_it_matters": "Resolving this changes whether the story reads as real agency or mostly participant-level involvement.",
                "referenced_entity_ids": ["ESS-002", "LEAD-005"],
                "supporting_det_signal_ids": ["DET-002"],
                "supporting_fragment_ids": fragments_by_entity.get("ESS-002", [])[:1],
            },
        ],
        "themes": [
            {
                "theme_id": "THEME-001",
                "title": "Aspirational Technologist or Practiced Builder",
                "framing": "This theme concerns the relationship between the applicant's stated technology identity and their demonstrated lived practice.",
                "what_this_theme_must_resolve": "Whether the applicant's technology-facing identity is already practiced and self-directed or still primarily aspirational.",
                "supporting_signal_ids": ["SIG-001", "SIG-002"],
            },
            {
                "theme_id": "THEME-002",
                "title": "Initiative, Ownership, and Real Agency",
                "framing": "This theme concerns whether the applicant's stories of contribution reflect genuine ownership under friction rather than surface participation.",
                "what_this_theme_must_resolve": "How the applicant actually acts, decides, and adapts when responsibility becomes real.",
                "supporting_signal_ids": ["SIG-003"],
            },
        ],
    }
    _write_json(OUTPUT_DIR / "03_call_1_fake_llm_response.json", fake_call_1_response)

    validated_call_1 = validate_signals(
        raw_text=json.dumps(fake_call_1_response),
        entity_id_map=expected_entity_id_map,
        deterministic_signals=deterministic_signals,
        essay_fragments=essay_fragments,
    )
    if not validated_call_1["passed"]:
        _write_json(OUTPUT_DIR / "03b_call_1_validation_errors.json", validated_call_1)
        raise RuntimeError("Fake Call 1 response did not pass validate_signals.")

    _write_json(OUTPUT_DIR / "04_call_1_sanitized_output.json", validated_call_1["sanitized_output"])

    call_2_bundle = construct_bundle(
        validated_call_1_output=validated_call_1["sanitized_output"],
        canonical=canonical,
        entity_id_map=expected_entity_id_map,
    )
    _write_json(OUTPUT_DIR / "05_call_2_bundle_input.json", call_2_bundle)

    call_2_messages = build_interview_messages(call_2_bundle, expected_entity_id_map)
    _write_json(OUTPUT_DIR / "06_call_2_prompt_messages.json", call_2_messages)

    fake_call_2_response = {
        "question_groups": [
            {
                "theme_id": "THEME-001",
                "group_title": "Technology Identity Questions",
                "questions": [
                    "Your essay makes technology sound central to how you see yourself. Outside coursework, where have you actually built something technical on your own and what happened when it became difficult?",
                    "Your academic record shows very strong structured performance, especially in mathematics. What is a problem you pursued when there was no clear method or answer key, and how did you know what to try next?",
                    "Looking at your current record, what is the strongest evidence you would give that technology is something you do and not only something you want to do?"
                ],
            },
            {
                "theme_id": "THEME-002",
                "group_title": "Ownership and Agency Questions",
                "questions": [
                    "In the stray-dog effort, what was one decision you made yourself after residents pushed back, and why did you choose that response instead of another one?",
                    "When you say you initiated that effort with classmates, what part of the work would not have happened if you had stepped away?",
                    "What did that experience teach you about the difference between caring about an issue and actually taking responsibility for it when other people are uncomfortable?"
                ],
            },
        ]
    }
    _write_json(OUTPUT_DIR / "07_call_2_fake_llm_response.json", fake_call_2_response)

    validated_call_2 = validate_question_groups(
        raw_text=json.dumps(fake_call_2_response),
        entity_id_map=expected_entity_id_map,
        bundle=call_2_bundle,
    )
    if not validated_call_2["passed"]:
        _write_json(OUTPUT_DIR / "07b_call_2_validation_errors.json", validated_call_2)
        raise RuntimeError("Fake Call 2 response did not pass validate_question_groups.")

    _write_json(OUTPUT_DIR / "08_call_2_sanitized_output.json", validated_call_2["sanitized_output"])

    ros_output = assemble_ros_v1(
        page_1=page_1,
        page_2=page_2,
        page_3=page_3,
        themes=validated_call_1["sanitized_output"]["themes"],
        signals=validated_call_1["sanitized_output"]["signals"],
        question_groups=validated_call_2["sanitized_output"]["question_groups"],
        report_metadata={
            "application_number": canonical["identifiers"]["application_id"],
            "generated_at": "2026-03-26T00:00:00Z",
            "canonical_version": canonical.get("canonical_version", "unknown"),
            "report_version": "ROS_v1",
            "generation_mode": "fake_llm_harness",
        },
    )
    ros_output["signal_data"] = {
        "deterministic_signals": deterministic_signals,
        "signals": validated_call_1["sanitized_output"]["signals"],
        "themes": validated_call_1["sanitized_output"]["themes"],
        "annotations": build_report_annotations(
            validated_call_1["sanitized_output"]["signals"],
            validated_call_1["sanitized_output"]["themes"],
            expected_entity_id_map,
            essay_fragments=essay_fragments,
        ),
    }
    _write_json(OUTPUT_DIR / "09_final_ros.json", ros_output)

    print(f"Wrote Stage 1.7 fake-LLM artifacts to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
