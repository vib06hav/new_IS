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
    engine = create_engine('postgresql://postgres:newpassword@localhost/interview_standardiser', connect_args={'options': '-c timezone=utc'})
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
    resp = client.post('/auth/login', json={'email': email, 'password': 'password123'})
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
            # Also mock HTTPX so we don't actually hit an LLM endpoint during local test
            mock_llm_response = {
                "snapshot": "Integration snapshot test.",
                "discussion_focus_areas": [],
                "suggested_questions": []
            }
            with patch('app.api.applications.generate_interview_prep', return_value=mock_llm_response):
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
            
run_integration_test()
