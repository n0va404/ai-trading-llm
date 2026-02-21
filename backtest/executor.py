"""
Backtest Executor - Phase 8 Implementation

Responsibilities:
- Reuse validation logic from Phase 5
- Simulate order fills based on candle OHLC
- Track entry price, exit price, duration, PnL
- Output resolved trade events
- No slippage (unless explicitly modeled)
- No spread (unless explicitly modeled)
- Deterministic fills only

This module simulates execution without touching MT5.

PHASE 8 CONSTRAINTS:
- NO MT5 calls
- NO actual order placement
- Deterministic fill simulation
- Reuse Phase 5 validation unchanged
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from execution.validator import OrderValidator


logger = logging.getLogger(__name__)


class BacktestExecutor:
    """
    Simulated order executor for backtesting.

    Reuses Phase 5 OrderValidator for validation.
    Simulates fills based on candle OHLC data.

    Rules:
    - Market orders: Fill at open of next candle
    - Pending orders: Fill if price touched during candle
    - No slippage (simplified)
    - No spread (simplified)
    - Deterministic behavior
    """

    def __init__(
        self,
        pair: str,
        validator: Optional[OrderValidator] = None,
        initial_balance: float = 10000.0
    ):
        """
        Initialize backtest executor.

        Args:
            pair: Trading pair symbol
            validator: OrderValidator instance (creates new if None)
            initial_balance: Starting account balance

        Note:
            Reuses OrderValidator from Phase 5.
            No MT5 connection required.
        """
        self.pair = pair
        self.validator = validator or OrderValidator()
        self.initial_balance = initial_balance
        self.current_balance = initial_balance

        # Track open positions
        self.positions: Dict[int, Dict[str, Any]] = {}

        # Track filled orders
        self.filled_orders: List[Dict[str, Any]] = []

        # Trade counter
        self._trade_counter = 0

    def validate_decision(self, decision: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate trading decision using Phase 5 validator.

        Args:
            decision: Decision dict from Phase 4 strategy

        Returns:
            Tuple of (is_valid, error_message)

        Note:
            Delegates to OrderValidator.validate_decision()
            No modification to validation logic.
        """
        return self.validator.validate_decision(decision)

    def execute_market_order(
        self,
        decision: Dict[str, Any],
        candle: Dict[str, Any],
        timestamp: str
    ) -> Dict[str, Any]:
        """
        Simulate market order execution.

        Args:
            decision: Decision dict from Phase 4 strategy
            candle: Current candle OHLC data
            timestamp: Order timestamp

        Returns:
            Execution result dict with structure:
            {
                "success": True,
                "ticket": 123456,
                "symbol": "XAUUSDm",
                "type": 0,  # 0=BUY, 1=SELL
                "lots": 0.01,
                "entry_price": 2936.50,
                "sl": 2924.50,
                "tp": 2954.50,
                "timestamp": "2026-02-21T10:00:00",
                "comment": "Simulated market order"
            }

        Note:
            Market orders fill at candle OPEN price.
            No slippage simulation (simplified).
        """
        action = decision["decision"]
        lots = 0.01  # TODO: Calculate from risk parameters

        # Map action to MT5 type
        order_type = 0 if action == "BUY" else 1

        # Fill at candle open (market order simulation)
        entry_price = candle["open"]

        # Generate ticket
        self._trade_counter += 1
        ticket = self._trade_counter

        # Extract SL/TP from decision context if present
        sl = decision.get("context", {}).get("stop_loss", 0.0)
        tp = decision.get("context", {}).get("take_profit", 0.0)

        # Create position record
        position = {
            "ticket": ticket,
            "symbol": self.pair,
            "type": order_type,
            "lots": lots,
            "entry_price": entry_price,
            "sl": sl,
            "tp": tp,
            "open_time": timestamp,
            "decision": decision,
            "current_price": entry_price
        }

        self.positions[ticket] = position
        self.filled_orders.append(position)

        logger.info(
            f"[BACKTEST] Market order filled: {action} {self.pair} "
            f"@ {entry_price:.2f} (Ticket: {ticket})"
        )

        return {
            "success": True,
            "ticket": ticket,
            "symbol": self.pair,
            "type": order_type,
            "lots": lots,
            "entry_price": entry_price,
            "sl": sl,
            "tp": tp,
            "timestamp": timestamp,
            "comment": "Simulated market order"
        }

    def execute_pending_order(
        self,
        decision: Dict[str, Any],
        candle: Dict[str, Any],
        timestamp: str
    ) -> Optional[Dict[str, Any]]:
        """
        Simulate pending order execution.

        Args:
            decision: Decision dict with entry_type="pending"
            candle: Current candle OHLC data
            timestamp: Current timestamp

        Returns:
            Execution result dict if filled, None if not filled

        Note:
            Pending orders fill if price level is touched.
            BUY_LIMIT/SELL_STOP: Fill if low <= price
            SELL_LIMIT/BUY_STOP: Fill if high >= price
        """
        pending_type = decision.get("pending_type", "")
        price = decision.get("context", {}).get("entry_price", 0.0)

        if price == 0:
            return None

        candle_low = candle["low"]
        candle_high = candle["high"]

        should_fill = False

        # Check if price was touched during candle
        if pending_type in ["BUY_LIMIT", "SELL_STOP"]:
            # Buy limit / Sell stop: fill if price went down to level
            should_fill = candle_low <= price
        elif pending_type in ["SELL_LIMIT", "BUY_STOP"]:
            # Sell limit / Buy stop: fill if price went up to level
            should_fill = candle_high >= price
        else:
            logger.warning(f"Unknown pending type: {pending_type}")
            return None

        if not should_fill:
            return None

        # Determine action from pending type
        if pending_type in ["BUY_LIMIT", "BUY_STOP"]:
            action = "BUY"
            order_type = 0
        else:
            action = "SELL"
            order_type = 1

        # Fill at trigger price
        entry_price = price

        # Generate ticket
        self._trade_counter += 1
        ticket = self._trade_counter

        # Extract SL/TP
        sl = decision.get("context", {}).get("stop_loss", 0.0)
        tp = decision.get("context", {}).get("take_profit", 0.0)

        # Create position record
        position = {
            "ticket": ticket,
            "symbol": self.pair,
            "type": order_type,
            "lots": 0.01,  # TODO: Calculate from risk
            "entry_price": entry_price,
            "sl": sl,
            "tp": tp,
            "open_time": timestamp,
            "decision": decision,
            "current_price": entry_price
        }

        self.positions[ticket] = position
        self.filled_orders.append(position)

        logger.info(
            f"[BACKTEST] Pending order filled: {pending_type} {self.pair} "
            f"@ {entry_price:.2f} (Ticket: {ticket})"
        )

        return {
            "success": True,
            "ticket": ticket,
            "symbol": self.pair,
            "type": order_type,
            "lots": 0.01,
            "entry_price": entry_price,
            "sl": sl,
            "tp": tp,
            "timestamp": timestamp,
            "comment": f"Simulated {pending_type} fill"
        }

    def close_position(
        self,
        ticket: int,
        candle: Dict[str, Any],
        timestamp: str,
        reason: str = "manual"
    ) -> Optional[Dict[str, Any]]:
        """
        Close a position and calculate PnL.

        Args:
            ticket: Position ticket number
            candle: Current candle OHLC data
            timestamp: Close timestamp
            reason: Reason for closing ("manual", "sl", "tp", "signal")

        Returns:
            Trade result dict with PnL info, or None if position not found

        Note:
            Exit at candle close price (simplified).
            Calculates PnL based on entry and exit prices.
        """
        if ticket not in self.positions:
            logger.warning(f"Position {ticket} not found")
            return None

        position = self.positions[ticket]
        exit_price = candle["close"]

        # Calculate PnL
        entry_price = position["entry_price"]
        lots = position["lots"]
        order_type = position["type"]

        # PnL calculation (simplified)
        # TODO: Use proper contract size and point value
        if order_type == 0:  # BUY
            pnl = (exit_price - entry_price) * lots * 100  # Assuming 1 lot = 100 units
        else:  # SELL
            pnl = (entry_price - exit_price) * lots * 100

        # Calculate duration
        from utils.time import parse_timestamp
        open_time = parse_timestamp(position["open_time"])
        close_time = parse_timestamp(timestamp)
        duration_sec = (close_time - open_time).total_seconds()

        # Determine result
        if pnl > 0:
            result = "win"
        elif pnl < 0:
            result = "loss"
        else:
            result = "breakeven"

        # Create trade result
        trade_result = {
            "ticket": ticket,
            "symbol": self.pair,
            "type": order_type,
            "lots": lots,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "pnl": pnl,
            "result": result,
            "duration_sec": duration_sec,
            "close_reason": reason,
            "open_time": position["open_time"],
            "close_time": timestamp,
            "decision": position["decision"]
        }

        # Remove from open positions
        del self.positions[ticket]

        # Update balance
        self.current_balance += pnl

        logger.info(
            f"[BACKTEST] Position closed: {ticket} {self.pair} "
            f"PnL: {pnl:.2f} ({result})"
        )

        return trade_result

    def check_sl_tp(
        self,
        candle: Dict[str, Any],
        timestamp: str
    ) -> List[Dict[str, Any]]:
        """
        Check if any positions hit SL or TP.

        Args:
            candle: Current candle OHLC data
            timestamp: Current timestamp

        Returns:
            List of closed positions (trade results)

        Note:
            Checks if candle high/low touched SL or TP levels.
            Priority: TP first, then SL.
        """
        closed = []

        candle_low = candle["low"]
        candle_high = candle["high"]

        # Need to copy keys to avoid modification during iteration
        tickets = list(self.positions.keys())

        for ticket in tickets:
            position = self.positions[ticket]
            sl = position.get("sl", 0.0)
            tp = position.get("tp", 0.0)
            order_type = position["type"]

            close_reason = None

            # Check TP
            if tp > 0:
                if order_type == 0:  # BUY - TP is above
                    if candle_high >= tp:
                        close_reason = "tp"
                else:  # SELL - TP is below
                    if candle_low <= tp:
                        close_reason = "tp"

            # Check SL (only if not hit TP)
            if close_reason is None and sl > 0:
                if order_type == 0:  # BUY - SL is below
                    if candle_low <= sl:
                        close_reason = "sl"
                else:  # SELL - SL is above
                    if candle_high >= sl:
                        close_reason = "sl"

            if close_reason:
                # For SL/TP fills, use the SL/TP price as exit price
                exit_price = tp if close_reason == "tp" else sl

                # Create modified candle for close_position
                fill_candle = candle.copy()
                fill_candle["close"] = exit_price

                trade_result = self.close_position(
                    ticket, fill_candle, timestamp, close_reason
                )

                if trade_result:
                    closed.append(trade_result)

        return closed

    def get_open_positions(self) -> List[Dict[str, Any]]:
        """
        Get all open positions.

        Returns:
            List of open position dicts
        """
        return list(self.positions.values())

    def get_balance(self) -> float:
        """
        Get current account balance.

        Returns:
            Current balance
        """
        return self.current_balance

    def get_equity(self) -> float:
        """
        Calculate current equity (balance + unrealized PnL).

        Returns:
            Current equity

        Note:
            Uses current price for unrealized PnL calculation.
            In backtest, this is candle close price.
        """
        equity = self.current_balance

        # Add unrealized PnL from open positions
        for position in self.positions.values():
            # Simplified - use entry price as current price
            # TODO: Pass current price to calculate unrealized PnL
            pass

        return equity
