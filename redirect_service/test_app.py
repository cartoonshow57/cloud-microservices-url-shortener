import os

os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("REDIS_PORT", "6379")

from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


class FakeRedis:
    """In-memory stand-in for Redis used during tests."""

    def __init__(self):
        self.store = {}

    def get(self, key):
        return self.store.get(key)

    def ping(self):
        return True


fake = FakeRedis()


@patch("app.get_redis", return_value=fake)
def test_redirect_existing_code(mock_redis):
    fake.store["url:abc123"] = "https://example.com"
    response = client.get("/abc123", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "https://example.com"


@patch("app.get_redis", return_value=fake)
def test_redirect_not_found(mock_redis):
    fake.store.clear()
    response = client.get("/nonexistent", follow_redirects=False)
    assert response.status_code == 404


@patch("app.get_redis", return_value=fake)
def test_health(mock_redis):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
