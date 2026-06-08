import uuid

from sqlalchemy import create_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.database import Base
from app.models.question_generated_version import QuestionGeneratedVersion
from app.models.question_generation_thread import QuestionGenerationThread
from app.models.question_version_rating import QuestionVersionRating
from app.rag.indexing import index_question_version, schedule_question_version_index
from app.rag.question_retrieval import retrieve_question_generation_context, retrieve_question_regeneration_examples


@compiles(JSONB, "sqlite")
def compile_jsonb(element, compiler, **kw):
    return "JSON"


@compiles(UUID, "sqlite")
def compile_uuid(element, compiler, **kw):
    return "CHAR(32)"


SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def test_regeneration_retrieval_uses_qdrant_and_excludes_current_application(monkeypatch):
    original_retrieval_limit = settings.RAG_RETRIEVAL_LIMIT
    original_candidate_limit = settings.RAG_CANDIDATE_LIMIT
    settings.RAG_RETRIEVAL_LIMIT = 2
    settings.RAG_CANDIDATE_LIMIT = 4

    current_application_id = uuid.uuid4()
    other_application_id = uuid.uuid4()
    try:
        monkeypatch.setattr("app.rag.question_retrieval.qdrant_enabled", lambda: True)
        monkeypatch.setattr(
            "app.rag.question_retrieval.search_question_points",
            lambda query_text, limit: [
                {
                    "point_id": "same-app",
                    "score": 0.99,
                    "payload": {
                        "application_id": str(current_application_id),
                        "question_text": "Same application should not leak in.",
                    },
                },
                {
                    "point_id": "lower-rated",
                    "score": 0.78,
                    "payload": {
                        "application_id": str(other_application_id),
                        "focus_area_id": "focus-a",
                        "question_role": "debugging probe",
                        "question_text": "What made the project difficult?",
                        "rating_avg": 2,
                        "rating_count": 1,
                    },
                },
                {
                    "point_id": "higher-rated",
                    "score": 0.7,
                    "payload": {
                        "application_id": str(other_application_id),
                        "focus_area_id": "focus-a",
                        "question_role": "debugging probe",
                        "question_text": "Where did your first approach break down?",
                        "rating_avg": 5,
                        "rating_count": 3,
                    },
                },
            ],
        )

        result = retrieve_question_regeneration_examples(
            db=None,
            application_id=current_application_id,
            focus_area_id="focus-a",
            theme_title="Building systems",
            theme_direction="Probe debugging depth",
            question_role="debugging probe",
            question_text="Tell me about a technical challenge.",
            lexical_fallback=lambda: [{"question_text": "fallback"}],
        )

        assert result.snapshot["provider"] == "qdrant"
        assert result.examples[0]["question_text"] == "Where did your first approach break down?"
        assert all(item["question_text"] != "Same application should not leak in." for item in result.examples)
        assert result.snapshot["selected_points"][0]["point_id"] == "higher-rated"
    finally:
        settings.RAG_RETRIEVAL_LIMIT = original_retrieval_limit
        settings.RAG_CANDIDATE_LIMIT = original_candidate_limit


def test_regeneration_retrieval_falls_back_when_qdrant_errors(monkeypatch):
    monkeypatch.setattr("app.rag.question_retrieval.qdrant_enabled", lambda: True)

    def boom(query_text, limit):
        raise RuntimeError("qdrant down")

    monkeypatch.setattr("app.rag.question_retrieval.search_question_points", boom)

    result = retrieve_question_regeneration_examples(
        db=None,
        application_id=uuid.uuid4(),
        focus_area_id="focus-a",
        theme_title="Theme",
        theme_direction="Direction",
        question_role="Role",
        question_text="Question",
        lexical_fallback=lambda: [{"question_text": "lexical example"}],
    )

    assert result.examples == [{"question_text": "lexical example"}]
    assert result.snapshot["provider"] == "lexical_fallback"
    assert result.snapshot["fallback_reason"] == "qdrant_error:RuntimeError"


