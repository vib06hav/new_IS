import json
from pathlib import Path

from app.agents.projection_builder import build_projection
from app.agents.signal_detector import detect_signals
from app.policy.guard import validate_signals


FIXTURE_DIR = Path(__file__).resolve().parent / "pipeline_stages"


def _academic_entry(
    level: str,
    year: str,
    score: str | None,
    board: str = "CBSE",
    school: str = "School A",
    subjects=None,
    predicted_score: str | None = None,
):
    return {
        "academic_level": level,
        "academic_year": year,
        "score_raw": score,
        "predicted_score_raw": predicted_score,
        "max_score_raw": None,
        "board_name": board,
        "school_name": school,
        "subject_entries": subjects or [],
    }


def _activity_entry(
    activity_type: str,
    name: str | None,
    position: str | None,
    duration: str | None,
    level: str | None,
    responsibilities: str | None = None,
):
    return {
        "activity_type": activity_type,
        "activity_name": name,
        "position_title": position,
        "duration": duration,
        "level": level,
        "achievement": None,
        "roles_and_responsibilities": responsibilities,
        "description_raw": None,
    }


def _subject(
    name: str,
    score: str | None,
    max_score: str = "100",
    predicted_score: str | None = None,
):
    return {
        "subject_name": name,
        "score_raw": score,
        "max_score_raw": max_score,
        "predicted_score_raw": predicted_score,
    }


def test_build_projection_excludes_9th_and_includes_all_later_subjects():
    canonical = {
        "identifiers": {"preferred_major": "Computer Science", "full_name": "Test Student"},
        "academic_entries": [
            _academic_entry(
                "9TH",
                "2022",
                "81",
                subjects=[
                    _subject("Math", "98"),
                    _subject("Science", "92"),
                    _subject("History", "88"),
                ],
            ),
            _academic_entry(
                "10TH",
                "2023",
                "94",
                subjects=[
                    _subject("Math", "99"),
                    _subject("Science", "97"),
                    _subject("Artificial Intelligence", "100"),
                ],
            ),
            _academic_entry(
                "11TH",
                "2024",
                "78",
                subjects=[
                    _subject("Math", "80", "100"),
                    _subject("Physics", "55", "70"),
                    _subject("Chemistry", "66", "70"),
                ],
            ),
            _academic_entry(
                "12TH",
                "2025",
                None,
                predicted_score="95",
                subjects=[
                    _subject("Math", None, "100", predicted_score="96"),
                    _subject("Physics", None, "100", predicted_score="91"),
                    _subject("Chemistry", None, "100", predicted_score="89"),
                ],
            ),
        ],
        "test_entries": [],
        "essay_entries": [],
        "activity_entries": [],
    }
    entity_id_map = [
        {"entity_id": "ACA-001", "collection": "academic_entries", "descriptor": "9TH"},
        {"entity_id": "ACA-002", "collection": "academic_entries", "descriptor": "10TH"},
        {"entity_id": "ACA-003", "collection": "academic_entries", "descriptor": "11TH"},
        {"entity_id": "ACA-004", "collection": "academic_entries", "descriptor": "12TH"},
    ]

    projection = build_projection(canonical, entity_id_map, [])

    assert [entry["level"] for entry in projection["academic_profile"]] == ["10TH", "11TH", "12TH"]
    assert [subject["subject"] for subject in projection["academic_profile"][0]["subjects_concise"]] == [
        "Math",
        "Science",
        "Artificial Intelligence",
    ]
    assert [subject["subject"] for subject in projection["academic_profile"][2]["subjects_concise"]] == [
        "Math",
        "Physics",
        "Chemistry",
    ]
    assert projection["academic_profile"][2]["subjects_concise"][0]["predicted_score"] == "96"


def test_detect_signals_ignores_9th_and_names_exact_subjects():
    canonical = {
        "academic_entries": [
            _academic_entry(
                "9TH",
                "2022",
                "60",
                subjects=[
                    _subject("Math", "95"),
                    _subject("Physics", "40"),
                    _subject("English", "92"),
                ],
            ),
            _academic_entry(
                "10TH",
                "2023",
                "88",
                subjects=[
                    _subject("Math", "97"),
                    _subject("Physics", "72"),
                    _subject("English", "94"),
                ],
            ),
            _academic_entry(
                "11TH",
                "2024",
                "82",
                subjects=[
                    _subject("Math", "92", "100"),
                    _subject("Physics", "48", "70"),
                    _subject("Chemistry", "68", "70"),
                ],
            ),
            _academic_entry(
                "12TH",
                "2025",
                None,
                predicted_score="85",
                subjects=[
                    _subject("Math", None, "100", predicted_score="94"),
                    _subject("Physics", None, "100", predicted_score="79"),
                    _subject("Chemistry", None, "100", predicted_score="90"),
                ],
            ),
        ],
        "activity_entries": [],
        "test_entries": [],
    }
    entity_id_map = [
        {"entity_id": "ACA-001", "collection": "academic_entries", "descriptor": "9TH"},
        {"entity_id": "ACA-002", "collection": "academic_entries", "descriptor": "10TH"},
        {"entity_id": "ACA-003", "collection": "academic_entries", "descriptor": "11TH"},
        {"entity_id": "ACA-004", "collection": "academic_entries", "descriptor": "12TH"},
    ]

    signals = detect_signals(canonical, entity_id_map)

    observations = [signal["observation"] for signal in signals if signal["signal_type"] == "subject_imbalance"]
    joined_observations = " ".join(observations)

    assert all("ACA-001" not in signal["referenced_entity_ids"] for signal in signals)
    assert "Physics" in joined_observations
    assert "Math" in joined_observations
    assert any("Physics was the lowest-scoring subject across 10TH and 11TH and 12TH" in text for text in observations)


