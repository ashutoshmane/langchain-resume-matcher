# Match: LinkedIn URL Job Posting + Resume PDF URL

Attempt to fetch a job description from LinkedIn and load a resume from a remote PDF URL.

## Request

```bash
curl -s -X POST http://localhost:8000/api/v1/match \
  -F "job_input_type=linkedin_url" \
  -F "job_url=https://www.linkedin.com/jobs/view/987654321" \
  -F "resume_input_type=pdf_url" \
  -F "resume_url=https://example.com/resumes/jane-doe.pdf" | python3 -m json.tool
```

## Success Response

```json
{
  "status": "success",
  "job_role": {
    "title": "Product Manager",
    "company": "Some Company",
    ...
  },
  "resume": { ... },
  "match_result": { ... }
}
```

## Blocked Response

If LinkedIn blocks the request, you'll get a `422` error. Switch to `pasted_text` as described in the [LinkedIn upload example](./match-linkedin-url-pdf-upload.md).
