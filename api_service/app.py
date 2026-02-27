import os
import string
import random

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl
import redis

app = FastAPI(title="URL Shortener API")

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
BASE_URL = os.getenv("BASE_URL", "http://localhost")

pool = redis.ConnectionPool(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)


def get_redis() -> redis.Redis:
    return redis.Redis(connection_pool=pool)


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
def shorten_url(req: ShortenRequest):
    r = get_redis()
    code = generate_code()
    while r.exists(f"url:{code}"):
        code = generate_code()

    r.set(f"url:{code}", str(req.url))
    return ShortenResponse(
        short_url=f"{BASE_URL}/{code}",
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
