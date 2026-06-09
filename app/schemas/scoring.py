"""Pydantic schemas for the scoring output."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ScoreComponent(BaseModel):
    """A single weighted score component with evidence."""

    component: str = Field(description="Name of the scoring component")
    score: float = Field(description="Numeric score for this component")
    max_score: float = Field(description="Maximum possible score")
    weight: float = Field(description="Weight of this component in overall score")
    matched_evidence: list[str] = Field(
        default_factory=list, description="Evidence from resume that matched"
    )
    missing_areas: list[str] = Field(
        default_factory=list, description="Required items not found"
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence in this component's extraction quality",
    )


class MatchResult(BaseModel):
    """Full scoring output."""

    overall_score: float = Field(description="Weighted overall score out of 100")
    score_breakdown: list[ScoreComponent] = Field(
        default_factory=list, description="Per-component breakdown"
    )

    matched_skills: list[str] = Field(
        default_factory=list, description="Skills present in both JD and resume"
    )
    missing_skills: list[str] = Field(
        default_factory=list, description="Required skills not found in resume"
    )

    experience_alignment: str = Field(
        default="", description="Summary of experience match"
    )
    red_flags: list[str] = Field(
        default_factory=list, description="Potential concerns or gaps"
    )
    improvement_suggestions: list[str] = Field(
        default_factory=list, description="How the candidate could improve their match"
    )

    citations_to_resume_sections: list[str] = Field(
        default_factory=list,
        description="Citations linking evidence to resume sections",
    )

    extraction_confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Overall confidence in the extraction quality",
    )
