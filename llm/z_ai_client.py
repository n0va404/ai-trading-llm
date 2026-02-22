"""
Z.AI API Client - Phase 7

Minimal HTTP client for Z.AI API with timeout and error handling.
LLM is READ-ONLY and ADVISORY ONLY - failures MUST NOT block trading.

Architecture:
- Stateless HTTP client (no session management)
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
    base_url: str = "https://api.z.ai/api/coding/paas/v4"  # Z.AI API endpoint
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
    Minimal HTTP client for Z.AI API.

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
        Initialize Z.AI client.

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
        self._headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def get_completion(
        self,
        prompt: str,
        response_schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get LLM completion with JSON output.

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
        import requests

        # Build request payload
        payload = {
            "model": self.config.model,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }

        # Add JSON schema constraint if provided
        if response_schema:
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "trading_analysis",
                    "strict": True,
                    "schema": response_schema
                }
            }

        # Make API call
        try:
            response = requests.post(
                f"{self.config.base_url}/chat/completions",
                headers=self._headers,
                json=payload,
                timeout=self.config.timeout
            )
        except requests.exceptions.Timeout:
            logger.warning("[LLM] Request timeout (>10s)")
            raise ZAiConnectionError("Request timeout")
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"[LLM] Connection error: {e}")
            raise ZAiConnectionError(f"Connection error: {e}")
        except requests.exceptions.RequestException as e:
            logger.warning(f"[LLM] Request error: {e}")
            raise ZAiConnectionError(f"Request error: {e}")

        # Check HTTP status
        if response.status_code >= 400:
            logger.warning(f"[LLM] API error: {response.status_code}")
            raise ZAiResponseError(
                f"API returned {response.status_code}: {response.text}"
            )

        # Parse response
        try:
            data = response.json()
            content = data["choices"][0]["message"]["content"]

            # Parse JSON content
            parsed = json.loads(content)

            logger.info("[LLM] Got valid response")
            return parsed

        except (KeyError, IndexError, json.JSONDecodeError) as e:
            logger.error(f"[LLM] Response parse error: {e}")
            raise ZAiValidationError(f"Failed to parse response: {e}")

    def health_check(self) -> bool:
        """
        Check if Z.AI API is accessible.

        Returns:
            True if API is reachable, False otherwise
        """
        import requests

        try:
            response = requests.get(
                f"{self.config.base_url}/models",
                headers=self._headers,
                timeout=5
            )
            return response.status_code == 200
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
