# Match: Public URL Job Posting + Resume PDF Upload

Fetch a job description from a public URL (e.g. company career page) and upload a resume PDF.

## Request

```bash
curl -s -X POST http://localhost:8000/api/v1/match \
  -F "job_input_type=public_url" \
  -F "job_url=https://careers.example.com/jobs/software-engineer" \
  -F "resume_input_type=pdf_upload" \
  -F "resume_file=@/path/to/resume.pdf" | python3 -m json.tool
```

## Response

```json
{
  "status": "success",
  "job_role": {
    "title": "Software Engineer",
    "company": "Example Corp",
    "location": "San Francisco, CA",
    "required_skills": ["python", "go", "kubernetes", "docker"],
    "years_of_experience": 3.0,
    "seniority_level": "Mid-level",
    ...
  },
  "resume": { ... },
  "match_result": {
    "overall_score": 68.0,
    "matched_skills": ["python", "docker"],
    "missing_skills": ["go", "kubernetes"],
    ...
  }
}
```
