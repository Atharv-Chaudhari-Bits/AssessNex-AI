"""
Routers package initialization.

Exports all API router instances.
"""

from backend.app.routers import health, questions, plagiarism, papers

__all__ = ["health", "questions", "plagiarism", "papers"]
