import os
import uuid
import pytest
from app.agents.orchestrator import run_pipeline
from app.canonical.version import CANONICAL_VERSION

def test_pipeline_orchestrator(tmp_path):
    # Create a dummy PDF file that will fail extraction, but test the orchestrator handles error propagation correctly
    # Note: testing full PDF extraction with pdfminer requires an actual PDF file,
    # so we test the orchestrator's reaction to file errors.
    
    non_existent_pdf = str(tmp_path / "missing.pdf")
    
    with pytest.raises(ValueError, match="Critical Failure"):
        run_pipeline(str(uuid.uuid4()), non_existent_pdf)

    # In a full integration suite, we'd provide a sample PDF and assert the output structure.
    # We rely on text_agents.py to test the mocked structure.
