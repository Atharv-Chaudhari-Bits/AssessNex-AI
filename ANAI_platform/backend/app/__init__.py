from backend.app.fix_imports import fix_langgraph
fix_langgraph()

"""
Backend package initialization.

Exports main FastAPI application.
"""

from backend.app.main import app

__all__ = ["app"]
