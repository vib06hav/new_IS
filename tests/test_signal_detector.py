import json
from pathlib import Path

from app.agents.projection_builder import build_projection
from app.agents.report_annotations import build_report_annotations
from app.agents.signal_detector import detect_signals
from app.policy.guard import validate_question_groups, validate_signals


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


def test_build_projection_adds_paragraph_and_sentence_group_essay_fragments():
    canonical = {
        "identifiers": {"preferred_major": "Computer Science"},
        "academic_entries": [],
        "test_entries": [],
        "essay_entries": [
            {
                "essay_identifier": "Essay With Paragraphs",
                "raw_text": "First paragraph line one.\n\nSecond paragraph line one.",
                "placeholder_flag": False,
            },
            {
                "essay_identifier": "Essay Without Paragraphs",
                "raw_text": "Sentence one. Sentence two. Sentence three.",
                "placeholder_flag": False,
            },
        ],
        "activity_entries": [],
    }
    entity_id_map = [
        {"entity_id": "ESS-001", "collection": "essay_entries", "descriptor": "Essay With Paragraphs"},
        {"entity_id": "ESS-002", "collection": "essay_entries", "descriptor": "Essay Without Paragraphs"},
    ]

    projection = build_projection(canonical, entity_id_map, [])

    paragraph_fragments = [fragment for fragment in projection["essay_fragments"] if fragment["entity_id"] == "ESS-001"]
    sentence_group_fragments = [fragment for fragment in projection["essay_fragments"] if fragment["entity_id"] == "ESS-002"]

    assert [fragment["fragment_id"] for fragment in paragraph_fragments] == ["ESS-001:F01", "ESS-001:F02"]
    assert paragraph_fragments[0]["text"] == "First paragraph line one."
    assert paragraph_fragments[1]["text"] == "Second paragraph line one."

    assert [fragment["fragment_id"] for fragment in sentence_group_fragments] == ["ESS-002:F01", "ESS-002:F02"]
    assert sentence_group_fragments[0]["text"] == "Sentence one. Sentence two."
    assert sentence_group_fragments[1]["text"] == "Sentence three."


def test_validate_signals_rejects_invented_det_ids_when_signal_set_is_empty():
    raw_output = json.dumps(
        {
            "signals": [
                {
                    "signal_id": "SIG-001",
                    "title": "Grounded title",
                    "evidence_anchor": "Quoted essay claim",
                    "direct_read": "Observed evidence",
                    "what_remains_open": "Specific open question",
                    "why_it_matters": "Specific relevance",
                    "referenced_entity_ids": ["ACA-001"],
                    "supporting_det_signal_ids": ["DET-999"],
                }
            ],
            "themes": [],
        }
    )
    entity_id_map = [{"entity_id": "ACA-001", "collection": "academic_entries", "descriptor": "9TH"}]

    result = validate_signals(raw_output, entity_id_map, [])

    assert result["passed"] is False
    assert any(
        violation["type"] == "invented_det_signal_id"
        for violation in result["violations_log"]
    )


def test_validate_signals_accepts_valid_supporting_fragment_ids():
    raw_output = json.dumps(
        {
            "signals": [
                {
                    "signal_id": "SIG-001",
                    "title": "Grounded title",
                    "evidence_anchor": "Quoted essay claim",
                    "direct_read": "Observed evidence",
                    "what_remains_open": "Specific open question",
                    "why_it_matters": "Specific relevance",
                    "referenced_entity_ids": ["ESS-001"],
                    "supporting_det_signal_ids": [],
                    "supporting_fragment_ids": ["ESS-001:F01"],
                }
            ],
            "themes": [
                {
                    "theme_id": "THEME-001",
                    "title": "Grounded theme",
                    "framing": "Grounded theme framing",
                    "what_this_theme_must_resolve": "Grounded theme resolution",
                    "supporting_signal_ids": ["SIG-001"],
                }
            ],
        }
    )
    entity_id_map = [{"entity_id": "ESS-001", "collection": "essay_entries", "descriptor": "Essay 1"}]
    essay_fragments = [
        {"fragment_id": "ESS-001:F01", "entity_id": "ESS-001", "text": "Essay evidence", "start_char": 0, "end_char": 13}
    ]

    result = validate_signals(raw_output, entity_id_map, [], essay_fragments=essay_fragments)

    assert result["passed"] is True
    assert result["sanitized_output"]["signals"][0]["supporting_fragment_ids"] == ["ESS-001:F01"]


