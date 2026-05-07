import os

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
import redis

from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(title="URL Redirect Service")

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
CACHE_TTL = int(os.getenv("CACHE_TTL", 3600))

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
    response = RedirectResponse(url=url, status_code=307)
    response.headers["Cache-Control"] = f"public, max-age={CACHE_TTL}, s-maxage={CACHE_TTL}"
    return response


Instrumentator().instrument(app).expose(app)
