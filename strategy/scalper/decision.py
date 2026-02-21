"""
Scalper Strategy Decision - Phase 4 Implementation

Responsibilities:
- Make scalper trading decisions
- Combine rule outputs
- Produce structured trade decisions
- No LLM, no execution, no side effects

This module produces deterministic trading decisions based on rules.
It does NOT execute trades or call external services.

PHASE 4 CONSTRAINTS:
- No order placement
- No execution layer imports
- No LLM calls
- No scheduler logic
- Deterministic output for same input
"""

from typing import Dict, Any, Optional
import logging
from strategy.scalper.rules import ScalperRules


logger = logging.getLogger(__name__)


def scalper_decision_job():
    """
    Job function to evaluate scalper opportunities.

    This is called by the scheduler (Phase 2) every scalper_decision_interval.

    Phase 4 Implementation:
    - Loads enabled pairs
    - For each pair: evaluate_decision() with market data
    - Produces structured decisions

    Note:
        In Phase 4, this is a placeholder.
        Actual integration with market data layer will be added in future phases.

    TODO: Load enabled pairs from config/pairs.yaml
    TODO: Create ScalperDecisionEngine for each pair
    TODO: Fetch market data from Phase 3 cache
    TODO: Store decisions for execution layer
    """
    # TODO: Implement actual job logic
    # This will be implemented when we have:
    # 1. Config loading mechanism
    # 2. Market data access (Phase 3)
    # 3. Decision storage mechanism

    raise NotImplementedError("scalper_decision_job not yet implemented - needs market data integration")


