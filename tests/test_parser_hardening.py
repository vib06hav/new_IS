from app.agents.activity_extractor import extract_activities
from app.agents.additional_info_extractor import extract_additional_info
from app.agents.assembler import assemble_canonical
from app.agents.academic_extractor import extract_academic_records
from app.agents.cross_section_detector import detect_cross_sections
from app.agents.integrity_analyzer import analyze_integrity
from app.agents.layout_extractor import _build_block_ir, _build_header_candidates, _build_issue_ir, _build_layout_issues, _build_page_stats
from app.agents.geographic_extractor import extract_geographic_context
from app.agents.personal_extractor import extract_personal_info
from app.agents.section_detector import detect_sections
from app.agents.test_extractor import extract_test_records
from tests.corpus_harness import _run_deterministic_pipeline_stages
from app.utils.row_grouper import build_layout_rows, group_blocks_into_rows
from app.utils.section_types import classify_section_label
from app.utils.text_normalization import normalize_pdf_text


def test_normalize_pdf_text_repairs_mojibake_and_ligatures():
    raw = "I\u00e2\u20ac\u2122ve seen co\u00e2\u20ac\u201ccurricular work with o\ufb03ce tools."
    assert normalize_pdf_text(raw) == "I've seen co-curricular work with office tools."


def test_section_detector_does_not_treat_board_name_as_section_header():
    blocks = [
        {"page": 1, "text": "Academic Records", "bbox": (30, 700, 140, 715)},
        {"page": 1, "text": "Jayshree Periwal International School", "bbox": (60, 660, 220, 672)},
        {"page": 1, "text": "CENTRAL BOARD OF SECONDARY\nEDUCATION(CBSE)", "bbox": (160, 650, 300, 685)},
        {"page": 1, "text": "2024", "bbox": (320, 660, 350, 672)},
        {"page": 1, "text": "Essays", "bbox": (30, 500, 90, 515)},
    ]

    result = detect_sections(blocks)
    labels = [section["label"] for section in result["sections"]]

    assert labels == ["Academic Records", "Essays"]
    assert result["sections"][0]["section_type"] == "academics"
    assert result["sections"][1]["section_type"] == "essays"
    assert result["sections"][0]["start_row_index"] == 0
    assert result["sections"][1]["start_row_index"] == 2
    assert len(result["rows"]) >= 3
    assert result["section_spans"][0]["start_row_index"] == 0
    assert result["section_spans"][0]["section_type"] == "academics"


def test_section_detector_does_not_treat_council_board_line_as_section_header():
    blocks = [
        {"page": 1, "text": "Academic Records", "bbox": (30, 700, 140, 715)},
        {"page": 1, "text": "COUNCIL FOR THE INDIAN SCHOOL\nCERTIFICATE EXAMINATIONS", "bbox": (150, 650, 330, 685)},
        {"page": 1, "text": "2024", "bbox": (350, 660, 380, 672)},
        {"page": 1, "text": "Essays", "bbox": (30, 500, 90, 515)},
    ]

    result = detect_sections(blocks)
    labels = [section["label"] for section in result["sections"]]

    assert labels == ["Academic Records", "Essays"]


def test_section_type_classifier_maps_known_aliases():
    assert classify_section_label("Father Details") == "parent_details"
    assert classify_section_label("Additional Information") == "additional_information"
    assert classify_section_label("Joint Entrance Examination (JEE) Main Details") == "standardized_tests"


def test_row_grouper_preserves_page_order_and_left_to_right_cells():
    blocks = [
        {"page": 2, "text": "B", "bbox": (200, 700, 220, 715)},
        {"page": 1, "text": "A2", "bbox": (200, 650, 220, 665)},
        {"page": 1, "text": "A1", "bbox": (20, 650, 60, 665)},
        {"page": 1, "text": "Top", "bbox": (20, 700, 60, 715)},
    ]

    rows = group_blocks_into_rows(blocks, y_threshold=12)
    row_texts = [[block["text"] for block in row] for row in rows]

    assert row_texts == [["Top"], ["A1", "A2"], ["B"]]


def test_build_layout_rows_exposes_shared_row_metadata():
    blocks = [
        {"page": 1, "text": "Academic Records", "bbox": (20, 700, 120, 715)},
        {"page": 1, "text": "Topper", "bbox": (220, 700, 280, 715)},
        {"page": 1, "text": "Mathematics", "bbox": (20, 660, 110, 675)},
    ]

    rows = build_layout_rows(blocks, y_threshold=12)

    assert rows[0]["row_index"] == 0
    assert rows[0]["page"] == 1
    assert rows[0]["text"] == "Academic Records Topper"
    assert rows[0]["x_span"] == [20, 280]
    assert rows[0]["y_span"] == [700, 715]
    assert rows[0]["candidate_header_score"] > 0


