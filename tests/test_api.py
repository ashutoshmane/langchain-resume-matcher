"""Tests for the resume-job matcher API."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_match_pasted_text_no_resume(client: AsyncClient):
    """Should fail when no resume file is provided."""
    response = await client.post(
        "/api/v1/match",
        data={
            "job_input_type": "pasted_text",
            "job_text": "Software Engineer with 5 years Python experience",
            "resume_input_type": "pdf_upload",
        },
    )
    # 400 or 422 — we expect an error because no file was attached
    assert response.status_code in (400, 422)


@pytest.mark.asyncio
async def test_match_missing_job_text(client: AsyncClient):
    """Should fail when pasted_text is selected but no text provided."""
    response = await client.post(
        "/api/v1/match",
        data={
            "job_input_type": "pasted_text",
            "resume_input_type": "pdf_upload",
        },
    )
    assert response.status_code in (400, 422)


@pytest.mark.asyncio
async def test_match_missing_url(client: AsyncClient):
    """Should fail when public_url is selected but no URL provided."""
    response = await client.post(
        "/api/v1/match",
        data={
            "job_input_type": "public_url",
            "resume_input_type": "pdf_url",
        },
    )
    assert response.status_code in (400, 422)
