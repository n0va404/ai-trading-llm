"""
Order Router - Phase 5 Implementation

Responsibilities:
- Accept validated decisions from Phase 4
- Convert decisions to MT5 payloads
- Route to correct MT5 endpoint
- Handle both market and pending orders

This module executes orders - it does NOT make trading decisions.
Decisions come from strategy modules, this module executes them.

PHASE 5 CONSTRAINTS:
- No business logic
- No price prediction
- No decision modification
- No strategy logic
- No auto-execution on import
"""

from typing import Dict, Any, Optional
from enum import Enum
import logging


logger = logging.getLogger(__name__)


class OrderType(Enum):
    """Order type enumeration."""
    MARKET_BUY = "MARKET_BUY"
    MARKET_SELL = "MARKET_SELL"
    PENDING_BUY_LIMIT = "PENDING_BUY_LIMIT"
    PENDING_BUY_STOP = "PENDING_BUY_STOP"
    PENDING_SELL_LIMIT = "PENDING_SELL_LIMIT"
    PENDING_SELL_STOP = "PENDING_SELL_STOP"


class OrderStatus(Enum):
    """Order status enumeration."""
    PENDING = "PENDING"
    PLACED = "PLACED"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class OrderRouter:
    """
    Router for sending orders to MT5 Bridge.

    Handles:
    - Decision validation
    - Payload construction
    - MT5 Bridge routing
    - Error propagation

    Does NOT:
    - Make trading decisions
    - Modify decisions
    - Predict prices
    - Auto-execute
    """

    def __init__(self, mt5_bridge, validator):
        """
        Initialize order router.

        Args:
            mt5_bridge: MT5BridgeClient instance (Phase 1)
            validator: OrderValidator instance (Phase 5)

        Note:
            No orders placed on init.
            No side effects.
        """
        self.mt5_bridge = mt5_bridge
        self.validator = validator

    def execute_decision(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a validated trading decision.

        Args:
            decision: Decision dict from Phase 4 strategy

        Returns:
            Execution result containing:
            - executed: Boolean indicating if order executed
            - order_id: MT5 order ID (if executed)
            - decision: Original decision (for reference)
            - error: Error message (if failed)

        Execution Flow:
        1. Validate decision schema
        2. Check if HOLD (no execution)
        3. Route to market or pending order
        4. Return result

        Raises:
            DecisionValidationError: If decision invalid
            MT5BridgeConnectionError: If MT5 connection fails
            MT5BridgeResponseError: If MT5 returns error

        Note:
            This is the main entry point for execution.
            Decisions MUST be validated first.
        """
        # Validate decision
        is_valid, error_msg = self.validator.validate_decision(decision)
        if not is_valid:
            raise DecisionValidationError(f"Decision validation failed: {error_msg}")

        # Check for HOLD (no execution)
        if decision["decision"] == "HOLD":
            return {
                "executed": False,
                "order_id": None,
                "decision": decision,
                "error": None,
                "reason": "HOLD decision - no execution"
            }

        # Route based on entry type
        entry_type = decision["entry_type"]

        if entry_type == "market":
            return self._execute_market_order(decision)
        elif entry_type == "pending":
            return self._execute_pending_order(decision)
        else:
            # entry_type == "none"
            return {
                "executed": False,
                "order_id": None,
                "decision": decision,
                "error": None,
                "reason": f"No execution (entry_type: {entry_type})"
            }

    def _execute_market_order(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a market order from decision.

        Args:
            decision: Decision dict with entry_type="market"

        Returns:
            Execution result dict

        Raises:
            MT5BridgeConnectionError: Connection fails
            MT5BridgeResponseError: MT5 returns error
        """
        symbol = decision["symbol"]
        action = decision["decision"]

        # Map action to MT5 type
        # MT5: 0=BUY, 1=SELL
        mt5_type = 0 if action == "BUY" else 1

        # Build payload for MT5 Bridge
        payload = {
            "symbol": symbol,
            "type": mt5_type,
            "volume": 0.01,  # TODO: Calculate from risk parameters
            "price": 0,  # 0 for market orders
            "comment": f"Decision from {decision['strategy']} strategy"
        }

        # Add SL/TP if available from strategy rules
        # TODO: Extract from decision or calculate
        # For now, placeholders
        # payload["sl"] = ...
        # payload["tp"] = ...

        try:
            # Call MT5 Bridge
            result = self.mt5_bridge.place_order(payload)

            # Check result
            if result.get("success"):
                order_id = result.get("ticket")
                logger.info(f"Market order executed: {action} {symbol} (ID: {order_id})")
                return {
                    "executed": True,
                    "order_id": order_id,
                    "decision": decision,
                    "error": None,
                    "reason": f"Market order placed: {action} {symbol}"
                }
            else:
                error = result.get("error", "Unknown error")
                logger.error(f"Market order failed: {error}")
                return {
                    "executed": False,
                    "order_id": None,
                    "decision": decision,
                    "error": error,
                    "reason": f"MT5 rejected order: {error}"
                }

        except Exception as e:
            logger.error(f"Market order exception: {e}")
            return {
                "executed": False,
                "order_id": None,
                "decision": decision,
                "error": str(e),
                "reason": f"Exception during execution: {e}"
            }

    def _execute_pending_order(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a pending order from decision.

        Args:
            decision: Decision dict with entry_type="pending"

        Returns:
            Execution result dict

        Raises:
            MT5BridgeConnectionError: Connection fails
            MT5BridgeResponseError: MT5 returns error
        """
        symbol = decision["symbol"]
        action = decision["decision"]
        pending_type = decision["pending_type"]

        # Map action and pending_type to MT5 format
        # MT5 accepts string types: "BUY_LIMIT", "SELL_LIMIT", etc.
        mt5_type = pending_type

        # Build payload for MT5 Bridge
        payload = {
            "symbol": symbol,
            "type": mt5_type,
            "volume": 0.01,  # TODO: Calculate from risk parameters
            # TODO: Get entry price from decision or calculate
            "price": 0,  # Placeholder - must be calculated
            "comment": f"Decision from {decision['strategy']} strategy"
        }

        # Add SL/TP if available
        # TODO: Extract from decision or calculate

        try:
            # Call MT5 Bridge
            result = self.mt5_bridge.place_pending_order(payload)

            # Check result
            if result.get("success"):
                order_id = result.get("ticket")
                logger.info(f"Pending order executed: {pending_type} {symbol} (ID: {order_id})")
                return {
                    "executed": True,
                    "order_id": order_id,
                    "decision": decision,
                    "error": None,
                    "reason": f"Pending order placed: {pending_type} {symbol}"
                }
            else:
                error = result.get("error", "Unknown error")
                logger.error(f"Pending order failed: {error}")
                return {
                    "executed": False,
                    "order_id": None,
                    "decision": decision,
                    "error": error,
                    "reason": f"MT5 rejected order: {error}"
                }

        except Exception as e:
            logger.error(f"Pending order exception: {e}")
            return {
                "executed": False,
                "order_id": None,
                "decision": decision,
                "error": str(e),
                "reason": f"Exception during execution: {e}"
            }

    # ========================================================================
    # LEGACY METHODS (Phase 0 Compatibility)
    # ========================================================================

    def place_market_order(
        self,
        pair: str,
        action: str,
        lots: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Place a market order (legacy method).

        Args:
            pair: Trading pair symbol
            action: 'BUY' or 'SELL'
            lots: Position size in lots
            stop_loss: Optional stop loss price
            take_profit: Optional take profit price

        Returns:
            Order result containing:
            - success: Boolean indicating if order placed
            - order_id: MT5 order ID (if successful)
            - error: Error message (if failed)

        Note:
            This is a legacy method from Phase 0.
            Prefer execute_decision() for new code.
        """
        # Validate
        is_valid, error_msg = self.validator.validate_market_order(
            pair, action, lots
        )
        if not is_valid:
            return {
                "success": False,
                "order_id": None,
                "error": error_msg
            }

        # Map action to MT5 type
        mt5_type = 0 if action == "BUY" else 1

        # Build payload
        payload = {
            "symbol": pair,
            "type": mt5_type,
            "volume": lots,
            "price": 0,  # 0 for market orders
        }

        if stop_loss is not None:
            payload["sl"] = stop_loss
        if take_profit is not None:
            payload["tp"] = take_profit

        # Add comment
        payload["comment"] = "Market order via OrderRouter"

        # Execute
        try:
            result = self.mt5_bridge.place_order(payload)
            return result
        except Exception as e:
            return {
                "success": False,
                "order_id": None,
                "error": str(e)
            }

    def place_pending_order(
        self,
        pair: str,
        action: str,
        order_type: OrderType,
        entry_price: float,
        lots: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        expiration: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Place a pending order (legacy method).

        Args:
            pair: Trading pair symbol
            action: 'BUY' or 'SELL'
            order_type: Type of pending order
            entry_price: Price level to trigger
            lots: Position size in lots
            stop_loss: Optional stop loss price
            take_profit: Optional take profit price
            expiration: Optional expiration timestamp

        Returns:
            Order result containing:
            - success: Boolean indicating if order placed
            - order_id: MT5 order ID (if successful)
            - error: Error message (if failed)

        Note:
            This is a legacy method from Phase 0.
            Prefer execute_decision() for new code.
        """
        # Map OrderType to string
        type_mapping = {
            OrderType.PENDING_BUY_LIMIT: "BUY_LIMIT",
            OrderType.PENDING_SELL_LIMIT: "SELL_LIMIT",
            OrderType.PENDING_BUY_STOP: "BUY_STOP",
            OrderType.PENDING_SELL_STOP: "SELL_STOP"
        }

        mt5_type = type_mapping.get(order_type, order_type.value)

        # Build payload
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

        # Add comment
        payload["comment"] = "Pending order via OrderRouter"

        # Execute
        try:
            result = self.mt5_bridge.place_pending_order(payload)
            return result
        except Exception as e:
            return {
                "success": False,
                "order_id": None,
                "error": str(e)
            }

    def cancel_order(self, order_id: int) -> Dict[str, Any]:
        """
        Cancel a pending order (legacy method).

        Args:
            order_id: MT5 order ID to cancel

        Returns:
            Cancellation result

        Note:
            TODO: Implement when MT5 Bridge has cancel endpoint
        """
        # TODO: MT5 Bridge API does not have /cancel endpoint yet
        return {
            "success": False,
            "order_id": order_id,
            "error": "Cancel not implemented - MT5 Bridge missing endpoint"
        }

    def close_position(self, position_id: int) -> Dict[str, Any]:
        """
        Close an open position (legacy method).

        Args:
            position_id: MT5 position ID to close

        Returns:
            Close result

        Note:
            TODO: Implement when MT5 Bridge has close endpoint
        """
        # TODO: Implement POST /close call
        return {
            "success": False,
            "position_id": position_id,
            "error": "Close not implemented yet"
        }


# Exception class for decision validation errors
class DecisionValidationError(Exception):
    """Raised when decision validation fails."""
    pass
