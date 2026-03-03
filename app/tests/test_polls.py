import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from app.main import app
from app.core.auth import verify_jwt

client = TestClient(app)

async def mock_verify_jwt():
    return {"user_id": "test_user", "role": "1", "is_inspector": True}

app.dependency_overrides[verify_jwt] = mock_verify_jwt

def test_healthcheck():
    response = client.get("/healthcheck")
    assert response.status_code == 200

def test_poll_lifecycle():
    poll_payload = {"type": "ban", "target_id": str(uuid4())}
    create_res = client.post("/api/polls/", json=poll_payload)
    
    assert create_res.status_code in [201, 409]
    
    if create_res.status_code == 201:
        poll_id = create_res.json()["id"]
        
        vote_payload = {"poll_id": poll_id, "voter_id": "test_user", "choice": "for"}
        vote_res = client.post(f"/api/polls/{poll_id}/vote", json=vote_payload)
        
        assert vote_res.status_code == 201