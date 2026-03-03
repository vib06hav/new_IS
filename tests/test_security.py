import pytest
from app.auth.security import get_password_hash, verify_password, create_access_token, decode_access_token

def test_password_hashing():
    password = "supersecretpassword123!"
    hashed = get_password_hash(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False

def test_jwt_encode_decode():
    data = {"sub": "test@example.com", "role": "admin"}
    token = create_access_token(data=data)
    assert token is not None
    
    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded.get("sub") == "test@example.com"
    assert decoded.get("role") == "admin"

def test_jwt_decode_invalid():
    assert decode_access_token("invalid.token.here") is None
