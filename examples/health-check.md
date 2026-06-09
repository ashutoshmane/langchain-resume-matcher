# Health Check

Verify the API is running.

## Request

```bash
curl -s http://localhost:8000/api/v1/health | python3 -m json.tool
```

## Response

```json
{
  "status": "ok"
}
```
