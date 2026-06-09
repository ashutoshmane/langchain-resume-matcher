"""Explainer module: generates human-readable reasoning with evidence.

Uses the LLM to produce a narrative explanation of the match result,
citing only evidence that was actually found in the resume.
"""

from __future__ import annotations

import logging

from langchain_core.prompts import ChatPromptTemplate

from app.core.llm_factory import create_chat_llm
from app.schemas.job import JobRole
from app.schemas.resume import Resume
from app.schemas.scoring import MatchResult

logger = logging.getLogger(__name__)

EXPLAINER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a professional career coach and resume reviewer. Write a concise, actionable explanation of a job-resume match result.

Rules:
- Only reference evidence that is explicitly listed in the match data below.
- Be honest about gaps — do not sugarcoat.
- Suggest 2-3 concrete improvements the candidate can make.
- Keep the tone constructive and professional.
- Output plain text (no markdown), about 3-4 paragraphs."""),
    ("human", """Job Title: {job_title}
Company: {company}

Overall Match Score: {overall_score}/100

Score Breakdown:
{breakdown}

Matched Skills: {matched_skills}
Missing Skills: {missing_skills}

Experience Alignment: {experience_alignment}

Red Flags: {red_flags}

Write the explanation."""),
])


class Explainer:
    """Generate a human-readable match explanation."""

    def __init__(self, model_name: str | None = None) -> None:
        self.llm = create_chat_llm(model_name=model_name, temperature=0.3)

    async def explain(
        self, job: JobRole, resume: Resume, result: MatchResult
    ) -> str:
        """Produce a narrative explanation of the match."""

        # Build a text breakdown
        breakdown_lines = []
        for comp in result.score_breakdown:
            breakdown_lines.append(
                f"  - {comp.component}: {comp.score}/{comp.max_score} "
                f"(matched: {comp.matched_evidence}, missing: {comp.missing_areas})"
            )
        breakdown_text = "\n".join(breakdown_lines)

        prompt = EXPLAINER_PROMPT
        try:
            response = await self.llm.ainvoke(
                prompt.format_messages(
                    job_title=job.title or "Unknown Role",
                    company=job.company or "Unknown Company",
                    overall_score=result.overall_score,
                    breakdown=breakdown_text,
                    matched_skills=", ".join(result.matched_skills) or "None",
                    missing_skills=", ".join(result.missing_skills) or "None",
                    experience_alignment=result.experience_alignment or "N/A",
                    red_flags=", ".join(result.red_flags) or "None",
                )
            )
            return str(response.content).strip()
        except Exception:
            logger.exception("Explainer LLM call failed")
            return self._static_explanation(result)

    @staticmethod
    def _static_explanation(result: MatchResult) -> str:
        """Generate a template-based explanation without LLM."""
        lines = [
            f"Overall match score: {result.overall_score}/100.",
        ]
        if result.matched_skills:
            lines.append(f"Matched skills include: {', '.join(result.matched_skills[:8])}.")
        if result.missing_skills:
            lines.append(f"Consider developing: {', '.join(result.missing_skills[:5])}.")
        if result.red_flags:
            lines.append(f"Note: {', '.join(result.red_flags)}")
        if result.improvement_suggestions:
            lines.append(f"Suggestions: {', '.join(result.improvement_suggestions)}")
        return " ".join(lines)


class ReportGenerator:
    """Assemble the full downloadable report as structured text."""

    @staticmethod
    async def generate(
        job: JobRole,
        resume: Resume,
        result: MatchResult,
        explanation: str,
    ) -> str:
        """Build a formatted text report."""
        sections = [
            "=" * 60,
            "LANGCHAIN RESUME MATCH REPORT",
            "=" * 60,
            "",
            f"JOB: {job.title or 'N/A'}",
            f"COMPANY: {job.company or 'N/A'}",
            f"CANDIDATE: {resume.full_name or 'N/A'}",
            "",
            f"OVERALL SCORE: {result.overall_score}/100",
            f"CONFIDENCE: {result.extraction_confidence:.0%}",
            "",
            "-" * 40,
            "SCORE BREAKDOWN",
            "-" * 40,
        ]

        for comp in result.score_breakdown:
            sections.append(f"  {comp.component}: {comp.score}/{comp.max_score}")
            if comp.matched_evidence:
                sections.append(f"    Matched: {', '.join(comp.matched_evidence)}")
            if comp.missing_areas:
                sections.append(f"    Missing: {', '.join(comp.missing_areas)}")

        sections += [
            "",
            "-" * 40,
            "MATCHED SKILLS",
            "-" * 40,
            ", ".join(result.matched_skills) if result.matched_skills else "None",
            "",
            "-" * 40,
            "MISSING SKILLS",
            "-" * 40,
            ", ".join(result.missing_skills) if result.missing_skills else "None",
            "",
            "-" * 40,
            "RED FLAGS",
            "-" * 40,
        ]
        sections.extend(result.red_flags if result.red_flags else ["None"])
        sections += [
            "",
            "-" * 40,
            "IMPROVEMENT SUGGESTIONS",
            "-" * 40,
        ]
        sections.extend(result.improvement_suggestions if result.improvement_suggestions else ["None"])
        sections += [
            "",
            "-" * 40,
            "EXPLANATION",
            "-" * 40,
            explanation,
            "",
            "-" * 40,
            "EVIDENCE CITATIONS",
            "-" * 40,
        ]
        sections.extend(result.citations_to_resume_sections if result.citations_to_resume_sections else ["None"])
        sections.append("")

        return "\n".join(sections)
