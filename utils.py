"""
Utility functions for AssessNex AI frontend.

This module provides helper functions for logging, formatting, and
UI-related operations.
"""

import logging
import streamlit as st
from typing import Dict, Any, List


def setup_logging(name: str) -> logging.Logger:
    """
    Setup logging for the frontend.

    Args:
        name: Logger name (typically __name__)

    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Console handler
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)

        logger.addHandler(handler)

    return logger


def format_question_display(question: Dict[str, Any]) -> str:
    """
    Format a question for display.

    Args:
        question: Question dictionary

    Returns:
        str: Formatted question string
    """
    formatted = f"**Q:** {question.get('question_text', 'N/A')}\n\n"

    if question.get("options"):
        formatted += "**Options:**\n"
        for i, option in enumerate(question.get("options", []), 1):
            formatted += f"  {chr(64+i)}. {option}\n"
        formatted += "\n"

    return formatted


def display_success_message(message: str):
    """
    Display a success message.

    Args:
        message: Success message
    """
    st.markdown(
        f"<div class='success-box'>{message}</div>",
        unsafe_allow_html=True,
    )


def display_error_message(message: str):
    """
    Display an error message.

    Args:
        message: Error message
    """
    st.markdown(
        f"<div class='error-box'>{message}</div>",
        unsafe_allow_html=True,
    )


def paginate_questions(
    questions: List[Dict[str, Any]],
    page_size: int = 5,
) -> List[List[Dict[str, Any]]]:
    """
    Paginate questions into chunks.

    Args:
        questions: List of questions
        page_size: Number of questions per page

    Returns:
        List[List[Dict[str, Any]]]: Paginated questions
    """
    return [
        questions[i : i + page_size]
        for i in range(0, len(questions), page_size)
    ]
