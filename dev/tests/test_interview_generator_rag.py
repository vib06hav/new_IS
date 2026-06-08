from app.agents.interview_generator import build_interview_messages


def test_build_interview_messages_includes_rag_context_as_guidance():
    messages = build_interview_messages(
        bundle={
            "application_id": "app-1",
            "focus_areas": [
                {
                    "focus_area": {
                        "focus_area_id": "FA-001",
                        "title": "Technical making",
                    }
                }
            ],
        },
        entity_id_map=[],
        rag_context={
            "provider": "qdrant",
            "strategy_version": "qdrant_generation_v1",
            "fallback_reason": None,
            "focus_area_examples": [
                {
                    "focus_area_id": "FA-001",
                    "focus_area_title": "Technical making",
                    "examples": [
                        {
                            "question_text": "Which project changed how you approached technical work?",
                            "question_role": "Concrete opener through project work.",
                            "why_this": "This opens through a concrete example.",
                            "rating_avg": 5,
                            "rating_count": 2,
                        }
                    ],
                }
            ],
        },
    )

    system_prompt = messages[0]["content"]
    user_prompt = messages[1]["content"]

    assert "quality and style guidance only" in system_prompt
    assert "Do not copy them" in system_prompt
    assert "RETRIEVED PRIOR QUESTION EXAMPLES" in user_prompt
    assert "Which project changed how you approached technical work?" in user_prompt
    assert '"question_groups"' in system_prompt
