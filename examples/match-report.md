# Match Report: Downloadable Plain-Text Report

Same inputs as `/match`, but returns a plain-text downloadable report instead of JSON.

## Request

```bash
curl -s -X POST http://localhost:8000/api/v1/match/report \
  -F "job_input_type=pasted_text" \
  -F "job_text=Senior Python Engineer. 5+ years experience. Must know Django, PostgreSQL, AWS." \
  -F "resume_input_type=pdf_upload" \
  -F "resume_file=@/path/to/resume.pdf" > match_report.txt
```

## Response (plain text)

```
========================================
  RESUME-JOB MATCH REPORT
========================================

Job Title: Senior Python Engineer
Company:   (not specified)

Overall Match Score: 82.5/100

--- Score Breakdown ---
  Skills Match:            28.0/35
  Experience Relevance:    25.0/25
  Seniority / Years Match: 15.0/15
  Domain / Industry:        8.0/10
  Education / Certs:        3.0/5
  Must-Have Keywords:       3.5/10

--- Skills ---
  Matched: python, django, postgresql
  Missing: aws

--- Experience ---
  Resume shows 6.0 years, meets the 5.0-year requirement

--- Red Flags ---
  (none)

--- Improvement Suggestions ---
  • Consider adding AWS experience
  • Highlight any B2B SaaS domain experience

--- Extraction Confidence ---
  0.95
```

You can also use any other `job_input_type` / `resume_input_type` combination with this endpoint:

```bash
# Public URL + PDF URL
curl -s -X POST http://localhost:8000/api/v1/match/report \
  -F "job_input_type=public_url" \
  -F "job_url=https://careers.example.com/jobs/devops-engineer" \
  -F "resume_input_type=pdf_url" \
  -F "resume_url=https://example.com/resumes/devops-engineer.pdf" > report.txt
```
