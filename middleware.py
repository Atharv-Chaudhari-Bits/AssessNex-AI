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

# """
# Request/Response logging middleware for FastAPI with prompt/agent response logging.
# """

# import time
# import logging
# import json
# from fastapi import Request
# from starlette.middleware.base import BaseHTTPMiddleware
# from starlette.responses import Response


# class LoggingMiddleware(BaseHTTPMiddleware):
#     """
#     Middleware to log all HTTP requests and responses with prompt/agent response tracking.
    
#     Logs request details (method, path, headers) and response details
#     (status code, response time) with special handling for AI prompts and agent responses.
#     """

#     def __init__(self, app, logger: logging.Logger = None):
#         """
#         Initialize logging middleware.

#         Args:
#             app: FastAPI application instance
#             logger: Python logger instance. If None, creates one.
#         """
#         super().__init__(app)
#         self.logger = logger or logging.getLogger("assessnex_ai")

#     async def dispatch(self, request: Request, call_next) -> Response:
#         """
#         Process request and log details with prompt/agent response tracking.

#         Args:
#             request: FastAPI request object
#             call_next: Callable to proceed to next middleware/handler

#         Returns:
#             Response: HTTP response from the application
#         """
#         # Extract request details
#         method = request.method
#         path = request.url.path
#         query_params = dict(request.query_params) if request.query_params else {}
        
#         # Store request body for later logging
#         request_body = None

#         # Log incoming request
#         self.logger.info(
#             f"→ INCOMING REQUEST: {method} {path}",
#             extra={"request_id": request.headers.get("x-request-id", "N/A")}
#         )
#         if query_params:
#             self.logger.debug(f"  Query params: {query_params}")

#         # Log body if it exists and is JSON
#         try:
#             if method in ["POST", "PUT", "PATCH"]:
#                 body = await request.body()
#                 if body:
#                     # Try to parse as JSON for better formatting
#                     try:
#                         request_body = json.loads(body)
                        
#                         # Check if this is a prompt-related endpoint
#                         is_prompt_request = any([
#                             "prompt" in path.lower(),
#                             "agent" in path.lower(),
#                             "chat" in path.lower(),
#                             "completion" in path.lower(),
#                             "generate" in path.lower()
#                         ])
                        
#                         # Log prompts specially
#                         if is_prompt_request:
#                             self.logger.info("📝 PROMPT RECEIVED:")
                            
#                             # Extract and log the actual prompt content
#                             if isinstance(request_body, dict):
#                                 # Common prompt field names in various APIs
#                                 prompt_fields = ['prompt', 'messages', 'content', 'text', 'input']
#                                 for field in prompt_fields:
#                                     if field in request_body:
#                                         prompt_content = request_body[field]
#                                         if isinstance(prompt_content, list):
#                                             # For chat messages format
#                                             for msg in prompt_content:
#                                                 if isinstance(msg, dict):
#                                                     role = msg.get('role', 'unknown')
#                                                     content = msg.get('content', '')
#                                                     self.logger.info(f"    [{role}]: {content[:500]}" + ("..." if len(content) > 500 else ""))
#                                         else:
#                                             # For simple prompt format
#                                             self.logger.info(f"    {prompt_content[:500]}" + ("..." if len(prompt_content) > 500 else ""))
#                                         break
                            
#                             self.logger.info(f"  Full request: {json.dumps(request_body, indent=2)[:1000]}")
#                         else:
#                             self.logger.debug(f"  Body size: {len(body)} bytes")
#                             self.logger.debug(f"  Body: {json.dumps(request_body, indent=2)[:500]}")
#                     except json.JSONDecodeError:
#                         self.logger.debug(f"  Body (raw): {body[:200]}...")
                    
#                     # Re-create body stream for the application
#                     async def receive():
#                         return {"type": "http.request", "body": body}
#                     request._receive = receive
#         except Exception as e:
#             self.logger.debug(f"  Could not log body: {str(e)}")

#         # Record start time
#         start_time = time.time()

#         # Process request
#         try:
#             response = await call_next(request)
            
#             # Try to capture and log response body for agent responses
#             response_body = b""
#             if hasattr(response, "body"):
#                 response_body = response.body
#             elif hasattr(response, "body_iterator"):
#                 # For streaming responses, we need to be careful
#                 # This is a simplified approach - you might need to handle streaming differently
#                 pass
                
#         except Exception as e:
#             # Log error and re-raise
#             elapsed_time = time.time() - start_time
#             self.logger.error(
#                 f"✗ REQUEST FAILED: {method} {path} - {type(e).__name__}: {str(e)} "
#                 f"({elapsed_time:.3f}s)"
#             )
#             raise

#         # Calculate elapsed time
#         elapsed_time = time.time() - start_time

#         # Log outgoing response with special handling for agent responses
#         status_code = response.status_code
#         status_emoji = "✓" if 200 <= status_code < 300 else "⚠" if 300 <= status_code < 400 else "✗"
        
#         # Check if this is an agent response
#         is_agent_response = any([
#             "agent" in path.lower(),
#             "chat" in path.lower(),
#             "completion" in path.lower(),
#             "generate" in path.lower()
#         ])
        
#         # Log agent responses specially
#         if is_agent_response and status_code < 400 and response_body:
#             try:
#                 response_data = json.loads(response_body)
#                 self.logger.info("🤖 AGENT RESPONSE:")
                
#                 # Extract and log the actual response content
#                 if isinstance(response_data, dict):
#                     # Common response field names
#                     response_fields = ['response', 'content', 'text', 'message', 'output', 'completion']
#                     for field in response_fields:
#                         if field in response_data:
#                             agent_response = response_data[field]
#                             if isinstance(agent_response, dict) and 'content' in agent_response:
#                                 # For OpenAI-style responses
#                                 self.logger.info(f"    {agent_response['content'][:500]}" + ("..." if len(agent_response['content']) > 500 else ""))
#                             elif isinstance(agent_response, str):
#                                 self.logger.info(f"    {agent_response[:500]}" + ("..." if len(agent_response) > 500 else ""))
#                             break
                    
#                     # Log choices array (common in OpenAI API)
#                     if 'choices' in response_data and response_data['choices']:
#                         for i, choice in enumerate(response_data['choices']):
#                             if 'message' in choice:
#                                 msg = choice['message']
#                                 role = msg.get('role', 'assistant')
#                                 content = msg.get('content', '')
#                                 self.logger.info(f"    [{role}]: {content[:500]}" + ("..." if len(content) > 500 else ""))
#                             elif 'text' in choice:
#                                 self.logger.info(f"    {choice['text'][:500]}" + ("..." if len(choice['text']) > 500 else ""))
                
#                 self.logger.info(f"  Full response: {json.dumps(response_data, indent=2)[:1000]}")
#             except (json.JSONDecodeError, Exception) as e:
#                 self.logger.debug(f"  Could not parse response body: {str(e)}")
#                 if response_body:
#                     self.logger.debug(f"  Raw response: {response_body[:500]}")

#         self.logger.info(
#             f"{status_emoji} RESPONSE: {method} {path} [{status_code}] ({elapsed_time:.3f}s)"
#         )

#         # Log warnings for error status codes
#         if status_code >= 400:
#             self.logger.warning(
#                 f"Response status {status_code} for {method} {path}"
#             )
#             if response_body and status_code >= 500:
#                 try:
#                     error_data = json.loads(response_body)
#                     self.logger.error(f"  Error details: {json.dumps(error_data, indent=2)}")
#                 except Exception:
#                     pass

#         return response