def test_validate_signals_rejects_invalid_supporting_fragment_ids():
    base_signal = {
        "signal_id": "SIG-001",
        "title": "Grounded title",
        "evidence_anchor": "Quoted essay claim",
        "direct_read": "Observed evidence",
        "what_remains_open": "Specific open question",
        "why_it_matters": "Specific relevance",
        "referenced_entity_ids": ["ESS-001"],
        "supporting_det_signal_ids": [],
    }
    entity_id_map = [{"entity_id": "ESS-001", "collection": "essay_entries", "descriptor": "Essay 1"}]
    essay_fragments = [
        {"fragment_id": "ESS-001:F01", "entity_id": "ESS-001", "text": "Essay evidence", "start_char": 0, "end_char": 13},
        {"fragment_id": "ESS-002:F01", "entity_id": "ESS-002", "text": "Other essay", "start_char": 0, "end_char": 10},
    ]

    invented_fragment_result = validate_signals(
        json.dumps(
            {
                "signals": [{**base_signal, "supporting_fragment_ids": ["ESS-001:F99"]}],
                "themes": [],
            }
        ),
        entity_id_map,
        [],
        essay_fragments=essay_fragments,
    )
    mismatch_result = validate_signals(
        json.dumps(
            {
                "signals": [{**base_signal, "supporting_fragment_ids": ["ESS-002:F01"]}],
                "themes": [],
            }
        ),
        entity_id_map,
        [],
        essay_fragments=essay_fragments,
    )
    invalid_type_result = validate_signals(
        json.dumps(
            {
                "signals": [{**base_signal, "supporting_fragment_ids": "ESS-001:F01"}],
                "themes": [],
            }
        ),
        entity_id_map,
        [],
        essay_fragments=essay_fragments,
    )
    too_many_result = validate_signals(
        json.dumps(
            {
                "signals": [
                    {
                        **base_signal,
                        "supporting_fragment_ids": ["ESS-001:F01", "ESS-001:F02", "ESS-001:F03", "ESS-001:F04"],
                    }
                ],
                "themes": [],
            }
        ),
        entity_id_map,
        [],
        essay_fragments=[
            {"fragment_id": "ESS-001:F01", "entity_id": "ESS-001", "text": "A", "start_char": 0, "end_char": 1},
            {"fragment_id": "ESS-001:F02", "entity_id": "ESS-001", "text": "B", "start_char": 1, "end_char": 2},
            {"fragment_id": "ESS-001:F03", "entity_id": "ESS-001", "text": "C", "start_char": 2, "end_char": 3},
            {"fragment_id": "ESS-001:F04", "entity_id": "ESS-001", "text": "D", "start_char": 3, "end_char": 4},
        ],
    )

    assert invented_fragment_result["passed"] is False
    assert any(violation["type"] == "invented_fragment_id" for violation in invented_fragment_result["violations_log"])

    assert mismatch_result["passed"] is False
    assert any(violation["type"] == "fragment_entity_mismatch" for violation in mismatch_result["violations_log"])

    assert invalid_type_result["passed"] is False
    assert any(violation["type"] == "invalid_type" for violation in invalid_type_result["violations_log"])

    assert too_many_result["passed"] is False
    assert any(violation["type"] == "too_many_fragment_ids" for violation in too_many_result["violations_log"])


