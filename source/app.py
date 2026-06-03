"""
FastAPI service exposing repo metadata from datetime.txt.

Endpoints:
    GET /alive      -- liveness probe; 200 if the process is running
    GET /ready      -- readiness probe; 200 if datetime.txt is readable
    GET /repo-name  -- returns the first word from datetime.txt
    GET /timestamp  -- returns the second word from datetime.txt
"""

import os

from fastapi import FastAPI, HTTPException

app = FastAPI()

DATETIME_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datetime.txt")


@app.get("/alive")
def alive() -> dict:
    """Liveness probe -- the process is running."""
    return {"alive": True}


@app.get("/ready")
def ready() -> dict:
    """Readiness probe -- datetime.txt is readable and well-formed."""
    try:
        _read_datetime()
    except Exception as exc:
        raise HTTPException(status_code=503, detail={"ready": False, "reason": str(exc)})
    return {"ready": True}


@app.get("/repo-name")
def repo_name() -> dict:
    """Return the first word of datetime.txt as the repo name."""
    name, _ = _read_datetime()
    return {"repo-name": name}


@app.get("/timestamp")
def timestamp() -> dict:
    """Return the second word of datetime.txt as the timestamp."""
    _, ts = _read_datetime()
    return {"timestamp": ts}


def _read_datetime() -> tuple[str, str]:
    """Read datetime.txt and return (repo_name, timestamp), raising on malformed input."""
    with open(DATETIME_FILE) as f:
        parts = f.read().split()
    if len(parts) < 2:
        raise ValueError(f"datetime.txt must contain two words, got: {parts}")
    return parts[0], parts[1]
