"""Active FastAPI routers."""

from backend.app.routers import documents, health, papers_enhanced, plagiarism, questions

__all__ = ["health", "questions", "plagiarism", "papers_enhanced", "documents"]
