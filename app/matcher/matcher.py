"""Matcher module: compares job requirements against resume using
embedding similarity + rule-based checks.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from app.embeddings.embedding_store import EmbeddingStore
from app.schemas.job import JobRole
from app.schemas.resume import Resume

logger = logging.getLogger(__name__)


@dataclass
class SkillMatchResult:
    matched: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    similarity_scores: dict[str, float] = field(default_factory=dict)
    confidence: float = 1.0


@dataclass
class ExperienceMatchResult:
    required_years: float | None = None
    actual_years: float | None = None
    meets_threshold: bool = False
    alignment_notes: list[str] = field(default_factory=list)
    confidence: float = 1.0


@dataclass
class SeniorityMatchResult:
    job_level: str = ""
    resume_level: str = ""
    level_match: bool = False
    notes: str = ""
    confidence: float = 1.0


@dataclass
class DomainMatchResult:
    job_domains: list[str] = field(default_factory=list)
    resume_domains: list[str] = field(default_factory=list)
    matched: list[str] = field(default_factory=list)
    confidence: float = 1.0


@dataclass
class EducationMatchResult:
    required: list[str] = field(default_factory=list)
    matched: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    confidence: float = 1.0


@dataclass
class KeywordMatchResult:
    required: list[str] = field(default_factory=list)
    found: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    confidence: float = 1.0


class Matcher:
    """Orchestrates matching between a JobRole and Resume."""

    def __init__(self, embedding_store: EmbeddingStore) -> None:
        self.store = embedding_store

    async def match(self, job: JobRole, resume: Resume) -> dict:
        """Run all matchers and return aggregated results."""
        return {
            "skills": await self.match_skills(job, resume),
            "experience": self.match_experience(job, resume),
            "seniority": self.match_seniority(job, resume),
            "domain": self.match_domain(job, resume),
            "education": self.match_education(job, resume),
            "keywords": self.match_keywords(job, resume),
        }

    async def match_skills(self, job: JobRole, resume: Resume) -> SkillMatchResult:
        result = SkillMatchResult()
        all_required = job.required_skills

        if not all_required:
            result.confidence = 0.5
            return result

        resume_skills_lower = {s.lower() for s in resume.skills}
        resume_tools_lower = {s.lower() for s in resume.tools_and_technologies}
        resume_all = resume_skills_lower | resume_tools_lower

        for req_skill in all_required:
            req_lower = req_skill.lower()

            # Direct substring match first
            found = False
            for rs in resume_all:
                if req_lower in rs or rs in req_lower:
                    result.matched.append(req_skill)
                    result.similarity_scores[req_skill] = 1.0
                    found = True
                    break

            if found:
                continue

            # Semantic similarity fallback
            sim = self.store.compute_similarity(req_skill, ", ".join(resume.skills))
            result.similarity_scores[req_skill] = sim
            if sim > 0.65:
                result.matched.append(req_skill)
            else:
                result.missing.append(req_skill)

        return result

    def match_experience(self, job: JobRole, resume: Resume) -> ExperienceMatchResult:
        result = ExperienceMatchResult(
            required_years=job.years_of_experience,
            actual_years=resume.total_years_experience,
        )

        if job.years_of_experience is None:
            result.alignment_notes.append("No explicit years requirement in JD")
            result.meets_threshold = True
            result.confidence = 0.7
            return result

        if resume.total_years_experience is None:
            result.alignment_notes.append("Could not determine total years from resume")
            result.confidence = 0.3
            return result

        if resume.total_years_experience >= job.years_of_experience:
            result.meets_threshold = True
            result.alignment_notes.append(
                f"Resume shows {resume.total_years_experience:.1f} years, "
                f"meets the {job.years_of_experience:.1f}-year requirement"
            )
        else:
            result.meets_threshold = False
            result.alignment_notes.append(
                f"Resume shows {resume.total_years_experience:.1f} years, "
                f"below the {job.years_of_experience:.1f}-year requirement"
            )

        return result

    def match_seniority(self, job: JobRole, resume: Resume) -> SeniorityMatchResult:
        from app.structurer.normalizer import SeniorityMapper

        job_level = SeniorityMapper.to_level(job.seniority_level) if job.seniority_level else 2

        # Infer resume level from total years and titles
        resume_titles = [exp.title for exp in resume.work_experiences]
        resume_title_text = " ".join(resume_titles)
        resume_level = SeniorityMapper.to_level(resume_title_text)

        # Adjust by experience
        if resume.total_years_experience is not None:
            if resume.total_years_experience >= 8:
                resume_level = max(resume_level, 3)
            elif resume.total_years_experience >= 5:
                resume_level = max(resume_level, 2)
            elif resume.total_years_experience >= 2:
                resume_level = max(resume_level, 1)

        level_match = resume_level >= job_level

        return SeniorityMatchResult(
            job_level=job.seniority_level or "mid-level",
            resume_level=f"inferred level {resume_level}",
            level_match=level_match,
            notes=(
                "Resume seniority meets or exceeds job requirement"
                if level_match
                else "Resume seniority appears below job requirement"
            ),
        )

    def match_domain(self, job: JobRole, resume: Resume) -> DomainMatchResult:
        job_domain = job.domain.lower().strip() if job.domain else ""
        resume_domains = [d.lower().strip() for d in resume.domains]

        matched = []
        if job_domain:
            for rd in resume_domains:
                if job_domain in rd or rd in job_domain:
                    matched.append(rd)

        return DomainMatchResult(
            job_domains=[job_domain] if job_domain else [],
            resume_domains=resume_domains,
            matched=matched,
        )

    def match_education(self, job: JobRole, resume: Resume) -> EducationMatchResult:
        required = job.education_requirements
        if not required:
            return EducationMatchResult(confidence=0.8)

        resume_edu_text = " ".join(
            f"{e.degree} {e.institution}" for e in resume.education
        ).lower()

        resume_cert_text = " ".join(c.name for c in resume.certifications).lower()
        combined = resume_edu_text + " " + resume_cert_text

        matched = []
        missing = []
        for req in required:
            req_lower = req.lower()
            if any(word in combined for word in req_lower.split()):
                matched.append(req)
            else:
                missing.append(req)

        return EducationMatchResult(
            required=required,
            matched=matched,
            missing=missing,
        )

    def match_keywords(self, job: JobRole, resume: Resume) -> KeywordMatchResult:
        required = job.must_have_keywords
        if not required:
            return KeywordMatchResult(confidence=0.8)

        resume_text = resume.all_text.lower()

        found = []
        missing = []
        for kw in required:
            kw_lower = kw.lower()
            if kw_lower in resume_text:
                found.append(kw)
            else:
                missing.append(kw)

        return KeywordMatchResult(
            required=required,
            found=found,
            missing=missing,
        )