def test_section_detector_can_reuse_prebuilt_rows():
    blocks = [
        {"page": 1, "text": "Academic Records", "bbox": (20, 700, 120, 715)},
        {"page": 1, "text": "School Name", "bbox": (20, 660, 120, 675)},
        {"page": 1, "text": "Essays", "bbox": (20, 500, 80, 515)},
    ]
    rows = build_layout_rows(blocks, y_threshold=12)

    result = detect_sections(blocks, rows=rows)

    assert result["rows"] == rows
    assert [section["label"] for section in result["sections"]] == ["Academic Records", "Essays"]


def test_build_header_candidates_uses_row_scores_and_section_type():
    rows = [
        {"row_index": 0, "page": 1, "text": "Academic Records", "candidate_header_score": 0.65},
        {"row_index": 1, "page": 1, "text": "Mathematics", "candidate_header_score": 0.2},
    ]

    candidates = _build_header_candidates(rows)

    assert candidates == [{
        "row_index": 0,
        "page": 1,
        "text": "Academic Records",
        "section_type": "academics",
        "candidate_header_score": 0.65,
    }]


def test_layout_ir_serialization_preserves_enriched_fields():
    blocks = [{
        "page": 1,
        "text": "Academic Records",
        "clean_text": "Academic Records",
        "first_line": "Academic Records",
        "line_count": 1,
        "char_count": 16,
        "is_all_caps": False,
        "bbox": (20, 700, 120, 715),
        "x0": 20,
        "y0": 700,
        "x1": 120,
        "y1": 715,
        "center_y": 707.5,
    }]
    issues = [{
        "issue_type": "missing_text_layer",
        "severity": "high",
        "source_stage": "layout_extraction",
        "page": None,
        "message": "No extractable text blocks were found in the PDF.",
    }]

    block_ir = _build_block_ir(blocks)
    issue_ir = _build_issue_ir(issues)

    assert block_ir[0]["first_line"] == "Academic Records"
    assert block_ir[0]["char_count"] == 16
    assert issue_ir[0]["issue_type"] == "missing_text_layer"
    assert issue_ir[0]["source_stage"] == "layout_extraction"


def test_layout_page_stats_count_blocks_text_and_headers():
    blocks = [
        {"page": 1, "text": "Personal Details", "bbox": (10, 700, 100, 715)},
        {"page": 1, "text": "Aarav Jain", "bbox": (200, 700, 260, 715)},
        {"page": 2, "text": "Essays", "bbox": (10, 700, 60, 715)},
    ]

    stats = _build_page_stats(blocks, page_count=2)

    assert stats[0]["page"] == 1
    assert stats[0]["block_count"] == 2
    assert stats[0]["header_candidate_count"] == 1
    assert stats[1]["page"] == 2
    assert stats[1]["block_count"] == 1
    assert stats[1]["header_candidate_count"] == 1


def test_layout_issues_flag_missing_text_layer():
    issues = _build_layout_issues(blocks=[], page_count=3)

    assert issues == [{
        "issue_type": "missing_text_layer",
        "severity": "high",
        "source_stage": "layout_extraction",
        "page": None,
        "message": "No extractable text blocks were found in the PDF.",
    }]


def test_personal_extractor_captures_preferred_major_from_same_row():
    blocks = [
        {"page": 1, "text": "Preferred Major", "bbox": (30, 700, 120, 715)},
        {"page": 1, "text": "Computer Science and Artificial Intelligence", "bbox": (300, 700, 520, 715)},
    ]

    result = extract_personal_info(blocks)

    assert result["identifiers"]["preferred_major"] == "Computer Science and Artificial Intelligence"
    assert result["identifiers"]["declared_preferences"]["major"] == "Computer Science and Artificial Intelligence"


def test_additional_info_extractor_captures_preferred_major_from_section_row():
    blocks = [
        {"page": 3, "text": "Preferred Major", "bbox": (40, 500, 150, 515)},
        {"page": 3, "text": "Mechanical Engineering", "bbox": (300, 500, 470, 515)},
    ]

    result = extract_additional_info(blocks)

    assert result["preferred_major"] == "Mechanical Engineering"
    assert result["confidence_score"] > 0


