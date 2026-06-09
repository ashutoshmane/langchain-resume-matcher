"""Pydantic schemas for structured job role extraction."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class JobRole(BaseModel):
    """Structured representation of a job description."""

    title: str = Field(default="", description="Job title extracted from description")
    company: str = Field(default="", description="Company name if available")
    location: str = Field(default="", description="Job location if available")

    responsibilities: list[str] = Field(
        default_factory=list, description="Key responsibilities"
    )
    required_skills: list[str] = Field(
        default_factory=list, description="Required technical and soft skills"
    )
    preferred_skills: list[str] = Field(
        default_factory=list, description="Nice-to-have skills"
    )

    years_of_experience: Optional[float] = Field(
        default=None, description="Minimum years of experience required"
    )
    seniority_level: str = Field(
        default="",
        description="e.g. Intern, Junior, Mid-level, Senior, Staff, Principal, Director",
    )

    domain: str = Field(default="", description="Industry domain, e.g. B2B SaaS, FinTech")
    education_requirements: list[str] = Field(
        default_factory=list, description="Required degrees or certifications"
    )

    tools_and_technologies: list[str] = Field(
        default_factory=list, description="Specific tools, platforms, or technologies"
    )

    must_have_keywords: list[str] = Field(
        default_factory=list, description="Hard-requirement keywords"
    )

    raw_text: str = Field(default="", description="Original raw text for reference")

    @property
    def all_skills(self) -> list[str]:
        return self.required_skills + self.preferred_skills
