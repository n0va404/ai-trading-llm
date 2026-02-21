"""
Swing Strategy Decision - Phase 4 Implementation

Responsibilities:
- Make swing trading decisions
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

from typing import Dict, Any, Optional, List
import logging
from strategy.swing.rules import SwingRules


logger = logging.getLogger(__name__)


def swing_decision_job():
    """
    Job function to evaluate swing opportunities.

    This is called by the scheduler (Phase 2) every swing_decision_interval.

    Phase 4 Implementation:
    - Loads enabled pairs
    - For each pair: evaluate_decision() with market data
    - Produces structured decisions

    Note:
        In Phase 4, this is a placeholder.
        Actual integration with market data layer will be added in future phases.

    TODO: Load enabled pairs from config/pairs.yaml
    TODO: Create SwingDecisionEngine for each pair
    TODO: Fetch market data from Phase 3 cache
    TODO: Store decisions for execution layer
    """
    # TODO: Implement actual job logic
    # This will be implemented when we have:
    # 1. Config loading mechanism
    # 2. Market data access (Phase 3)
    # 3. Decision storage mechanism

    raise NotImplementedError("swing_decision_job not yet implemented - needs market data integration")


class SwingDecisionEngine:
    """
    Decision engine for swing strategy.

    Produces deterministic trading decisions based on rules.
    Each pair has its own decision engine for isolation.

    NO LLM - Pure rule-based decisions in Phase 4.
    """

    def __init__(self, pair: str, rules: Optional[SwingRules] = None):
        """
        Initialize swing decision engine for a specific pair.

        Args:
            pair: Trading pair symbol
            rules: Optional SwingRules instance (creates default if None)

        Note:
            No external calls on init.
            No state persistence.
        """
        self.pair = pair
        self.rules = rules or SwingRules(pair)

    def evaluate(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate and produce swing trading decision.

        Args:
            market_data: Market data dict containing:
                - bid: Current bid price
                - ask: Current ask price
                - spread: Spread in points
                - ohlc_data: OHLC history for trend analysis

        Returns:
            Decision dict with EXACT schema:
            {
                "strategy": "swing",
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

        Swing Decision Logic:
        1. Validate entry conditions via rules
        2. Analyze trend from OHLC data
        3. Check support/resistance
        4. Produce decision (HOLD is acceptable)
        5. Calculate confidence
        6. Map trend to BUY/SELL/HOLD

        Note:
            Pure function - no side effects.
            Deterministic output for same input.
            No LLM calls in Phase 4.
        """
        # Validate entry conditions
        validation = self.rules.validate_entry(market_data)

        # Analyze trend
        ohlc_data = market_data.get("ohlc_data", [])
        trend_analysis = self._analyze_trend(ohlc_data)

        # Check support/resistance
        sr_levels = self.rules.detect_support_resistance(ohlc_data)

        # Determine context
        context = self._build_context(market_data, trend_analysis)

        # Make decision
        decision = self._make_decision(
            validation,
            trend_analysis,
            sr_levels,
            context
        )

        # Calculate final confidence
        confidence = self._calculate_final_confidence(
            validation["confidence"],
            trend_analysis.get("strength", 0),
            decision
        )

        # Build result
        result = {
            "strategy": "swing",
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

    def _analyze_trend(self, ohlc_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze trend from OHLC data.

        Args:
            ohlc_data: List of OHLC candles

        Returns:
            Trend analysis dict

        Note:
            Swing uses longer-term trend analysis.
        """
        if not ohlc_data or len(ohlc_data) < 3:
            return {
                "trend": "ranging",
                "strength": 0.0,
                "momentum": 0.5
            }

        # Use more candles for swing (longer perspective)
        recent = ohlc_data[:min(50, len(ohlc_data))]

        # Calculate moving averages (swing uses longer MAs)
        closes = [candle.get("close", 0) for candle in recent]

        if len(closes) < 10:
            return {
                "trend": "ranging",
                "strength": 0.0,
                "momentum": 0.5
            }

        # Multiple timeframes for confirmation
        ma_fast = sum(closes[:10]) / 10  # 10-bar MA
        ma_slow = sum(closes[:30]) / 30 if len(closes) >= 30 else sum(closes) / len(closes)  # 30-bar MA

        # Determine trend
        if ma_fast > ma_slow * 1.005:
            trend = "bullish"
            strength = min((ma_fast / ma_slow - 1.0) * 200, 1.0)
        elif ma_fast < ma_slow * 0.995:
            trend = "bearish"
            strength = min((ma_slow / ma_fast - 1.0) * 200, 1.0)
        else:
            trend = "ranging"
            strength = 0.0

        # Calculate momentum (swing uses longer-term momentum)
        if len(closes) >= 20:
            recent_avg = sum(closes[:10]) / 10
            older_avg = sum(closes[10:20]) / 10
            momentum = (recent_avg - older_avg) / older_avg if older_avg > 0 else 0
            momentum = max(min(momentum * 50, 1.0), -1.0)
            momentum = (momentum + 1) / 2  # Convert to 0-1
        else:
            momentum = 0.5

        return {
            "trend": trend,
            "strength": max(strength, 0.0),
            "momentum": momentum
        }

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
            Swing uses M15-H1 timeframes (medium-term decisions).
        """
        # Determine volatility state
        momentum = trend_analysis.get("momentum", 0.5)
        if momentum < 0.3:
            volatility_state = "low"
        elif momentum > 0.7:
            volatility_state = "high"
        else:
            volatility_state = "normal"

        # Get trend state from analysis
        trend_state = trend_analysis.get("trend", "ranging")

        # Swing uses medium timeframes
        timeframe = "H1"  # Could be configurable

        return {
            "timeframe": timeframe,
            "volatility_state": volatility_state,
            "trend_state": trend_state
        }

    def _make_decision(
        self,
        validation: Dict[str, Any],
        trend_analysis: Dict[str, Any],
        sr_levels: Dict[str, Any],
        context: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Make trading decision based on validation and trend.

        Args:
            validation: Entry validation result
            trend_analysis: Trend analysis result
            sr_levels: Support/resistance levels
            context: Decision context

        Returns:
            Decision dict with action, entry_type, pending_type, reason

        Swing Decision Rules:
        - HOLD is acceptable and expected
        - Only enter on clear trends
        - Consider support/resistance
        - Prefer patience over action

        Note:
            Swing is more conservative than scalper.
        """
        # Check if we should HOLD
        if not validation["valid"]:
            # Entry conditions not met - HOLD (acceptable for swing)
            return {
                "action": "HOLD",
                "entry_type": "none",
                "pending_type": "none",
                "reason": validation["reason"]
            }

        # Entry conditions valid - evaluate trend
        trend = context.get("trend_state", "ranging")
        confidence = validation["confidence"]
        strength = trend_analysis.get("strength", 0)

        # Swing requires clear trend - ranging means HOLD
        if trend == "ranging":
            return {
                "action": "HOLD",
                "entry_type": "none",
                "pending_type": "none",
                "reason": "No clear trend - swing waits for direction"
            }

        # Swing requires minimum strength
        if strength < 0.4:
            return {
                "action": "HOLD",
                "entry_type": "none",
                "pending_type": "none",
                "reason": f"Trend too weak (strength: {strength:.2f}) - waiting for confirmation"
            }

        # Map trend to action
        if trend == "bullish":
            action = "BUY"
            reason = f"Bullish trend confirmed (strength: {strength:.2f}, confidence: {confidence:.2f})"
        elif trend == "bearish":
            action = "SELL"
            reason = f"Bearish trend confirmed (strength: {strength:.2f}, confidence: {confidence:.2f})"
        else:
            # Fallback to HOLD
            action = "HOLD"
            reason = "Insufficient trend confirmation"

        # Swing can use pending orders for better entries
        # For now, use market orders (will be enhanced in Phase 5)
        entry_type = "market" if action != "HOLD" else "none"
        pending_type = "none"

        # TODO: In Phase 5, add logic for pending orders at S/R levels

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
            Swing requires higher confidence than scalper.
            HOLD has medium confidence (acceptable).
        """
        if decision["action"] == "HOLD":
            # HOLD is acceptable for swing - medium confidence
            return 0.5

        # Combine validation confidence and trend strength
        # Swing weights trend strength more heavily
        final_confidence = (validation_confidence * 0.4) + (trend_strength * 0.6)
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
