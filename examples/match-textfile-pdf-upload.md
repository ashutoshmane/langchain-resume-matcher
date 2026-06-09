# Match: Text File Job Description + Resume PDF Upload

Provide the job description as a path to a local text file and upload a resume PDF.

## Request

```bash
curl -s -X POST http://localhost:8000/api/v1/match \
  -F "job_input_type=text_file" \
  -F "job_text=/path/to/job-description.txt" \
  -F "resume_input_type=pdf_upload" \
  -F "resume_file=@/path/to/resume.pdf" | python3 -m json.tool
```

## Response

```json
{
  "status": "success",
  "job_role": {
    "title": "DevOps Engineer",
    "required_skills": ["aws", "terraform", "docker", "kubernetes", "ci/cd"],
    "years_of_experience": 4.0,
    ...
  },
  "resume": { ... },
  "match_result": {
    "overall_score": 90.5,
    "matched_skills": ["aws", "terraform", "docker", "kubernetes", "ci/cd"],
    "missing_skills": [],
    ...
  }
}
```
