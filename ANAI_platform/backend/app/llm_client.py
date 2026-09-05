"""Single LLM gateway for AssessNex AI.

Gemini is the active provider. Legacy providers are deliberately disabled by
configuration flags and are not imported unless explicitly enabled.
"""

import json
import random
import time
from functools import wraps
from typing import Any, Dict, Iterator, List, Optional

from langchain_core.messages import HumanMessage, SystemMessage

from backend.app.config import get_settings
from backend.app.utils.logger import get_logger

logger = get_logger(__name__)


def retry_with_backoff(max_retries: int, min_wait: float, max_wait: float):
    """Retry only transient/rate-limit failures with bounded exponential backoff."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    last_exception = exc
                    text = str(exc).lower()
                    transient = any(code in text for code in ("429", "500", "502", "503", "504"))
                    transient = transient or any(term in text for term in ("rate limit", "temporarily", "timeout"))
                    if not transient or attempt >= max_retries:
                        raise

                    wait = min(max_wait, min_wait * (2**attempt))
                    wait += random.uniform(0, wait * 0.1)
                    logger.warning(
                        "%s failed (attempt %s/%s); retrying in %.1fs: %s",
                        func.__name__, attempt + 1, max_retries + 1, wait, exc,
                    )
                    time.sleep(wait)
            raise last_exception  # pragma: no cover

        return wrapper

    return decorator


class LLMClient:
    """Thread-safe-enough process singleton around the configured LangChain model."""

    _instance: Optional["LLMClient"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        settings = get_settings()
        provider = settings.LLM_PROVIDER.strip().lower()
        if provider != "google":
            raise RuntimeError(
                f"Unsupported active LLM provider '{provider}'. "
                "AssessNex AI is currently configured for Gemini only."
            )
        if not settings.ENABLE_PROVIDER_GEMINI:
            raise RuntimeError("Gemini provider is disabled (ENABLE_PROVIDER_GEMINI=false).")
        if not settings.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY is required when Gemini is enabled.")

        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
        except ImportError as exc:
            raise ImportError(
                "Gemini support requires langchain-google-genai."
            ) from exc

        self.llm = ChatGoogleGenerativeAI(
            model=settings.GOOGLE_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
            timeout=settings.REQUEST_TIMEOUT,
            max_retries=0,
        )
        self.settings = settings
        self.provider = "google"
        self.model = settings.GOOGLE_MODEL
        self.fallback_model = settings.GOOGLE_FALLBACK_MODEL.strip()
        self._fallback_llm = None
        self._initialized = True
        logger.info("Initialized Gemini provider: %s", self.model)

    @staticmethod
    def _content(response: Any) -> str:
        content = getattr(response, "content", response)
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict) and "text" in item:
                    parts.append(str(item["text"]))
                else:
                    parts.append(str(item))
            return "".join(parts)
        return str(content)

    @staticmethod
    def _strip_json_fence(content: str) -> str:
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1] if "\n" in content else content[3:]
            if content.rstrip().endswith("```"):
                content = content.rstrip()[:-3]
        return content.strip()

    @retry_with_backoff(3, 2.0, 30.0)
    def _invoke(self, messages: List[Any]) -> str:
        try:
            response = self.llm.invoke(messages)
            return self._content(response).strip()
        except Exception as exc:
            # Optional production fallback, controlled entirely by an env variable.
            # It is only used after the primary model fails; normal traffic stays on GOOGLE_MODEL.
            if not self.fallback_model or self.fallback_model == self.model:
                raise
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                if self._fallback_llm is None:
                    self._fallback_llm = ChatGoogleGenerativeAI(
                        model=self.fallback_model, google_api_key=self.settings.GOOGLE_API_KEY,
                        temperature=self.settings.LLM_TEMPERATURE, max_tokens=self.settings.LLM_MAX_TOKENS,
                        timeout=self.settings.REQUEST_TIMEOUT, max_retries=0,
                    )
                logger.warning("Primary Gemini model %s failed; using fallback model %s: %s", self.model, self.fallback_model, exc)
                response = self._fallback_llm.invoke(messages)
                return self._content(response).strip()
            except Exception:
                raise exc

    def generate_message(self, prompt: str, system_message: Optional[str] = None) -> str:
        """Generate plain text from Gemini."""
        if not prompt or not prompt.strip():
            raise ValueError("prompt must not be empty")

        messages: List[Any] = []
        if system_message:
            messages.append(SystemMessage(content=system_message))
        messages.append(HumanMessage(content=prompt))
        return self._invoke(messages)

    def create_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Compatibility method used by existing agents."""
        if not messages:
            raise ValueError("messages must not be empty")

        system_parts = [m["content"] for m in messages if m.get("role") == "system"]
        user_parts = [m["content"] for m in messages if m.get("role") in {"user", "human"}]
        system_message = "\n\n".join(system_parts) or None
        prompt = "\n\n".join(user_parts)

        if response_format and response_format.get("type") == "json_object":
            instruction = "Return ONLY valid JSON. Do not use Markdown fences or commentary."
            system_message = f"{system_message}\n\n{instruction}" if system_message else instruction

        # Per-call generation settings are intentionally not mutated on the shared model.
        del temperature, max_tokens
        content = self.generate_message(prompt, system_message)
        if response_format and response_format.get("type") == "json_object":
            content = self._strip_json_fence(content)
            json.loads(content)  # Fail fast rather than pretending a string is valid JSON.

        return {
            "content": content,
            "model": self.model,
            "usage": {},
            "finish_reason": "stop",
        }

    def generate_json_message(self, prompt: str, system_message: Optional[str] = None) -> str:
        """Generate and validate a JSON object/array response."""
        system = system_message or ""
        system = f"{system}\n\nReturn ONLY valid JSON. No Markdown fences or commentary."
        content = self.generate_message(prompt, system)
        content = self._strip_json_fence(content)
        json.loads(content)
        return content

    def stream_message(self, prompt: str) -> Iterator[str]:
        """Stream Gemini output without wrapping the stream in a long blocking retry."""
        if not prompt or not prompt.strip():
            raise ValueError("prompt must not be empty")
        for chunk in self.llm.stream(prompt):
            text = self._content(chunk)
            if text:
                yield text

    def is_available(self) -> bool:
        """Return configuration availability without making a billable model call."""
        try:
            return bool(
                self.provider == "google"
                and self.settings.ENABLE_PROVIDER_GEMINI
                and self.settings.GOOGLE_API_KEY
            )
        except Exception:
            return False


def get_llm_client() -> LLMClient:
    """Return the process-wide LLM client."""
    return LLMClient()
