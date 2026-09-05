"""
AssessNex AI Backend Main Application.

FastAPI application for generating AI/ML MTech level questions using
Google Gemini and agentic AI patterns.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from backend.app.config import get_settings
from backend.app.utils import get_logger
from backend.app.middleware import LoggingMiddleware
from backend.app.routers import health, questions, plagiarism, papers_enhanced, documents, evaluation

# Get logger
app_logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifespan events.

    Handles startup and shutdown events for the FastAPI application.
    """
    # Startup
    app_logger.info("AssessNex AI Backend starting up...")
    app_logger.info(f"Environment: {get_settings().ENVIRONMENT}")
    app_logger.info(f"Debug: {get_settings().DEBUG}")

    yield

    # Shutdown
    app_logger.info("AssessNex AI Backend shutting down...")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        FastAPI: Configured FastAPI application instance
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        description="Platform for generating AI/ML MTech level questions using Agentic AI",
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        lifespan=lifespan,
    )

    # Configure CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add request/response logging middleware
    app.add_middleware(LoggingMiddleware, logger=app_logger)

    # Include routers
    app.include_router(health.router)
    app.include_router(questions.router, prefix=settings.API_V1_STR)
    app.include_router(plagiarism.router, prefix=settings.API_V1_STR)
    app.include_router(papers_enhanced.router, prefix=settings.API_V1_STR)
    app.include_router(documents.router, prefix=settings.API_V1_STR)
    app.include_router(evaluation.router, prefix=settings.API_V1_STR)

    # Root endpoint
    @app.get("/", tags=["root"])
    async def root():
        """
        Root endpoint providing API information.

        Returns:
            dict: API information and available endpoints
        """
        return {
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "running",
            "docs": "/docs",
            "redoc": "/redoc",
            "health": "/health",
            "api_prefix": settings.API_V1_STR,
        }

    # Health check
    @app.get("/health", tags=["health"])
    async def health_endpoint():
        """
        Quick health check endpoint.

        Returns:
            dict: Health status
        """
        return {"status": "ok"}

    # Exception handler for validation errors
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request, exc: RequestValidationError):
        """
        Handle request validation errors.

        Args:
            request: FastAPI request object
            exc: Validation error exception

        Returns:
            JSONResponse: Error response with details
        """
        app_logger.warning(f"Validation error: {exc}")

        return JSONResponse(
            status_code=422,
            content={
                "error": "validation_error",
                "message": "Invalid request data",
                "details": exc.errors(),
            },
        )

    # Exception handler for general exceptions
    @app.exception_handler(Exception)
    async def general_exception_handler(request, exc: Exception):
        """
        Handle general exceptions.

        Args:
            request: FastAPI request object
            exc: Exception

        Returns:
            JSONResponse: Error response
        """
        app_logger.error(f"Unhandled exception: {str(exc)}")

        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "message": "An unexpected error occurred",
            },
        )

    app_logger.info(f"FastAPI application created successfully")

    return app


# Create application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()

    app_logger.info(
        f"Starting server on {settings.SERVER_HOST}:{settings.SERVER_PORT}"
    )

    uvicorn.run(
        "main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower(),
    )
