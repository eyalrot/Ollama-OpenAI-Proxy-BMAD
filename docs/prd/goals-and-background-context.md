# Goals and Background Context

## Goals

- Enable zero-code migration for existing Ollama applications to work with OpenAI-compatible backends
- Maintain 100% compatibility with the official Ollama SDK
- Provide a simple, stateless proxy service that translates between Ollama and OpenAI API formats
- Support all core Ollama functionality including model listing, text generation, chat, and embeddings
- Allow deployment via multiple methods: Docker, Docker Compose, Python wheel, and PyPI
- Ensure reliable streaming support for real-time responses
- Minimize dependencies and complexity following KISS principles

## Background Context

The Ollama-OpenAI Proxy Service addresses a critical migration challenge faced by organizations using Ollama-based applications. Many teams have built integrations using the Ollama API and SDK but need to leverage OpenAI or OpenAI-compatible services for enhanced capabilities, cost optimization, or organizational requirements. Currently, this migration requires significant code rewrites and testing efforts. This proxy service eliminates that barrier by acting as a transparent translation layer, allowing existing Ollama applications to communicate with OpenAI backends without any code modifications.

The service implements the Ollama API specification while using the OpenAI Python SDK as a client library to communicate with backends. This architectural approach ensures reliability through the use of official SDKs while maintaining the simplicity needed for a translation-only service.

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-01-23 | 1.0 | Initial PRD creation from existing documentation | Eyal Rot |
