"""
Market Data Puller - Phase 3 Implementation

Responsibilities:
- Fetch market data via MT5BridgeClient
- Enforce cache-first logic
- Minimize GET requests to MT5 Bridge
- Provide explicit methods for different data types

This module is driven by scheduler jobs (Phase 2).
It does NOT make trading decisions - only data collection.

PHASE 3 CONSTRAINTS:
- No auto-refresh
- No polling
- Caller decides WHEN to call
- Caller decides TTL
- No trading logic
- No strategy logic
"""

import time
import logging
from typing import Dict, Any, Optional, List


# Configure logging
logger = logging.getLogger(__name__)


class MarketPuller:
    """
    Market data puller with cache-first design.

    Fetches data from MT5 Bridge only if cache is expired or missing.
    Each puller instance is specific to a trading pair (pair isolation).
    """

    def __init__(
        self,
        pair: str,
        mt5_bridge,
        cache,
        default_ttl: float = 1.0
    ):
        """
        Initialize market puller for a specific pair.

        Args:
            pair: Trading pair symbol (e.g., "XAUUSDm")
            mt5_bridge: MT5BridgeClient instance (Phase 1)
            cache: MarketCache instance (Phase 3)
            default_ttl: Default TTL for cached data in seconds

        Note:
            MT5BridgeClient is injected (dependency injection).
            Cache is injected (dependency injection).
            No network calls on init.
        """
        self.pair = pair
        self.mt5_bridge = mt5_bridge
        self.cache = cache
        self.default_ttl = default_ttl

    # ========================================================================
    # TICK DATA METHODS
    # ========================================================================

    def get_tick(self, ttl: Optional[float] = None) -> Dict[str, Any]:
        """
        Get current tick data (cache-first).

        Args:
            ttl: Cache TTL in seconds (uses default_ttl if None)

        Returns:
            Tick data dict containing:
            - symbol: Trading pair symbol
            - bid: Current bid price
            - ask: Current ask price
            - spread: Spread in points
            - timestamp: Unix timestamp from MT5

        Cache-First Logic:
        1. Check cache for valid entry
        2. If valid → return cached
        3. If expired/missing → fetch from MT5
        4. Update cache
        5. Return fresh data

        Raises:
            MT5BridgeConnectionError: MT5 Bridge connection fails
            MT5BridgeResponseError: MT5 Bridge returns error

        Note:
            This is the primary method for current price data.
        """
        cache_ttl = ttl if ttl is not None else self.default_ttl

        # Check cache first
        cached = self.cache.get_tick(self.pair, ttl=cache_ttl)
        if cached is not None:
            logger.debug(f"Cache hit for {self.pair} tick")
            return cached

        # Cache miss/expired - fetch from MT5
        logger.debug(f"Cache miss for {self.pair} tick - fetching from MT5")
        fresh = self._fetch_tick()
        self.cache.set_tick(self.pair, fresh)
        return fresh

    def _fetch_tick(self) -> Dict[str, Any]:
        """
        Fetch tick data from MT5 Bridge.

        Returns:
            Tick data dict from MT5 Bridge

        Raises:
            MT5BridgeConnectionError: Connection fails
            MT5BridgeResponseError: MT5 returns error
        """
        return self.mt5_bridge.get_tick(self.pair)

    # ========================================================================
    # MULTIPLE TICKS METHODS
    # ========================================================================

    def get_ticks(self, count: int, ttl: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Get recent tick history (cache-first).

        Args:
            count: Number of ticks to retrieve
            ttl: Cache TTL in seconds (uses default_ttl if None)

        Returns:
            List of tick dicts (most recent first):
            - time: Tick timestamp
            - bid: Bid price
            - ask: Ask price
            - volume: Tick volume

        Cache-First Logic:
        1. Check cache for (symbol, "ticks", count)
        2. If valid → return cached
        3. If expired/missing → fetch from MT5
        4. Update cache
        5. Return fresh data

        Raises:
            MT5BridgeConnectionError: MT5 Bridge connection fails
            MT5BridgeResponseError: MT5 Bridge returns error
        """
        cache_ttl = ttl if ttl is not None else self.default_ttl

        # Check cache first
        cached = self.cache.get_ticks(self.pair, count, ttl=cache_ttl)
        if cached is not None:
            logger.debug(f"Cache hit for {self.pair} ticks({count})")
            return cached

        # Cache miss/expired - fetch from MT5
        logger.debug(f"Cache miss for {self.pair} ticks({count}) - fetching from MT5")
        fresh = self._fetch_ticks(count)
        self.cache.set_ticks(self.pair, count, fresh)
        return fresh

    def _fetch_ticks(self, count: int) -> List[Dict[str, Any]]:
        """
        Fetch multiple ticks from MT5 Bridge.

        Args:
            count: Number of ticks to retrieve

        Returns:
            List of tick dicts from MT5 Bridge

        Raises:
            MT5BridgeConnectionError: Connection fails
            MT5BridgeResponseError: MT5 returns error
        """
        return self.mt5_bridge.get_ticks(self.pair, count=count)

    # ========================================================================
    # OHLC DATA METHODS
    # ========================================================================

    def get_ohlc(
        self,
        timeframe: int = 60,
        bars: int = 100,
        ttl: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Get OHLC candle data (cache-first).

        Args:
            timeframe: Timeframe in minutes (default: 60 = H1)
                       Valid: 1 (M1), 5 (M5), 15 (M15), 30 (M30),
                              60 (H1), 240 (H4), 1440 (D1)
            bars: Number of bars to retrieve (default: 100)
            ttl: Cache TTL in seconds (uses default_ttl if None)

        Returns:
            List of OHLC dicts (most recent first):
            - time: Candle open time
            - open: Open price
            - high: High price
            - low: Low price
            - close: Close price
            - volume: Tick volume

        Cache-First Logic:
        1. Check cache for (symbol, "ohlc", timeframe, bars)
        2. If valid → return cached
        3. If expired/missing → fetch from MT5
        4. Update cache
        5. Return fresh data

        Raises:
            MT5BridgeConnectionError: MT5 Bridge connection fails
            MT5BridgeResponseError: MT5 Bridge returns error
        """
        cache_ttl = ttl if ttl is not None else self.default_ttl

        # Check cache first
        cached = self.cache.get_ohlc(self.pair, timeframe, bars, ttl=cache_ttl)
        if cached is not None:
            logger.debug(f"Cache hit for {self.pair} OHLC({timeframe}, {bars})")
            return cached

        # Cache miss/expired - fetch from MT5
        logger.debug(f"Cache miss for {self.pair} OHLC({timeframe}, {bars}) - fetching from MT5")
        fresh = self._fetch_ohlc(timeframe, bars)
        self.cache.set_ohlc(self.pair, timeframe, bars, fresh)
        return fresh

    def _fetch_ohlc(self, timeframe: int, bars: int) -> List[Dict[str, Any]]:
        """
        Fetch OHLC data from MT5 Bridge.

        Args:
            timeframe: Timeframe in minutes
            bars: Number of bars

        Returns:
            List of OHLC dicts from MT5 Bridge

        Raises:
            MT5BridgeConnectionError: Connection fails
            MT5BridgeResponseError: MT5 returns error
        """
        return self.mt5_bridge.get_ohlc(self.pair, timeframe=timeframe, bars=bars)

    # ========================================================================
    # CONVENIENCE METHODS
    # ========================================================================

    def get_current_prices(self, ttl: Optional[float] = None) -> Dict[str, float]:
        """
        Get current bid/ask prices (convenience method).

        Args:
            ttl: Cache TTL in seconds

        Returns:
            Dict with:
            - bid: Current bid price
            - ask: Current ask price
            - spread: Current spread
            - timestamp: Unix timestamp

        Note:
            This is a convenience wrapper around get_tick().
        """
        tick = self.get_tick(ttl=ttl)
        return {
            "bid": tick["bid"],
            "ask": tick["ask"],
            "spread": tick["spread"],
            "timestamp": tick.get("timestamp", time.time())
        }

    def refresh_cache(self):
        """
        Force cache refresh (fetch fresh data from MT5).

        Bypasses cache TTL and fetches fresh data.
        Useful for:
        - Manual refresh scenarios
        - Cache invalidation
        - Testing

        Note:
            This updates cache with fresh data.
            Next get_xxx() call will use refreshed cache.
        """
        logger.info(f"Force refreshing cache for {self.pair}")

        # Refresh tick
        fresh_tick = self._fetch_tick()
        self.cache.set_tick(self.pair, fresh_tick)

        # Note: We don't refresh ticks/OHLC here
        # Those are only refreshed when explicitly requested
        # This prevents unnecessary fetches

    # ========================================================================
    # LEGACY METHOD (Phase 0 Compatibility)
    # ========================================================================

    def pull(self) -> Dict[str, Any]:
        """
        Pull current market data (legacy method).

        Returns:
            Market data dict (same as get_tick())

        Note:
            This is a legacy method from Phase 0.
            It simply calls get_tick().
        """
        return self.get_tick()


# ========================================================================
# SCHEDULER JOB FUNCTION
# ========================================================================

def pull_market_data_job():
    """
    Job function to pull market data for all enabled pairs.

    This is called by the scheduler (Phase 2) every market_data_pull_interval.

    Phase 3 Implementation:
    - Loads enabled pairs from config/pairs.yaml
    - For each pair: get_tick() with default TTL
    - This refreshes the cache for all pairs

    Note:
        In Phase 3, this is a placeholder.
        Actual config loading will be added when config layer is implemented.
        For now, it demonstrates the integration pattern.

    TODO: Load enabled pairs from config/pairs.yaml
    TODO: Create MarketPuller instance for each pair
    TODO: Call puller.get_tick() for each pair
    """
    # TODO: Implement actual job logic
    # This will be implemented when we have:
    # 1. Config loading mechanism
    # 2. MT5BridgeClient injection
    # 3. Shared MarketCache instance

    # Example pattern (for reference):
    # from execution.mt5_bridge import MT5BridgeClient
    # from data.market.cache import MarketCache
    #
    # mt5 = MT5BridgeClient()
    # cache = MarketCache()
    # pairs = load_enabled_pairs()  # TODO: implement
    #
    # pullers = {pair: MarketPuller(pair, mt5, cache) for pair in pairs}
    #
    # for pair, puller in pullers.items():
    #     try:
    #         puller.get_tick()  # Refreshes cache
    #         logger.info(f"Refreshed market data for {pair}")
    #     except Exception as e:
    #         logger.error(f"Failed to pull market data for {pair}: {e}")

    raise NotImplementedError("pull_market_data_job not yet implemented - needs config layer")