def test_validate_signals_accepts_themes_and_theme_linkage():
    raw_output = json.dumps(
        {
            "signals": [
                {
                    "signal_id": "SIG-001",
                    "title": "Grounded title",
                    "evidence_anchor": "Quoted essay claim",
                    "direct_read": "Observed evidence",
                    "what_remains_open": "Specific open question",
                    "why_it_matters": "Specific relevance",
                    "referenced_entity_ids": ["ACA-001"],
                    "supporting_det_signal_ids": ["DET-001"],
                }
            ],
            "themes": [
                {
                    "theme_id": "THEME-001",
                    "title": "Grounded theme",
                    "framing": "Grounded theme framing",
                    "what_this_theme_must_resolve": "Grounded theme resolution",
                    "supporting_signal_ids": ["SIG-001"],
                }
            ],
        }
    )
    entity_id_map = [{"entity_id": "ACA-001", "collection": "academic_entries", "descriptor": "10TH"}]
    deterministic_signals = [{"signal_id": "DET-001", "referenced_entity_ids": ["ACA-001"]}]

    result = validate_signals(raw_output, entity_id_map, deterministic_signals)

    assert result["passed"] is True
    assert result["sanitized_output"]["signals"][0]["theme_id"] == "THEME-001"
    assert result["sanitized_output"]["themes"][0]["theme_id"] == "THEME-001"
    assert result["sanitized_output"]["themes"][0]["referenced_entity_ids"] == ["ACA-001"]


def test_validate_signals_rejects_theme_with_unknown_supporting_signal():
    raw_output = json.dumps(
        {
            "signals": [
                {
                    "signal_id": "SIG-001",
                    "title": "Grounded title",
                    "evidence_anchor": "Quoted essay claim",
                    "direct_read": "Observed evidence",
                    "what_remains_open": "Specific open question",
                    "why_it_matters": "Specific relevance",
                    "referenced_entity_ids": ["ACA-001"],
                    "supporting_det_signal_ids": ["DET-001"],
                }
            ],
            "themes": [
                {
                    "theme_id": "THEME-001",
                    "title": "Grounded theme",
                    "framing": "Grounded theme framing",
                    "what_this_theme_must_resolve": "Grounded theme resolution",
                    "supporting_signal_ids": ["SIG-999"],
                }
            ],
        }
    )
    entity_id_map = [{"entity_id": "ACA-001", "collection": "academic_entries", "descriptor": "10TH"}]
    deterministic_signals = [{"signal_id": "DET-001", "referenced_entity_ids": ["ACA-001"]}]

    result = validate_signals(raw_output, entity_id_map, deterministic_signals)

    assert result["passed"] is False
    assert any(
        violation["type"] == "unknown_supporting_signal_id"
        for violation in result["violations_log"]
    )


def test_validate_signals_rejects_orphan_theme():
    raw_output = json.dumps(
        {
            "signals": [
                {
                    "signal_id": "SIG-001",
                    "title": "Grounded title",
                    "evidence_anchor": "Quoted essay claim",
                    "direct_read": "Observed evidence",
                    "what_remains_open": "Specific open question",
                    "why_it_matters": "Specific relevance",
                    "referenced_entity_ids": ["ACA-001"],
                    "supporting_det_signal_ids": ["DET-001"],
                }
            ],
            "themes": [
                {
                    "theme_id": "THEME-001",
                    "title": "Grounded theme",
                    "framing": "Grounded theme framing",
                    "what_this_theme_must_resolve": "Grounded theme resolution",
                    "supporting_signal_ids": ["SIG-001"],
                },
                {
                    "theme_id": "THEME-002",
                    "title": "Orphan theme",
                    "framing": "No member signals",
                    "what_this_theme_must_resolve": "No member signals",
                    "supporting_signal_ids": [],
                },
            ],
        }
    )
    entity_id_map = [{"entity_id": "ACA-001", "collection": "academic_entries", "descriptor": "10TH"}]
    deterministic_signals = [{"signal_id": "DET-001", "referenced_entity_ids": ["ACA-001"]}]

    result = validate_signals(raw_output, entity_id_map, deterministic_signals)

    assert result["passed"] is False
    assert any(
        violation["type"] == "orphan_theme"
        for violation in result["violations_log"]
    )