def test_additional_info_extractor_can_use_broader_layout_search_for_same_row_value():
    section_blocks = [
        {"page": 3, "text": "Preferred Major", "bbox": (40, 500, 150, 515)},
    ]
    all_blocks = [
        {"page": 3, "text": "Preferred Major", "bbox": (40, 500, 150, 515)},
        {"page": 3, "text": "Computer Science and Artificial Intelligence", "bbox": (300, 500, 520, 515)},
        {"page": 3, "text": "References", "bbox": (40, 460, 110, 475)},
    ]

    result = extract_additional_info(section_blocks, all_blocks=all_blocks)

    assert result["preferred_major"] == "Computer Science and Artificial Intelligence"


def test_personal_extractor_parses_parent_sections_from_section_metadata():
    personal_blocks = [
        {"page": 1, "text": "Full Name", "bbox": (20, 700, 90, 715)},
        {"page": 1, "text": "Aarav Jain", "bbox": (180, 700, 240, 715)},
    ]
    parent_sections = [
        {
            "label": "Father Details",
            "blocks": [
                {"page": 1, "text": "Name", "bbox": (20, 650, 60, 665)},
                {"page": 1, "text": "Rajesh Jain", "bbox": (180, 650, 250, 665)},
                {"page": 1, "text": "Organization", "bbox": (20, 630, 90, 645)},
                {"page": 1, "text": "Acme Industries", "bbox": (180, 630, 280, 645)},
            ],
        },
        {
            "label": "Mother Details",
            "blocks": [
                {"page": 1, "text": "Name", "bbox": (20, 600, 60, 615)},
                {"page": 1, "text": "Sunita Jain", "bbox": (180, 600, 245, 615)},
                {"page": 1, "text": "Highest Degree Attained", "bbox": (20, 580, 150, 595)},
                {"page": 1, "text": "M.Sc", "bbox": (180, 580, 210, 595)},
            ],
        },
    ]

    result = extract_personal_info(personal_blocks, parent_sections=parent_sections)

    assert result["identifiers"]["full_name"] == "Aarav Jain"
    assert result["identifiers"]["family_background"]["father"]["name"] == "Rajesh Jain"
    assert result["identifiers"]["family_background"]["father"]["organization"] == "Acme Industries"
    assert result["identifiers"]["family_background"]["mother"]["name"] == "Sunita Jain"
    assert result["identifiers"]["family_background"]["mother"]["education"] == "M.Sc"


def test_personal_extractor_ignores_generic_parent_grouping_section():
    parent_sections = [
        {
            "label": "Parent Details",
            "blocks": [
                {"page": 1, "text": "Name", "bbox": (20, 650, 60, 665)},
                {"page": 1, "text": "Rajesh Jain", "bbox": (180, 650, 250, 665)},
            ],
        }
    ]

    result = extract_personal_info([], parent_sections=parent_sections)

    assert result["identifiers"]["family_background"]["father"]["name"] is None
    assert result["identifiers"]["family_background"]["mother"]["name"] is None


def test_geographic_extractor_prefers_permanent_address_when_available():
    address_sections = [
        {
            "label": "Communication Address",
            "blocks": [
                {"page": 1, "text": "Town/City", "bbox": (20, 650, 80, 665)},
                {"page": 1, "text": "Gurugram", "bbox": (180, 650, 240, 665)},
                {"page": 1, "text": "State", "bbox": (20, 630, 60, 645)},
                {"page": 1, "text": "Haryana", "bbox": (180, 630, 235, 645)},
                {"page": 1, "text": "Country Name", "bbox": (20, 610, 100, 625)},
                {"page": 1, "text": "India", "bbox": (180, 610, 215, 625)},
            ],
        },
        {
            "label": "Permanent Address",
            "blocks": [
                {"page": 1, "text": "Town/City", "bbox": (20, 580, 80, 595)},
                {"page": 1, "text": "Jaipur", "bbox": (180, 580, 220, 595)},
                {"page": 1, "text": "State", "bbox": (20, 560, 60, 575)},
                {"page": 1, "text": "Rajasthan", "bbox": (180, 560, 250, 575)},
                {"page": 1, "text": "Country Name", "bbox": (20, 540, 100, 555)},
                {"page": 1, "text": "India", "bbox": (180, 540, 215, 555)},
            ],
        },
    ]

    result = extract_geographic_context(address_sections)

    assert result["geographic_context"] == {
        "city": "Jaipur",
        "state": "Rajasthan",
        "country": "India",
    }


