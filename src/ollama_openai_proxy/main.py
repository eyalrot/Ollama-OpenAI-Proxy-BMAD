"""Main entry point for Ollama-OpenAI Proxy Service."""
import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Configure JSON logging
logging.basicConfig(
    level=logging.INFO,
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

__version__ = "0.1.0"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown."""
    logger.info("Starting Ollama-OpenAI Proxy Service")
    yield
    logger.info("Shutting down Ollama-OpenAI Proxy Service")


app = FastAPI(
    title="Ollama-OpenAI Proxy",
    description="OpenAI-compatible proxy for Ollama API",
    version=__version__,
    lifespan=lifespan
)


@app.get("/health")
async def health_check() -> JSONResponse:
    """Health check endpoint."""
    return JSONResponse(
        content={
            "status": "healthy",
            "version": __version__
        }
    )


def main() -> None:
    """Run the application."""
    import uvicorn
    uvicorn.run(
        "ollama_openai_proxy.main:app",
        host="0.0.0.0",
        port=11434,
        reload=True
    )


if __name__ == "__main__":
    main()