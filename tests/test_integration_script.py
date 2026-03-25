import os
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.user import User
from app.auth.security import get_password_hash
from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch

def run_integration_test():
    # Setup test DB
    engine = create_engine('postgresql://postgres:postgres_password@db/ag_db', connect_args={'options': '-c timezone=utc'})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    # Create test user
    email = f'test_{uuid.uuid4()}@example.com'
    pwd = get_password_hash('password123')
    user = User(email=email, password_hash=pwd, role='admin')
    db.add(user)
    db.commit()
    db.refresh(user)
    print(f'Created user: {user.email}')
    
    # Use TestClient to login
    client = TestClient(app, raise_server_exceptions=True)
    resp = client.post('/auth/login', data={'username': email, 'password': 'password123'})
    token = resp.json()['access_token']
    
    # Create a dummy PDF
    pdf_path = f'test_{uuid.uuid4()}.pdf'
    with open(pdf_path, 'w') as f:
        f.write('dummy pdf content')
        
    try:
        # Mock extract_layout_blocks to avoid needing a real PDF
        mock_blocks = {
            "blocks": [
                {"page": 1, "text": "Personal Information\nName: Integration Test\nDate of Birth: 2000-01-01", "bbox": (0,0,10,10)},
                {"page": 1, "text": "Academics\nClass 12\nBoard: CBSE\nPercentage: 95%", "bbox": (0,0,10,10)}
            ],
            "page_count": 1,
            "confidence_score": 0.99
        }
        
        with patch('app.agents.orchestrator.extract_layout_blocks', return_value=mock_blocks):
            # Mock the LLM to avoid real AI generation time
            mock_llm_response = {
                "themes": [
                    {
                        "theme_id": "THEME-001",
                        "title": "Mock",
                        "framing": "Mock framing",
                        "what_this_theme_must_resolve": "Mock resolve",
                        "supporting_signal_ids": ["SIG-001"],
                        "referenced_entity_ids": []
                    }
                ],
                "signals": [
                    {
                        "signal_id": "SIG-001",
                        "theme_id": "THEME-001",
                        "title": "Mock signal",
                        "evidence_anchor": "Mock anchor",
                        "direct_read": "Mock direct read",
                        "what_remains_open": "Mock open question",
                        "why_it_matters": "Mock matters",
                        "referenced_entity_ids": [],
                        "supporting_det_signal_ids": []
                    }
                ],
                "question_groups": [
                    {"theme_id": "THEME-001", "group_title": "Mock Group", "questions": ["Mock question?"]}
                ]
            }
            with patch('app.agents.synthesis_agent.generate_synthesis', return_value=mock_llm_response):
                with open(pdf_path, 'rb') as f:
                    upload_resp = client.post('/applications/upload', files={'file': ('test.pdf', f, 'application/pdf')}, headers={'Authorization': f'Bearer {token}'})
            
        print(f'Upload Response Code: {upload_resp.status_code}')
        if upload_resp.status_code != 201:
            print(f'Upload Failed: {upload_resp.json()}')
        else:
            json_resp = upload_resp.json()
            print(f'Application ID: {json_resp.get("id")}')
            print(f'Status: {json_resp.get("status")}')
            print(f'Synthesis Included: {"synthesis" in json_resp}')
    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
            
if __name__ == "__main__":
    run_integration_test()
