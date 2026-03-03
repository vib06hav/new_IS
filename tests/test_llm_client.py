import pytest
from unittest.mock import patch, MagicMock
from app.llm.client import generate_interview_prep

def test_generate_interview_prep_success():
    mock_canonical = {"canonical_version": "1.0", "identifiers": {"application_id": "123"}}
    
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [{
            "message": {
                "content": '{"snapshot": "Applicant data shows...", "discussion_focus_areas": ["Math Olympiad"], "suggested_questions": ["Explain your role?"]}'
            }
        }]
    }

    with patch("httpx.post", return_value=mock_response) as mock_post:
        result = generate_interview_prep(mock_canonical)
        
        mock_post.assert_called_once()
        assert "snapshot" in result
        assert "discussion_focus_areas" in result
        assert "suggested_questions" in result
        assert len(result["suggested_questions"]) == 1
        
        # Check prompt enforces rules
        call_kwargs = mock_post.call_args.kwargs
        prompt_content = call_kwargs["json"]["messages"][0]["content"]
        assert "Do not use evaluative adjectives" in prompt_content
        assert "Canonical Representation:" in prompt_content
