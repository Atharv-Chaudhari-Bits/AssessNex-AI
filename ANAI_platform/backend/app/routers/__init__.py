"""
Routers package initialization.

Exports all API router instances.
"""

from backend.app.routers import health, questions, plagiarism, papers_enhanced, documents

__all__ = ["health", "questions", "plagiarism", "papers_enhanced", "documents"]
