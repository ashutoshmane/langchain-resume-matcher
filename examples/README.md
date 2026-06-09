# Examples

Example requests for every variation of the Resume-Job Matcher API.

## Endpoints

| # | File | `job_input_type` | `resume_input_type` |
|---|------|-------------------|---------------------|
| 1 | [`health-check.md`](./health-check.md) | — | — |
| 2 | [`match-pasted-text-pdf-upload.md`](./match-pasted-text-pdf-upload.md) | `pasted_text` | `pdf_upload` |
| 3 | [`match-pasted-text-pdf-url.md`](./match-pasted-text-pdf-url.md) | `pasted_text` | `pdf_url` |
| 4 | [`match-public-url-pdf-upload.md`](./match-public-url-pdf-upload.md) | `public_url` | `pdf_upload` |
| 5 | [`match-public-url-pdf-url.md`](./match-public-url-pdf-url.md) | `public_url` | `pdf_url` |
| 6 | [`match-linkedin-url-pdf-upload.md`](./match-linkedin-url-pdf-upload.md) | `linkedin_url` | `pdf_upload` |
| 7 | [`match-linkedin-url-pdf-url.md`](./match-linkedin-url-pdf-url.md) | `linkedin_url` | `pdf_url` |
| 8 | [`match-textfile-pdf-upload.md`](./match-textfile-pdf-upload.md) | `text_file` | `pdf_upload` |
| 9 | [`match-textfile-pdf-url.md`](./match-textfile-pdf-url.md) | `text_file` | `pdf_url` |
| 10 | [`match-report.md`](./match-report.md) | Any | Any |

All examples use the `POST /api/v1/match` endpoint except for:

- **Health check** → `GET /api/v1/health`
- **Report** → `POST /api/v1/match/report`

## Quick Reference

```bash
# 1. Health check
curl http://localhost:8000/api/v1/health

# 2. Match: paste JD + upload resume PDF
curl -X POST http://localhost:8000/api/v1/match \
  -F "job_input_type=pasted_text" \
  -F "job_text=Senior Python Engineer..." \
  -F "resume_input_type=pdf_upload" \
  -F "resume_file=@resume.pdf"

# 3. Match: paste JD + remote resume PDF URL
curl -X POST http://localhost:8000/api/v1/match \
  -F "job_input_type=pasted_text" \
  -F "job_text=Junior Frontend Developer..." \
  -F "resume_input_type=pdf_url" \
  -F "resume_url=https://example.com/resume.pdf"

# 4. Match: public URL job posting + upload resume PDF
curl -X POST http://localhost:8000/api/v1/match \
  -F "job_input_type=public_url" \
  -F "job_url=https://careers.example.com/jobs/engineer" \
  -F "resume_input_type=pdf_upload" \
  -F "resume_file=@resume.pdf"

# 5. Match: LinkedIn URL + upload resume PDF
curl -X POST http://localhost:8000/api/v1/match \
  -F "job_input_type=linkedin_url" \
  -F "job_url=https://www.linkedin.com/jobs/view/123" \
  -F "resume_input_type=pdf_upload" \
  -F "resume_file=@resume.pdf"

# 6. Match: text file path + upload resume PDF
curl -X POST http://localhost:8000/api/v1/match \
  -F "job_input_type=text_file" \
  -F "job_text=/path/to/jd.txt" \
  -F "resume_input_type=pdf_upload" \
  -F "resume_file=@resume.pdf"

# 7. Downloadable report
curl -X POST http://localhost:8000/api/v1/match/report \
  -F "job_input_type=pasted_text" \
  -F "job_text=Senior Python Engineer..." \
  -F "resume_input_type=pdf_upload" \
  -F "resume_file=@resume.pdf" > report.txt
```
