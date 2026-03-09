import os
import string
import random

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl
import redis

app = FastAPI(title="URL Shortener API")

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
BASE_URL = os.getenv("BASE_URL", "http://localhost")
RATE_LIMIT = int(os.getenv("RATE_LIMIT", 10))
RATE_WINDOW = int(os.getenv("RATE_WINDOW", 60))

pool = redis.ConnectionPool(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)


def get_redis() -> redis.Redis:
    return redis.Redis(connection_pool=pool)


def check_rate_limit(client_ip: str, r: redis.Redis) -> tuple[bool, int]:
    key = f"rate:{client_ip}"
    current = r.get(key)
    if current is None:
        r.set(key, 1, ex=RATE_WINDOW)
        return True, RATE_LIMIT - 1
    count = int(current)
    if count >= RATE_LIMIT:
        ttl = r.ttl(key)
        return False, 0
    r.incr(key)
    return True, RATE_LIMIT - count - 1


class ShortenRequest(BaseModel):
    url: HttpUrl


class ShortenResponse(BaseModel):
    short_url: str
    code: str
    original_url: str


def generate_code(length: int = 6) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(random.choices(alphabet, k=length))


@app.post("/shorten", response_model=ShortenResponse)
def shorten_url(req: ShortenRequest, request: Request):
    r = get_redis()

    client_ip = request.headers.get("X-Real-IP", request.client.host)
    allowed, remaining = check_rate_limit(client_ip, r)
    if not allowed:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded. Try again later."},
            headers={"X-RateLimit-Limit": str(RATE_LIMIT), "X-RateLimit-Remaining": "0"},
        )

    code = generate_code()
    while r.exists(f"url:{code}"):
        code = generate_code()

    r.set(f"url:{code}", str(req.url))
    return ShortenResponse(
        short_url=f"{BASE_URL}/r/{code}",
        code=code,
        original_url=str(req.url),
    )


@app.get("/urls")
def list_urls():
    r = get_redis()
    keys = r.keys("url:*")
    urls = {}
    for key in keys:
        code = key.replace("url:", "")
        urls[code] = r.get(key)
    return urls


@app.get("/health")
def health():
    try:
        r = get_redis()
        r.ping()
        return {"status": "healthy", "redis": "connected"}
    except redis.ConnectionError:
        raise HTTPException(status_code=503, detail="Redis unavailable")
