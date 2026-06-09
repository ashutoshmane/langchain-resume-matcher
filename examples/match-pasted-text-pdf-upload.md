# Match: Pasted Job Text + Resume PDF Upload

The most common usage — paste a job description and upload a resume PDF file.

## Request

```bash
curl -s -X POST http://localhost:8000/api/v1/match \
  -F "job_input_type=pasted_text" \
  -F "job_text=Senior Python Engineer. 5+ years experience. Must know Django, PostgreSQL, AWS. B2B SaaS experience preferred." \
  -F "resume_input_type=pdf_upload" \
  -F "resume_file=@/path/to/resume.pdf" | python3 -m json.tool
```

## Response

```json
{
  "status": "success",
  "job_role": {
    "title": "Senior Python Engineer",
    "company": "",
    "location": "",
    "responsibilities": [],
    "required_skills": ["python", "django", "postgresql", "aws"],
    "preferred_skills": [],
    "years_of_experience": 5.0,
    "seniority_level": "Senior",
    "domain": "B2B SaaS",
    "education_requirements": [],
    "tools_and_technologies": [],
    "must_have_keywords": [],
    "raw_text": "Senior Python Engineer. 5+ years experience..."
  },
  "resume": {
    "full_name": "Jane Doe",
    "email": "jane@example.com",
    "phone": "",
    "linkedin_url": "",
    "location": "",
    "summary": "...",
    "skills": ["python", "django", "postgresql", "docker", "aws", "redis"],
    "tools_and_technologies": [],
    "work_experiences": [...],
    "total_years_experience": 6.0,
    "education": [...],
    "certifications": [],
    "domains": ["SaaS"],
    "raw_sections": [],
    "raw_text": "..."
  },
  "match_result": {
    "overall_score": 82.5,
    "score_breakdown": [...],
    "matched_skills": ["python", "django", "postgresql"],
    "missing_skills": ["aws"],
    "experience_alignment": "Resume shows 6.0 years, meets the 5.0-year requirement",
    "red_flags": [],
    "improvement_suggestions": ["Consider adding AWS experience"],
    "citations_to_resume_sections": [],
    "extraction_confidence": 0.95
  }
}
```