def test_geographic_extractor_skips_neighboring_address_labels_when_extracting_state():
    address_sections = [
        {
            "label": "Communication Address",
            "blocks": [
                {"page": 1, "text": "State", "bbox": (20, 650, 55, 665)},
                {"page": 1, "text": "District:", "bbox": (140, 650, 190, 665)},
                {"page": 1, "text": "Delhi", "bbox": (210, 650, 245, 665)},
                {"page": 1, "text": "Town/City", "bbox": (20, 630, 80, 645)},
                {"page": 1, "text": "New Delhi", "bbox": (210, 630, 270, 645)},
                {"page": 1, "text": "Country Name", "bbox": (20, 610, 100, 625)},
                {"page": 1, "text": "India", "bbox": (210, 610, 245, 625)},
            ],
        }
    ]

    result = extract_geographic_context(address_sections)

    assert result["geographic_context"] == {
        "city": "New Delhi",
        "state": "Delhi",
        "country": "India",
    }


def test_academic_extractor_can_use_shared_rows_without_regrouping():
    row_blocks = [
        {"page": 1, "text": "School Name", "bbox": (20, 700, 110, 715)},
        {"page": 1, "text": "Board", "bbox": (170, 700, 220, 715)},
        {"page": 1, "text": "Class 12", "bbox": (20, 675, 80, 690)},
        {"page": 1, "text": "Example School", "bbox": (20, 650, 120, 665)},
        {"page": 1, "text": "CBSE", "bbox": (170, 650, 210, 665)},
    ]
    rows = [
        {"row_index": 10, "blocks": row_blocks[:2]},
        {"row_index": 11, "blocks": row_blocks[2:]},
    ]

    result = extract_academic_records(row_blocks, rows=rows)

    assert len(result["academic_entries"]) == 1
    assert result["academic_entries"][0]["academic_level"] == "12"
    assert result["academic_entries"][0]["school_name"] == "Example School"
    assert result["academic_entries"][0]["board_name"] == "CBSE"


def test_academic_extractor_preserves_predicted_only_subject_rows():
    row_blocks = [
        {"page": 1, "text": "School Name", "bbox": (20, 720, 110, 735)},
        {"page": 1, "text": "Board", "bbox": (150, 720, 200, 735)},
        {"page": 1, "text": "Year of Passing", "bbox": (260, 720, 340, 735)},
        {"page": 1, "text": "Result Status", "bbox": (360, 720, 430, 735)},
        {"page": 1, "text": "Marking Scheme", "bbox": (450, 720, 540, 735)},
        {"page": 1, "text": "Obtained Percentage/CGPA", "bbox": (560, 720, 700, 735)},
        {"page": 1, "text": "12th", "bbox": (20, 695, 50, 710)},
        {"page": 1, "text": "Example School", "bbox": (80, 695, 180, 710)},
        {"page": 1, "text": "ISC", "bbox": (260, 695, 290, 710)},
        {"page": 1, "text": "2025", "bbox": (300, 695, 330, 710)},
        {"page": 1, "text": "Appearing", "bbox": (380, 695, 440, 710)},
        {"page": 1, "text": "Percentage", "bbox": (470, 695, 540, 710)},
        {"page": 1, "text": "96", "bbox": (590, 695, 605, 710)},
        {"page": 1, "text": "Predicted Marks/Grades", "bbox": (20, 670, 140, 685)},
        {"page": 1, "text": "Subject", "bbox": (120, 645, 160, 660)},
        {"page": 1, "text": "Maximum Marks/Grade", "bbox": (300, 645, 400, 660)},
        {"page": 1, "text": "Predicted Marks/Grade", "bbox": (470, 645, 570, 660)},
        {"page": 1, "text": "Mathematics", "bbox": (120, 620, 190, 635)},
        {"page": 1, "text": "100", "bbox": (300, 620, 325, 635)},
        {"page": 1, "text": "97", "bbox": (470, 620, 490, 635)},
    ]
    rows = [
        {"row_index": 0, "blocks": row_blocks[:6]},
        {"row_index": 1, "blocks": row_blocks[6:13]},
        {"row_index": 2, "blocks": [row_blocks[13]]},
        {"row_index": 3, "blocks": row_blocks[14:17]},
        {"row_index": 4, "blocks": row_blocks[17:20]},
    ]

    result = extract_academic_records(row_blocks, rows=rows)
    entry = result["academic_entries"][0]

    assert entry["academic_level"] == "12TH"
    assert entry["score_raw"] == "96"
    assert len(entry["subject_entries"]) == 1
    assert entry["subject_entries"][0]["subject_name"] == "Mathematics"
    assert entry["subject_entries"][0]["score_raw"] is None
    assert entry["subject_entries"][0]["predicted_score_raw"] == "97"


