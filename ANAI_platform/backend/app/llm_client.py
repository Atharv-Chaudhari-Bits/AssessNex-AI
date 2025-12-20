"""
LLM client module for AssessNex AI.

This module handles the initialization and interaction with Azure OpenAI
for question generation using the LangChain library.
"""

from typing import Optional, List
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from backend.app.config import get_settings
from backend.app.utils.logger import get_logger


logger = get_logger(__name__)


class LLMClient:
    """
    Client for interacting with Azure OpenAI LLM.

    This class encapsulates all LLM operations including initialization,
    message generation, and error handling.
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
        """Initialize the LLM client with Azure OpenAI configuration."""
        if self._initialized:
            return

        settings = get_settings()

        logger.info("Initializing Azure OpenAI LLM Client")

        try:
            self.llm = AzureChatOpenAI(
                api_key=settings.AZURE_OPENAI_API_KEY,
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                azure_deployment=settings.AZURE_DEPLOYMENT,
                api_version=settings.AZURE_API_VERSION,
                max_retries=settings.LLM_MAX_RETRIES,
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS,  # Ensure enough tokens for multiple questions
            )

            self.settings = settings
            self._initialized = True

            logger.info("Azure OpenAI LLM Client initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize LLM Client: {str(e)}")
            raise

    def generate_message(self, prompt: str, system_message: Optional[str] = None) -> str:
        """
        Generate a message from the LLM.

        Args:
            prompt: Input prompt for the LLM
            system_message: Optional system message to set context/role for the LLM

        Returns:
            str: Generated message

        Raises:
            Exception: If generation fails
        """
        logger.debug(f"Generating message with prompt: {prompt[:100]}...")

        try:
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

        except Exception as e:
            logger.error(f"Error generating LLM message: {str(e)}")
            raise

    def generate_json_message(self, prompt: str) -> str:
        """
        Generate a JSON-formatted message from the LLM.

        Args:
            prompt: Input prompt for the LLM (should request JSON format)

        Returns:
            str: JSON formatted response

        Raises:
            Exception: If generation or parsing fails
        """
        logger.debug("Generating JSON message from LLM")

        try:
            response = self.generate_message(prompt)
            return response

        except Exception as e:
            logger.error(f"Error generating JSON message: {str(e)}")
            raise

    def stream_message(self, prompt: str):
        """
        Stream a message from the LLM.

        Args:
            prompt: Input prompt for the LLM

        Yields:
            str: Chunks of the generated message

        Raises:
            Exception: If streaming fails
        """
        logger.debug("Starting message stream")

        try:
            for chunk in self.llm.stream(prompt):
                if hasattr(chunk, "content"):
                    yield chunk.content
                else:
                    yield str(chunk)

        except Exception as e:
            logger.error(f"Error streaming message: {str(e)}")
            raise

    def is_available(self) -> bool:
        """
        Check if LLM is available and responsive.

        Returns:
            bool: True if LLM is available, False otherwise
        """
        try:
            logger.debug("Checking LLM availability")
            self.generate_message("Say 'OK' in one word.")
            logger.info("LLM is available")
            return True

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
