"""
Order Validator - Phase 5 Implementation

Responsibilities:
- Validate decision schema completeness
- Validate decision consistency
- Validate confidence threshold
- Validate symbol exists in config
- Check risk limits from config/risk.yaml

This module validates orders - it does NOT execute them.
Execution is handled by order_router.

PHASE 5 CONSTRAINTS:
- No order placement
- No strategy logic
- No auto-fix or silent coercion
- Validation is strict
- No decision modification
"""

from typing import Dict, Any, Optional, Tuple
import logging
from pathlib import Path
import yaml


logger = logging.getLogger(__name__)


class DecisionValidationError(Exception):
    """Raised when decision validation fails."""
    pass


class OrderValidator:
    """
    Validator for trading decisions and orders.

    Ensures all decisions respect:
    - Schema completeness
    - Decision consistency
    - Risk limits from config/risk.yaml
    """

    # Default confidence threshold
    DEFAULT_MIN_CONFIDENCE = 0.5

    def __init__(
        self,
        risk_config: Optional[Dict[str, Any]] = None,
        pairs_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize order validator.

        Args:
            risk_config: Risk configuration from config/risk.yaml
            pairs_config: Pairs configuration from config/pairs.yaml

        Note:
            If configs not provided, will load from files.
        """
        if risk_config is None:
            self.risk_config = self._load_risk_config()
        else:
            self.risk_config = risk_config

        if pairs_config is None:
            self.pairs_config = self._load_pairs_config()
        else:
            self.pairs_config = pairs_config

        self.min_confidence = self.DEFAULT_MIN_CONFIDENCE

    def _load_risk_config(self) -> Dict[str, Any]:
        """Load risk configuration from config/risk.yaml."""
        config_path = Path(__file__).parent.parent / "config" / "risk.yaml"
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def _load_pairs_config(self) -> Dict[str, Any]:
        """Load pairs configuration from config/pairs.yaml."""
        config_path = Path(__file__).parent.parent / "config" / "pairs.yaml"
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def validate_decision(self, decision: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate a trading decision from strategy.

        Args:
            decision: Decision dict from Phase 4 strategy

        Returns:
            Tuple of (is_valid, error_message)

        Validation Checks:
        1. Schema completeness (all 8 keys present)
        2. Decision consistency (HOLD → no execution)
        3. Confidence threshold
        4. Symbol exists in config
        5. Entry type consistency

        Raises:
            DecisionValidationError: If validation fails critically

        Note:
            Pure validation - no side effects.
            Does NOT modify decision.
        """
        # Check 1: Schema completeness
        required_keys = [
            "strategy", "symbol", "decision", "confidence",
            "entry_type", "pending_type", "reason", "context"
        ]
        for key in required_keys:
            if key not in decision:
                return False, f"Missing required key: {key}"

        # Check 2: Decision values
        valid_decisions = ["BUY", "SELL", "HOLD"]
        if decision["decision"] not in valid_decisions:
            return False, f"Invalid decision: {decision['decision']}"

        # Check 3: Confidence range
        conf = decision["confidence"]
        if not isinstance(conf, (int, float)) or conf < 0.0 or conf > 1.0:
            return False, f"Invalid confidence: {conf}"

        # Check 4: Confidence threshold
        if conf < self.min_confidence:
            return False, f"Confidence below threshold: {conf} < {self.min_confidence}"

        # Check 5: Decision consistency (HOLD constraints)
        if decision["decision"] == "HOLD":
            if decision["entry_type"] != "none":
                return False, "HOLD decisions must have entry_type='none'"
            if decision["pending_type"] != "none":
                return False, "HOLD decisions must have pending_type='none'"

        # Check 6: Entry type consistency
        if decision["entry_type"] not in ["market", "pending", "none"]:
            return False, f"Invalid entry_type: {decision['entry_type']}"

        # Check 7: Pending type consistency
        valid_pending = ["BUY_LIMIT", "SELL_LIMIT", "BUY_STOP", "SELL_STOP", "none"]
        if decision["pending_type"] not in valid_pending:
            return False, f"Invalid pending_type: {decision['pending_type']}"

        # Check 8: Entry/pending consistency
        if decision["entry_type"] == "market":
            if decision["pending_type"] != "none":
                return False, "Market orders must have pending_type='none'"
        elif decision["entry_type"] == "pending":
            if decision["pending_type"] == "none":
                return False, "Pending orders must have valid pending_type"

        # Check 9: Symbol exists in config
        if not self._symbol_exists(decision["symbol"]):
            return False, f"Symbol not in config: {decision['symbol']}"

        # Check 10: Context presence
        context = decision.get("context", {})
        required_context = ["timeframe", "volatility_state", "trend_state"]
        for key in required_context:
            if key not in context:
                return False, f"Missing context key: {key}"

        # All checks passed
        return True, None

    def validate_market_order(
        self,
        pair: str,
        action: str,
        lots: float,
        account_data: Optional[Dict[str, Any]] = None,
        current_exposure: Optional[Dict[str, float]] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate a market order.

        Args:
            pair: Trading pair symbol
            action: 'BUY' or 'SELL'
            lots: Position size in lots
            account_data: Current account state (optional for Phase 5)
            current_exposure: Current exposure per pair (optional for Phase 5)

        Returns:
            Tuple of (is_valid, error_message)

        Checks:
        - Position size within limits
        - Total exposure within limits
        - Sufficient margin
        - Risk per trade within limits

        Note:
            In Phase 5, account_data and current_exposure are optional.
            Full risk validation will be added when account layer is implemented.
        """
        # Check action
        if action not in ["BUY", "SELL"]:
            return False, f"Invalid action: {action}"

        # Check lots
        if lots <= 0:
            return False, f"Invalid lots: {lots} (must be > 0)"

        # TODO: Add more checks when account layer is implemented
        # - Check max_capital_risk_per_trade
        # - Check max_total_exposure
        # - Check max_concurrent_trades
        # - Check daily_loss_limit

        return True, None

    def validate_pending_order(
        self,
        pair: str,
        action: str,
        order_type: str,
        entry_price: float,
        current_price: float,
        lots: float
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate a pending order.

        Args:
            pair: Trading pair symbol
            action: 'BUY' or 'SELL'
            order_type: Type of pending order
            entry_price: Price level to trigger
            current_price: Current market price
            lots: Position size in lots

        Returns:
            Tuple of (is_valid, error_message)

        Checks:
        - Entry price distance from current price
        - Order type compatibility (e.g., BUY_STOP above current)
        - Position size limits

        Order Type Compatibility:
        - BUY_LIMIT: entry_price < current_price
        - SELL_LIMIT: entry_price > current_price
        - BUY_STOP: entry_price > current_price
        - SELL_STOP: entry_price < current_price
        """
        # Check action
        if action not in ["BUY", "SELL"]:
            return False, f"Invalid action: {action}"

        # Check order type
        valid_types = ["BUY_LIMIT", "SELL_LIMIT", "BUY_STOP", "SELL_STOP"]
        if order_type not in valid_types:
            return False, f"Invalid order_type: {order_type}"

        # Check lots
        if lots <= 0:
            return False, f"Invalid lots: {lots} (must be > 0)"

        # Check order type compatibility
        if order_type == "BUY_LIMIT":
            if action == "BUY":
                if entry_price >= current_price:
                    return False, f"BUY_LIMIT must be below current: {entry_price} >= {current_price}"
        elif order_type == "SELL_LIMIT":
            if action == "SELL":
                if entry_price <= current_price:
                    return False, f"SELL_LIMIT must be above current: {entry_price} <= {current_price}"
        elif order_type == "BUY_STOP":
            if action == "BUY":
                if entry_price <= current_price:
                    return False, f"BUY_STOP must be above current: {entry_price} <= {current_price}"
        elif order_type == "SELL_STOP":
            if action == "SELL":
                if entry_price >= current_price:
                    return False, f"SELL_STOP must be below current: {entry_price} >= {current_price}"

        return True, None

    def check_risk_limits(
        self,
        lots: float,
        account_data: Optional[Dict[str, Any]] = None,
        current_exposure: Optional[Dict[str, float]] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if order respects risk limits.

        Args:
            lots: Position size in lots
            account_data: Current account state (optional for Phase 5)
            current_exposure: Current exposure per pair (optional for Phase 5)

        Returns:
            Tuple of (is_valid, error_message)

        Note:
            In Phase 5, this is a simplified version.
            Full risk validation will be added when account layer is implemented.
        """
        # TODO: Implement full risk limit checks in later phases
        # For now, just check basic lot size
        if lots <= 0:
            return False, f"Invalid lots: {lots}"

        # Check max_capital_risk_per_trade
        if account_data:
            max_risk_pct = self.risk_config.get("max_capital_risk_per_trade", 2.0)
            balance = account_data.get("balance", 0)
            if balance > 0:
                # TODO: Calculate actual risk amount
                # For now, just check lots not excessive
                max_lots = 10.0  # Simplified limit
                if lots > max_lots:
                    return False, f"Lots exceeds maximum: {lots} > {max_lots}"

        return True, None

    def calculate_position_risk(
        self,
        pair: str,
        lots: float,
        entry_price: float,
        stop_loss: float
    ) -> float:
        """
        Calculate risk amount for a position.

        Args:
            pair: Trading pair symbol
            lots: Position size in lots
            entry_price: Entry price
            stop_loss: Stop loss price

        Returns:
            Risk amount in account currency

        Note:
            Simplified calculation for Phase 5.
            Will be enhanced with contract size in later phases.
        """
        # Simple risk calculation (price difference * lots)
        # TODO: Add contract size multiplier in production
        risk_per_lot = abs(entry_price - stop_loss)
        total_risk = risk_per_lot * lots
        return total_risk

    def _symbol_exists(self, symbol: str) -> bool:
        """
        Check if symbol exists in config/pairs.yaml.

        Args:
            symbol: Trading pair symbol

        Returns:
            True if symbol is enabled in config

        Note:
            In Phase 5, we accept any symbol since config may not be populated yet.
        """
        # TODO: Check against actual config when populated
        # For now, accept any non-empty symbol
        return bool(symbol and len(symbol) > 0)
