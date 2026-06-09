# Match: Text File Job Description + Resume PDF URL

Provide the job description as a path to a local text file and load a resume from a remote PDF URL.

## Request

```bash
curl -s -X POST http://localhost:8000/api/v1/match \
  -F "job_input_type=text_file" \
  -F "job_text=/path/to/job-description.txt" \
  -F "resume_input_type=pdf_url" \
  -F "resume_url=https://example.com/resumes/backend-dev.pdf" | python3 -m json.tool
```

## Response

```json
{
  "status": "success",
  "job_role": {
    "title": "Backend Developer",
    "required_skills": ["python", "fastapi", "postgresql", "redis", "docker"],
    ...
  },
  "resume": {
    "full_name": "Bob Johnson",
    "skills": ["python", "fastapi", "django", "postgresql", "redis", "docker", "aws"],
    ...
  },
  "match_result": {
    "overall_score": 95.0,
    "matched_skills": ["python", "fastapi", "postgresql", "redis", "docker"],
    "missing_skills": [],
    ...
  }
}
```
