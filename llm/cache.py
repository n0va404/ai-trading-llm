"""
LLM Response Cache - Phase 7

TTL-based cache for LLM responses.
Reduces duplicate API calls for similar prompts.

Architecture:
- In-memory cache (dict-based)
- TTL expiration (default: 5 minutes)
- Thread-safe operations
- LRU eviction when full
"""

import hashlib
import json
import time
import threading
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class LLMCache:
    """
    Thread-safe TTL-based cache for LLM responses.

    **CRITICAL:** This is OPTIONAL caching only.
    - Cache miss = normal behavior
    - LLM failure NOT caused by cache
    """

    def __init__(self, max_size: int = 1000, ttl: int = 300):
        """
        Initialize LLM cache.

        Args:
            max_size: Maximum number of cached responses
            ttl: Time-to-live in seconds (default: 5 minutes)
        """
        self.max_size = max_size
        self.ttl = ttl
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._access_time: Dict[str, float] = {}
        self._lock = threading.Lock()

    def get(self, prompt: str) -> Optional[Dict[str, Any]]:
        """
        Get cached response for a prompt.

        Args:
            prompt: Prompt string

        Returns:
            Cached response or None if not found/expired
        """
        key = self._hash_prompt(prompt)

        with self._lock:
            if key not in self._cache:
                return None

            entry = self._cache[key]

            # Check TTL
            if time.time() - entry["timestamp"] > self.ttl:
                # Expired
                del self._cache[key]
                del self._access_time[key]
                return None

            # Update access time (LRU)
            self._access_time[key] = time.time()

            logger.debug(f"[LLM Cache] Hit for prompt hash: {key[:8]}...")
            return entry["response"]

    def set(self, prompt: str, response: Dict[str, Any]):
        """
        Cache a response for a prompt.

        Args:
            prompt: Prompt string
            response: Response to cache
        """
        key = self._hash_prompt(prompt)

        with self._lock:
            # Evict oldest if full
            if len(self._cache) >= self.max_size and key not in self._cache:
                self._evict_oldest()

            # Store entry
            self._cache[key] = {
                "response": response,
                "timestamp": time.time()
            }
            self._access_time[key] = time.time()

            logger.debug(f"[LLM Cache] Cached prompt hash: {key[:8]}...")

    def clear(self):
        """Clear all cached responses."""
        with self._lock:
            self._cache.clear()
            self._access_time.clear()
            logger.info("[LLM Cache] Cleared all entries")

    def _evict_oldest(self):
        """Evict the least recently used entry."""
        if not self._access_time:
            return

        # Find oldest entry
        oldest_key = min(self._access_time, key=self._access_time.get)

        # Remove it
        del self._cache[oldest_key]
        del self._access_time[oldest_key]

        logger.debug(f"[LLM Cache] Evicted LRU entry: {oldest_key[:8]}...")

    def _hash_prompt(self, prompt: str) -> str:
        """
        Generate stable hash for prompt.

        Args:
            prompt: Prompt string

        Returns:
            SHA256 hash string
        """
        # Normalize prompt (whitespace, case for JSON keys)
        normalized = json.dumps(prompt, sort_keys=True)
        return hashlib.sha256(normalized.encode()).hexdigest()
