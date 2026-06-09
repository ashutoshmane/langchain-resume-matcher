"""Pydantic schemas for API request/response models."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.job import JobRole
from app.schemas.resume import Resume
from app.schemas.scoring import MatchResult


class JobInputType(str, Enum):
    pasted_text = "pasted_text"
    public_url = "public_url"
    linkedin_url = "linkedin_url"
    text_file = "text_file"


class ResumeInputType(str, Enum):
    pdf_upload = "pdf_upload"
    pdf_url = "pdf_url"


class JobInput(BaseModel):
    """User-provided job role input."""

    input_type: JobInputType = Field(description="How the job description is provided")
    text: Optional[str] = Field(
        default=None, description="Pasted job description text"
    )
    url: Optional[str] = Field(
        default=None, description="URL to a job posting"
    )


class ResumeInput(BaseModel):
    """User-provided resume input (metadata only; file via multipart)."""

    input_type: ResumeInputType = Field(description="How the resume is provided")
    url: Optional[str] = Field(
        default=None, description="URL to a resume PDF"
    )


class MatchRequest(BaseModel):
    """Combined match request."""

    job: JobInput = Field(description="Job description input")
    resume: ResumeInput = Field(description="Resume input")


class MatchResponse(BaseModel):
    """API response after matching."""

    status: str = Field(default="success")
    job_role: JobRole = Field(description="Structured job role extracted")
    resume: Resume = Field(description="Structured resume extracted")
    match_result: MatchResult = Field(description="Scoring and matching results")


class ErrorResponse(BaseModel):
    status: str = Field(default="error")
    message: str
    detail: Optional[str] = None
