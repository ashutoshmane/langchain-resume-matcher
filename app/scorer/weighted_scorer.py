"""Weighted scorer: produces a MatchResult from matcher outputs.

Scoring weights (configurable via settings):
- Skills match:     35
- Experience:       25
- Seniority/years:  15
- Domain/industry:  10
- Education/certs:   5
- Must-have keywords:10
Total:             100
"""

from __future__ import annotations

import logging

from app.core.config import settings
from app.matcher.matcher import (
    Matcher,
    SkillMatchResult,
    ExperienceMatchResult,
    SeniorityMatchResult,
    DomainMatchResult,
    EducationMatchResult,
    KeywordMatchResult,
)
from app.schemas.job import JobRole
from app.schemas.resume import Resume
from app.schemas.scoring import MatchResult, ScoreComponent

logger = logging.getLogger(__name__)


class WeightedScorer:
    """Compute the final weighted score from matcher outputs."""

    def __init__(self, matcher: Matcher) -> None:
        self.matcher = matcher

    async def score(self, job: JobRole, resume: Resume) -> MatchResult:
        """Run matching and produce a scored MatchResult."""
        matches = await self.matcher.match(job, resume)

        components: list[ScoreComponent] = []
        overall = 0.0
        total_confidence = 0.0
        confidence_count = 0

        comp = self._score_skills(matches["skills"])
        components.append(comp)
        overall += comp.score * comp.weight / 100
        total_confidence += comp.confidence
        confidence_count += 1

        comp = self._score_experience(matches["experience"])
        components.append(comp)
        overall += comp.score * comp.weight / 100
        total_confidence += comp.confidence
        confidence_count += 1

        comp = self._score_seniority(matches["seniority"])
        components.append(comp)
        overall += comp.score * comp.weight / 100
        total_confidence += comp.confidence
        confidence_count += 1

        comp = self._score_domain(matches["domain"])
        components.append(comp)
        overall += comp.score * comp.weight / 100
        total_confidence += comp.confidence
        confidence_count += 1

        comp = self._score_education(matches["education"])
        components.append(comp)
        overall += comp.score * comp.weight / 100
        total_confidence += comp.confidence
        confidence_count += 1

        comp = self._score_keywords(matches["keywords"])
        components.append(comp)
        overall += comp.score * comp.weight / 100
        total_confidence += comp.confidence
        confidence_count += 1

        red_flags = self._collect_red_flags(matches, resume)
        improvements = self._generate_improvements(matches)

        overall = round(overall, 1)
        extraction_confidence = round(total_confidence / max(confidence_count, 1), 2)

        return MatchResult(
            overall_score=overall,
            score_breakdown=components,
            matched_skills=matches["skills"].matched,
            missing_skills=matches["skills"].missing,
            experience_alignment="; ".join(matches["experience"].alignment_notes),
            red_flags=red_flags,
            improvement_suggestions=improvements,
            citations_to_resume_sections=self._gather_citations(matches, resume),
            extraction_confidence=extraction_confidence,
        )

    def _score_skills(self, m: SkillMatchResult) -> ScoreComponent:
        total = len(m.matched) + len(m.missing)
        if total == 0:
            return ScoreComponent(
                component="Skills Match",
                score=0,
                max_score=settings.weight_skills,
                weight=settings.weight_skills,
                matched_evidence=[],
                missing_areas=[],
                confidence=m.confidence,
            )
        ratio = len(m.matched) / total
        max_s = settings.weight_skills
        return ScoreComponent(
            component="Skills Match",
            score=round(ratio * max_s, 1),
            max_score=max_s,
            weight=settings.weight_skills,
            matched_evidence=m.matched,
            missing_areas=m.missing,
            confidence=m.confidence,
        )

    def _score_experience(self, m: ExperienceMatchResult) -> ScoreComponent:
        if m.required_years is None:
            return ScoreComponent(
                component="Experience Relevance",
                score=settings.weight_experience,
                max_score=settings.weight_experience,
                weight=settings.weight_experience,
                matched_evidence=m.alignment_notes,
                missing_areas=[],
                confidence=m.confidence,
            )
        if m.meets_threshold:
            return ScoreComponent(
                component="Experience Relevance",
                score=settings.weight_experience,
                max_score=settings.weight_experience,
                weight=settings.weight_experience,
                matched_evidence=m.alignment_notes,
                missing_areas=[],
                confidence=m.confidence,
            )
        if m.actual_years and m.required_years > 0:
            ratio = min(m.actual_years / m.required_years, 1.0)
        else:
            ratio = 0.3
        return ScoreComponent(
            component="Experience Relevance",
            score=round(ratio * settings.weight_experience, 1),
            max_score=settings.weight_experience,
            weight=settings.weight_experience,
            matched_evidence=m.alignment_notes,
            missing_areas=["Does not meet minimum years requirement"],
            confidence=m.confidence,
        )

    def _score_seniority(self, m: SeniorityMatchResult) -> ScoreComponent:
        score = settings.weight_seniority if m.level_match else settings.weight_seniority * 0.4
        return ScoreComponent(
            component="Seniority / Years Match",
            score=round(score, 1),
            max_score=settings.weight_seniority,
            weight=settings.weight_seniority,
            matched_evidence=[m.notes] if m.level_match else [],
            missing_areas=[] if m.level_match else [m.notes],
            confidence=m.confidence,
        )

    def _score_domain(self, m: DomainMatchResult) -> ScoreComponent:
        if not m.job_domains:
            return ScoreComponent(
                component="Domain / Industry Match",
                score=settings.weight_domain,
                max_score=settings.weight_domain,
                weight=settings.weight_domain,
                matched_evidence=["No specific domain required"],
                missing_areas=[],
                confidence=m.confidence,
            )
        score = settings.weight_domain if m.matched else settings.weight_domain * 0.3
        return ScoreComponent(
            component="Domain / Industry Match",
            score=round(score, 1),
            max_score=settings.weight_domain,
            weight=settings.weight_domain,
            matched_evidence=m.matched,
            missing_areas=m.job_domains if not m.matched else [],
            confidence=m.confidence,
        )

    def _score_education(self, m: EducationMatchResult) -> ScoreComponent:
        total = len(m.required)
        if total == 0:
            return ScoreComponent(
                component="Education / Certifications",
                score=settings.weight_education,
                max_score=settings.weight_education,
                weight=settings.weight_education,
                matched_evidence=["No specific education requirements"],
                missing_areas=[],
                confidence=m.confidence,
            )
        ratio = len(m.matched) / total
        return ScoreComponent(
            component="Education / Certifications",
            score=round(ratio * settings.weight_education, 1),
            max_score=settings.weight_education,
            weight=settings.weight_education,
            matched_evidence=m.matched,
            missing_areas=m.missing,
            confidence=m.confidence,
        )

    def _score_keywords(self, m: KeywordMatchResult) -> ScoreComponent:
        total = len(m.required)
        if total == 0:
            return ScoreComponent(
                component="Must-Have Keywords",
                score=settings.weight_keywords,
                max_score=settings.weight_keywords,
                weight=settings.weight_keywords,
                matched_evidence=["No must-have keywords specified"],
                missing_areas=[],
                confidence=m.confidence,
            )
        ratio = len(m.found) / total
        return ScoreComponent(
            component="Must-Have Keywords",
            score=round(ratio * settings.weight_keywords, 1),
            max_score=settings.weight_keywords,
            weight=settings.weight_keywords,
            matched_evidence=m.found,
            missing_areas=m.missing,
            confidence=m.confidence,
        )

    @staticmethod
    def _collect_red_flags(matches: dict, resume: Resume) -> list[str]:
        flags: list[str] = []
        if not matches["experience"].meets_threshold and matches["experience"].required_years:
            flags.append(
                f"Below minimum experience: need {matches['experience'].required_years} years"
            )
        if not matches["seniority"].level_match:
            flags.append("Seniority level appears below job requirement")
        if matches["keywords"].missing:
            flags.append(
                f"Missing must-have keywords: {', '.join(matches['keywords'].missing)}"
            )
        return flags

    @staticmethod
    def _generate_improvements(matches: dict) -> list[str]:
        improvements: list[str] = []
        if matches["skills"].missing:
            improvements.append(
                f"Consider adding skills: {', '.join(matches['skills'].missing[:5])}"
            )
        if matches["keywords"].missing:
            improvements.append(
                f"Address missing keywords: {', '.join(matches['keywords'].missing)}"
            )
        if matches["education"].missing:
            improvements.append(
                f"Consider obtaining: {', '.join(matches['education'].missing)}"
            )
        return improvements

    @staticmethod
    def _gather_citations(matches: dict, resume: Resume) -> list[str]:
        """Build citation strings linking evidence to resume sections."""
        citations: list[str] = []
        if matches["skills"].matched:
            citations.append(
                f"Skills found: {', '.join(matches['skills'].matched[:5])}"
            )
        experiences = resume.work_experiences
        if experiences:
            companies = [e.company for e in experiences if e.company]
            if companies:
                citations.append(f"Experience at: {', '.join(companies[:3])}")
        return citations
