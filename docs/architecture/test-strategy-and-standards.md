# Test Strategy and Standards

## Testing Philosophy

- **Primary Goal:** Verify complete Ollama SDK compatibility with proxy service
- **Approach:** SDK-driven testing - use official Ollama SDK as test client
- **Coverage Goals:** 100% Ollama SDK method coverage, 80% code coverage
- **Test Pyramid:** 60% unit, 30% integration (SDK compatibility), 10% E2E
- **Success Criteria:** Existing Ollama code works unchanged when pointed at proxy

## Test Types and Organization

### Unit Tests

- **Framework:** pytest 7.4.3
- **File Convention:** test_{module_name}.py
- **Location:** tests/unit/
- **Mocking Library:** pytest-mock, unittest.mock
- **Coverage Requirement:** 90% for core modules

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
  - **Streaming:** Test SSE responses with SDK streaming methods
  - **Compatibility Matrix:** Test all SDK methods against proxy

**SDK Compatibility Test Suite:**
```python