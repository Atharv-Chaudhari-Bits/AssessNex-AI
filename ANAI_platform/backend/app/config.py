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
from pathlib import Path
from typing import Optional, Dict, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Load .env file from backend directory
ENV_FILE = Path(__file__).parent.parent / ".env"
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)
else:
    print(f"Warning: .env file not found at {ENV_FILE}")


class Settings(BaseSettings):
    """
    Application settings class using Pydantic for validation.

    This class loads configuration from environment variables and provides
    defaults for non-sensitive application settings.
    """
    
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding='utf-8',
        case_sensitive=True,
        extra='ignore'
    )

    # Application Settings
    APP_NAME: str = "AssessNex AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # LLM Provider Selection
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai")  # Options: "openai", "google", "grok", "groq"
    
    # Azure OpenAI Configuration
    AZURE_OPENAI_API_KEY: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    AZURE_DEPLOYMENT: str = os.getenv("AZURE_DEPLOYMENT", "gpt-4o")
    AZURE_API_VERSION: str = os.getenv("AZURE_API_VERSION", "2024-08-01-preview")
    
    # Google AI (Gemini) Configuration
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    GOOGLE_MODEL: str = os.getenv("GOOGLE_MODEL", "gemini-2.0-flash")
    
    # Grok LLM Configuration
    GROK_API_KEY: str = os.getenv("GROK_API_KEY", "")
    GROK_MODEL: str = os.getenv("GROK_MODEL", "grok-2-vision-1212")

    # Groq Configuration
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "mixtral-8x7b-32768")

    # LLM Configuration
    LLM_MAX_RETRIES: int = int(os.getenv("LLM_MAX_RETRIES", "3"))
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.5"))
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "8192"))
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "120"))

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
    SERVER_HOST: str = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", "8000"))
    RELOAD: bool = os.getenv("RELOAD", "False").lower() in ("true", "1", "yes")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")


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
