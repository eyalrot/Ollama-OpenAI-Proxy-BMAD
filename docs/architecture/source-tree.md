# Source Tree

```plaintext
ollama-openai-proxy/
├── src/
│   ├── __init__.py
│   ├── main.py                    # FastAPI application entry
│   ├── config.py                  # Configuration management
│   ├── models/
│   │   ├── __init__.py
│   │   ├── ollama.py             # Ollama request/response models
│   │   └── openai.py             # OpenAI model mappings
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── tags.py               # GET /api/tags endpoint
│   │   ├── generate.py           # POST /api/generate endpoint
│   │   ├── chat.py               # POST /api/chat endpoint
│   │   └── embeddings.py         # POST /api/embeddings endpoint
│   ├── services/
│   │   ├── __init__.py
│   │   ├── translator.py         # Core translation logic
│   │   └── openai_client.py      # OpenAI SDK wrapper
│   └── utils/
│       ├── __init__.py
│       ├── errors.py             # Error handling utilities
│       └── streaming.py          # SSE streaming helpers
├── tests/
│   ├── __init__.py
│   ├── conftest.py               # pytest configuration
│   ├── unit/
│   │   ├── test_models.py
│   │   ├── test_translator.py
│   │   └── test_routers.py
│   └── integration/
│       ├── test_ollama_sdk.py
│       ├── test_streaming.py
│       └── test_error_handling.py
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── scripts/
│   ├── start.sh                  # Development start script
│   ├── test.sh                   # Test runner script
│   ├── build.sh                  # Build wheel package
│   └── publish.sh                # Publish to PyPI
├── requirements.txt              # Production dependencies
├── requirements-dev.txt          # Development dependencies
├── pyproject.toml               # Project configuration (PEP 517)
├── setup.py                      # Package setup (for compatibility)
├── setup.cfg                     # Setup configuration
├── MANIFEST.in                   # Package manifest
├── .env.example                 # Environment variables template
├── LICENSE                       # License file
└── README.md                    # Project documentation
```
