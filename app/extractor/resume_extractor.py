"""Extract structured resume information from raw text using an LLM."""

from __future__ import annotations

import json
import logging

from langchain_core.documents import Document
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.core.llm_factory import create_chat_llm
from app.schemas.resume import Resume

logger = logging.getLogger(__name__)

RESUME_EXTRACTION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an expert resume parser. Extract structured information from the provided resume text.

Instructions:
- Extract the candidate's full name, email, phone, and LinkedIn URL if present.
- Parse the professional summary or objective statement.
- List ALL skills mentioned (technical, soft, domain-specific).
- List all tools, platforms, frameworks, and technologies.
- For each work experience entry, extract: title, company, dates, and key highlights.
- Calculate total years of professional experience if possible (approximate if needed).
- For each education entry, extract: degree, institution, and year.
- For each certification, extract: name, issuer, and year.
- Identify industries/domains the candidate has worked in.
- Split the resume into logical sections with their headings.

Be thorough — capture every skill and experience mentioned.
If a field cannot be determined, leave it empty or as its default value.

{format_instructions}"""),
    ("human", "Resume Text:\n\n{resume_text}"),
])


class ResumeExtractor:
    """Use an LLM to extract a structured Resume from raw resume text."""

    def __init__(self, model_name: str | None = None) -> None:
        self.llm = create_chat_llm(model_name=model_name, temperature=0.0)
        self.parser = PydanticOutputParser(pydantic_object=Resume)

    async def extract(self, doc: Document) -> Resume:
        """Extract structured resume data from a Document."""
        prompt = RESUME_EXTRACTION_PROMPT.partial(
            format_instructions=self.parser.get_format_instructions(),
        )
        chain = prompt | self.llm | self.parser

        # Truncate if excessively long
        text = doc.page_content[:12000]

        try:
            result: Resume = await chain.ainvoke({"resume_text": text})
            result.raw_text = text
            logger.info("Extracted resume for: %s", result.full_name or "Unknown")
            return result
        except Exception:
            logger.exception("LLM extraction failed, attempting JSON repair")
            return await self._fallback_extract(doc)

    async def _fallback_extract(self, doc: Document) -> Resume:
        repair_prompt = ChatPromptTemplate.from_messages([
            ("system", "Extract the resume into valid JSON matching this schema. Return ONLY the JSON object."),
            ("human", "{text}"),
        ])
        text = doc.page_content[:8000]
        response = await self.llm.ainvoke(repair_prompt.format_messages(text=text))
        try:
            data = json.loads(str(response.content))
            return Resume(**data, raw_text=text)
        except Exception:
            logger.warning("Fallback extraction also failed; returning minimal Resume")
            return Resume(raw_text=text)
