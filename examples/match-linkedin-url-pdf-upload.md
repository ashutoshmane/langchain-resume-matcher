# Match: LinkedIn URL Job Posting + Resume PDF Upload

Attempt to fetch a job description from a LinkedIn URL with a polite User-Agent.  
If LinkedIn blocks the request, the API returns a `422` error instructing you to paste the text manually.

## Request

```bash
curl -s -X POST http://localhost:8000/api/v1/match \
  -F "job_input_type=linkedin_url" \
  -F "job_url=https://www.linkedin.com/jobs/view/123456789" \
  -F "resume_input_type=pdf_upload" \
  -F "resume_file=@/path/to/resume.pdf" | python3 -m json.tool
```

## Success Response

```json
{
  "status": "success",
  "job_role": {
    "title": "Data Scientist",
    "company": "LinkedIn-scraped Company",
    ...
  },
  "resume": { ... },
  "match_result": { ... }
}
```

## Blocked Response (LinkedIn Login Wall)

```json
{
  "detail": "LinkedIn returned a non-public page (likely a login wall). Please use job_input_type='pasted_text' and provide the job description text directly."
}
```

In that case, fall back to:

```bash
curl -s -X POST http://localhost:8000/api/v1/match \
  -F "job_input_type=pasted_text" \
  -F "job_text=Paste the full job description here..." \
  -F "resume_input_type=pdf_upload" \
  -F "resume_file=@/path/to/resume.pdf"
```