def test_validate_signals_rejects_signal_pointing_to_unknown_theme():
    raw_output = json.dumps(
        {
            "signals": [
                {
                    "signal_id": "SIG-001",
                    "title": "Grounded title",
                    "evidence_anchor": "Quoted essay claim",
                    "direct_read": "Observed evidence",
                    "what_remains_open": "Specific open question",
                    "why_it_matters": "Specific relevance",
                    "referenced_entity_ids": ["ACA-001"],
                    "supporting_det_signal_ids": ["DET-001"],
                }
            ],
            "themes": [
                {
                    "theme_id": "THEME-001",
                    "title": "Grounded theme",
                    "framing": "Grounded theme framing",
                    "what_this_theme_must_resolve": "Grounded theme resolution",
                    "supporting_signal_ids": ["SIG-001", "SIG-999"],
                }
            ],
        }
    )
    entity_id_map = [{"entity_id": "ACA-001", "collection": "academic_entries", "descriptor": "10TH"}]
    deterministic_signals = [{"signal_id": "DET-001", "referenced_entity_ids": ["ACA-001"]}]

    result = validate_signals(raw_output, entity_id_map, deterministic_signals)

    assert result["passed"] is False
    assert any(
        violation["type"] == "unknown_supporting_signal_id"
        for violation in result["violations_log"]
    )


def test_validate_signals_rejects_signal_linked_to_multiple_themes():
    raw_output = json.dumps(
        {
            "signals": [
                {
                    "signal_id": "SIG-001",
                    "title": "Grounded title",
                    "evidence_anchor": "Quoted essay claim",
                    "direct_read": "Observed evidence",
                    "what_remains_open": "Specific open question",
                    "why_it_matters": "Specific relevance",
                    "referenced_entity_ids": ["ACA-001"],
                    "supporting_det_signal_ids": ["DET-001"],
                }
            ],
            "themes": [
                {
                    "theme_id": "THEME-001",
                    "title": "Grounded theme",
                    "framing": "Grounded theme framing",
                    "what_this_theme_must_resolve": "Grounded theme resolution",
                    "supporting_signal_ids": ["SIG-001"],
                },
                {
                    "theme_id": "THEME-002",
                    "title": "Second theme",
                    "framing": "Second theme framing",
                    "what_this_theme_must_resolve": "Second theme resolution",
                    "supporting_signal_ids": ["SIG-001"],
                }
            ],
        }
    )
    entity_id_map = [
        {"entity_id": "ACA-001", "collection": "academic_entries", "descriptor": "10TH"},
        {"entity_id": "ACA-002", "collection": "academic_entries", "descriptor": "11TH"},
    ]
    deterministic_signals = [{"signal_id": "DET-001", "referenced_entity_ids": ["ACA-001"]}]

    result = validate_signals(raw_output, entity_id_map, deterministic_signals)

    assert result["passed"] is False
    assert any(
        violation["type"] == "signal_linked_multiple_times"
        for violation in result["violations_log"]
    )


def test_validate_question_groups_accepts_question_groups_only():
    raw_output = json.dumps(
        {
            "question_groups": [
                {
                    "theme_id": "THEME-001",
                    "group_title": "Theme one questions",
                    "questions": ["Why did this specific applicant choose the Physics path?"],
                },
                {
                    "theme_id": "THEME-002",
                    "group_title": "Theme two questions",
                    "questions": ["How did the applicant respond to the board transition?"],
                },
            ]
        }
    )
    bundle = {
        "themes": [
            {"theme_id": "THEME-001", "title": "Theme 1", "framing": "Frame 1", "what_this_theme_must_resolve": "Resolve 1", "supporting_signal_ids": ["SIG-001"], "referenced_entity_ids": ["ACA-001"]},
            {"theme_id": "THEME-002", "title": "Theme 2", "framing": "Frame 2", "what_this_theme_must_resolve": "Resolve 2", "supporting_signal_ids": ["SIG-002"], "referenced_entity_ids": ["ACA-002"]},
        ]
    }

    result = validate_question_groups(raw_output, [], bundle)

    assert result["passed"] is True
    assert [group["theme_id"] for group in result["sanitized_output"]["question_groups"]] == [
        "THEME-001",
        "THEME-002",
    ]


