"""FastAPI routes for the LangChain Resume Matcher."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.core.config import settings
from app.embeddings.embedding_store import EmbeddingStore
from app.explainer.explainer import Explainer, ReportGenerator
from app.extractor.job_extractor import JobExtractor
from app.extractor.resume_extractor import ResumeExtractor
from app.loaders.pdf_loader import PDFLoader
from app.loaders.text_loader import TextFileLoader
from app.loaders.web_loader import LinkedInBlockedError, WebPageLoader
from app.matcher.matcher import Matcher
from app.scorer.weighted_scorer import WeightedScorer
from app.schemas.job import JobRole
from app.schemas.request import (
    ErrorResponse,
    JobInput,
    JobInputType,
    MatchRequest,
    MatchResponse,
    ResumeInput,
    ResumeInputType,
)
from app.schemas.resume import Resume
from app.schemas.scoring import MatchResult
from app.structurer.normalizer import Structurer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["matching"])

# ---------------------------------------------------------------------------
# Shared service instances (created once at import)
# ---------------------------------------------------------------------------
job_extractor = JobExtractor()
resume_extractor = ResumeExtractor()
structurer = Structurer()
embedding_store = EmbeddingStore()
matcher = Matcher(embedding_store)
scorer = WeightedScorer(matcher)
explainer = Explainer()
web_loader = WebPageLoader()
pdf_loader = PDFLoader()
text_loader = TextFileLoader()

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.get("/health")
async def health():
    return {"status": "ok"}


@router.post("/match", response_model=MatchResponse)
async def match_resume_to_job(
    job_input_type: JobInputType = Form(...),
    job_text: Optional[str] = Form(None),
    job_url: Optional[str] = Form(None),
    resume_input_type: ResumeInputType = Form(...),
    resume_url: Optional[str] = Form(None),
    resume_file: Optional[UploadFile] = File(None),
) -> MatchResponse:
    """Match a resume against a job description.

    Accepts multipart/form-data with:
    - job_input_type: pasted_text | public_url | linkedin_url | text_file
    - job_text: pasted job description (for pasted_text)
    - job_url: URL to job posting (for public_url, linkedin_url)
    - resume_input_type: pdf_upload | pdf_url
    - resume_url: URL to resume PDF (for pdf_url)
    - resume_file: uploaded PDF file (for pdf_upload)
    """

    # ------------------------------------------------------------------
    # 1. Ingest job description
    # ------------------------------------------------------------------
    try:
        job_doc = await _ingest_job(job_input_type, job_text, job_url)
        logger.info("job_doc: page_content length=%s, metadata=%s", len(job_doc.page_content) if job_doc.page_content else 0, job_doc.metadata)
    except LinkedInBlockedError as e:
        raise HTTPException(
            status_code=422,
            detail=f"{e}\n\nPlease use job_input_type='pasted_text' and provide the job description text directly.",
        )
    except Exception as e:
        logger.exception("Job ingestion failed")
        raise HTTPException(status_code=400, detail=f"Failed to ingest job description: {e}")

    # ------------------------------------------------------------------
    # 2. Ingest resume
    # ------------------------------------------------------------------
    try:
        resume_doc = await _ingest_resume(resume_input_type, resume_url, resume_file)
    except Exception as e:
        logger.exception("Resume ingestion failed")
        raise HTTPException(status_code=400, detail=f"Failed to ingest resume: {e}")

    # ------------------------------------------------------------------
    # 3. Extract structured data
    # ------------------------------------------------------------------
    job_role: JobRole = await job_extractor.extract(job_doc)
    resume: Resume = await resume_extractor.extract(resume_doc)

    # ------------------------------------------------------------------
    # 4. Normalize / structure
    # ------------------------------------------------------------------
    job_role = structurer.structure_job(job_role)
    resume = structurer.structure_resume(resume)

    # ------------------------------------------------------------------
    # 5. Index resume for semantic search
    # ------------------------------------------------------------------
    await embedding_store.index_resume(resume_doc)

    # ------------------------------------------------------------------
    # 6. Match & score
    # ------------------------------------------------------------------
    match_result: MatchResult = await scorer.score(job_role, resume)

    # ------------------------------------------------------------------
    # 7. Explain (optional — we include it in the response)
    # ------------------------------------------------------------------
    explanation = await explainer.explain(job_role, resume, match_result)

    return MatchResponse(
        status="success",
        job_role=job_role,
        resume=resume,
        match_result=match_result,
    )


@router.post("/match/report")
async def match_with_report(
    job_input_type: JobInputType = Form(...),
    job_text: Optional[str] = Form(None),
    job_url: Optional[str] = Form(None),
    resume_input_type: ResumeInputType = Form(...),
    resume_url: Optional[str] = Form(None),
    resume_file: Optional[UploadFile] = File(None),
):
    """Same as /match but returns a plain-text downloadable report."""
    # Reuse the match logic
    try:
        job_doc = await _ingest_job(job_input_type, job_text, job_url)
    except LinkedInBlockedError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Job ingestion failed: {e}")

    try:
        resume_doc = await _ingest_resume(resume_input_type, resume_url, resume_file)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Resume ingestion failed: {e}")

    job_role = await job_extractor.extract(job_doc)
    resume = await resume_extractor.extract(resume_doc)
    job_role = structurer.structure_job(job_role)
    resume = structurer.structure_resume(resume)
    await embedding_store.index_resume(resume_doc)
    match_result = await scorer.score(job_role, resume)
    explanation = await explainer.explain(job_role, resume, match_result)

    report = await ReportGenerator.generate(job_role, resume, match_result, explanation)

    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(content=report, media_type="text/plain")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
async def _ingest_job(
    input_type: JobInputType,
    text: Optional[str],
    url: Optional[str],
):
    """Route job ingestion to the correct loader."""
    if input_type == JobInputType.pasted_text:
        if not text:
            raise ValueError("job_text is required for pasted_text input type")
        return TextFileLoader.from_string(text, source="pasted_text")

    elif input_type in (JobInputType.public_url, JobInputType.linkedin_url):
        if not url:
            raise ValueError(f"job_url is required for {input_type.value} input type")
        return await web_loader.load(url)

    elif input_type == JobInputType.text_file:
        if not text:
            raise ValueError("job_text should contain the file path for text_file input type")
        return await text_loader.load(text)

    else:
        raise ValueError(f"Unknown job input type: {input_type}")


async def _ingest_resume(
    input_type: ResumeInputType,
    url: Optional[str],
    file: Optional[UploadFile],
):
    """Route resume ingestion to the correct loader."""
    if input_type == ResumeInputType.pdf_upload:
        if not file:
            raise ValueError("resume_file is required for pdf_upload input type")
        # Save uploaded file
        file_path = settings.upload_path / f"resume_{file.filename or 'upload.pdf'}"
        content = await file.read()
        file_path.write_bytes(content)
        return await pdf_loader.load(file_path)

    elif input_type == ResumeInputType.pdf_url:
        if not url:
            raise ValueError("resume_url is required for pdf_url input type")
        return await pdf_loader.load_from_url(url)

    else:
        raise ValueError(f"Unknown resume input type: {input_type}")
