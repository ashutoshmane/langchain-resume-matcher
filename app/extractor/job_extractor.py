"""Extract structured job role information from raw text using an LLM."""

from __future__ import annotations

import json
import logging

from langchain_core.documents import Document
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.core.llm_factory import create_chat_llm
from app.schemas.job import JobRole

logger = logging.getLogger(__name__)

JOB_EXTRACTION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an expert job description parser. Extract structured information from the provided content.

The input may be clean text OR raw HTML from a job posting page. If it contains HTML, look for job details within HTML elements and attributes (e.g., <h1> for title, <div class="job-description"> for responsibilities).

Instructions:
- Extract the job title, company name, and location if present.
- List all required skills (technical and soft) separately from preferred/nice-to-have skills.
- Identify the minimum years of experience required and the seniority level.
- Determine the industry domain (e.g., B2B SaaS, FinTech, Healthcare).
- List education requirements and specific certifications mentioned.
- List all tools, platforms, and technologies mentioned.
- Extract "must-have" keywords that appear to be hard requirements.

Be precise — only include items explicitly mentioned or strongly implied by the text.
If a field cannot be determined, leave it empty or as its default value.

{format_instructions}"""),
    ("human", "Job Description Content:\n\n{job_text}"),
])


class JobExtractor:
    """Use an LLM to extract a structured JobRole from raw job description text."""

    def __init__(self, model_name: str | None = None) -> None:
        self.llm = create_chat_llm(model_name=model_name, temperature=0.0)
        self.parser = PydanticOutputParser(pydantic_object=JobRole)

    async def extract(self, doc: Document) -> JobRole:
        """Extract structured job role from a Document."""
        prompt = JOB_EXTRACTION_PROMPT.partial(
            format_instructions=self.parser.get_format_instructions(),
        )
        chain = prompt | self.llm | self.parser

        try:
            result: JobRole = await chain.ainvoke({"job_text": doc.page_content})
            result.raw_text = doc.page_content
            logger.info("Extracted job role: %s at %s", result.title, result.company)
            return result
        except Exception:
            logger.exception("LLM extraction failed, attempting JSON repair")
            return await self._fallback_extract(doc)

    async def _fallback_extract(self, doc: Document) -> JobRole:
        """Attempt a looser extraction if the structured one fails."""
        repair_prompt = ChatPromptTemplate.from_messages([
            ("system", "Extract the job role into valid JSON matching this schema. Return ONLY the JSON object."),
            ("human", "{text}"),
        ])
        response = await self.llm.ainvoke(repair_prompt.format_messages(text=doc.page_content[:4000]))
        try:
            data = json.loads(str(response.content))
            return JobRole(**data, raw_text=doc.page_content)
        except Exception:
            logger.warning("Fallback extraction also failed; returning minimal JobRole")
            return JobRole(raw_text=doc.page_content)
