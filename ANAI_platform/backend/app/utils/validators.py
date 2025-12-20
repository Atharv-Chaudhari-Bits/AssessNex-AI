"""
Validators module for AssessNex AI.

This module contains validation functions and utilities for request
validation and data sanitization.
"""

from typing import List, Optional
from pydantic import ValidationError
from backend.app.utils.logger import get_logger
from backend.app.config import get_settings


logger = get_logger(__name__)


def validate_subject(subject: str) -> bool:
    """
    Validate if the given subject is available.

    Args:
        subject: Subject to validate

    Returns:
        bool: True if subject is valid, False otherwise
    """
    settings = get_settings()
    return subject in settings.SUBJECTS


def validate_question_type(question_type: str) -> bool:
    """
    Validate if the given question type is valid.

    Args:
        question_type: Question type to validate

    Returns:
        bool: True if question type is valid, False otherwise
    """
    settings = get_settings()
    return question_type in settings.QUESTION_TYPES


def validate_difficulty_level(difficulty: str) -> bool:
    """
    Validate if the given difficulty level is valid.

    Args:
        difficulty: Difficulty level to validate

    Returns:
        bool: True if difficulty level is valid, False otherwise
    """
    settings = get_settings()
    return difficulty in settings.DIFFICULTY_LEVELS


def validate_num_questions(num_questions: int) -> bool:
    """
    Validate the number of questions requested.

    Args:
        num_questions: Number of questions

    Returns:
        bool: True if number is within valid range, False otherwise
    """
    settings = get_settings()
    return 1 <= num_questions <= settings.MAX_QUESTIONS_COUNT


def sanitize_input(text: str, max_length: int = 5000) -> Optional[str]:
    """
    Sanitize and validate user input.

    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length

    Returns:
        str: Sanitized text or None if invalid

    Raises:
        ValueError: If text exceeds maximum length
    """
    if not text:
        return None

    text = text.strip()

    if len(text) > max_length:
        raise ValueError(f"Input exceeds maximum length of {max_length}")

    return text
