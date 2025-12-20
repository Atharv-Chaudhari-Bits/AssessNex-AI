"""
Configuration module for AssessNex AI Backend.

This module contains all configuration settings for the FastAPI application,
including Azure OpenAI credentials, logging setup, and application constants.

PEP 8 Compliant: Uses environment variables for sensitive data and follows
Python naming conventions.
"""

import os
import logging
from functools import lru_cache
from typing import Optional, Dict, List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings class using Pydantic for validation.

    This class loads configuration from environment variables and provides
    defaults for non-sensitive application settings.
    """

    # Application Settings
    APP_NAME: str = "AssessNex AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Azure OpenAI Configuration
    AZURE_OPENAI_API_KEY: str = os.getenv(
        "AZURE_OPENAI_API_KEY",
        ""
    )
    AZURE_OPENAI_ENDPOINT: str = os.getenv(
        "AZURE_OPENAI_ENDPOINT",
        ""
    )
    AZURE_DEPLOYMENT: str = os.getenv("AZURE_DEPLOYMENT", "gpt-4o")
    AZURE_API_VERSION: str = os.getenv("AZURE_API_VERSION", "2024-08-01-preview")

    # LLM Configuration
    LLM_MAX_RETRIES: int = 3
    LLM_TEMPERATURE: float = 0.5
    LLM_MAX_TOKENS: int = 8192  # Increased for generating multiple questions with detailed answers
    REQUEST_TIMEOUT: int = 120  # Increased timeout for larger responses

    # Question Generation Settings
    SUBJECTS: List[str] = [
        "Machine Learning",
        "Deep Learning",
        "Natural Language Processing",
        "Computer Vision",
        "Artificial Intelligence",
        "Reinforcement Learning",
        "Data Science",
        "Cryptography",
    ]

    QUESTION_TYPES: List[str] = [
        "Multiple Choice",
        "Short Answer",
        "Long Answer",
        "Code Implementation",
        "Essay",
        "True/False",
        "Fill in the Blank",
        "Scenario-Based",
        "Code Output Prediction",
        "Complexity Analysis",
        "Numerical Problem",
        "Diagram-Based",
        "Assignment",
        "Question Paper",
    ]
    
    # Extended features
    ENABLE_IMAGE_QUESTIONS: bool = True
    ENABLE_ASSIGNMENT_GENERATION: bool = True
    ENABLE_QUESTION_PAPER_GENERATION: bool = True
    ENABLE_PLAGIARISM_CHECK: bool = True
    
    # Paper generation defaults
    DEFAULT_PAPER_DIFFICULTY_DIST: Dict[str, int] = {
        "Easy": 30,
        "Medium": 50,
        "Hard": 20,
    }
    
    DEFAULT_PAPER_QUESTION_TYPE_DIST: Dict[str, int] = {
        "Multiple Choice": 30,
        "Short Answer": 40,
        "Coding": 20,
        "Essay": 10,
    }

    DIFFICULTY_LEVELS: List[str] = [
        "Easy",
        "Medium",
        "Hard",
    ]

    DEFAULT_QUESTIONS_COUNT: int = 5
    MAX_QUESTIONS_COUNT: int = 50

    # API Configuration
    API_V1_STR: str = "/api/v1"
    CORS_ORIGINS: List[str] = [
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8501",
    ]

    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "assessnex_ai.log"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Server Configuration
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000
    RELOAD: bool = False

    class Config:
        """Pydantic configuration for environment variable loading."""
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    This function uses LRU cache to ensure only one Settings instance
    is created during the application lifetime.

    Returns:
        Settings: Cached Settings instance
    """
    return Settings()


def setup_logging() -> logging.Logger:
    """
    Configure application logging with console and file output.

    Sets up logging with both file and console handlers. Console output
    is set to DEBUG level to show all processing steps during development.
    File output uses the configured LOG_LEVEL from settings.

    Returns:
        logging.Logger: Configured logger instance
    """
    settings = get_settings()

    logger = logging.getLogger("assessnex_ai")
    logger.setLevel(logging.DEBUG)  # Set to DEBUG to capture all messages

    # Create formatters with more detail
    detailed_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    simple_formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S"
    )

    # File Handler - uses configured log level
    file_handler = logging.FileHandler(settings.LOG_FILE)
    file_handler.setLevel(getattr(logging, settings.LOG_LEVEL))
    file_handler.setFormatter(detailed_formatter)

    # Console Handler - always DEBUG for development visibility
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(simple_formatter)

    # Add handlers to logger (prevent duplicate logs)
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger


# Initialize logger
logger = setup_logging()

# Create settings instance for import
settings = Settings()
