"""
Logging utility module for AssessNex AI.

This module provides a centralized logging configuration that can be used
throughout the application for consistent logging behavior.
"""

import logging
import sys
from typing import Optional
from backend.app.config import get_settings


class LoggerSetup:
    """
    Centralized logging setup class.

    Provides methods to configure and retrieve logger instances with
    consistent formatting and handlers.
    """

    _loggers: dict = {}

    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """
        Get or create a logger instance.

        Args:
            name: Name of the logger (typically __name__)

        Returns:
            logging.Logger: Configured logger instance
        """
        if name in LoggerSetup._loggers:
            return LoggerSetup._loggers[name]

        settings = get_settings()
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, settings.LOG_LEVEL))

        # Only add handlers if they don't exist
        if not logger.handlers:
            formatter = logging.Formatter(
                fmt=settings.LOG_FORMAT,
                datefmt="%Y-%m-%d %H:%M:%S"
            )

            # Console Handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

        LoggerSetup._loggers[name] = logger
        return logger


def get_logger(name: str) -> logging.Logger:
    """
    Convenience function to get a logger instance.

    Args:
        name: Logger name

    Returns:
        logging.Logger: Configured logger instance

    Example:
        >>> from backend.app.utils.logger import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Application started")
    """
    return LoggerSetup.get_logger(name)
