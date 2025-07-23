# Security

## Input Validation

- **Validation Library:** Pydantic 2.5.0
- **Validation Location:** Router level before processing
- **Required Rules:**
  - All external inputs MUST be validated
  - Validation at API boundary before processing
  - Whitelist approach preferred over blacklist

## Authentication & Authorization

- **Auth Method:** API key pass-through to backend
- **Session Management:** No sessions - stateless
- **Required Patterns:**
  - Never log API keys
  - Validate API key format if provided
  - Pass through Authorization header unchanged

## Secrets Management

- **Development:** .env file (git-ignored)
- **Production:** Environment variables from orchestrator
- **Code Requirements:**
  - NEVER hardcode secrets
  - Access via configuration service only
  - No secrets in logs or error messages

## API Security

- **Rate Limiting:** Delegated to backend API
- **CORS Policy:** Configurable, disabled by default
- **Security Headers:** X-Content-Type-Options, X-Frame-Options
- **HTTPS Enforcement:** TLS termination at ingress

## Data Protection

- **Encryption at Rest:** N/A - no data storage
- **Encryption in Transit:** HTTPS for all external calls
- **PII Handling:** No PII storage or logging
- **Logging Restrictions:** No request/response bodies, no API keys

## Dependency Security

- **Scanning Tool:** pip-audit in CI
- **Update Policy:** Monthly security updates
- **Approval Process:** PR required for all dependency changes

## Security Testing

- **SAST Tool:** bandit for Python code
- **DAST Tool:** N/A - stateless API
- **Penetration Testing:** Annual for production deployments
