import os

os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("REDIS_PORT", "6379")
os.environ.setdefault("BASE_URL", "http://localhost")

from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


class FakeRedis:
    """In-memory stand-in for Redis used during tests."""

    def __init__(self):
        self.store = {}

    def exists(self, key):
        return key in self.store

    def set(self, key, value):
        self.store[key] = value

    def get(self, key):
        return self.store.get(key)

    def keys(self, pattern="*"):
        import fnmatch
        return [k for k in self.store if fnmatch.fnmatch(k, pattern)]

    def ping(self):
        return True


fake = FakeRedis()


@patch("app.get_redis", return_value=fake)
def test_shorten_url(mock_redis):
    fake.store.clear()
    response = client.post("/shorten", json={"url": "https://example.com"})
    assert response.status_code == 200
    data = response.json()
    assert "short_url" in data
    assert "code" in data
    assert data["original_url"] == "https://example.com/"
    assert len(data["code"]) == 6


@patch("app.get_redis", return_value=fake)
def test_shorten_returns_different_codes(mock_redis):
    fake.store.clear()
    r1 = client.post("/shorten", json={"url": "https://example.com"})
    r2 = client.post("/shorten", json={"url": "https://example.org"})
    assert r1.json()["code"] != r2.json()["code"]


@patch("app.get_redis", return_value=fake)
def test_list_urls(mock_redis):
    fake.store.clear()
    client.post("/shorten", json={"url": "https://example.com"})
    response = client.get("/urls")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


@patch("app.get_redis", return_value=fake)
def test_shorten_invalid_url(mock_redis):
    response = client.post("/shorten", json={"url": "not-a-url"})
    assert response.status_code == 422


@patch("app.get_redis", return_value=fake)
def test_health(mock_redis):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