def test_academic_extractor_dedupes_stacked_duplicate_blocks():
    blocks = [
        {"page": 1, "text": "School Name", "bbox": (20, 720, 110, 735)},
        {"page": 1, "text": "Board", "bbox": (170, 720, 220, 735)},
        {"page": 1, "text": "Class 12", "bbox": (20, 695, 80, 710)},
        {"page": 1, "text": "Example School", "bbox": (20, 670, 120, 685)},
        {"page": 1, "text": "Example School", "bbox": (20.5, 670.5, 120.5, 685.5)},
        {"page": 1, "text": "CBSE", "bbox": (170, 670, 210, 685)},
    ]
    rows = [
        {"row_index": 0, "blocks": blocks[:2]},
        {"row_index": 1, "blocks": blocks[2:]},
    ]

    result = extract_academic_records(blocks, rows=rows)

    assert result["academic_entries"][0]["school_name"] == "Example School"


def test_test_extractor_can_use_shared_rows_without_regrouping():
    row_blocks = [
        {"page": 1, "text": "JEE Main", "bbox": (20, 700, 80, 715)},
        {"page": 1, "text": "Aggregate NTA Score", "bbox": (20, 675, 130, 690)},
        {"page": 1, "text": "97.69", "bbox": (180, 675, 220, 690)},
    ]
    rows = [
        {"row_index": 5, "blocks": [row_blocks[0]]},
        {"row_index": 6, "blocks": row_blocks[1:]},
    ]

    result = extract_test_records(row_blocks, rows=rows)

    assert len(result["test_entries"]) == 1
    assert result["test_entries"][0]["test_name"] == "JEE Mains"
    assert result["test_entries"][0]["total_score"] == "97.69"


def test_corpus_parent_and_12th_regressions_are_fixed():
    from pathlib import Path

    for pdf_name in [
        "Dummy App (1)_v8_filled.pdf",
        "Dummy App (2)_v8_filled.pdf",
        "Dummy App (3)_v8_filled.pdf",
        "Dummy App (5)_v8_filled.pdf",
        "Dummy App (8)_v8_filled.pdf",
    ]:
        stages = _run_deterministic_pipeline_stages(
            Path("tests/pdfs") / pdf_name,
            parser_engine_version="v2",
        )
        family_background = stages["personal_data"]["identifiers"]["family_background"]
        assert family_background["father"]["name"]
        if any(
            section.get("label") == "Mother Details"
            for section in stages["section_data"]["sections"]
        ):
            assert family_background["mother"]["name"]

        twelfth = next(
            entry
            for entry in stages["academic_data"]["academic_entries"]
            if "12" in str(entry.get("academic_level") or "")
        )
        assert twelfth["subject_entries"]


def test_activity_extractor_can_parse_forced_section_without_embedded_section_header(monkeypatch):
    monkeypatch.setattr("app.agents.activity_extractor.get_page_heights", lambda _pdf_path: {1: 842.0})
    monkeypatch.setattr("app.agents.activity_extractor.get_vertical_lines", lambda *_args, **_kwargs: [0.0, 180.0, 300.0, 420.0, 620.0])

    blocks = [
        {"page": 1, "text": "Activity", "bbox": (30, 700, 120, 715)},
        {"page": 1, "text": "Level", "bbox": (210, 700, 260, 715)},
        {"page": 1, "text": "Duration", "bbox": (330, 700, 390, 715)},
        {"page": 1, "text": "Achievement", "bbox": (470, 700, 560, 715)},
        {"page": 1, "text": "Robotics Club", "bbox": (30, 675, 140, 690)},
        {"page": 1, "text": "National", "bbox": (210, 675, 270, 690)},
        {"page": 1, "text": "3", "bbox": (330, 675, 340, 690)},
        {"page": 1, "text": "Won design challenge", "bbox": (470, 675, 590, 690)},
    ]

    result = extract_activities(blocks, pdf_path="synthetic.pdf", forced_section="extracurricular")

    assert len(result["activity_entries"]) == 1
    entry = result["activity_entries"][0]
    assert entry["activity_type"] == "extracurricular"
    assert entry["activity_name"] == "Robotics Club"
    assert entry["level"] == "National"
    assert entry["duration"] == "3"
    assert entry["achievement"] == "Won design challenge"


