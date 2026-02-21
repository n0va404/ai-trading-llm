"""
MT5 Bridge Client - Phase 1 Implementation

Responsibilities:
- Thin HTTP client wrapper for MT5 Bridge API
- Strict request/response handling
- NO trading logic
- NO strategy logic
- NO caching
- NO retry logic
- Stateless transport adapter only

This client follows the MT5 Bridge API documentation exactly:
https://github.com/n0va404/kairos-core/blob/main/docs/MT5_BRIDGE_API.md

IMPORTANT:
- All methods are thin wrappers around HTTP endpoints
- No interpretation of results beyond HTTP status + JSON schema
- Errors are loud and explicit (exceptions, not silent failures)
- No automatic retries
- No connection pooling (stateless)
"""

from typing import Dict, Any, List, Optional
import requests
import json


class MT5BridgeError(Exception):
    """Base exception for MT5 Bridge errors."""
    pass


class MT5BridgeConnectionError(MT5BridgeError):
    """Raised when HTTP connection fails."""
    pass


class MT5BridgeResponseError(MT5BridgeError):
    """Raised when MT5 Bridge returns success=False."""
    pass


class MT5BridgeClient:
    """
    Stateless HTTP client for MT5 Bridge service.

    This client:
    - Does NOT cache responses
    - Does NOT store global state
    - Does NOT auto-retry requests
    - Does NOT perform scheduling
    - Does NOT contain trading logic

    It is a pure transport adapter.
    """

    # Default base URL from MT5 Bridge documentation
    DEFAULT_BASE_URL = "http://localhost:8080"

    def __init__(self, base_url: Optional[str] = None, timeout: int = 5):
        """
        Initialize MT5 Bridge client.

        Args:
            base_url: Base URL of MT5 Bridge (default: http://localhost:8080)
            timeout: HTTP request timeout in seconds (default: 5)

        Note:
            No connection is established on init.
            Connection happens per-request.
        """
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.timeout = timeout

    # ========================================
    # SYSTEM & HEALTH
    # ========================================

    def health_check(self) -> Dict[str, Any]:
        """
        Health check for monitoring.

        Endpoint: GET /health

        Returns:
            {
                "status": "healthy",
                "mt5_connection": true,
                "timestamp": "2026-02-19T13:00:00.000000"
            }

        Raises:
            MT5BridgeConnectionError: HTTP request fails
            MT5BridgeResponseError: MT5 Bridge returns error
        """
        url = f"{self.base_url}/health"
        response = self._get(url)
        return response

    # ========================================
    # MARKET DATA
    # ========================================

    def get_tick(self, symbol: str) -> Dict[str, Any]:
        """
        Get current tick data for a symbol.

        Endpoint: GET /tick/<symbol>

        Args:
            symbol: Trading pair symbol (e.g., "XAUUSDm")

        Returns:
            {
                "symbol": "XAUUSDm",
                "bid": 2936.12,
                "ask": 2936.87,
                "spread": 0.75,
                "timestamp": "2026-02-19T13:00:00.000000"
            }

        Raises:
            MT5BridgeConnectionError: HTTP request fails
            MT5BridgeResponseError: MT5 Bridge returns error
        """
        url = f"{self.base_url}/tick/{symbol}"
        response = self._get(url)
        return response["data"]

    def get_ticks(self, symbol: str, count: int = 10) -> List[Dict[str, Any]]:
        """
        Get last N ticks for a symbol.

        Endpoint: GET /ticks/<symbol>?count=<count>

        Args:
            symbol: Trading pair symbol (e.g., "XAUUSDm")
            count: Number of ticks to retrieve (default: 10)

        Returns:
            [
                {
                    "time": "2026-02-19T13:00:01.123",
                    "bid": 2936.12,
                    "ask": 2936.87,
                    "volume": 1
                },
                ... (most recent first)
            ]

        Raises:
            MT5BridgeConnectionError: HTTP request fails
            MT5BridgeResponseError: MT5 Bridge returns error
        """
        url = f"{self.base_url}/ticks/{symbol}"
        params = {"count": count}
        response = self._get(url, params=params)
        return response["data"]

    def get_ohlc(
        self,
        symbol: str,
        timeframe: int = 60,
        bars: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get OHLC candle data for a symbol.

        Endpoint: GET /ohlc/<symbol>?tf=<timeframe>&count=<bars>

        Args:
            symbol: Trading pair symbol (e.g., "XAUUSDm")
            timeframe: Timeframe in minutes (default: 60)
                      Valid: 1 (M1), 5 (M5), 15 (M15), 30 (M30),
                             60 (H1), 240 (H4), 1440 (D1)
            bars: Number of bars to retrieve (default: 100)

        Returns:
            [
                {
                    "time": "2026-02-19T12:00:00",
                    "open": 2934.50,
                    "high": 2940.20,
                    "low": 2930.10,
                    "close": 2936.12,
                    "volume": 150
                },
                ... (most recent first)
            ]

        Raises:
            MT5BridgeConnectionError: HTTP request fails
            MT5BridgeResponseError: MT5 Bridge returns error
        """
        url = f"{self.base_url}/ohlc/{symbol}"
        params = {"tf": timeframe, "count": bars}
        response = self._get(url, params=params)
        return response["data"]

    # ========================================
    # ACCOUNT STATE
    # ========================================

    def get_account(self) -> Dict[str, Any]:
        """
        Get account information.

        Endpoint: GET /account

        Returns:
            {
                "login": 12345678,
                "server": "MetaQuotes-Demo",
                "balance": 10000.00,
                "equity": 10000.00,
                "margin": 0.00,
                "free_margin": 10000.00,
                "leverage": 100,
                "currency": "USD"
            }

        Raises:
            MT5BridgeConnectionError: HTTP request fails
            MT5BridgeResponseError: MT5 Bridge returns error
        """
        url = f"{self.base_url}/account"
        response = self._get(url)
        return response["data"]

    def get_positions(self) -> List[Dict[str, Any]]:
        """
        Get all open positions.

        Endpoint: GET /positions

        Returns:
            [
                {
                    "ticket": 123456,
                    "symbol": "XAUUSDm",
                    "type": 0,  # 0=BUY, 1=SELL
                    "lots": 0.01,
                    "open_price": 2936.50,
                    "current_price": 2938.20,
                    "sl": 2924.50,
                    "tp": 2954.50,
                    "profit": 1.70,
                    "comment": "AI Generated Trade"
                },
                ...
            ]

        Raises:
            MT5BridgeConnectionError: HTTP request fails
            MT5BridgeResponseError: MT5 Bridge returns error
        """
        url = f"{self.base_url}/positions"
        response = self._get(url)
        return response["data"]

    def get_orders(self) -> List[Dict[str, Any]]:
        """
        Get all pending orders.

        Endpoint: GET /orders

        Returns:
            [
                {
                    "ticket": 123457,
                    "symbol": "EURUSDm",
                    "type": 2,  # 2=BUY_LIMIT, 3=SELL_LIMIT, 4=BUY_STOP, 5=SELL_STOP
                    "lots": 0.01,
                    "price": 1.0800,
                    "sl": 1.0750,
                    "tp": 1.0900,
                    "comment": "AI Pending Trade"
                },
                ...
            ]

        Raises:
            MT5BridgeConnectionError: HTTP request fails
            MT5BridgeResponseError: MT5 Bridge returns error
        """
        url = f"{self.base_url}/orders"
        response = self._get(url)
        return response["data"]

    # ========================================
    # TRADE EXECUTION
    # ========================================

    def place_order(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Place a market order.

        Endpoint: POST /place

        Args:
            payload: Order payload with exact structure:
                {
                    "symbol": "XAUUSDm",
                    "type": 0,  # 0=BUY, 1=SELL
                    "volume": 0.01,
                    "price": 0,  # 0 for market orders
                    "sl": 2924.50,  # optional
                    "tp": 2954.50,  # optional
                    "comment": "AI Generated Trade"  # optional
                }

        Returns:
            {
                "success": true,
                "ticket": 123456,
                "message": "Order placed successfully"
            }

        Raises:
            MT5BridgeConnectionError: HTTP request fails
            MT5BridgeResponseError: MT5 Bridge returns error

        Note:
            Payload validation is NOT performed here.
            Caller must ensure payload matches MT5 Bridge spec.
        """
        url = f"{self.base_url}/place"
        response = self._post(url, payload)
        return response

    def place_pending_order(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Place a pending order.

        Endpoint: POST /pending

        Args:
            payload: Pending order payload with exact structure:
                {
                    "symbol": "XAUUSDm",
                    "type": "BUY_LIMIT",  # or 2
                    "volume": 0.01,
                    "price": 2930.00,
                    "sl": 2924.50,  # optional
                    "tp": 2954.50,  # optional
                    "comment": "AI Pending Trade"  # optional
                }

                Valid types: "BUY_LIMIT" (2), "SELL_LIMIT" (3),
                            "BUY_STOP" (4), "SELL_STOP" (5)

        Returns:
            {
                "success": true,
                "ticket": 123457,
                "message": "Pending order placed"
            }

        Raises:
            MT5BridgeConnectionError: HTTP request fails
            MT5BridgeResponseError: MT5 Bridge returns error

        Note:
            Payload validation is NOT performed here.
            Caller must ensure payload matches MT5 Bridge spec.
        """
        url = f"{self.base_url}/pending"
        response = self._post(url, payload)
        return response

    # ========================================
    # HELPER METHODS (HTTP transport)
    # ========================================

    def _get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform HTTP GET request.

        Args:
            url: Full URL for request
            params: Optional query parameters

        Returns:
            Parsed JSON response

        Raises:
            MT5BridgeConnectionError: HTTP request fails
            MT5BridgeResponseError: Response has success=False
        """
        try:
            response = requests.get(
                url,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()

            data = response.json()

            # Check for MT5 Bridge error response
            if not data.get("success", True):
                error_msg = data.get("error", "Unknown error")
                raise MT5BridgeResponseError(error_msg)

            return data

        except requests.RequestException as e:
            raise MT5BridgeConnectionError(f"HTTP GET failed: {e}")
        except json.JSONDecodeError as e:
            raise MT5BridgeResponseError(f"Invalid JSON response: {e}")

    def _post(
        self,
        url: str,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform HTTP POST request.

        Args:
            url: Full URL for request
            payload: Request body as dictionary

        Returns:
            Parsed JSON response

        Raises:
            MT5BridgeConnectionError: HTTP request fails
            MT5BridgeResponseError: Response has success=False
        """
        try:
            response = requests.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=self.timeout
            )
            response.raise_for_status()

            data = response.json()

            # Check for MT5 Bridge error response
            if not data.get("success", True):
                error_msg = data.get("error", "Unknown error")
                raise MT5BridgeResponseError(error_msg)

            return data

        except requests.RequestException as e:
            raise MT5BridgeConnectionError(f"HTTP POST failed: {e}")
        except json.JSONDecodeError as e:
            raise MT5BridgeResponseError(f"Invalid JSON response: {e}")


# =============================================================================
# COMPATIBILITY LAYER (Phase 0 Integration)
# =============================================================================
# The following class maintains Phase 0's MT5Bridge interface
# while using the new MT5BridgeClient internally.
# This ensures backward compatibility with Phase 0 code.
# =============================================================================

class MT5Bridge:
    """
    Compatibility wrapper for Phase 0 interface.

    This class maintains the Phase 0 interface contract while
    internally using MT5BridgeClient for actual communication.

    DEPRECATED: Use MT5BridgeClient directly for new code.
    """

    def __init__(self, base_url: str = "http://localhost:8080"):
        """
        Initialize MT5 Bridge wrapper.

        Args:
            base_url: Base URL of MT5 Bridge service
        """
        self._client = MT5BridgeClient(base_url=base_url)

    def get_account_info(self) -> Dict[str, Any]:
        """
        Get account information from MT5.

        Returns:
            Account info dict (Phase 0 format)

        Note: Maps to MT5BridgeClient.get_account()
        """
        return self._client.get_account()

    def get_market_data(self, pair: str) -> Dict[str, Any]:
        """
        Get current market data for a pair.

        Args:
            pair: Trading pair symbol

        Returns:
            Market data dict (Phase 0 format)

        Note: Maps to MT5BridgeClient.get_tick()
        """
        return self._client.get_tick(pair)

    def place_market_order(
        self,
        pair: str,
        action: str,
        lots: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Place a market order via MT5.

        Args:
            pair: Trading pair symbol
            action: 'BUY' or 'SELL'
            lots: Position size in lots
            stop_loss: Optional stop loss price
            take_profit: Optional take profit price

        Returns:
            Order result dict (Phase 0 format)

        Note: Maps to MT5BridgeClient.place_order()
        """
        # Map Phase 0 action to MT5 Bridge type
        order_type = 0 if action.upper() == "BUY" else 1

        payload = {
            "symbol": pair,
            "type": order_type,
            "volume": lots,
            "price": 0  # 0 for market orders
        }

        if stop_loss is not None:
            payload["sl"] = stop_loss
        if take_profit is not None:
            payload["tp"] = take_profit

        return self._client.place_order(payload)

    def place_pending_order(
        self,
        pair: str,
        action: str,
        order_type: str,
        entry_price: float,
        lots: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        expiration: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Place a pending order via MT5.

        Args:
            pair: Trading pair symbol
            action: 'BUY' or 'SELL'
            order_type: Type of pending order
            entry_price: Price level to trigger
            lots: Position size in lots
            stop_loss: Optional stop loss price
            take_profit: Optional take profit price
            expiration: Optional expiration timestamp (not used in MT5 Bridge API)

        Returns:
            Order result dict

        Note: Maps to MT5BridgeClient.place_pending_order()
              Expiration is NOT supported by MT5 Bridge API
        """
        # Map Phase 0 order_type to MT5 Bridge format
        type_mapping = {
            "BUY_LIMIT": "BUY_LIMIT",
            "SELL_LIMIT": "SELL_LIMIT",
            "BUY_STOP": "BUY_STOP",
            "SELL_STOP": "SELL_STOP"
        }

        mt5_type = type_mapping.get(order_type.upper(), order_type)

        payload = {
            "symbol": pair,
            "type": mt5_type,
            "volume": lots,
            "price": entry_price
        }

        if stop_loss is not None:
            payload["sl"] = stop_loss
        if take_profit is not None:
            payload["tp"] = take_profit

        # TODO: Expiration not supported by MT5 Bridge API - add to comment field?
        if expiration is not None:
            payload["comment"] = f"Expires: {expiration}"

        return self._client.place_pending_order(payload)

    def cancel_order(self, order_id: int) -> Dict[str, Any]:
        """
        Cancel a pending order.

        Args:
            order_id: MT5 order ID to cancel

        Returns:
            Cancellation result

        Note: MT5 Bridge API does not have a cancel endpoint.
              This is a placeholder for future implementation.
        """
        # TODO: MT5 Bridge API does not have /cancel endpoint
        # Need to check if there's an alternative method
        raise NotImplementedError(
            "cancel_order not implemented - MT5 Bridge API missing /cancel endpoint"
        )

    def close_position(self, position_id: int) -> Dict[str, Any]:
        """
        Close an open position.

        Args:
            position_id: MT5 position ID to close

        Returns:
            Close result

        Note: This would map to POST /close endpoint
        """
        # TODO: Implement POST /close call
        url = f"{self._client.base_url}/close"
        payload = {"ticket": position_id}
        return self._client._post(url, payload)

    def get_open_positions(self) -> List[Dict[str, Any]]:
        """
        Get all open positions.

        Returns:
            List of position dictionaries

        Note: Maps to MT5BridgeClient.get_positions()
        """
        return self._client.get_positions()

    def get_pending_orders(self) -> List[Dict[str, Any]]:
        """
        Get all pending orders.

        Returns:
            List of order dictionaries

        Note: Maps to MT5BridgeClient.get_orders()
        """
        return self._client.get_orders()
