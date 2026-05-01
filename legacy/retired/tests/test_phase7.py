import os
import sys
import json
import logging
from unittest.mock import patch
from sqlalchemy import create_engine, inspect, text
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app)

def run_tests():
    print("=== Phase 7 Validation Script ===")
    
    # 3. Schema Integrity
    print("Testing Schema Integrity...")
    engine = create_engine(settings.DATABASE_URL)
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    assert {"users", "applications", "canonical_records", "synthesis_records"}.issubset(tables)
    assert len(tables) == 5, f"Unexpected extra tables: {tables}"
    
    users_cols = {c['name']: str(c['type']) for c in inspector.get_columns('users')}
    assert users_cols['id'] == 'UUID'
    
    app_cols = {c['name']: str(c['type']) for c in inspector.get_columns('applications')}
    assert app_cols['id'] == 'UUID'
    
    canon_cols = {c['name']: str(c['type']) for c in inspector.get_columns('canonical_records')}
    assert canon_cols['canonical_data'] == 'JSONB'
    
    syn_cols = {c['name']: str(c['type']) for c in inspector.get_columns('synthesis_records')}
    assert syn_cols['synthesis_output'] == 'JSONB'
    print("✅ Schema Integrity: Passed")

    # 4. Auth Flow
    print("Testing Auth Flow...")
    import time
    username = f"test_{int(time.time())}@example.com"
    password = "testpassword123"
    
    res = client.post("/auth/register", json={
        "email": username,
        "password": password,
        "role": "interviewer"
    })
    assert res.status_code == 201, res.text
    
    res = client.post("/auth/login", data={
        "username": username,
        "password": password
    })
    assert res.status_code == 200, res.text
    token = res.json()["access_token"]
    print("✅ Auth Flow: Passed")

    # 5. Full Pipeline Execution
    print("Testing Full Pipeline Execution...")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create dummy PDF
    pdf_content = b"%PDF-1.4\n1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj\n2 0 obj <</Type /Pages /Kids [3 0 R] /Count 1>> endobj\n3 0 obj <</Type /Page /Parent 2 0 R /Resources <<>> /MediaBox [0 0 612 792] /Contents 4 0 R>> endobj\n4 0 obj <</Length 41>> stream\nBT /F1 12 Tf 0 0 Td (Sample test PDF) Tj ET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000213 00000 n \ntrailer <</Size 5 /Root 1 0 R>>\nstartxref\n304\n%%EOF\n"
    
    with patch('httpx.post') as mock_post:
        mock_response = mock_post.return_value
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": json.dumps({
                "snapshot": "Neutral structural output.",
                "discussion_focus_areas": ["Area 1", "Area 2"],
                "suggested_questions": ["Question 1?"]
            })
        }
        
        with patch('app.agents.orchestrator.extract_layout_blocks') as mock_layout:
            mock_layout.return_value = {
                "blocks": [{"text": "SAT: 1500\nDate: 2023\nGPA: 4.0", "page": 1, "type": "paragraph"}],
                "page_count": 1,
                "confidence_score": 0.95
            }
            
            res = client.post(
                "/applications/upload", 
                headers=headers,
                files={"file": ("dummy.pdf", pdf_content, "application/pdf")}
            )
            
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["status"] == "complete"
    assert "synthesis" in data
    assert "snapshot" in data["synthesis"]
    
    app_id = data["id"]
    
    # 6. Canonical Integrity
    print("Testing Canonical & Policy Guard Integrity...")
    with engine.connect() as conn:
        canon_res = conn.execute(text(f"SELECT canonical_version, canonical_data FROM canonical_records WHERE application_id = '{app_id}'")).fetchone()
        assert canon_res is not None
        assert canon_res[0] == "1.0"
        canon_data = canon_res[1]
        assert isinstance(canon_data["academic_entries"], list)
        assert isinstance(canon_data["test_entries"], list)
        assert isinstance(canon_data["essay_entries"], list)
        assert isinstance(canon_data["activity_entries"], list)
        assert isinstance(canon_data["timeline_entries"], list)
        assert "identifiers" in canon_data
        
        syn_res = conn.execute(text(f"SELECT policy_passed, policy_violations_log FROM synthesis_records WHERE application_id = '{app_id}'")).fetchone()
        assert syn_res is not None
        assert syn_res[0] is True
        assert syn_res[1] is None or len(syn_res[1]) == 0
    
    print("✅ Pipeline, LLM, Canonical & Policy Integrity: Passed")
    print("\nALL AUTOMATED CHECKS COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()