def test_integrity_analyzer_flags_text_encoding_and_truncated_activity_text():
    result = analyze_integrity(
        identifiers={"full_name": "Aarav Jain"},
        academic_entries=[{"entry_id": "acad-1"}],
        essay_entries=[{"entry_id": "essay-1", "raw_text": "Iâ€™ve always loved engineering.", "placeholder_flag": False}],
        activity_entries=[{
            "entry_id": "act-1",
            "activity_name": None,
            "position_title": "School House Captain",
            "roles_and_responsibilities": "Was the School House Captain at",
            "achievement": None,
            "description_raw": None,
            "activity_type": "leadership",
        }],
    )

    anomaly_types = {anomaly["anomaly_type"] for anomaly in result["anomalies"]}
    assert "text_encoding_artifact" in anomaly_types
    assert "truncated_activity_text" in anomaly_types


def test_integrity_analyzer_uses_layout_and_section_evidence():
    result = analyze_integrity(
        identifiers={"full_name": "Aarav Jain"},
        academic_entries=[{"entry_id": "acad-1"}],
        essay_entries=[],
        activity_entries=[],
        layout_meta={
            "issues": [{
                "issue_type": "missing_text_layer",
                "severity": "high",
                "source_stage": "layout_extraction",
                "message": "No extractable text blocks were found in the PDF.",
            }],
            "page_stats": [
                {"page": 1, "block_count": 1},
                {"page": 2, "block_count": 2},
                {"page": 3, "block_count": 1},
            ],
        },
        section_meta={"sections": [{"label": "Unknown Header", "section_type": None}]},
    )

    anomaly_types = {anomaly["anomaly_type"] for anomaly in result["anomalies"]}
    assert "missing_text_layer" in anomaly_types
    assert "untyped_sections" in anomaly_types
    assert "low_text_density" in anomaly_types
    assert result["confidence_score"] < 0.95


def test_assembler_aggregate_confidence_penalizes_layout_and_section_quality():
    canonical = assemble_canonical(
        application_id="app-1",
        layout_meta={
            "confidence_score": 0.95,
            "issues": [{"issue_type": "missing_text_layer"}],
            "page_stats": [{"page": 1, "block_count": 1}, {"page": 2, "block_count": 1}],
        },
        section_meta={
            "confidence_score": 0.90,
            "sections": [{"label": "Unknown Header", "section_type": None}],
        },
        identifiers_data={"confidence_score": 0.85, "identifiers": {"full_name": "Aarav Jain", "family_background": None}},
        academic_data={"confidence_score": 0.85, "academic_entries": []},
        test_data={"confidence_score": 0.90, "test_entries": []},
        essay_data={"confidence_score": 0.90, "essay_entries": []},
        activity_data={"confidence_score": 0.90, "activity_entries": [], "preferred_major": None},
        cross_section_data={"confidence_score": 0.90, "entity_map": []},
        integrity_data={"confidence_score": 0.80, "anomalies": [{
            "anomaly_id": "anom-1",
            "anomaly_type": "missing_text_layer",
            "severity_level": "high",
            "source_reference": "layout_extraction",
            "description": "No extractable text blocks were found in the PDF.",
        }]},
    )

    assert canonical["extraction_confidence"]["aggregate_confidence"] < 0.8


def test_cross_section_detector_requires_cross_collection_and_filters_generic_tokens():
    result = detect_cross_sections(
        academic_entries=[{
            "entry_id": "acad-1",
            "academic_level": "12TH",
            "subject_entries": [{"subject_name": "Mathematics"}],
        }],
        test_entries=[],
        essay_entries=[],
        activity_entries=[
            {"entry_id": "act-1", "activity_name": "Mathematics Club", "position_title": None, "achievement": None, "roles_and_responsibilities": None, "description_raw": None},
            {"entry_id": "act-2", "activity_name": "School Council", "position_title": "School House Captain", "achievement": None, "roles_and_responsibilities": None, "description_raw": None},
        ],
    )

    entity_tokens = {entity["entity_token"] for entity in result["entity_map"]}

    assert "Mathematics" in entity_tokens
    assert "School" not in entity_tokens
