"""
Request/Response logging middleware for FastAPI.

Logs all incoming requests and outgoing responses with timing information.
"""

import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all HTTP requests and responses.
    
    Logs request details (method, path, headers) and response details
    (status code, response time) for monitoring and debugging.
    """

    def __init__(self, app, logger: logging.Logger = None):
        """
        Initialize logging middleware.

        Args:
            app: FastAPI application instance
            logger: Python logger instance. If None, creates one.
        """
        super().__init__(app)
        self.logger = logger or logging.getLogger("assessnex_ai")

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request and log details.

        Args:
            request: FastAPI request object
            call_next: Callable to proceed to next middleware/handler

        Returns:
            Response: HTTP response from the application
        """
        # Extract request details
        method = request.method
        path = request.url.path
        query_params = dict(request.query_params) if request.query_params else {}

        # Log incoming request
        self.logger.debug(
            f"→ INCOMING REQUEST: {method} {path}",
            extra={"request_id": request.headers.get("x-request-id", "N/A")}
        )
        if query_params:
            self.logger.debug(f"  Query params: {query_params}")

        # Log body if it exists and is JSON
        try:
            if method in ["POST", "PUT", "PATCH"]:
                body = await request.body()
                if body:
                    # Re-create body stream for the application
                    async def receive():
                        return {"type": "http.request", "body": body}
                    request._receive = receive
                    self.logger.debug(f"  Body size: {len(body)} bytes")
        except Exception as e:
            self.logger.debug(f"  Could not log body: {str(e)}")

        # Record start time
        start_time = time.time()

        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            # Log error and re-raise
            elapsed_time = time.time() - start_time
            self.logger.error(
                f"✗ REQUEST FAILED: {method} {path} - {type(e).__name__}: {str(e)} "
                f"({elapsed_time:.3f}s)"
            )
            raise

        # Calculate elapsed time
        elapsed_time = time.time() - start_time

        # Log outgoing response
        status_code = response.status_code
        status_emoji = "✓" if 200 <= status_code < 300 else "⚠" if 300 <= status_code < 400 else "✗"
        
        self.logger.debug(
            f"{status_emoji} RESPONSE: {method} {path} [{status_code}] ({elapsed_time:.3f}s)"
        )

        # Log response headers if verbose
        if status_code >= 400:
            self.logger.warning(
                f"Response status {status_code} for {method} {path}"
            )

        return response
