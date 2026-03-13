# API Documentation

## `POST /api/v1/audit`
Initiates a new accessibility audit over a URL.

**Required JSON payload**:
```json
{
  "url": "https://example.com",
  "engines": ["wcag_deterministic", "structural_engine"]
}
```

**Response**:
`200 OK`
```json
{
  "audit_id": "uuid-v4",
  "status": "started",
  "url": "https://example.com"
}
```

## `GET /api/v1/audit/{audit_id}`
Retrieves a fully generated `AuditReport`.

**Response (Sample)**:
```json
{
  "id": "uuid-v4",
  "issues": [
    {
       "title": "Low text contrast",
       "severity": "serious",
       "engine_name": "contrast_engine"
    }
  ]
}
```

## `GET /api/v1/engines`
Returns all registered and loaded engines available to the orchestrator.

## `GET /metrics`
Exposed for Prometheus scraper services. Includes API route execution latency and failure states.