def test_detect_signals_normalizes_with_max_score_not_raw_score():
    canonical = {
        "academic_entries": [
            _academic_entry(
                "10TH",
                "2023",
                "90",
                subjects=[
                    _subject("Mathematics", "130", "150"),
                    _subject("Physics", "55", "60"),
                    _subject("Chemistry", "75", "100"),
                ],
            ),
        ],
        "activity_entries": [],
        "test_entries": [],
    }
    entity_id_map = [{"entity_id": "ACA-001", "collection": "academic_entries", "descriptor": "10TH"}]

    signals = detect_signals(canonical, entity_id_map)

    imbalance_signal = next(signal for signal in signals if signal["signal_type"] == "subject_imbalance")
    assert "Chemistry was the lowest subject at 75.0%" in imbalance_signal["observation"]
    assert "Physics was the highest at 91.7%" in imbalance_signal["observation"]


def test_detect_signals_skips_subject_imbalance_when_only_language_would_anchor_high_end():
    canonical = {
        "academic_entries": [
            _academic_entry(
                "12TH",
                "2025",
                "90",
                subjects=[
                    _subject("Physics", "52", "60"),
                    _subject("Chemistry", "56", "60"),
                    _subject("Sanskrit", "99", "100"),
                ],
            ),
        ],
        "activity_entries": [],
        "test_entries": [],
    }
    entity_id_map = [{"entity_id": "ACA-001", "collection": "academic_entries", "descriptor": "12TH"}]

    signals = detect_signals(canonical, entity_id_map)

    assert signals == []


def test_detect_signals_activity_rules_prefer_non_personal_and_allow_leadership_position():
    canonical = {
        "academic_entries": [],
        "activity_entries": [
            _activity_entry("leadership", None, "Head Boy", None, None),
            _activity_entry("extracurricular", "Keyboard", None, "4", "National"),
            _activity_entry("co_curricular", "MUN", None, "1", "District"),
            _activity_entry("extracurricular", "Badminton", "Captain", "3", "Personal", responsibilities="Led practice sessions"),
            _activity_entry("co_curricular", "Reading", "Lead", "3", "Personal", responsibilities=None),
        ],
        "test_entries": [],
    }
    entity_id_map = [
        {"entity_id": "LEAD-001", "collection": "activity_entries", "descriptor": "Head Boy"},
        {"entity_id": "ACT-001", "collection": "activity_entries", "descriptor": "Keyboard"},
        {"entity_id": "ACT-002", "collection": "activity_entries", "descriptor": "MUN"},
        {"entity_id": "ACT-003", "collection": "activity_entries", "descriptor": "Badminton"},
        {"entity_id": "ACT-004", "collection": "activity_entries", "descriptor": "Reading"},
    ]

    signals = detect_signals(canonical, entity_id_map)

    assert [signal["signal_type"] for signal in signals] == [
        "leadership_depth",
        "sustained_commitment",
        "sustained_commitment",
        "sustained_commitment",
    ]
    assert signals[0]["referenced_entity_ids"] == ["LEAD-001"]
    assert signals[1]["referenced_entity_ids"] == ["ACT-001"]
    assert signals[2]["referenced_entity_ids"] == ["ACT-002"]
    assert signals[3]["referenced_entity_ids"] == ["ACT-003"]
    assert "over 4.0 years" in signals[1]["observation"]
    assert "over 1.0 years" in signals[2]["observation"]
    assert "3.0 years" in signals[3]["observation"]
    assert all(signal["referenced_entity_ids"] != ["ACT-004"] for signal in signals)


def test_build_projection_allows_empty_deterministic_signals_and_omits_academic_summary():
    canonical = json.loads((FIXTURE_DIR / "11_canonical_assembled.json").read_text(encoding="utf-8"))
    entity_id_map = json.loads((FIXTURE_DIR / "12_entity_id_map.json").read_text(encoding="utf-8"))

    projection = build_projection(canonical, entity_id_map, [])

    assert "academic_summary" not in projection
    assert projection["deterministic_signals"] == []
    assert set(projection["applicant_context"].keys()) == {"preferred_major"}


def test_validate_signals_rejects_invented_det_ids_when_signal_set_is_empty():
    raw_output = json.dumps(
        {
            "interpreted_signals": [
                {
                    "signal_id": "INT-001",
                    "title": "Grounded title",
                    "essay_claim": "Quoted essay claim",
                    "evidence_observation": "Observed evidence",
                    "tension_or_coherence": "COHERENCE - factual relationship",
                    "interview_hook": "Specific interview hook",
                    "referenced_entity_ids": ["ACA-001"],
                    "supporting_det_signal_ids": ["DET-999"],
                }
            ]
        }
    )
    entity_id_map = [{"entity_id": "ACA-001", "collection": "academic_entries", "descriptor": "9TH"}]

    result = validate_signals(raw_output, entity_id_map, [])

    assert result["passed"] is False
    assert any(
        violation["type"] == "invented_det_signal_id"
        for violation in result["violations_log"]
    )
