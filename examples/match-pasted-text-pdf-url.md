# Match: Pasted Job Text + Resume PDF URL

Paste a job description and point to a resume PDF hosted online.

## Request

```bash
curl -s -X POST http://localhost:8000/api/v1/match \
  -F "job_input_type=pasted_text" \
  -F "job_text=Junior Frontend Developer. Must know React, TypeScript, and CSS. 1-2 years experience." \
  -F "resume_input_type=pdf_url" \
  -F "resume_url=https://example.com/resumes/john-doe.pdf" | python3 -m json.tool
```

## Response

```json
{
  "status": "success",
  "job_role": {
    "title": "Junior Frontend Developer",
    "required_skills": ["react", "typescript", "css"],
    "years_of_experience": 2.0,
    "seniority_level": "Junior",
    "domain": "",
    ...
  },
  "resume": {
    "full_name": "John Doe",
    "skills": ["react", "typescript", "javascript", "css", "html", "git"],
    "total_years_experience": 1.5,
    ...
  },
  "match_result": {
    "overall_score": 75.0,
    "matched_skills": ["react", "typescript", "css"],
    "missing_skills": [],
    "improvement_suggestions": ["Consider adding more experience to meet the 2-year threshold"],
    ...
  }
}
```
