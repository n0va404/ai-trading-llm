"""
Market Data Puller

Responsibilities:
- Pull current market data for all enabled pairs
- Store data in cache for strategy consumption
- Update pair state with latest prices

This module is a job function - called by the scheduler on interval.
It does NOT make trading decisions - only data collection.
"""

from typing import Dict, Any


# TODO: Import when implemented
# from data.market.cache import MarketCache
# from execution.mt5_bridge import MT5Bridge


def pull_market_data_job():
    """
    Job function to pull market data for all enabled pairs.

    This is called by the scheduler every market_data_pull_interval seconds.

    TODO: Implement market data pulling
    TODO: Load enabled pairs from config/pairs.yaml
    TODO: Call MT5 Bridge for current prices
    TODO: Update cache with latest data
    """
    raise NotImplementedError("pull_market_data_job not yet implemented")


class MarketPuller:
    """
    Market data puller for a single trading pair.

    Each pair has its own puller instance for isolation.
    """

    def __init__(self, pair: str, mt5_bridge, cache):
        """
        Initialize market puller for a specific pair.

        Args:
            pair: Trading pair symbol (e.g., "XAUUSDm")
            mt5_bridge: MT5 Bridge connection
            cache: Market cache instance

        TODO: Implement initialization
        """
        self.pair = pair
        self.mt5_bridge = mt5_bridge
        self.cache = cache
        raise NotImplementedError("MarketPuller.__init__ not yet implemented")

    def pull(self) -> Dict[str, Any]:
        """
        Pull current market data for this pair.

        Returns:
            Dictionary containing:
            - bid: Current bid price
            - ask: Current ask price
            - spread: Current spread in points
            - timestamp: Unix timestamp of data

        TODO: Implement MT5 Bridge call
        TODO: Handle connection errors
        TODO: Update cache
        """
        raise NotImplementedError("pull not yet implemented")
