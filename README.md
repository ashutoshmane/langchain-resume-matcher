# LangChain Resume Matcher

AI-powered resume-to-job-description matching. Upload a resume PDF and provide a job description (pasted text, URL, or file) — get a weighted match score with evidence-based explanations.

## Architecture

```
User Input (JD + Resume)
        │
        ▼
  ┌─────────────┐
  │ Input Handler│   Web loader (URL/LinkedIn), PDF loader, text loader
  └──────┬──────┘
         │ Document objects
         ▼
  ┌─────────────┐
  │  Extractor   │   LLM → structured JobRole / Resume (Pydantic)
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │  Structurer  │   Normalize skills, map seniority, clean data
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │  Embeddings  │   Chunk resume → Chroma/FAISS vector store
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │   Matcher    │   Skills (semantic), experience, seniority, domain, education, keywords
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │   Scorer     │   Weighted score out of 100 with per-component breakdown
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │  Explainer   │   LLM narrative + downloadable report
  └─────────────┘
```

## Scoring Weights

| Component               | Weight |
|-------------------------|--------|
| Skills Match            | 35     |
| Experience Relevance    | 25     |
| Seniority / Years Match | 15     |
| Domain / Industry       | 10     |
| Education / Certs       | 5      |
| Must-Have Keywords      | 10     |
| **Total**               | **100**|

## Quick Start

### 1. Set up environment

```bash
cp .env.example .env
# Edit .env with your OPENAI_API_KEY or DEEPSEEK_API_KEY
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the API

```bash
uvicorn app.main:app --reload
```

The API is available at `http://localhost:8000`.  
Interactive docs at `http://localhost:8000/docs`.

### 4. Docker

```bash
docker compose up --build
```

## API Endpoints

### `POST /api/v1/match`

Multipart form with:

| Field              | Type   | Description                                    |
|--------------------|--------|------------------------------------------------|
| `job_input_type`   | enum   | `pasted_text`, `public_url`, `linkedin_url`, `text_file` |
| `job_text`         | string | Pasted JD text (for `pasted_text`)             |
| `job_url`          | string | URL to job posting                             |
| `resume_input_type`| enum   | `pdf_upload`, `pdf_url`                        |
| `resume_url`       | string | URL to resume PDF (for `pdf_url`)              |
| `resume_file`      | file   | Uploaded PDF (for `pdf_upload`)                |

### `POST /api/v1/match/report`

Same inputs, returns a plain-text downloadable report.

### `GET /api/v1/health`

Health check.

## Example

```bash
curl -X POST http://localhost:8000/api/v1/match \
  -F "job_input_type=pasted_text" \
  -F "job_text=Senior Python Engineer. 5+ years experience. Must know Django, PostgreSQL, AWS. B2B SaaS experience preferred." \
  -F "resume_input_type=pdf_upload" \
  -F "resume_file=@/path/to/resume.pdf"
```

Response:

```json
{
  "status": "success",
  "job_role": {
    "title": "Senior Python Engineer",
    "required_skills": ["python", "django", "postgresql", "aws"],
    "years_of_experience": 5.0,
    "domain": "B2B SaaS",
    ...
  },
  "resume": {
    "full_name": "Jane Doe",
    "skills": ["python", "django", "postgresql", "docker", ...],
    ...
  },
  "match_result": {
    "overall_score": 82.5,
    "score_breakdown": [...],
    "matched_skills": ["python", "django", "postgresql"],
    "missing_skills": ["aws"],
    "red_flags": [],
    "improvement_suggestions": ["Consider adding AWS experience"],
    ...
  }
}
```

## LinkedIn Notice

LinkedIn has [crawling terms](https://www.linkedin.com/legal/crawling-terms) that restrict automated access. This project attempts a polite, best-effort fetch of LinkedIn job pages. If the page is blocked or returns a login wall, the API returns a `422` error instructing the user to paste the job description text manually.

## Development Phases

1. ✅ **MVP**: Pasted JD text + resume PDF upload
2. ✅ **Phase 2**: Generic public URL ingestion (company career pages)
3. ✅ **Phase 3**: LinkedIn URL support with fallback to manual paste
4. 🔜 **Phase 4**: Downloadable report endpoint (implemented)

## Tech Stack

- **LangChain** — document ingestion, chains, prompts
- **FastAPI** — REST API
- **Pydantic v2** — structured schemas
- **Chroma / FAISS** — local vector search
- **OpenAI / DeepSeek** — LLM extraction + scoring (DeepSeek takes priority if both keys are set)
- **OpenAI / sentence-transformers** — embeddings (OpenAI if key set, local HuggingFace fallback)
- **pdfplumber / pypdf / Unstructured** — PDF parsing
