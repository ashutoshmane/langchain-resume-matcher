"""Pydantic schemas for structured resume extraction."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ResumeSection(BaseModel):
    """A single parsed section of a resume."""

    heading: str = Field(default="", description="Section heading, e.g. Experience, Education")
    content: str = Field(default="", description="Full text of the section")


class WorkExperience(BaseModel):
    """A single work experience entry."""

    title: str = Field(default="")
    company: str = Field(default="")
    start_date: str = Field(default="")
    end_date: str = Field(default="")
    duration_years: Optional[float] = Field(default=None)
    highlights: list[str] = Field(default_factory=list)


class Education(BaseModel):
    """A single education entry."""

    degree: str = Field(default="")
    institution: str = Field(default="")
    year: str = Field(default="")


class Certification(BaseModel):
    """A single certification entry."""

    name: str = Field(default="")
    issuer: str = Field(default="")
    year: str = Field(default="")


class Resume(BaseModel):
    """Structured representation of a parsed resume."""

    full_name: str = Field(default="", description="Candidate's full name")
    email: str = Field(default="")
    phone: str = Field(default="")
    linkedin_url: str = Field(default="")
    location: str = Field(default="")

    summary: str = Field(default="", description="Professional summary or objective")

    skills: list[str] = Field(
        default_factory=list, description="All skills extracted from resume"
    )
    tools_and_technologies: list[str] = Field(
        default_factory=list, description="Tools, platforms, frameworks"
    )

    work_experiences: list[WorkExperience] = Field(default_factory=list)
    total_years_experience: Optional[float] = Field(
        default=None, description="Aggregated years of professional experience"
    )

    education: list[Education] = Field(default_factory=list)
    certifications: list[Certification] = Field(default_factory=list)

    domains: list[str] = Field(
        default_factory=list, description="Industries/domains worked in"
    )

    raw_sections: list[ResumeSection] = Field(default_factory=list)
    raw_text: str = Field(default="", description="Original full text for reference")

    @property
    def all_text(self) -> str:
        if self.raw_text:
            return self.raw_text
        return "\n".join(s.content for s in self.raw_sections)
