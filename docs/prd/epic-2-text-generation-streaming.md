# Epic 2: Text Generation & Streaming

Implement the core text generation functionality with full streaming support. This epic delivers the ability to generate text using Ollama's generate() method, supporting both streaming and non-streaming modes. This is the most critical functionality for most Ollama applications, enabling them to perform AI text generation through OpenAI backends.

## Story 2.1: Implement /api/generate Endpoint

As an Ollama SDK user,
I want to generate text using client.generate() method,
so that I can create AI-generated content through the proxy.

### Acceptance Criteria

1: POST /api/generate endpoint is implemented in FastAPI
2: Endpoint accepts Ollama generate request format with model, prompt, and options
3: Request is validated using Pydantic models
4: Endpoint supports both streaming and non-streaming modes based on request
5: Non-streaming responses return complete JSON response
6: Streaming responses use Server-Sent Events format

## Story 2.2: Translation Engine for Generate Requests

As a developer,
I want to translate Ollama generate requests to OpenAI chat completion format,
so that the requests can be processed by OpenAI backends.

### Acceptance Criteria

1: Translation function converts Ollama prompt to OpenAI messages format
2: Ollama options (temperature, top_p, etc.) are mapped to OpenAI parameters
3: Model name is preserved in the OpenAI request
4: Stream parameter is correctly passed through
5: Translation handles missing optional parameters with defaults
6: Unit tests cover all parameter mappings and edge cases

## Story 2.3: Translation Engine for Generate Responses

As a developer,
I want to translate OpenAI completion responses back to Ollama format,
so that Ollama clients receive expected response structure.

### Acceptance Criteria

1: Translation converts OpenAI chat completion to Ollama generate response
2: Response includes model, created_at, response text, and done flag
3: Timestamps are converted to ISO format
4: Token usage information is included if available
5: Translation handles both complete and streamed responses
6: Error responses maintain Ollama's expected structure

## Story 2.4: Streaming Response Implementation

As an Ollama SDK user,
I want to receive streaming responses for real-time text generation,
so that I can see output as it's being generated.

### Acceptance Criteria

1: Streaming endpoint returns Server-Sent Events (SSE) format
2: Each chunk is a complete JSON object with Ollama format
3: Stream includes incremental response text in each chunk
4: Final chunk has done=true flag
5: Stream handles client disconnections gracefully
6: Errors during streaming are properly formatted and sent

## Story 2.5: Ollama SDK Integration Test for Generate

As an Ollama SDK user,
I want to verify client.generate() works for non-streaming requests,
so that I can generate complete responses.

### Acceptance Criteria

1: Integration test uses Ollama SDK to call generate() without streaming
2: Test verifies complete response is returned with expected fields
3: Test confirms response text is present and non-empty
4: Test verifies model name matches request
5: Test checks done=true flag is set
6: Multiple prompts are tested to ensure consistency

## Story 2.6: Ollama SDK Integration Test for Streaming

As an Ollama SDK user,
I want to verify streaming generation works with the SDK,
so that I can build real-time applications.

### Acceptance Criteria

1: Integration test uses Ollama SDK with stream=True parameter
2: Test collects all chunks from the stream
3: Test verifies each chunk has correct format
4: Test confirms final chunk has done=true
5: Test reconstructs full response from chunks
6: Test verifies streaming provides same result as non-streaming

## Story 2.7: Error Handling for Generation

As a developer,
I want comprehensive error handling for generation requests,
so that clients receive appropriate error messages.

### Acceptance Criteria

1: Rate limit errors (429) are properly translated to Ollama format
2: Authentication errors (401) return appropriate Ollama error structure
3: Model not found errors are handled with clear messages
4: Network timeouts are caught and reported
5: Invalid request parameters return 400 with details
6: All errors include correlation IDs for debugging
