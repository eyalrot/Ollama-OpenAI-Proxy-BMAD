"""Main entry point for Ollama-OpenAI Proxy Service."""
import logging
import os
import signal
import sys
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Dict

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from .config import get_settings
from .exceptions import ConfigurationError
from .routes import chat, embeddings, generate, tags
from .services.openai_service import OpenAIService

# Will be configured after settings are loaded
logger = logging.getLogger(__name__)

__version__ = "0.1.0"

# Metrics tracking
metrics: Dict[str, Any] = {
    "requests_total": 0,
    "requests_success": 0,
    "requests_failed": 0,
    "last_request_time": None,
}


def configure_logging(log_level: str) -> None:
    """Configure application logging."""
    # Configure container-friendly JSON logging
    # Structured logging format for containers (unused variable for documentation)

    logging.basicConfig(
        level=getattr(logging, log_level),
        format=(
            '{"time": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", '
            '"message": "%(message)s", "container_id": "' + os.getenv("HOSTNAME", "unknown") + '", '
            '"environment": "' + os.getenv("ENV", "production") + '"}'
        ),
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Handle application startup and shutdown."""
    try:
        # Record startup time
        app.state.startup_time = time.time()

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


@app.middleware("http")
async def track_metrics(request: Any, call_next: Any) -> Any:
    """Track request metrics for monitoring."""
    global metrics

    start_time = time.time()
    metrics["requests_total"] += 1

    try:
        response = await call_next(request)
        if 200 <= response.status_code < 400:
            metrics["requests_success"] += 1
        else:
            metrics["requests_failed"] += 1

        # Track response time
        duration = time.time() - start_time
        response.headers["X-Response-Time"] = f"{duration:.3f}"

        # Log request
        logger.info(
            "Request completed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_seconds": duration,
                "client_host": request.client.host if request.client else "unknown",
            },
        )

        metrics["last_request_time"] = datetime.now(timezone.utc).isoformat()
        return response

    except Exception as e:
        metrics["requests_failed"] += 1
        logger.error(f"Request failed: {e}")
        raise


@app.get("/health")
async def health_check() -> JSONResponse:
    """
    Comprehensive health check endpoint.
    Returns detailed health status of the application and its dependencies.
    """
    health_info: Dict[str, Any] = {
        "status": "healthy",
        "version": __version__,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": os.getenv("ENV", "production"),
        "container_id": os.getenv("HOSTNAME", "unknown"),
    }

    try:
        # Verify we can access settings
        settings = app.state.settings
        health_info["configured"] = True
        health_info["port"] = settings.proxy_port

        # Add uptime if available
        if hasattr(app.state, "startup_time"):
            health_info["uptime_seconds"] = int(time.time() - app.state.startup_time)

        # Check OpenAI service health
        if hasattr(app.state, "openai_service"):
            try:
                service = app.state.openai_service
                openai_health = await service.health_check()
                health_info["openai"] = {
                    "status": openai_health["status"],
                    "models_available": openai_health.get("models_available", 0),
                }
            except Exception as e:
                health_info["openai"] = {
                    "status": "error",
                    "error": str(e),
                }
                health_info["status"] = "degraded"

        status_code = 200 if health_info["status"] == "healthy" else 200  # Still return 200 for degraded
        return JSONResponse(status_code=status_code, content=health_info)

    except Exception as e:
        health_info.update(
            {
                "status": "unhealthy",
                "configured": False,
                "error": str(e),
            }
        )
        return JSONResponse(status_code=503, content=health_info)


@app.get("/ready")
async def readiness_check() -> JSONResponse:
    """
    Readiness probe endpoint.
    Checks if the application is ready to serve requests.
    """
    try:
        # Check if all components are initialized
        if not hasattr(app.state, "settings") or not hasattr(app.state, "openai_service"):
            return JSONResponse(
                status_code=503,
                content={
                    "status": "not_ready",
                    "reason": "Service components not initialized",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )

        # Check OpenAI service connectivity
        service = app.state.openai_service
        health = await service.health_check()

        if health["status"] != "healthy":
            return JSONResponse(
                status_code=503,
                content={
                    "status": "not_ready",
                    "reason": "OpenAI service not healthy",
                    "details": health,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )

        # All checks passed
        return JSONResponse(
            status_code=200,
            content={
                "status": "ready",
                "version": __version__,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "uptime_seconds": int(time.time() - app.state.startup_time),
            },
        )
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )


@app.get("/live")
async def liveness_check() -> JSONResponse:
    """
    Liveness probe endpoint.
    Simple check to verify the application process is alive and responsive.
    """
    return JSONResponse(
        status_code=200,
        content={
            "status": "alive",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "container_id": os.getenv("HOSTNAME", "unknown"),
            "uptime_seconds": int(time.time() - app.state.startup_time) if hasattr(app.state, "startup_time") else 0,
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


@app.get("/metrics")
async def get_metrics() -> JSONResponse:
    """
    Application metrics endpoint for monitoring.
    Returns Prometheus-compatible metrics.
    """
    global metrics

    # Calculate success rate
    success_rate = 0.0
    if metrics["requests_total"] > 0:
        success_rate = (metrics["requests_success"] / metrics["requests_total"]) * 100

    # Get uptime
    uptime_seconds = 0
    if hasattr(app.state, "startup_time") and app.state.startup_time is not None:
        uptime_seconds = int(time.time() - app.state.startup_time)

    return JSONResponse(
        content={
            "app_info": {
                "name": "ollama-openai-proxy",
                "version": __version__,
                "environment": os.getenv("ENV", "production"),
                "container_id": os.getenv("HOSTNAME", "unknown"),
            },
            "uptime_seconds": uptime_seconds,
            "requests": {
                "total": metrics["requests_total"],
                "success": metrics["requests_success"],
                "failed": metrics["requests_failed"],
                "success_rate_percent": round(success_rate, 2),
                "last_request_time": metrics["last_request_time"],
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


def handle_shutdown(signum: int, frame: Any) -> None:
    """Handle graceful shutdown on SIGTERM/SIGINT."""
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    sys.exit(0)


def main() -> None:
    """Run the application."""
    import uvicorn

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)

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
