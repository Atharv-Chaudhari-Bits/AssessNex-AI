"""
LLM client module for AssessNex AI.

This module handles the initialization and interaction with multiple LLM providers:
- Azure OpenAI
- Google AI (Gemini)
- Grok LLM

Uses the LangChain library for unified interface across providers.
"""

import time
import random
from functools import wraps
from typing import Optional, List, Union
from langchain_core.messages import SystemMessage, HumanMessage
from backend.app.config import get_settings
from backend.app.utils.logger import get_logger


logger = get_logger(__name__)


def retry_with_backoff(max_retries: int = 5, min_wait: int = 60, max_wait: int = 300):
    """
    Decorator to retry a function with exponential backoff for rate limiting (429) and other transient errors.
    
    Args:
        max_retries: Maximum number of retry attempts (default: 5)
        min_wait: Minimum wait time in seconds (default: 60 = 1 minute)
        max_wait: Maximum wait time in seconds (default: 300 = 5 minutes)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    error_str = str(e)
                    last_exception = e
                    
                    # Check if it's a rate limiting error or transient error
                    is_rate_limit = "429" in error_str or "rate" in error_str.lower() or "tpm" in error_str.lower() or "rpm" in error_str.lower()
                    is_transient = any(code in error_str for code in ["500", "502", "503", "504"])
                    
                    if not (is_rate_limit or is_transient) or attempt == max_retries:
                        raise
                    
                    # Calculate backoff with exponential increase and jitter
                    base_wait = min(min_wait * (2 ** attempt), max_wait)
                    jitter = random.uniform(0, base_wait * 0.1)  # Add up to 10% jitter
                    wait_time = base_wait + jitter
                    
                    logger.warning(
                        f"Rate limit or transient error in {func.__name__} (attempt {attempt + 1}/{max_retries + 1}). "
                        f"Error: {error_str}. Retrying in {wait_time:.1f} seconds..."
                    )
                    
                    time.sleep(wait_time)
            
            raise last_exception
        return wrapper
    return decorator


class LLMClient:
    """
    Client for interacting with multiple LLM providers.

    This class encapsulates all LLM operations including initialization,
    message generation, and error handling for OpenAI, Google Gemini, and Grok.
    """

    _instance: Optional["LLMClient"] = None

    def __new__(cls):
        """
        Singleton pattern to ensure only one LLM client instance.

        Returns:
            LLMClient: Singleton instance
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the LLM client based on configured provider."""
        if self._initialized:
            return

        settings = get_settings()
        provider = settings.LLM_PROVIDER.lower()

        logger.info(f"Initializing LLM Client with provider: {provider}")

        try:
            if provider == "openai":
                self._init_openai(settings)
            elif provider == "google":
                self._init_google(settings)
            elif provider == "grok":
                self._init_grok(settings)
            elif provider == "groq":
                self._init_groq(settings)
            else:
                raise ValueError(f"Unsupported LLM provider: {provider}")

            self.settings = settings
            self.provider = provider
            self._initialized = True

            logger.info(f"{provider.upper()} LLM Client initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize LLM Client: {str(e)}")
            raise

    def _init_openai(self, settings):
        """Initialize Azure OpenAI client."""
        from langchain_openai import AzureChatOpenAI
        
        if not settings.AZURE_OPENAI_API_KEY or not settings.AZURE_OPENAI_ENDPOINT:
            raise ValueError("Azure OpenAI API key and endpoint are required")

        self.llm = AzureChatOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            azure_deployment=settings.AZURE_DEPLOYMENT,
            api_version=settings.AZURE_API_VERSION,
            max_retries=settings.LLM_MAX_RETRIES,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
        )

    def _init_google(self, settings):
        """Initialize Google Gemini client."""
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
        except ImportError:
            logger.error("langchain-google-genai is not installed")
            raise ImportError(
                "Please install langchain-google-genai: pip install langchain-google-genai"
            )
        
        if not settings.GOOGLE_API_KEY:
            raise ValueError("Google API key is required for Google Gemini")

        self.llm = ChatGoogleGenerativeAI(
            model=settings.GOOGLE_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
        )

    def _init_grok(self, settings):
        """Initialize Grok LLM client."""
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            logger.error("langchain-openai is not installed")
            raise ImportError(
                "Please install langchain-openai: pip install langchain-openai"
            )
        
        if not settings.GROK_API_KEY:
            raise ValueError("Grok API key is required")

        # Grok uses OpenAI-compatible API
        self.llm = ChatOpenAI(
            model=settings.GROK_MODEL,
            api_key=settings.GROK_API_KEY,
            base_url="https://api.x.ai/v1",  # Grok API endpoint
            max_retries=settings.LLM_MAX_RETRIES,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
        )

    def _init_groq(self, settings):
        """Initialize Groq LLM client."""
        try:
            from langchain_groq import ChatGroq
        except ImportError:
            logger.error("langchain-groq is not installed")
            raise ImportError(
                "Please install langchain-groq: pip install langchain-groq"
            )
        
        if not settings.GROQ_API_KEY:
            raise ValueError("Groq API key is required")

        self.llm = ChatGroq(
            model=settings.GROQ_MODEL,
            api_key=settings.GROQ_API_KEY,
            max_retries=settings.LLM_MAX_RETRIES,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
        )

    def generate_message(self, prompt: str, system_message: Optional[str] = None) -> str:
        """
        Generate a message from the LLM with automatic retry on rate limits.

        Args:
            prompt: Input prompt for the LLM
            system_message: Optional system message to set context/role for the LLM

        Returns:
            str: Generated message

        Raises:
            Exception: If generation fails after all retries
        """
        @retry_with_backoff(max_retries=5, min_wait=60, max_wait=300)
        def _generate():
            logger.debug(f"Generating message with prompt: {prompt[:100]}...")
            
            # Build messages list
            messages = []
            if system_message:
                messages.append(SystemMessage(content=system_message))
            messages.append(HumanMessage(content=prompt))
            
            # Use invoke with messages if system message is provided
            if system_message:
                response = self.llm.invoke(messages)
            else:
                response = self.llm.invoke(prompt)

            if hasattr(response, "content"):
                result = response.content
            else:
                result = str(response)

            logger.debug(f"LLM response generated successfully")
            return result
        
        try:
            return _generate()
        except Exception as e:
            logger.error(f"Error generating LLM message after retries: {str(e)}")
            raise

    def generate_json_message(self, prompt: str) -> str:
        """
        Generate a JSON-formatted message from the LLM with automatic retry on rate limits.

        Args:
            prompt: Input prompt for the LLM (should request JSON format)

        Returns:
            str: JSON formatted response

        Raises:
            Exception: If generation or parsing fails after all retries
        """
        @retry_with_backoff(max_retries=5, min_wait=60, max_wait=300)
        def _generate_json():
            logger.debug("Generating JSON message from LLM")
            response = self.generate_message(prompt)
            return response
        
        try:
            return _generate_json()
        except Exception as e:
            logger.error(f"Error generating JSON message after retries: {str(e)}")
            raise

    def stream_message(self, prompt: str):
        """
        Stream a message from the LLM with automatic retry on rate limits.

        Args:
            prompt: Input prompt for the LLM

        Yields:
            str: Chunks of the generated message

        Raises:
            Exception: If streaming fails after all retries
        """
        @retry_with_backoff(max_retries=5, min_wait=60, max_wait=300)
        def _stream():
            logger.debug("Starting message stream")
            chunks = []
            
            for chunk in self.llm.stream(prompt):
                if hasattr(chunk, "content"):
                    chunks.append(chunk.content)
                else:
                    chunks.append(str(chunk))
            
            return chunks
        
        try:
            for chunk in _stream():
                yield chunk
        except Exception as e:
            logger.error(f"Error streaming message after retries: {str(e)}")
            raise

    def is_available(self) -> bool:
        """
        Check if LLM is available and responsive with automatic retry on rate limits.

        Returns:
            bool: True if LLM is available, False otherwise
        """
        @retry_with_backoff(max_retries=3, min_wait=60, max_wait=300)
        def _check_availability():
            logger.debug("Checking LLM availability")
            self.generate_message("Say 'OK' in one word.")
            logger.info("LLM is available")
            return True
        
        try:
            return _check_availability()
        except Exception as e:
            logger.error(f"LLM availability check failed: {str(e)}")
            return False


def get_llm_client() -> LLMClient:
    """
    Get the singleton LLM client instance.

    Returns:
        LLMClient: LLM client instance

    Example:
        >>> from backend.app.llm_client import get_llm_client
        >>> client = get_llm_client()
        >>> response = client.generate_message("Hello")
    """
    return LLMClient()
