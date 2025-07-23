# API Compliance Checklist

This checklist MUST be completed before implementing any Ollama API endpoint to prevent SDK compatibility issues.

## Pre-Implementation Checklist

- [ ] **Review API Specification**
  - [ ] Check `/docs/architecture/ollama-api-analysis.md` for endpoint details
  - [ ] Review Postman collection at `/docs/architecture/Ollama REST API.postman_collection.json`
  - [ ] Identify ALL required fields (watch for duplicates!)
  - [ ] Note any special formatting requirements (timestamps, arrays, etc.)

- [ ] **Check for Known Issues**
  - [ ] Review `/docs/architecture/epic-1-fix-guide.md` for lessons learned
  - [ ] Check if endpoint has duplicate fields (like name/model in /api/tags)
  - [ ] Verify timestamp format requirements (RFC3339 with timezone)
  - [ ] Understand streaming format (newline-delimited JSON)

- [ ] **Set Up Contract Tests**
  - [ ] Create contract test BEFORE implementation
  - [ ] Use OpenAPI schema validation
  - [ ] Include field duplication checks
  - [ ] Test both streaming and non-streaming modes

## Implementation Checklist

- [ ] **Use Correct Models**
  - [ ] Import from `/src/ollama_openai_proxy/models/ollama.py`
  - [ ] Ensure all required fields are included (especially duplicate fields!)
  - [ ] The models now handle field duplication automatically in __init__
  - [ ] Add proper field descriptions and examples

- [ ] **Follow Translation Patterns**
  - [ ] Map OpenAI responses to exact Ollama format
  - [ ] Preserve all required fields
  - [ ] Handle context arrays properly
  - [ ] Maintain correct data types

- [ ] **Error Handling**
  - [ ] Return Ollama-compatible error format
  - [ ] Use appropriate HTTP status codes
  - [ ] Include error field in response

## Testing Checklist

- [ ] **Contract Testing**
  - [ ] Run: `pytest tests/contract/test_[endpoint]_contract.py`
  - [ ] Verify all fields match schema
  - [ ] Check duplicate fields are present and equal
  - [ ] Validate against real Ollama responses

- [ ] **SDK Testing**
  - [ ] Test with official Ollama Python SDK
  - [ ] Run: `python examples/test_ollama_sdk.py`
  - [ ] Verify SDK methods work correctly
  - [ ] Check for any transformation issues

- [ ] **CLI Testing**
  - [ ] Test with Ollama CLI commands
  - [ ] Example: `OLLAMA_HOST=http://localhost:11434 ollama list`
  - [ ] Verify output format matches expectations

- [ ] **Validation Tool**
  - [ ] Run: `python tools/validate_against_openapi.py`
  - [ ] Fix any schema validation errors
  - [ ] Document any intentional deviations

## Post-Implementation Checklist

- [ ] **Documentation**
  - [ ] Update endpoint documentation
  - [ ] Add any new quirks to this checklist
  - [ ] Document any SDK transformation behavior

- [ ] **Regression Testing**
  - [ ] Run full test suite: `pytest`
  - [ ] Verify no existing tests broken
  - [ ] Check integration with other endpoints

- [ ] **Performance Check**
  - [ ] Verify response times are reasonable
  - [ ] Check streaming performance
  - [ ] Monitor memory usage for large responses

## Common Pitfalls

1. **Missing Duplicate Fields**: The #1 cause of SDK failures
   - Always check if Ollama expects duplicate fields
   - Example: /api/tags requires both `name` and `model`

2. **Incorrect Timestamp Format**
   - Use: `2023-08-04T19:56:02.647123-08:00`
   - Not: `2023-08-04T19:56:02.647Z`

3. **Wrong Streaming Format**
   - Use: Newline-delimited JSON objects
   - Not: JSON array or Server-Sent Events format

4. **Missing Context Arrays**
   - Preserve token arrays in responses
   - Required for conversation continuity

5. **SDK Response Transformation**
   - SDK may modify API responses
   - Test with both raw API and SDK

## Emergency Fixes

If SDK compatibility issues arise:

1. Check the corrected models for the fix
2. Run contract tests to identify missing fields
3. Use validation tool to find schema mismatches
4. Compare with real Ollama API responses
5. Update this checklist with new findings

Remember: It's better to over-specify fields than to miss required ones!