"""
Candle Data Loader - Phase 8 Implementation

Responsibilities:
- Load historical OHLC data from file
- Yield candles one-by-one in chronological order
- No caching
- No aggregation
- No random access

This module provides sequential access to historical market data.

PHASE 8 CONSTRAINTS:
- NO MT5 calls
- NO random access
- NO skipping ahead
- NO caching of historical data
- Pure sequential iteration only
"""

import json
import logging
from typing import Iterator, Dict, Any, Optional
from pathlib import Path


logger = logging.getLogger(__name__)


class InvalidCandleError(Exception):
    """Raised when candle data is invalid."""
    pass


class CandleDataLoader:
    """
    Sequential loader for historical OHLC candle data.

    Provides one-way iteration through historical data.
    No random access, no skipping, no caching.

    Usage:
        loader = CandleDataLoader(file_path)
        for candle in loader.candles():
            # Process candle
            pass
    """

    REQUIRED_FIELDS = ["timestamp", "open", "high", "low", "close", "volume"]

    def __init__(self, file_path: Path):
        """
        Initialize candle data loader.

        Args:
            file_path: Path to historical data file (JSON or JSONL)

        Raises:
            FileNotFoundError: If file doesn't exist
            InvalidCandleError: If data format is invalid

        Note:
            No data loading on init.
            Candles loaded on-demand during iteration.
        """
        self.file_path = Path(file_path)

        if not self.file_path.exists():
            raise FileNotFoundError(f"Historical data file not found: {file_path}")

        self._line_number = 0

    def candles(self) -> Iterator[Dict[str, Any]]:
        """
        Yield candles one-by-one in chronological order.

        Yields:
            Candle dict with structure:
            {
                "timestamp": "2026-02-21T10:00:00",
                "open": 2934.50,
                "high": 2940.20,
                "low": 2930.10,
                "close": 2936.12,
                "volume": 150
            }

        Raises:
            InvalidCandleError: If candle data is invalid

        Note:
            Sequential access only.
            No caching, no random access.
        """
        self._line_number = 0

        # Detect file format
        if self.file_path.suffix == ".jsonl":
            yield from self._load_jsonl()
        elif self.file_path.suffix == ".json":
            yield from self._load_json_array()
        else:
            # Try JSONL first, fallback to JSON array
            try:
                yield from self._load_jsonl()
            except Exception:
                yield from self._load_json_array()

    def _load_jsonl(self) -> Iterator[Dict[str, Any]]:
        """
        Load candles from JSONL file (one JSON per line).

        Yields:
            Validated candle dicts

        Raises:
            InvalidCandleError: If candle is invalid
        """
        with open(self.file_path, 'r') as f:
            for line in f:
                self._line_number += 1

                if not line.strip():
                    continue  # Skip empty lines

                try:
                    candle = json.loads(line.strip())
                    self._validate_candle(candle)
                    yield candle

                except json.JSONDecodeError as e:
                    raise InvalidCandleError(
                        f"Invalid JSON at line {self._line_number}: {e}"
                    )
                except InvalidCandleError as e:
                    raise InvalidCandleError(
                        f"Invalid candle at line {self._line_number}: {e}"
                    )

    def _load_json_array(self) -> Iterator[Dict[str, Any]]:
        """
        Load candles from JSON array file.

        Yields:
            Validated candle dicts

        Raises:
            InvalidCandleError: If candle is invalid
        """
        with open(self.file_path, 'r') as f:
            try:
                data = json.load(f)

                if not isinstance(data, list):
                    raise InvalidCandleError(
                        f"Root element must be array, got {type(data).__name__}"
                    )

                for idx, candle in enumerate(data, 1):
                    self._line_number = idx
                    self._validate_candle(candle)
                    yield candle

            except json.JSONDecodeError as e:
                raise InvalidCandleError(f"Invalid JSON file: {e}")

    def _validate_candle(self, candle: Dict[str, Any]):
        """
        Validate candle structure and values.

        Args:
            candle: Candle dict to validate

        Raises:
            InvalidCandleError: If candle is invalid

        Note:
            Strict validation - all fields must be present and valid.
        """
        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if field not in candle:
                raise InvalidCandleError(
                    f"Missing required field: {field}"
                )

        # Validate timestamp
        if not isinstance(candle["timestamp"], str):
            raise InvalidCandleError(
                f"timestamp must be string, got {type(candle['timestamp']).__name__}"
            )

        # Validate OHLCV are numeric
        for field in ["open", "high", "low", "close", "volume"]:
            value = candle[field]
            if not isinstance(value, (int, float)):
                raise InvalidCandleError(
                    f"{field} must be numeric, got {type(value).__name__}"
                )

        # Validate OHLC relationships
        o, h, l, c = candle["open"], candle["high"], candle["low"], candle["close"]

        if h < max(o, c):
            raise InvalidCandleError(
                f"high ({h}) must be >= max(open, close) ({max(o, c)})"
            )

        if l > min(o, c):
            raise InvalidCandleError(
                f"low ({l}) must be <= min(open, close) ({min(o, c)})"
            )

        if h < l:
            raise InvalidCandleError(
                f"high ({h}) must be >= low ({l})"
            )

        # Validate volume non-negative
        if candle["volume"] < 0:
            raise InvalidCandleError(
                f"volume must be >= 0, got {candle['volume']}"
            )

    def count(self) -> int:
        """
        Count total candles in file.

        Returns:
            Number of candles

        Note:
            This requires reading the entire file.
            Use sparingly - it's O(n).
        """
        count = 0
        for _ in self.candles():
            count += 1
        return count

    def get_pair(self) -> Optional[str]:
        """
        Extract pair symbol from file path.

        Returns:
            Pair symbol if in path, None otherwise

        Example:
            "data/XAUUSDm_h1.json" → "XAUUSDm"
        """
        # Try to extract from filename
        stem = self.file_path.stem  # filename without extension
        # Common patterns: SYMBOL_tf, SYMBOL_h1, etc.
        parts = stem.split('_')
        if len(parts) > 0:
            return parts[0]
        return None
