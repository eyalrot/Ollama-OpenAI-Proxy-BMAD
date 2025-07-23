"""Main entry point for Ollama-OpenAI Proxy Service."""
import logging
import sys
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from .config import get_settings
from .exceptions import ConfigurationError
from .routes import chat, embeddings, generate, tags
from .services.openai_service import OpenAIService

# Will be configured after settings are loaded
logger = logging.getLogger(__name__)

__version__ = "0.1.0"


def configure_logging(log_level: str) -> None:
    """Configure application logging."""
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='{"time": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}',
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Handle application startup and shutdown."""
    try:
        # Load and validate settings
        settings = get_settings()

        # Configure logging with the specified level
        configure_logging(settings.log_level)

        # Initialize OpenAI service
        openai_service = OpenAIService(settings)

        # Log startup information
        logger.info(
            "Starting Ollama-OpenAI Proxy Service",
            extra={
                "version": __version__,
                "port": settings.proxy_port,
                "log_level": settings.log_level,
                "openai_base_url": settings.openai_api_base_url,
            },
        )

        # Store in app state
        app.state.settings = settings
        app.state.openai_service = openai_service

        yield

    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise ConfigurationError(f"Application startup failed: {e}") from e
    finally:
        # Cleanup
        if hasattr(app.state, "openai_service"):
            await app.state.openai_service.close()
        logger.info("Shutting down Ollama-OpenAI Proxy Service")


# Create FastAPI app
app = FastAPI(
    title="Ollama-OpenAI Proxy",
    description="OpenAI-compatible proxy for Ollama API",
    version=__version__,
    lifespan=lifespan,
)

# Include routers
app.include_router(tags.router)
app.include_router(generate.router)
app.include_router(chat.router)
app.include_router(embeddings.router)


@app.get("/health")
async def health_check() -> JSONResponse:
    """Health check endpoint."""
    try:
        # Verify we can access settings
        settings = app.state.settings

        return JSONResponse(
            content={"status": "healthy", "version": __version__, "configured": True, "port": settings.proxy_port}
        )
    except Exception:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "version": __version__,
                "configured": False,
                "error": "Configuration not loaded",
            },
        )


@app.get("/config/validate")
async def validate_config() -> JSONResponse:
    """Validate configuration (excludes sensitive data)."""
    try:
        settings = app.state.settings

        return JSONResponse(
            content={
                "status": "valid",
                "config": {
                    "openai_api_base_url": settings.openai_api_base_url,
                    "proxy_port": settings.proxy_port,
                    "log_level": settings.log_level,
                    "request_timeout": settings.request_timeout,
                    "api_key_configured": bool(settings.openai_api_key),
                },
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Configuration validation failed: {e!s}") from e


@app.get("/openai/health")
async def openai_health_check() -> JSONResponse:
    """Check OpenAI API connectivity."""
    try:
        service = app.state.openai_service
        health = await service.health_check()

        status_code = 200 if health["status"] == "healthy" else 503
        return JSONResponse(status_code=status_code, content=health)
    except Exception as e:
        return JSONResponse(status_code=503, content={"status": "error", "error": str(e)})


def main() -> None:
    """Run the application."""
    import uvicorn

    try:
        # Load settings to fail fast if configuration is invalid
        settings = get_settings()

        # Configure logging before starting the server
        configure_logging(settings.log_level)

        logger.info(f"Starting server on port {settings.proxy_port}")

        uvicorn.run(
            "ollama_openai_proxy.main:app",
            host="0.0.0.0",
            port=settings.proxy_port,
            reload=True,
            log_config=None,  # Use our custom logging
        )
    except ConfigurationError as e:
        print(f"Configuration Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Failed to start application: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