class ScalperDecisionEngine:
    """
    Decision engine for scalper strategy.

    Produces deterministic trading decisions based on rules.
    Each pair has its own decision engine for isolation.

    NO LLM - Pure rule-based decisions in Phase 4.
    """

    def __init__(self, pair: str, rules: Optional[ScalperRules] = None):
        """
        Initialize scalper decision engine for a specific pair.

        Args:
            pair: Trading pair symbol
            rules: Optional ScalperRules instance (creates default if None)

        Note:
            No external calls on init.
            No state persistence.
        """
        self.pair = pair
        self.rules = rules or ScalperRules(pair)

    def evaluate(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate and produce scalper trading decision.

        Args:
            market_data: Market data dict containing:
                - bid: Current bid price
                - ask: Current ask price
                - spread: Spread in points
                - Optional: ohlc_data for trend analysis

        Returns:
            Decision dict with EXACT schema:
            {
                "strategy": "scalper",
                "symbol": str,
                "decision": "BUY" | "SELL" | "HOLD",
                "confidence": 0.0-1.0,
                "entry_type": "market" | "pending" | "none",
                "pending_type": "BUY_LIMIT" | "SELL_LIMIT" | "BUY_STOP" | "SELL_STOP" | "none",
                "reason": str,
                "context": {
                    "timeframe": "M1" | "M5" | "M15" | "H1",
                    "volatility_state": "low" | "normal" | "high",
                    "trend_state": "bullish" | "bearish" | "ranging"
                }
            }

        Scalper Decision Logic:
        1. Validate entry conditions via rules
        2. Analyze trend from OHLC data
        3. Produce decision (prefer action over HOLD)
        4. Calculate confidence
        5. Map trend to BUY/SELL/HOLD

        Note:
            Pure function - no side effects.
            Deterministic output for same input.
            No LLM calls in Phase 4.
        """
        # Validate entry conditions
        validation = self.rules.validate_entry(market_data)

        # Analyze trend
        ohlc_data = market_data.get("ohlc_data", [])
        trend_analysis = self.rules.analyze_trend(ohlc_data)

        # Determine context
        context = self._build_context(market_data, trend_analysis)

        # Make decision
        decision = self._make_decision(validation, trend_analysis, context)

        # Calculate final confidence
        confidence = self._calculate_final_confidence(
            validation["confidence"],
            trend_analysis["strength"],
            decision
        )

        # Build result
        result = {
            "strategy": "scalper",
            "symbol": self.pair,
            "decision": decision["action"],
            "confidence": confidence,
            "entry_type": decision["entry_type"],
            "pending_type": decision["pending_type"],
            "reason": decision["reason"],
            "context": context
        }

        # Validate schema
        self._validate_schema(result)

        return result

    def _build_context(
        self,
        market_data: Dict[str, Any],
        trend_analysis: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Build decision context dict.

        Args:
            market_data: Current market data
            trend_analysis: Trend analysis from rules

        Returns:
            Context dict with timeframe, volatility_state, trend_state

        Note:
            Scalper uses M1-M5 timeframes (fast decisions).
        """
        # Determine volatility state
        volatility = trend_analysis.get("momentum", 0.5)
        if volatility < 0.3:
            volatility_state = "low"
        elif volatility > 0.7:
            volatility_state = "high"
        else:
            volatility_state = "normal"

        # Get trend state from analysis
        trend_state = trend_analysis.get("trend", "ranging")

        # Scalper uses short timeframes
        timeframe = "M1"  # Could be configurable

        return {
            "timeframe": timeframe,
            "volatility_state": volatility_state,
            "trend_state": trend_state
        }

    def _make_decision(
        self,
        validation: Dict[str, Any],
        trend_analysis: Dict[str, Any],
        context: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Make trading decision based on validation and trend.

        Args:
            validation: Entry validation result
            trend_analysis: Trend analysis result
            context: Decision context

        Returns:
            Decision dict with action, entry_type, pending_type, reason

        Scalper Decision Rules:
        - MUST prefer action over HOLD
        - HOLD only if: spread too large OR volatility anomaly
        - Follow trend for direction
        """
        # Check if we should HOLD
        if not validation["valid"]:
            # Entry conditions not met - HOLD
            return {
                "action": "HOLD",
                "entry_type": "none",
                "pending_type": "none",
                "reason": validation["reason"]
            }

        # Entry conditions valid - make directional decision
        trend = context.get("trend_state", "ranging")
        confidence = validation["confidence"]

        # Scalper prefers action - convert ranging to bias
        if trend == "ranging":
            # In ranging market, scalper waits for clearer signal
            # But scalper MUST prefer action, so use momentum
            momentum = trend_analysis.get("momentum", 0.5)
            if momentum > 0.6:
                trend = "bullish"
            elif momentum < 0.4:
                trend = "bearish"
            else:
                # Truly ranging - still HOLD (but with different reason)
                return {
                    "action": "HOLD",
                    "entry_type": "none",
                    "pending_type": "none",
                    "reason": "Ranging market with no clear bias - waiting for direction"
                }

        # Map trend to action
        if trend == "bullish":
            action = "BUY"
            reason = f"Bullish trend detected (confidence: {confidence:.2f})"
        elif trend == "bearish":
            action = "SELL"
            reason = f"Bearish trend detected (confidence: {confidence:.2f})"
        else:
            # Fallback to HOLD
            action = "HOLD"
            reason = "Insufficient directional signal"

        # Scalper uses market orders (fast execution)
        entry_type = "market" if action != "HOLD" else "none"
        pending_type = "none"  # Scalper doesn't use pending orders

        return {
            "action": action,
            "entry_type": entry_type,
            "pending_type": pending_type,
            "reason": reason
        }

    def _calculate_final_confidence(
        self,
        validation_confidence: float,
        trend_strength: float,
        decision: Dict[str, Any]
    ) -> float:
        """
        Calculate final confidence score.

        Args:
            validation_confidence: Confidence from validation
            trend_strength: Trend strength from analysis
            decision: Decision dict

        Returns:
            Final confidence (0-1)

        Note:
            If HOLD, confidence is low.
            If action, combine validation and trend confidence.
        """
        if decision["action"] == "HOLD":
            # HOLD has low confidence
            return 0.3

        # Combine validation confidence and trend strength
        final_confidence = (validation_confidence * 0.6) + (trend_strength * 0.4)
        return min(max(final_confidence, 0.0), 1.0)

    def _validate_schema(self, decision: Dict[str, Any]):
        """
        Validate decision schema matches required format.

        Args:
            decision: Decision dict to validate

        Raises:
            ValueError: If schema invalid

        Required Keys:
        - strategy: str
        - symbol: str
        - decision: "BUY" | "SELL" | "HOLD"
        - confidence: float (0-1)
        - entry_type: str
        - pending_type: str
        - reason: str
        - context: dict with timeframe, volatility_state, trend_state
        """
        required_keys = [
            "strategy", "symbol", "decision", "confidence",
            "entry_type", "pending_type", "reason", "context"
        ]

        for key in required_keys:
            if key not in decision:
                raise ValueError(f"Missing required key: {key}")

        # Validate decision value
        valid_decisions = ["BUY", "SELL", "HOLD"]
        if decision["decision"] not in valid_decisions:
            raise ValueError(f"Invalid decision: {decision['decision']}")

        # Validate confidence range
        conf = decision["confidence"]
        if not isinstance(conf, (int, float)) or conf < 0.0 or conf > 1.0:
            raise ValueError(f"Invalid confidence: {conf}")

        # Validate context
        context = decision["context"]
        required_context = ["timeframe", "volatility_state", "trend_state"]
        for key in required_context:
            if key not in context:
                raise ValueError(f"Missing context key: {key}")

        # Validate HOLD constraints
        if decision["decision"] == "HOLD":
            if decision["entry_type"] != "none":
                raise ValueError("HOLD decisions must have entry_type='none'")
            if decision["pending_type"] != "none":
                raise ValueError("HOLD decisions must have pending_type='none'")
