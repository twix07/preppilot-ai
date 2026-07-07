"""Test config: force SQLite + mock LLM before any app import, provide an auth'd client."""
from __future__ import annotations

import os
import tempfile

# MUST run before importing app modules (settings are read at import time).
_DB_FD, _DB_PATH = tempfile.mkstemp(suffix=".db")
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_DB_PATH}"
os.environ["ANTHROPIC_API_KEY"] = ""          # -> deterministic mock mode
os.environ["ALLOW_DEV_LOGIN"] = "true"
os.environ["ENVIRONMENT"] = "development"
os.environ["READINESS_MIN_SESSIONS"] = "3"

import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402


@pytest_asyncio.fixture
async def app():
    from app.db.session import init_db
    from app.main import create_app

    await init_db()
    return create_app()


@pytest_asyncio.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def auth_client(client):
    resp = await client.post("/auth/dev-login", json={"email": "t@test.io", "name": "Tester"})
    token = resp.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client
