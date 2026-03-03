import pytest
from app.policy.guard import validate_synthesis_output

def test_policy_guard_clean_output():
    """Test standard clean output without evaluative terms."""
    clean_output = {
        "snapshot": "The applicant has completed 12 years of formal education.",
        "discussion_focus_areas": ["Math olympiad participation", "Physics project"],
        "suggested_questions": ["Can you describe your role in the math club?"]
    }
    
    result = validate_synthesis_output(clean_output)
    
    assert result["passed"] is True
    assert len(result["violations_log"]) == 0
    assert result["sanitized_output"] == clean_output
    assert "policy_version" in result

def test_policy_guard_evaluative_output():
    """Test that evaluative terms are flagged."""
    dirty_output = {
        "snapshot": "This is a strong candidate with a strong academic record.",
        "discussion_focus_areas": ["Impressive leadership skills"],
        "suggested_questions": ["How did you achieve such top-performing student results?"]
    }
    
    result = validate_synthesis_output(dirty_output, sanitize=False)
    
    assert result["passed"] is False
    assert len(result["violations_log"]) > 0
    assert result["sanitized_output"] == dirty_output # Without sanitize=True, it doesn't redact

    # Find specific violation fields
    fields_violated = [v["field"] for v in result["violations_log"]]
    assert "snapshot" in fields_violated
    assert "discussion_focus_areas[0]" in fields_violated
    assert "suggested_questions[0]" in fields_violated

def test_policy_guard_sanitization():
    """Test that violating phrases are redacted when sanitize=True."""
    dirty_output = {
        "snapshot": "This is a competitive applicant.",
        "discussion_focus_areas": ["Math"],
        "suggested_questions": ["None"]
    }
    
    result = validate_synthesis_output(dirty_output, sanitize=True)
    
    assert result["passed"] is False
    assert "[REDACTED" in result["sanitized_output"]["snapshot"]
    assert "competitive applicant" not in result["sanitized_output"]["snapshot"]
