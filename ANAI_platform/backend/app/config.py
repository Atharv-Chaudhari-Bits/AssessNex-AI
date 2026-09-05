"""Application configuration for AssessNex AI.

Gemini is the active LLM provider. Legacy providers are intentionally kept
behind feature flags so they can be re-enabled later without contaminating the
active runtime path.
"""

import logging
from functools import lru_cache
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parents[1] / ".env"
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)


class Settings(BaseSettings):
    """Validated application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "AssessNex AI"
    APP_VERSION: str = "2.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    # LLM: Gemini is the only active provider by default.
    LLM_PROVIDER: str = "google"
    ENABLE_PROVIDER_GEMINI: bool = True
    ENABLE_PROVIDER_OPENAI: bool = False
    ENABLE_PROVIDER_GROK: bool = False
    ENABLE_PROVIDER_GROQ: bool = False

    GOOGLE_API_KEY: str = ""
    GOOGLE_MODEL: str = "gemini-2.5-flash"

    # Legacy provider configuration is retained for controlled migration only.
    AZURE_OPENAI_API_KEY: str = ""
    AZURE_OPENAI_ENDPOINT: str = ""
    AZURE_DEPLOYMENT: str = "gpt-4o"
    AZURE_API_VERSION: str = "2024-08-01-preview"
    GROK_API_KEY: str = ""
    GROK_MODEL: str = "grok-2-vision-1212"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "mixtral-8x7b-32768"

    LLM_MAX_RETRIES: int = 3
    LLM_RETRY_MIN_SECONDS: float = 2.0
    LLM_RETRY_MAX_SECONDS: float = 30.0
    LLM_TEMPERATURE: float = 0.5
    LLM_MAX_TOKENS: int = 8192
    REQUEST_TIMEOUT: int = 120

    # Feature flags
    ENABLE_DOCUMENT_RAG: bool = False
    ENABLE_IMAGE_QUESTIONS: bool = False
    ENABLE_ASSIGNMENT_GENERATION: bool = True
    ENABLE_QUESTION_PAPER_GENERATION: bool = True
    ENABLE_PLAGIARISM_CHECK: bool = False
    ENABLE_LEGACY_STREAMLIT_FRONTEND: bool = False

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
    DIFFICULTY_LEVELS: List[str] = ["Easy", "Medium", "Hard"]
    DEFAULT_QUESTIONS_COUNT: int = 5
    MAX_QUESTIONS_COUNT: int = 50

    # API/server
    API_V1_STR: str = "/api/v1"
    CORS_ORIGINS: List[str] = [
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
    ]
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000
    RELOAD: bool = False

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "assessnex_ai.log"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def setup_logging() -> logging.Logger:
    """Configure the application logger once."""
    settings = get_settings()
    logger = logging.getLogger("assessnex_ai")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

    if logger.handlers:
        return logger

    formatter = logging.Formatter(settings.LOG_FORMAT)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    try:
        file_handler = logging.FileHandler(settings.LOG_FILE)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except OSError:
        logger.warning("Could not create log file %s", settings.LOG_FILE)

    return logger


logger = setup_logging()
settings = get_settings()
