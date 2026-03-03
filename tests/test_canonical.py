import pytest
from app.canonical.model import (
    CanonicalData, Identifiers, ProfileMeta, AcademicEntry, TestEntry,
    EssayEntry, ActivityEntry, TimelineEntry, CrossReferences, IntegrityReport,
    ExtractionConfidence, SubjectEntry, SectionalScore, EntityTokenMatch,
    SourceReference, Anomaly, AgentScore
)
from app.canonical.version import CANONICAL_VERSION

def test_canonical_model_instantiation():
    # Identifiers
    identifiers = Identifiers(
        application_id="app-12345",
        full_name="John Doe",
        date_of_birth="2005-01-01",
        declared_preferences={"major": "Computer Science"},
        demographic_flags={"first_generation": True}
    )

    # Profile Meta
    profile_meta = ProfileMeta(
        source_document_page_count=5,
        extraction_timestamp="2026-03-01T10:00:00Z",
        layout_block_count=120,
        detected_section_labels=["Personal Information", "Academics", "Extracurriculars"]
    )

    # Academic Entry
    academic_entry = AcademicEntry(
        entry_id="acad-1",
        academic_level="Class 12",
        board_name="CBSE",
        academic_year="2024",
        marking_scheme_raw="Percentage",
        grading_mode="percentage",
        score_raw="95%",
        subject_entries=[
            SubjectEntry(subject_name="Mathematics", score_raw="98")
        ],
        component_tags=["core"],
        confidence_score=0.98
    )

    # Test Entry
    test_entry = TestEntry(
        entry_id="test-1",
        test_name="SAT",
        test_date="2023-12-01",
        total_score="1500",
        sectional_scores=[
            SectionalScore(label="Math", raw_score="800"),
            SectionalScore(label="Reading", raw_score="700")
        ],
        result_status="available",
        confidence_score=0.99
    )

    # Essay Entry
    essay_entry = EssayEntry(
        entry_id="essay-1",
        essay_identifier="Personal Statement",
        raw_text="I have always loved computers...",
        word_count=500,
        character_count=3000,
        placeholder_flag=False,
        duplication_ratio=0.01,
        short_response_flag=False,
        confidence_score=0.95
    )

    # Activity Entry
    activity_entry = ActivityEntry(
        entry_id="act-1",
        category="Club",
        activity_name="Robotics",
        level="School",
        duration="2 years",
        description_raw="Built a robot.",
        upload_flag=False,
        confidence_score=0.90
    )

    # Timeline Entry
    timeline_entry = TimelineEntry(
        entry_id="tl-1",
        year="2023",
        event_label="Joined Robotics",
        source_type="activity",
        source_reference="act-1"
    )

    # Cross References
    cross_refs = CrossReferences(
        entity_map=[
            EntityTokenMatch(
                entity_token="Robotics",
                source_references=[SourceReference(source_type="activity", entry_id="act-1")]
            )
        ]
    )

    # Integrity Report
    integrity = IntegrityReport(
        anomalies=[
            Anomaly(
                anomaly_id="anom-1",
                anomaly_type="missing_section",
                severity_level="medium",
                description="Missing test scores section."
            )
        ]
    )

    # Extraction Confidence
    confidence = ExtractionConfidence(
        agent_scores=[
            AgentScore(agent_id=1, agent_name="Layout Block Extractor", confidence_score=0.99)
        ],
        aggregate_confidence=0.95
    )

    # Canonical Root
    canonical_data = CanonicalData(
        identifiers=identifiers,
        profile_meta=profile_meta,
        academic_entries=[academic_entry],
        test_entries=[test_entry],
        essay_entries=[essay_entry],
        activity_entries=[activity_entry],
        timeline_entries=[timeline_entry],
        cross_references=cross_refs,
        integrity_report=integrity,
        extraction_confidence=confidence
    )

    # Assertions to ensure version is automatically populated and model is instantiated correctly
    assert canonical_data.canonical_version == CANONICAL_VERSION
    assert canonical_data.identifiers.application_id == "app-12345"
    assert len(canonical_data.academic_entries) == 1
    assert canonical_data.academic_entries[0].academic_level == "Class 12"
    assert len(canonical_data.test_entries[0].sectional_scores) == 2
