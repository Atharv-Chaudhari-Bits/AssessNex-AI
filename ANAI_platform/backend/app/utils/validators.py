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

# Constants for validation (in case settings aren't loaded)
DEFAULT_BLOOM_LEVELS = ["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"]


def validate_subject(subject: str) -> bool:
    """
    Validate if the given subject is available.

    Args:
        subject: Subject to validate

    Returns:
        bool: True if subject is valid, False otherwise
    """
    try:
        settings = get_settings()
        valid_subjects = settings.SUBJECTS
    except Exception:
        # Fallback to a reasonable default if settings not available
        valid_subjects = ["Machine Learning", "Deep Learning", "Natural Language Processing", 
                          "Computer Vision", "Artificial Intelligence", "Reinforcement Learning",
                          "Data Science", "Cryptography", "Algorithms", "Data Structures"]
    
    # Check exact match
    if subject in valid_subjects:
        return True
    
    # Check case-insensitive match
    subject_lower = subject.lower()
    for valid in valid_subjects:
        if valid.lower() == subject_lower:
            return True
    
    # Allow custom subjects (non-empty string)
    if subject and isinstance(subject, str) and len(subject.strip()) > 0:
        logger.info(f"Custom subject accepted: {subject}")
        return True
    
    logger.warning(f"Subject validation failed: {subject}")
    return False


# At the top of validators.py, update the VALID_QUESTION_TYPES list:

VALID_QUESTION_TYPES = [
    "Multiple Choice", "Long Answer", "Short Answer", "Diagram-Based",
    "Code-Based", "Code Implementation", "Code Output Prediction",
    "Coding Problem", "Numerical Problem", "True/False", "Essay",
    "Scenario-Based", "Fill in the Blank", "Matching", "Complexity Analysis"
]

# Then update the validate_question_type function:

def validate_question_type(question_type: str) -> bool:
    """
    Validate if the given question type is valid.

    Args:
        question_type: Question type to validate

    Returns:
        bool: True if question type is valid, False otherwise
    """
    try:
        settings = get_settings()
        valid_types = settings.QUESTION_TYPES
    except Exception:
        valid_types = VALID_QUESTION_TYPES  # Use the updated list
    
    # Check exact match
    if question_type in valid_types:
        return True
    
    # Check case-insensitive match
    type_lower = question_type.lower()
    for valid in valid_types:
        if valid.lower() == type_lower:
            return True
    
    # Also check if it's in our expanded list
    if question_type in VALID_QUESTION_TYPES:
        return True
    
    logger.warning(f"Question type validation failed: {question_type}")
    return False


def validate_difficulty_level(difficulty: str) -> bool:
    """
    Validate if the given difficulty level is valid.

    Args:
        difficulty: Difficulty level to validate

    Returns:
        bool: True if difficulty level is valid, False otherwise
    """
    try:
        settings = get_settings()
        valid_levels = settings.DIFFICULTY_LEVELS
    except Exception:
        valid_levels = ["Easy", "Medium", "Hard", "Very Hard", "Expert"]
    
    # Check exact match
    if difficulty in valid_levels:
        return True
    
    # Check case-insensitive match
    diff_lower = difficulty.lower()
    for valid in valid_levels:
        if valid.lower() == diff_lower:
            return True
    
    logger.warning(f"Difficulty level validation failed: {difficulty}")
    return False


def validate_bloom_level(bloom_level: str) -> bool:
    """
    Validate if the given Bloom's taxonomy level is valid.

    Args:
        bloom_level: Bloom's taxonomy level to validate

    Returns:
        bool: True if Bloom's level is valid, False otherwise
    """
    valid_levels = DEFAULT_BLOOM_LEVELS
    
    # Check exact match
    if bloom_level in valid_levels:
        return True
    
    # Check case-insensitive match
    level_lower = bloom_level.lower()
    for valid in valid_levels:
        if valid.lower() == level_lower:
            return True
    
    logger.warning(f"Bloom's level validation failed: {bloom_level}")
    return False


def validate_num_questions(num_questions: int, min_val: int = 1, max_val: int = 50) -> bool:
    """
    Validate the number of questions requested.

    Args:
        num_questions: Number of questions
        min_val: Minimum allowed value
        max_val: Maximum allowed value

    Returns:
        bool: True if number is within valid range, False otherwise
    """
    try:
        settings = get_settings()
        max_allowed = settings.MAX_QUESTIONS_COUNT
    except Exception:
        max_allowed = max_val
    
    if not isinstance(num_questions, int):
        logger.warning(f"num_questions is not an integer: {type(num_questions)}")
        return False
    
    return min_val <= num_questions <= max_allowed


def validate_topic_focus(topic_focus: Optional[List[str]]) -> bool:
    """
    Validate topic focus list.

    Args:
        topic_focus: List of topics to focus on

    Returns:
        bool: True if valid, False otherwise
    """
    if topic_focus is None:
        return True
    
    if not isinstance(topic_focus, list):
        logger.warning(f"topic_focus is not a list: {type(topic_focus)}")
        return False
    
    return all(isinstance(t, str) and len(t.strip()) > 0 for t in topic_focus)


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

    if not isinstance(text, str):
        try:
            text = str(text)
        except Exception:
            logger.warning(f"Could not convert input to string: {type(text)}")
            return None

    text = text.strip()

    if len(text) > max_length:
        raise ValueError(f"Input exceeds maximum length of {max_length}")

    # Remove any potentially harmful characters (basic sanitization)
    # This is a simple example - adjust based on your needs
    text = text.replace('<', '&lt;').replace('>', '&gt;')
    
    return text


def sanitize_document_text(text: str, max_length: int = 10000) -> Optional[str]:
    """
    Sanitize document text with higher length limit.

    Args:
        text: Document text to sanitize
        max_length: Maximum allowed length (higher for documents)

    Returns:
        str: Sanitized text or None if invalid
    """
    return sanitize_input(text, max_length)


def validate_all(
    subject: str,
    question_type: str,
    difficulty: str,
    num_questions: int,
    bloom_level: Optional[str] = None
) -> tuple[bool, str]:
    """
    Validate all common parameters at once.

    Args:
        subject: Subject to validate
        question_type: Question type to validate
        difficulty: Difficulty level to validate
        num_questions: Number of questions to validate
        bloom_level: Optional Bloom's level to validate

    Returns:
        tuple[bool, str]: (is_valid, error_message)
    """
    if not validate_subject(subject):
        return False, f"Invalid subject: {subject}"
    
    if not validate_question_type(question_type):
        return False, f"Invalid question type: {question_type}"
    
    if not validate_difficulty_level(difficulty):
        return False, f"Invalid difficulty level: {difficulty}"
    
    if not validate_num_questions(num_questions):
        return False, f"Invalid number of questions: {num_questions}"
    
    if bloom_level is not None and not validate_bloom_level(bloom_level):
        return False, f"Invalid Bloom's level: {bloom_level}"
    
    return True, "Validation successful"