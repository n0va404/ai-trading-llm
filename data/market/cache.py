"""
Market Data Cache - Phase 3 Implementation

Responsibilities:
- Store market data in memory with TTL
- Track timestamp per entry
- Determine cache validity via TTL
- Thread-safe read/write operations

This is an in-memory cache only - no persistence.
Cache is explicit (no magic) with O(1) lookup and write.

PHASE 3 CONSTRAINTS:
- No disk persistence
- No background cleanup threads
- TTL value passed from caller
- Cache lookup MUST be O(1)
- Cache write MUST be O(1)
"""

import time
import threading
from typing import Dict, Any, Optional, Tuple


class MarketCache:
    """
    TTL-based thread-safe in-memory cache for market data.

    Cache keys are tuples: (symbol, data_type, ...)
    Cache values include data + timestamp for TTL validation.

    Supported cache keys:
    - (symbol, "tick") - Single tick data
    - (symbol, "ticks", count) - Multiple ticks
    - (symbol, "ohlc", timeframe, bars) - OHLC bars
    """

    def __init__(self):
        """
        Initialize the market cache.

        Creates empty thread-safe cache storage.
        No auto-cleanup threads (caller manages stale data).
        """
        self._cache: Dict[Tuple, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def get(
        self,
        key: Tuple,
        ttl: Optional[float] = None,
        current_time: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached data if valid (exists and not expired).

        Args:
            key: Cache key tuple (e.g., ("XAUUSDm", "tick"))
            ttl: Time-to-live in seconds (None = no expiry check)
            current_time: Optional Unix timestamp (uses time.time() if None)

        Returns:
            Cached data dict if valid, None if expired/missing

        TTL Logic:
        - If ttl is None: Return data if exists (no expiry check)
        - If ttl is provided: Return data only if (now - timestamp) < ttl

        Note:
            This is O(1) lookup.
        """
        now = current_time if current_time is not None else time.time()

        with self._lock:
            if key not in self._cache:
                return None

            entry = self._cache[key]

            # Check TTL if provided
            if ttl is not None:
                timestamp = entry.get("timestamp", 0)
                age = now - timestamp
                if age >= ttl:
                    # Expired
                    return None

            # Return cached data
            return entry.get("data")

    def set(
        self,
        key: Tuple,
        data: Dict[str, Any],
        current_time: Optional[float] = None
    ):
        """
        Store data in cache with current timestamp.

        Args:
            key: Cache key tuple
            data: Data to cache
            current_time: Optional Unix timestamp (uses time.time() if None)

        Note:
            This is O(1) write.
            Overwrites existing entry if key exists.
        """
        now = current_time if current_time is not None else time.time()

        with self._lock:
            self._cache[key] = {
                "data": data,
                "timestamp": now
            }

    def invalidate(self, key: Tuple):
        """
        Remove specific entry from cache.

        Args:
            key: Cache key tuple to invalidate

        Useful for:
        - Manual cache invalidation
        - Forced refresh scenarios
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]

    def clear(self):
        """
        Clear all cached data.

        Useful for:
        - Testing
        - Cache reset scenarios
        """
        with self._lock:
            self._cache.clear()

    def get_age(self, key: Tuple, current_time: Optional[float] = None) -> Optional[float]:
        """
        Get age of cached entry in seconds.

        Args:
            key: Cache key tuple
            current_time: Optional Unix timestamp

        Returns:
            Age in seconds, or None if key not found

        Useful for:
        - Monitoring cache freshness
        - Debugging cache behavior
        """
        now = current_time if current_time is not None else time.time()

        with self._lock:
            if key not in self._cache:
                return None

            entry = self._cache[key]
            timestamp = entry.get("timestamp", 0)
            return now - timestamp

    def is_valid(self, key: Tuple, ttl: float, current_time: Optional[float] = None) -> bool:
        """
        Check if cached entry is valid (exists and not expired).

        Args:
            key: Cache key tuple
            ttl: Time-to-live in seconds
            current_time: Optional Unix timestamp

        Returns:
            True if cache exists and is within TTL

        Note:
            Does NOT return the data, only validity check.
        """
        return self.get(key, ttl=ttl, current_time=current_time) is not None

    def size(self) -> int:
        """
        Get number of cached entries.

        Returns:
            Number of entries in cache

        Note:
            For monitoring/debugging purposes.
        """
        with self._lock:
            return len(self._cache)

    # ========================================================================
    # CONVENIENCE METHODS FOR SPECIFIC DATA TYPES
    # These provide cleaner API for common use cases
    # ========================================================================

    def get_tick(
        self,
        symbol: str,
        ttl: Optional[float] = None,
        current_time: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached tick data for symbol.

        Args:
            symbol: Trading pair symbol
            ttl: Optional TTL in seconds
            current_time: Optional Unix timestamp

        Returns:
            Tick data dict or None if not cached/expired

        Cache key: (symbol, "tick")
        """
        key = (symbol, "tick")
        return self.get(key, ttl=ttl, current_time=current_time)

    def set_tick(self, symbol: str, tick_data: Dict[str, Any], current_time: Optional[float] = None):
        """
        Cache tick data for symbol.

        Args:
            symbol: Trading pair symbol
            tick_data: Tick data dict from MT5 Bridge
            current_time: Optional Unix timestamp
        """
        key = (symbol, "tick")
        self.set(key, tick_data, current_time=current_time)

    def get_ticks(
        self,
        symbol: str,
        count: int,
        ttl: Optional[float] = None,
        current_time: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached multiple ticks for symbol.

        Args:
            symbol: Trading pair symbol
            count: Number of ticks (part of cache key)
            ttl: Optional TTL in seconds
            current_time: Optional Unix timestamp

        Returns:
            Ticks data dict or None if not cached/expired

        Cache key: (symbol, "ticks", count)
        """
        key = (symbol, "ticks", count)
        return self.get(key, ttl=ttl, current_time=current_time)

    def set_ticks(
        self,
        symbol: str,
        count: int,
        ticks_data: Dict[str, Any],
        current_time: Optional[float] = None
    ):
        """
        Cache multiple ticks for symbol.

        Args:
            symbol: Trading pair symbol
            count: Number of ticks (part of cache key)
            ticks_data: Ticks data dict from MT5 Bridge
            current_time: Optional Unix timestamp
        """
        key = (symbol, "ticks", count)
        self.set(key, ticks_data, current_time=current_time)

    def get_ohlc(
        self,
        symbol: str,
        timeframe: int,
        bars: int,
        ttl: Optional[float] = None,
        current_time: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached OHLC bars for symbol.

        Args:
            symbol: Trading pair symbol
            timeframe: Timeframe in minutes (part of cache key)
            bars: Number of bars (part of cache key)
            ttl: Optional TTL in seconds
            current_time: Optional Unix timestamp

        Returns:
            OHLC data dict or None if not cached/expired

        Cache key: (symbol, "ohlc", timeframe, bars)
        """
        key = (symbol, "ohlc", timeframe, bars)
        return self.get(key, ttl=ttl, current_time=current_time)

    def set_ohlc(
        self,
        symbol: str,
        timeframe: int,
        bars: int,
        ohlc_data: Dict[str, Any],
        current_time: Optional[float] = None
    ):
        """
        Cache OHLC bars for symbol.

        Args:
            symbol: Trading pair symbol
            timeframe: Timeframe in minutes
            bars: Number of bars
            ohlc_data: OHLC data dict from MT5 Bridge
            current_time: Optional Unix timestamp
        """
        key = (symbol, "ohlc", timeframe, bars)
        self.set(key, ohlc_data, current_time=current_time)

    # ========================================================================
    # LEGACY METHODS (Phase 0 Compatibility)
    # These maintain backward compatibility with Phase 0 interface
    # ========================================================================

    def update(self, pair: str, data: Dict[str, Any]):
        """
        Update cache with new market data (legacy method).

        Args:
            pair: Trading pair symbol
            data: Market data dictionary

        Note:
            This is a legacy method from Phase 0.
            It stores data under ("pair", "tick") key.
        """
        self.set_tick(pair, data)

    def get_bid(self, pair: str, ttl: Optional[float] = None) -> Optional[float]:
        """
        Get current bid price for pair (legacy method).

        Args:
            pair: Trading pair symbol
            ttl: Optional TTL in seconds

        Returns:
            Bid price or None if not available/expired
        """
        tick_data = self.get_tick(pair, ttl=ttl)
        if tick_data is None:
            return None
        return tick_data.get("bid")

    def get_ask(self, pair: str, ttl: Optional[float] = None) -> Optional[float]:
        """
        Get current ask price for pair (legacy method).

        Args:
            pair: Trading pair symbol
            ttl: Optional TTL in seconds

        Returns:
            Ask price or None if not available/expired
        """
        tick_data = self.get_tick(pair, ttl=ttl)
        if tick_data is None:
            return None
        return tick_data.get("ask")

    def get_spread(self, pair: str, ttl: Optional[float] = None) -> Optional[float]:
        """
        Get current spread for pair (legacy method).

        Args:
            pair: Trading pair symbol
            ttl: Optional TTL in seconds

        Returns:
            Spread in points or None if not available/expired
        """
        tick_data = self.get_tick(pair, ttl=ttl)
        if tick_data is None:
            return None
        return tick_data.get("spread")