def test_build_report_annotations_derives_page_2_entities_and_page_3_fragments():
    signals = [
        {
            "signal_id": "SIG-001",
            "theme_id": "THEME-001",
            "referenced_entity_ids": ["ACA-004", "ESS-001", "ACT-003"],
            "supporting_fragment_ids": ["ESS-001:F02"],
        },
        {
            "signal_id": "SIG-002",
            "theme_id": "THEME-001",
            "referenced_entity_ids": ["ACA-004", "TEST-001"],
            "supporting_fragment_ids": [],
        },
    ]
    entity_id_map = [
        {"entity_id": "ACA-004", "collection": "academic_entries", "descriptor": "12TH"},
        {"entity_id": "ESS-001", "collection": "essay_entries", "descriptor": "Essay 1"},
        {"entity_id": "ACT-003", "collection": "activity_entries", "descriptor": "Olympiads"},
        {"entity_id": "TEST-001", "collection": "test_entries", "descriptor": "JEE Mains"},
    ]
    essay_fragments = [
        {"fragment_id": "ESS-001:F02", "entity_id": "ESS-001", "text": "Essay evidence", "start_char": 50, "end_char": 90}
    ]

    annotations = build_report_annotations(signals, [], entity_id_map, essay_fragments=essay_fragments)

    assert annotations["page_1_entities"] == {}
    assert annotations["page_2_entities"]["ACA-004"] == {
        "signal_ids": ["SIG-001", "SIG-002"],
        "theme_ids": ["THEME-001"],
    }
    assert annotations["page_2_entities"]["ACT-003"] == {
        "signal_ids": ["SIG-001"],
        "theme_ids": ["THEME-001"],
    }
    assert annotations["page_3_fragments"]["ESS-001"] == [
        {
            "fragment_id": "ESS-001:F02",
            "start_char": 50,
            "end_char": 90,
            "signal_ids": ["SIG-001"],
            "theme_ids": ["THEME-001"],
        }
    ]


def test_validate_question_groups_rejects_missing_theme_coverage():
    raw_output = json.dumps(
        {
            "question_groups": [
                {
                    "theme_id": "THEME-001",
                    "group_title": "Theme one questions",
                    "questions": ["Why did this specific applicant choose the Physics path?"],
                }
            ]
        }
    )
    bundle = {
        "themes": [
            {"theme_id": "THEME-001", "title": "Theme 1", "framing": "Frame 1", "what_this_theme_must_resolve": "Resolve 1", "supporting_signal_ids": ["SIG-001"], "referenced_entity_ids": ["ACA-001"]},
            {"theme_id": "THEME-002", "title": "Theme 2", "framing": "Frame 2", "what_this_theme_must_resolve": "Resolve 2", "supporting_signal_ids": ["SIG-002"], "referenced_entity_ids": ["ACA-002"]},
        ]
    }

    result = validate_question_groups(raw_output, [], bundle)

    assert result["passed"] is False
    assert any(
        violation["type"] == "missing_theme_coverage"
        for violation in result["violations_log"]
    )


def test_validate_question_groups_rejects_duplicate_theme_groups():
    raw_output = json.dumps(
        {
            "question_groups": [
                {
                    "theme_id": "THEME-001",
                    "group_title": "Theme one questions",
                    "questions": ["Why did this specific applicant choose the Physics path?"],
                },
                {
                    "theme_id": "THEME-001",
                    "group_title": "Theme one more questions",
                    "questions": ["How did the applicant approach that same choice?"],
                },
            ]
        }
    )
    bundle = {
        "themes": [
            {"theme_id": "THEME-001", "title": "Theme 1", "framing": "Frame 1", "what_this_theme_must_resolve": "Resolve 1", "supporting_signal_ids": ["SIG-001"], "referenced_entity_ids": ["ACA-001"]},
        ]
    }

    result = validate_question_groups(raw_output, [], bundle)

    assert result["passed"] is False
    assert any(
        violation["type"] == "duplicate_theme_group"
        for violation in result["violations_log"]
    )


def test_validate_question_groups_rejects_invented_theme_ids():
    raw_output = json.dumps(
        {
            "question_groups": [
                {
                    "theme_id": "THEME-999",
                    "group_title": "Unknown theme questions",
                    "questions": ["Why did this specific applicant choose the Physics path?"],
                }
            ]
        }
    )
    bundle = {
        "themes": [
            {"theme_id": "THEME-001", "title": "Theme 1", "framing": "Frame 1", "what_this_theme_must_resolve": "Resolve 1", "supporting_signal_ids": ["SIG-001"], "referenced_entity_ids": ["ACA-001"]},
        ]
    }

    result = validate_question_groups(raw_output, [], bundle)

    assert result["passed"] is False
    assert any(
        violation["type"] == "broken_linkage"
        for violation in result["violations_log"]
    )
