# API Endpoint Template

## Endpoint Name
Brief description of what this endpoint does

## HTTP Method and URL
```
POST /api/v1/endpoint-name
```

## Authentication
- [ ] No authentication required
- [ ] API key required
- [ ] Bearer token required
- [ ] Session authentication

## Request

### Headers
```json
{
  "Content-Type": "application/json",
  "Authorization": "Bearer <token>"
}
```

### Path Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| param1    | string | Yes      | Description |

### Query Parameters
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| limit     | integer | No      | 10      | Number of items to return |
| offset    | integer | No      | 0       | Number of items to skip |

### Request Body
```json
{
  "field1": "string",
  "field2": 123,
  "field3": true
}
```

#### Schema
| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| field1 | string | Yes | max 255 chars | Field description |
| field2 | integer | Yes | > 0 | Field description |

## Response

### Success Response (200)
```json
{
  "success": true,
  "data": {
    "id": 123,
    "name": "Example",
    "created_at": "2023-01-01T00:00:00Z"
  },
  "meta": {
    "total": 1,
    "page": 1,
    "per_page": 10
  }
}
```

### Error Responses

#### 400 Bad Request
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field1": ["This field is required"]
    }
  }
}
```

#### 401 Unauthorized
```json
{
  "success": false,
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Authentication required"
  }
}
```

#### 404 Not Found
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Resource not found"
  }
}
```

#### 500 Internal Server Error
```json
{
  "success": false,
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "An internal error occurred"
  }
}
```

## Examples

### cURL
```bash
curl -X POST "http://localhost:8001/api/v1/endpoint-name" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-token" \
  -d '{
    "field1": "example",
    "field2": 123
  }'
```

### JavaScript
```javascript
const response = await fetch('/api/v1/endpoint-name', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer your-token'
  },
  body: JSON.stringify({
    field1: 'example',
    field2: 123
  })
});

const data = await response.json();
```

### Python
```python
import requests

response = requests.post(
    'http://localhost:8001/api/v1/endpoint-name',
    headers={
        'Content-Type': 'application/json',
        'Authorization': 'Bearer your-token'
    },
    json={
        'field1': 'example',
        'field2': 123
    }
)

data = response.json()
```

## Rate Limiting
- Limit: 100 requests per minute per user
- Header: `X-RateLimit-Remaining`

## Notes
- Additional implementation notes
- Known limitations
- Related endpoints

## Changelog
- v1.1: Added new field3 parameter
- v1.0: Initial implementation