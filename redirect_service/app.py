import os

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
import redis

app = FastAPI(title="URL Redirect Service")

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

pool = redis.ConnectionPool(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)


def get_redis() -> redis.Redis:
    return redis.Redis(connection_pool=pool)


@app.get("/health")
def health():
    try:
        r = get_redis()
        r.ping()
        return {"status": "healthy", "redis": "connected"}
    except redis.ConnectionError:
        raise HTTPException(status_code=503, detail="Redis unavailable")


@app.get("/{code}")
def redirect(code: str):
    r = get_redis()
    url = r.get(f"url:{code}")
    if not url:
        raise HTTPException(status_code=404, detail="Short URL not found")
    return RedirectResponse(url=url, status_code=307)
