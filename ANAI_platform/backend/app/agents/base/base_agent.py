"""
Base Formatting Agent - Abstract base class for all formatting agents.

This module provides the foundation for all specialized formatting agents,
ensuring consistent interface, error handling, and validation capabilities.
"""

import re
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple, Union
from enum import Enum

from backend.app.llm_client import get_llm_client
from backend.app.utils import get_logger

logger = get_logger(__name__)


class ContentType(Enum):
    """Enumeration of content types that agents can process."""
    CODE = "code"
    LATEX = "latex"
    MERMAID = "mermaid"
    ASCII = "ascii"
    MARKDOWN = "markdown"
    TABLE = "table"
    TEXT = "text"
    DIAGRAM = "diagram"
    IMAGE_DESCRIPTION = "image_description"


class ValidationLevel(Enum):
    """Validation strictness levels."""
    NONE = "none"
    BASIC = "basic"
    STRICT = "strict"
    COMPREHENSIVE = "comprehensive"


@dataclass
class AgentConfig:
    """Configuration for an agent."""
    name: str
    content_type: ContentType
    max_retries: int = 3
    validation_level: ValidationLevel = ValidationLevel.BASIC
    timeout_seconds: int = 30
    enable_llm_fallback: bool = True
    enable_caching: bool = False
    custom_settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResult:
    """Result from an agent operation."""
    success: bool
    content: str
    original_content: str
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    retries_used: int = 0
    agent_name: str = ""
    validation_passed: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "success": self.success,
            "content": self.content,
            "original_content": self.original_content,
            "errors": self.errors,
            "warnings": self.warnings,
            "metadata": self.metadata,
            "retries_used": self.retries_used,
            "agent_name": self.agent_name,
            "validation_passed": self.validation_passed,
        }


