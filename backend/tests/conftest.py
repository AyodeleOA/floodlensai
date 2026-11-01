from __future__ import annotations

import asyncio
import os
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# Set test environment variables before importing app
os.environ.setdefault("APP_ENV", "local")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("AI_PROVIDER_MODE", "mock")
os.environ.setdefault("DEMO_MODE", "true")
os.environ.setdefault("S3_MEDIA_BUCKET", "")

from app.db.base import Base
from app.db.session import async_session_factory, engine
from app.main import app


@pytest_asyncio.fixture(scope="session")
async def setup_db():
    """Create all tables for the test session."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session(setup_db) -> AsyncGenerator:
    """Provide a fresh DB session for each test."""
    async with async_session_factory() as session:
        yield session
        # Clean up after each test
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(table.delete())
        await session.commit()


@pytest_asyncio.fixture
async def client(setup_db) -> AsyncGenerator[AsyncClient, None]:
    """Provide an async HTTP test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_user_headers():
    """Headers simulating a logged-in reviewer for mock auth."""
    return {
        "X-User-Role": "reviewer",
        "X-User-Id": str(uuid.uuid4()),
        "X-User-Email": "reviewer@test.floodlens.ai",
    }


@pytest.fixture
def admin_headers():
    """Headers simulating an admin user for mock auth."""
    return {
        "X-User-Role": "authority_admin",
        "X-User-Id": str(uuid.uuid4()),
        "X-User-Email": "admin@test.floodlens.ai",
    }
