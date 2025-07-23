# Error Handling Strategy

## General Approach

- **Error Model:** Exception-based with typed errors from OpenAI SDK
- **Exception Hierarchy:** OpenAI SDK exceptions → HTTP exceptions → Client errors
- **Error Propagation:** Catch at service boundary, translate to HTTP status codes

## Logging Standards

- **Library:** Python logging module
- **Format:** JSON structured logging
- **Levels:** DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Required Context:**
  - Correlation ID: UUID per request
  - Service Context: endpoint, method, model
  - User Context: No PII, only request metadata

## Error Handling Patterns

### External API Errors

- **Retry Policy:** Built into OpenAI SDK with exponential backoff
- **Circuit Breaker:** Not implemented - rely on SDK retry logic
- **Timeout Configuration:** 60s default, 300s for streaming
- **Error Translation:** SDK exceptions to HTTP status codes

### Business Logic Errors

- **Custom Exceptions:** ValidationError, TranslationError
- **User-Facing Errors:** {"error": {"message": "...", "type": "...", "code": "..."}}
- **Error Codes:** Standard HTTP status codes

### Data Consistency

- **Transaction Strategy:** N/A - stateless service
- **Compensation Logic:** N/A - no state changes
- **Idempotency:** All operations naturally idempotent