class BaseFormattingAgent(ABC):
    """
    Abstract base class for all formatting agents.
    
    Provides:
    - Common interface for all agents
    - LLM client integration
    - Error handling and retry logic
    - Validation framework
    - Logging and metrics
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """
        Initialize the base agent.
        
        Args:
            config: Agent configuration. If None, uses default config.
        """
        self.config = config or self._get_default_config()
        self.llm_client = get_llm_client()
        self._cache: Dict[str, AgentResult] = {}
        logger.info(f"{self.config.name} initialized")
    
    @abstractmethod
    def _get_default_config(self) -> AgentConfig:
        """Return default configuration for this agent."""
        pass
    
    @abstractmethod
    def _get_system_prompt(self) -> str:
        """Return the system prompt for LLM interactions."""
        pass
    
    @abstractmethod
    def _get_format_prompt(self, content: str, **kwargs) -> str:
        """Return the formatting prompt for the content."""
        pass
    
    @abstractmethod
    def _validate_output(self, content: str) -> Tuple[bool, List[str]]:
        """
        Validate the formatted output.
        
        Args:
            content: The formatted content to validate
            
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        pass
    
    def format(self, content: str, **kwargs) -> AgentResult:
        """
        Format the content using this agent.
        
        Args:
            content: The content to format
            **kwargs: Additional arguments for formatting
            
        Returns:
            AgentResult with formatted content
        """
        # Check cache first
        cache_key = self._get_cache_key(content, kwargs)
        if self.config.enable_caching and cache_key in self._cache:
            logger.debug(f"Cache hit for {self.config.name}")
            return self._cache[cache_key]
        
        result = AgentResult(
            success=False,
            content=content,
            original_content=content,
            agent_name=self.config.name,
        )
        
        # Pre-validation - check if content needs formatting
        if self._is_already_formatted(content):
            result.success = True
            result.metadata["skipped"] = True
            result.metadata["reason"] = "Already properly formatted"
            logger.debug(f"{self.config.name}: Content already formatted, skipping")
            return result
        
        # Try formatting with retries
        for attempt in range(self.config.max_retries):
            try:
                formatted_content = self._format_content(content, **kwargs)
                
                # Validate the output
                is_valid, errors = self._validate_output(formatted_content)
                
                if is_valid:
                    result.success = True
                    result.content = formatted_content
                    result.validation_passed = True
                    result.retries_used = attempt
                    logger.info(f"{self.config.name}: Successfully formatted on attempt {attempt + 1}")
                    break
                else:
                    result.warnings.extend(errors)
                    logger.warning(f"{self.config.name}: Validation failed on attempt {attempt + 1}: {errors}")
                    
                    # If LLM fallback is enabled, try to fix the content
                    if self.config.enable_llm_fallback and attempt < self.config.max_retries - 1:
                        content = self._fix_with_llm(formatted_content, errors)
                    
            except Exception as e:
                error_msg = f"Error on attempt {attempt + 1}: {str(e)}"
                result.errors.append(error_msg)
                logger.error(f"{self.config.name}: {error_msg}")
        
        # Final fallback - return best effort or original
        if not result.success:
            result.content = self._get_best_effort(content, **kwargs)
            result.metadata["fallback_used"] = True
        
        # Cache the result
        if self.config.enable_caching:
            self._cache[cache_key] = result
        
        return result
    
    def _format_content(self, content: str, **kwargs) -> str:
        """
        Internal method to format content using LLM.
        
        Args:
            content: Content to format
            **kwargs: Additional arguments
            
        Returns:
            Formatted content string
        """
        prompt = self._get_format_prompt(content, **kwargs)
        system_prompt = self._get_system_prompt()
        
        response = self.llm_client.generate_json_message(
            prompt,
            system_message=system_prompt
        )
        
        # Parse response
        if isinstance(response, str):
            try:
                response = json.loads(response)
            except json.JSONDecodeError:
                # If not JSON, return as-is
                return response
        
        if isinstance(response, dict):
            return response.get("formatted_content", response.get("content", content))
        
        return str(response)
    
    def _fix_with_llm(self, content: str, errors: List[str]) -> str:
        """
        Use LLM to fix validation errors.
        
        Args:
            content: Content with errors
            errors: List of error messages
            
        Returns:
            Fixed content
        """
        fix_prompt = f"""The following content has formatting errors that need to be fixed:

Content:
{content}

Errors:
{chr(10).join(f'- {e}' for e in errors)}

Please fix these errors and return the corrected content.
Return a JSON object with:
{{
    "formatted_content": "the corrected content"
}}"""
        
        try:
            response = self.llm_client.generate_json_message(
                fix_prompt,
                system_message=self._get_system_prompt()
            )
            
            if isinstance(response, str):
                response = json.loads(response)
            
            return response.get("formatted_content", content)
            
        except Exception as e:
            logger.error(f"Error fixing content with LLM: {e}")
            return content
    
    def _is_already_formatted(self, content: str) -> bool:
        """
        Check if content is already properly formatted.
        Override in subclasses for specific checks.
        """
        return False
    
    def _get_best_effort(self, content: str, **kwargs) -> str:
        """
        Return best-effort formatting without LLM.
        Override in subclasses for specific transformations.
        """
        return content
    
    def _get_cache_key(self, content: str, kwargs: Dict[str, Any]) -> str:
        """Generate a cache key for the content and options."""
        import hashlib
        key_string = f"{content}:{json.dumps(kwargs, sort_keys=True)}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def validate(self, content: str) -> Tuple[bool, List[str]]:
        """
        Public method to validate content without formatting.
        
        Args:
            content: Content to validate
            
        Returns:
            Tuple of (is_valid, list of errors)
        """
        return self._validate_output(content)
    
    def get_info(self) -> Dict[str, Any]:
        """Get agent information and capabilities."""
        return {
            "name": self.config.name,
            "content_type": self.config.content_type.value,
            "validation_level": self.config.validation_level.value,
            "max_retries": self.config.max_retries,
            "enable_llm_fallback": self.config.enable_llm_fallback,
        }
