"""Normalize and clean extracted job and resume data into a canonical form.

Handles:
- Skill name normalization (lowercase, dedup, alias mapping)
- Years-of-experience calculation
- Seniority-level mapping
"""

from __future__ import annotations

import re
from typing import ClassVar

from app.schemas.job import JobRole
from app.schemas.resume import Resume


class SkillNormalizer:
    """Normalize skill names and map common aliases."""

    ALIASES: ClassVar[dict[str, str]] = {
        "js": "javascript",
        "ts": "typescript",
        "react.js": "react",
        "reactjs": "react",
        "vue.js": "vue",
        "vuejs": "vue",
        "node": "node.js",
        "nodejs": "node.js",
        "golang": "go",
        "cpp": "c++",
        "csharp": "c#",
        "ml": "machine learning",
        "ai": "artificial intelligence",
        "llm": "large language models",
        "gen ai": "generative ai",
        "k8s": "kubernetes",
        "aws cloud": "aws",
        "gcp": "google cloud platform",
        "azure cloud": "azure",
        "ci/cd": "ci/cd pipelines",
        "cicd": "ci/cd pipelines",
        "db": "databases",
        "sql server": "mssql",
        "pg": "postgresql",
        "postgres": "postgresql",
    }

    @classmethod
    def normalize(cls, skill: str) -> str:
        """Return the canonical form of a skill name."""
        s = skill.strip().lower()
        # Remove trailing parentheticals like "(2 years)"
        s = re.sub(r"\s*\(.*?\)\s*", "", s)
        return cls.ALIASES.get(s, s)

    @classmethod
    def normalize_list(cls, skills: list[str]) -> list[str]:
        """Normalize and deduplicate a list of skill strings."""
        seen: set[str] = set()
        result: list[str] = []
        for sk in skills:
            norm = cls.normalize(sk)
            if norm and norm not in seen:
                seen.add(norm)
                result.append(norm)
        return result


class SeniorityMapper:
    """Map seniority strings to canonical levels."""

    LEVELS: ClassVar[dict[str, int]] = {
        "intern": 0,
        "internship": 0,
        "junior": 1,
        "entry level": 1,
        "entry-level": 1,
        "associate": 1,
        "mid": 2,
        "mid-level": 2,
        "midlevel": 2,
        "senior": 3,
        "sr": 3,
        "lead": 4,
        "tech lead": 4,
        "technical lead": 4,
        "staff": 5,
        "principal": 6,
        "director": 7,
        "vp": 8,
        "head": 8,
    }

    @classmethod
    def to_level(cls, text: str) -> int:
        """Convert a seniority string to a numeric level."""
        t = text.lower().strip()
        for key, level in cls.LEVELS.items():
            if key in t:
                return level
        return 2  # default mid-level


class Structurer:
    """Apply normalization to both JobRole and Resume after extraction."""

    def structure_job(self, job: JobRole) -> JobRole:
        """Normalize and clean a JobRole."""
        job.required_skills = SkillNormalizer.normalize_list(job.required_skills)
        job.preferred_skills = SkillNormalizer.normalize_list(job.preferred_skills)
        job.tools_and_technologies = SkillNormalizer.normalize_list(job.tools_and_technologies)
        job.must_have_keywords = [k.lower().strip() for k in job.must_have_keywords]
        return job

    def structure_resume(self, resume: Resume) -> Resume:
        """Normalize and clean a Resume."""
        resume.skills = SkillNormalizer.normalize_list(resume.skills)
        resume.tools_and_technologies = SkillNormalizer.normalize_list(
            resume.tools_and_technologies
        )
        resume.domains = [d.lower().strip() for d in resume.domains]

        # Calculate total years if not set
        if resume.total_years_experience is None and resume.work_experiences:
            total = sum(
                (exp.duration_years or 0) for exp in resume.work_experiences
            )
            if total > 0:
                resume.total_years_experience = total

        return resume
