# Match: Public URL Job Posting + Resume PDF URL

Fetch a job description from a public URL and load a resume from a remote PDF URL.

## Request

```bash
curl -s -X POST http://localhost:8000/api/v1/match \
  -F "job_input_type=public_url" \
  -F "job_url=https://careers.example.com/jobs/devops-engineer" \
  -F "resume_input_type=pdf_url" \
  -F "resume_url=https://example.com/resumes/devops-engineer.pdf" | python3 -m json.tool
```

## Response

```json
{
  "status": "success",
  "job_role": {
    "title": "DevOps Engineer",
    "company": "Example Corp",
    "required_skills": ["aws", "terraform", "docker", "kubernetes", "ansible"],
    ...
  },
  "resume": {
    "full_name": "Alice Smith",
    "skills": ["aws", "terraform", "docker", "kubernetes", "gitlab-ci", "python"],
    ...
  },
  "match_result": {
    "overall_score": 85.0,
    "matched_skills": ["aws", "terraform", "docker", "kubernetes"],
    "missing_skills": ["ansible"],
    ...
  }
}
```
