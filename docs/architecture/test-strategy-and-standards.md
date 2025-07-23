# Test Strategy and Standards

## Testing Philosophy

- **Primary Goal:** Verify complete Ollama SDK compatibility with proxy service
- **Approach:** SDK-driven testing - use official Ollama SDK as test client
- **Coverage Goals:** 100% Ollama SDK method coverage, 80% code coverage
- **Test Pyramid:** 60% unit, 30% integration (SDK compatibility), 10% E2E
- **Success Criteria:** Existing Ollama code works unchanged when pointed at proxy

## Test Environment Strategy

### Local Development Testing
- **Environment:** Python virtual environment (venv)
- **Setup:** `pytest` runs from activated venv
- **Dependencies:** Installed via `pip install -r requirements-dev.txt`
- **Benefits:** Isolated, reproducible test environment

### CI/CD Testing
- **Environment:** GitHub Actions containers
- **Setup:** Fresh container for each test run
- **Dependencies:** Direct pip install (no venv)
- **Benefits:** Clean slate, no cross-contamination

## Test Types and Organization

### Unit Tests

- **Framework:** pytest 7.4.3
- **File Convention:** test_{module_name}.py
- **Location:** tests/unit/
- **Mocking Library:** pytest-mock, unittest.mock
- **Coverage Requirement:** 90% for core modules
- **Local Execution:** Run from within activated venv
- **CI Execution:** Run directly in container

**AI Agent Requirements:**
- Generate tests for all public methods
- Cover edge cases and error conditions
- Follow AAA pattern (Arrange, Act, Assert)
- Mock all external dependencies

### Integration Tests

- **Scope:** Ollama SDK compatibility testing with all proxy endpoints
- **Location:** tests/integration/
- **Primary Focus:** Verify official Ollama Python SDK works seamlessly with proxy
- **Test Infrastructure:**
  - **Ollama SDK:** Use official SDK as test client
  - **OpenAI Backend:** Mock responses using pytest fixtures

### Contract Tests (NEW - Critical for API Compliance)

- **Purpose:** Validate API responses against Ollama's exact specification
- **Location:** tests/contract/
- **Framework:** JSON Schema validation with OpenAPI spec
- **Coverage:** All Ollama API endpoints
- **Execution:** Must pass before any PR merge

**Contract Test Requirements:**
1. Validate response structure matches OpenAPI schema
2. Check for required fields (including duplicates like name/model)
3. Verify timestamp formats and data types
4. Test both streaming and non-streaming responses
5. Compare with recorded real Ollama responses

**Example Contract Test:**
```python
def test_tags_endpoint_contract(test_client, openapi_spec):
    response = test_client.get("/api/tags")
    schema = openapi_spec["paths"]["/api/tags"]["get"]["responses"]["200"]
    validate(response.json(), schema)
    # Verify critical duplicate fields
    model = response.json()["models"][0]
    assert model["name"] == model["model"]  # Must be equal!
```
  - **Streaming:** Test SSE responses with SDK streaming methods
  - **Compatibility Matrix:** Test all SDK methods against proxy

**SDK Compatibility Test Suite:**
```python