def test_generation_retrieval_builds_focus_area_context(monkeypatch):
    current_application_id = uuid.uuid4()
    other_application_id = uuid.uuid4()
    monkeypatch.setattr("app.rag.question_retrieval.qdrant_enabled", lambda: True)
    monkeypatch.setattr(
        "app.rag.question_retrieval.search_question_points",
        lambda query_text, limit: [
            {
                "point_id": "current-app",
                "score": 0.99,
                "payload": {
                    "application_id": str(current_application_id),
                    "question_text": "Should be excluded.",
                },
            },
            {
                "point_id": "prior-good-question",
                "score": 0.81,
                "payload": {
                    "application_id": str(other_application_id),
                    "focus_area_id": "FA-001",
                    "question_role": "Concrete opener through project work.",
                    "question_text": "Which project changed how you approached technical work?",
                    "why_this": "This opens through a concrete example.",
                    "rating_avg": 5,
                    "rating_count": 2,
                },
            },
        ],
    )

    result = retrieve_question_generation_context(
        application_id=current_application_id,
        question_bundle={
            "focus_areas": [
                {
                    "focus_area": {
                        "focus_area_id": "FA-001",
                        "title": "Technical making",
                        "territory": "How the applicant builds through uncertainty.",
                        "what_makes_it_worth_time": "The file shows repeated self-directed building.",
                    },
                    "themes": [{"title": "Builder energy", "interview_direction": "Probe how hands-on the work is."}],
                    "signals": [
                        {
                            "signal": {
                                "title": "Project signal",
                                "core_observation": "The applicant describes self-led implementation.",
                            }
                        }
                    ],
                }
            ]
        },
    )

    assert result["provider"] == "qdrant"
    assert result["fallback_reason"] is None
    assert result["focus_area_examples"][0]["focus_area_id"] == "FA-001"
    assert result["focus_area_examples"][0]["examples"][0]["question_text"] == (
        "Which project changed how you approached technical work?"
    )
    assert result["focus_area_examples"][0]["selected_points"][0]["point_id"] == "prior-good-question"


def test_generation_retrieval_disables_cleanly(monkeypatch):
    monkeypatch.setattr("app.rag.question_retrieval.qdrant_enabled", lambda: False)

    result = retrieve_question_generation_context(
        application_id=uuid.uuid4(),
        question_bundle={"focus_areas": []},
    )

    assert result["provider"] == "disabled"
    assert result["fallback_reason"] == "qdrant_disabled"
    assert result["focus_area_examples"] == []


def test_index_question_version_builds_qdrant_payload(monkeypatch):
    db = TestingSessionLocal()
    captured = {}
    try:
        db.query(QuestionVersionRating).delete()
        db.query(QuestionGeneratedVersion).delete()
        db.query(QuestionGenerationThread).delete()

        application_id = uuid.uuid4()
        thread_id = uuid.uuid4()
        version_id = uuid.uuid4()
        user_id = uuid.uuid4()

        thread = QuestionGenerationThread(
            id=thread_id,
            application_id=application_id,
            focus_area_id="focus-a",
            base_question_id="q1",
            question_role="debugging probe",
            theme_title_snapshot="Systems",
            theme_direction_snapshot="Understand debugging choices",
        )
        version = QuestionGeneratedVersion(
            id=version_id,
            thread_id=thread_id,
            application_id=application_id,
            focus_area_id="focus-a",
            base_question_id="q1",
            version_index=1,
            question_text="Where did your first approach break down?",
            why_this="It asks for concrete debugging evidence.",
            generation_source="system_initial",
            is_active=True,
        )
        rating = QuestionVersionRating(
            question_version_id=version_id,
            application_id=application_id,
            rated_by_user_id=user_id,
            surface_role="admin",
            surface_phase="pre_assignment",
            rating=5,
        )
        db.add_all([thread, version, rating])
        db.commit()

        def fake_upsert_question_point(*, point_id, text, payload):
            captured["point_id"] = point_id
            captured["text"] = text
            captured["payload"] = payload
            return {"status": "indexed"}

        monkeypatch.setattr("app.rag.indexing.upsert_question_point", fake_upsert_question_point)

        result = index_question_version(db, version_id)

        assert result["status"] == "indexed"
        assert captured["point_id"] == str(version_id)
        assert "Where did your first approach break down?" in captured["text"]
        assert captured["payload"]["question_role"] == "debugging probe"
        assert captured["payload"]["rating_avg"] == 5
        assert captured["payload"]["rating_count"] == 1
    finally:
        db.close()


def test_schedule_question_version_index_dispatches_after_commit(monkeypatch):
    original_qdrant_url = settings.QDRANT_URL
    original_qdrant_disable = settings.QDRANT_DISABLE
    settings.QDRANT_URL = "http://qdrant.test:6333"
    settings.QDRANT_DISABLE = False
    calls = []

    class FakeTask:
        @staticmethod
        def apply_async(args, queue):
            calls.append({"args": args, "queue": queue})

    monkeypatch.setattr("app.tasks.rag.index_question_version_task", FakeTask)

    db = TestingSessionLocal()
    try:
        version_id = uuid.uuid4()
        schedule_question_version_index(db, version_id)
        assert calls == []

        db.commit()

        assert calls == [{"args": [str(version_id)], "queue": settings.CELERY_QUEUE_GENERATION}]
    finally:
        settings.QDRANT_URL = original_qdrant_url
        settings.QDRANT_DISABLE = original_qdrant_disable
        db.close()
