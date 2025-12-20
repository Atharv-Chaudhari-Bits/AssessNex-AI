"""
Health check endpoints router.

Provides endpoints for checking application health and readiness.
"""

from fastapi import APIRouter, HTTPException
from backend.app.config import get_settings
from backend.app.schemas import HealthCheckResponse, ErrorResponse
from backend.app.utils import get_logger
from backend.app.llm_client import get_llm_client


logger = get_logger(__name__)
router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Health Check",
    description="Check if the application is running and healthy"
)
async def health_check() -> HealthCheckResponse:
    """
    Health check endpoint.

    Returns:
        HealthCheckResponse: Health status information

    Raises:
        HTTPException: If health check fails
    """
    try:
        settings = get_settings()

        return HealthCheckResponse(
            status="healthy",
            version=settings.APP_VERSION,
            environment=settings.ENVIRONMENT,
        )

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Health check failed")


@router.get(
    "/health/ready",
    response_model=HealthCheckResponse,
    summary="Readiness Check",
    description="Check if the application is ready to handle requests"
)
async def readiness_check() -> HealthCheckResponse:
    """
    Readiness check endpoint.

    Verifies that the application is properly configured and
    all dependencies are available.

    Returns:
        HealthCheckResponse: Readiness status

    Raises:
        HTTPException: If readiness check fails
    """
    try:
        settings = get_settings()

        # Check LLM availability
        llm_client = get_llm_client()
        if not llm_client.is_available():
            raise Exception("LLM is not available")

        return HealthCheckResponse(
            status="ready",
            version=settings.APP_VERSION,
            environment=settings.ENVIRONMENT,
        )

    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"Service not ready: {str(e)}"
        )


@router.get(
    "/health/llm",
    response_model=dict,
    summary="LLM Health Check",
    description="Check if the LLM service is available"
)
async def llm_health_check() -> dict:
    """
    Check LLM service availability.

    Returns:
        dict: LLM status information

    Raises:
        HTTPException: If LLM is not available
    """
    try:
        llm_client = get_llm_client()

        is_available = llm_client.is_available()

        return {
            "status": "available" if is_available else "unavailable",
            "service": "Azure OpenAI",
            "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"LLM health check failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"LLM check failed: {str(e)}"
        )
