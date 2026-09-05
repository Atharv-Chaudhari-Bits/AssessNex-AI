"""
Frontend configuration for AssessNex AI Streamlit application.

This module contains configuration constants for the Streamlit frontend
application and helper functions for UI setup.
"""

import os
from typing import Dict, List


class StreamlitConfig:
    """Configuration for Streamlit application."""

    # API Configuration
    API_BASE_URL: str = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
    API_V1_PREFIX: str = "/api/v1"
    TIMEOUT: int = 60

    # UI Configuration
    APP_TITLE: str = "AssessNex AI"
    APP_ICON: str = "🤖"
    PAGE_CONFIG_LAYOUT: str = "wide"
    THEME: str = "light"

    # Colors
    PRIMARY_COLOR: str = "#2E86AB"
    SECONDARY_COLOR: str = "#A23B72"
    SUCCESS_COLOR: str = "#06A77D"
    WARNING_COLOR: str = "#F18F01"
    ERROR_COLOR: str = "#C1121F"

    # Display Settings
    QUESTIONS_PER_PAGE: int = 5
    MAX_QUESTIONS: int = 50
    DEFAULT_QUESTIONS: int = 5

    # Cache Settings
    CACHE_TTL: int = 3600  # 1 hour


def get_api_endpoints() -> Dict[str, str]:
    """
    Get API endpoints dictionary.

    Returns:
        Dict[str, str]: API endpoints
    """
    config = StreamlitConfig()

    return {
        "health": f"{config.API_BASE_URL}/health",
        "subjects": f"{config.API_BASE_URL}{config.API_V1_PREFIX}/questions/subjects",
        "generate": f"{config.API_BASE_URL}{config.API_V1_PREFIX}/questions/generate",
        "info": f"{config.API_BASE_URL}{config.API_V1_PREFIX}/questions/info",
    }


def get_question_types() -> List[str]:
    """
    Get list of question types for question generation.
    
    Note: "Assignment" and "Question Paper" are NOT included here as they are
    not question types - they have dedicated tabs for generation.

    Returns:
        List[str]: Available question types
    """
    return [
        "Multiple Choice",
        "Short Answer",
        "Long Answer",
        "Essay",
        "Code Implementation",
        "True/False",
        "Fill in the Blank",
        "Scenario-Based",
        "Code Output Prediction",
        "Complexity Analysis",
        "Numerical Problem",
        "Diagram-Based",
    ]


def get_difficulty_levels() -> List[str]:
    """
    Get list of difficulty levels.

    Returns:
        List[str]: Available difficulty levels
    """
    return ["Easy", "Medium", "Hard"]


def get_diagram_formats() -> List[str]:
    """
    Get list of diagram format options for Diagram-Based questions.

    Returns:
        List[str]: Available diagram formats
    """
    return [
        "Mermaid.js (Interactive Flowcharts)",
        "ASCII Art (Text-based Diagrams)",
    ]
