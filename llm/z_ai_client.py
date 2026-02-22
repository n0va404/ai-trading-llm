"""
Z.AI API Client - Phase 7

OpenAI SDK-based client for Z.AI API with timeout and error handling.
LLM is READ-ONLY and ADVISORY ONLY - failures MUST NOT block trading.

Architecture:
- Uses OpenAI SDK for cleaner API interaction
- Fixed JSON output schema
- 10s timeout (never block trading)
- No retries (LLM is non-critical)
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ZAiConfig:
    """Z.AI client configuration."""
    api_key: str
    base_url: str = "https://api.z.ai/api/paas/v4/"  # Z.AI API endpoint
    model: str = "glm-4.7"  # GLM-4.7 model
    timeout: int = 10  # seconds
    max_tokens: int = 1000
    temperature: float = 0.3  # Low temperature for consistent analysis


class ZAiClientError(Exception):
    """Base exception for Z.AI client errors."""
    pass


class ZAiConnectionError(ZAiClientError):
    """Connection or network error."""
    pass


class ZAiResponseError(ZAiClientError):
    """API response error (4xx, 5xx)."""
    pass


class ZAiValidationError(ZAiClientError):
    """Response validation error."""
    pass


class ZAiClient:
    """
    OpenAI SDK-based client for Z.AI API.

    **CRITICAL:** This client is for ADVISORY LLM calls only.
    - Failures MUST NOT block trading
    - No retries (trading continues without LLM insights)
    - Fixed timeout (10s max)

    Usage:
        client = ZAiClient(api_key="your_api_key")

        response = client.get_completion(
            prompt="Analyze this trading decision...",
            response_schema={
                "type": "object",
                "properties": {...}
            }
        )
    """

    def __init__(self, config: Optional[ZAiConfig] = None):
        """
        Initialize Z.AI client using OpenAI SDK.

        Args:
            config: Client configuration (optional, loads from env if not provided)
        """
        if config is None:
            api_key = os.getenv("ZAI_API_KEY")
            if not api_key:
                raise ZAiClientError(
                    "ZAI_API_KEY not set. LLM features disabled."
                )
            config = ZAiConfig(api_key=api_key)

        self.config = config

        # Initialize OpenAI client with Z.AI configuration
        try:
            from openai import OpenAI
            self._client = OpenAI(
                api_key=config.api_key,
                base_url=config.base_url,
                timeout=config.timeout
            )
            logger.info("[LLM] OpenAI SDK client initialized")
        except ImportError:
            raise ZAiClientError(
                "OpenAI SDK not installed. Run: pip install openai"
            )

    def get_completion(
        self,
        prompt: str,
        response_schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get LLM completion with JSON output using OpenAI SDK.

        Args:
            prompt: Input prompt for LLM
            response_schema: Optional JSON schema for response validation

        Returns:
            Dict with LLM response (parsed JSON)

        Raises:
            ZAiConnectionError: Network/connection error
            ZAiResponseError: API returned error
            ZAiValidationError: Response validation failed
        """
        # Build messages
        messages = [{"role": "user", "content": prompt}]

        # Build completion parameters
        completion_params = {
            "model": self.config.model,
            "messages": messages,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature
        }

        # Add JSON schema constraint if provided
        if response_schema:
            completion_params["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "trading_analysis",
                    "strict": True,
                    "schema": response_schema
                }
            }

        # Make API call using OpenAI SDK
        try:
            logger.debug(f"[LLM] Sending request to {self.config.model}")
            completion = self._client.chat.completions.create(**completion_params)

            # Extract content
            content = completion.choices[0].message.content

            # Parse JSON content
            parsed = json.loads(content)

            logger.info("[LLM] Got valid response from OpenAI SDK")
            return parsed

        except json.JSONDecodeError as e:
            logger.error(f"[LLM] Response JSON parse error: {e}")
            raise ZAiValidationError(f"Failed to parse response JSON: {e}")
        except Exception as e:
            # Handle various OpenAI SDK errors
            error_type = type(e).__name__

            if "timeout" in error_type.lower() or "connection" in error_type.lower():
                logger.warning(f"[LLM] Connection error: {e}")
                raise ZAiConnectionError(f"Connection error: {e}")
            elif "authentication" in error_type.lower() or "permission" in error_type.lower():
                logger.error(f"[LLM] Authentication error: {e}")
                raise ZAiResponseError(f"Authentication failed: {e}")
            elif "rate" in error_type.lower():
                logger.warning(f"[LLM] Rate limit error: {e}")
                raise ZAiResponseError(f"Rate limit exceeded: {e}")
            else:
                logger.error(f"[LLM] API error: {e}")
                raise ZAiResponseError(f"API error: {e}")

    def health_check(self) -> bool:
        """
        Check if Z.AI API is accessible using OpenAI SDK.

        Returns:
            True if API is reachable, False otherwise
        """
        try:
            # Try to list models (lightweight health check)
            self._client.models.list()
            logger.info("[LLM] Health check passed")
            return True
        except Exception as e:
            logger.warning(f"[LLM] Health check failed: {e}")
            return False


def get_llm_client() -> Optional[ZAiClient]:
    """
    Factory function to get configured LLM client.

    Returns:
        Configured ZAiClient instance, or None if ZAI_API_KEY not set

    **CRITICAL:** Returns None if API key not set - LLM is OPTIONAL.
    """
    api_key = os.getenv("ZAI_API_KEY")
    if not api_key:
        logger.warning("[LLM] ZAI_API_KEY not set - LLM features disabled")
        return None

    try:
        return ZAiClient()
    except Exception as e:
        logger.error(f"[LLM] Failed to initialize client: {e}")
        return None
