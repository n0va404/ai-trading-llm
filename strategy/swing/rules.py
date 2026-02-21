"""
Swing Strategy Rules - Phase 4 Implementation

Responsibilities:
- Define swing trading-specific trading rules
- Validate trade conditions for swing trading
- Calculate entry/exit parameters for swing trading
- Pure signal logic (no side effects)

This module contains ONLY rule definitions - no execution logic.
Rules are evaluated by the decision module.

PHASE 4 CONSTRAINTS:
- No order placement
- No position tracking
- No account access
- No LLM calls
- Deterministic output for same input
"""

from typing import Dict, Any, Optional, List
import logging


logger = logging.getLogger(__name__)


class SwingRules:
    """
    Swing trading strategy rules definition.

    Swing trading is medium-term trading with:
    - Longer holding periods (hours to days)
    - Larger profit targets
    - Wider stop losses
    - Trend-following approach
    - HOLD is acceptable and expected
    """

    # Swing-specific thresholds
    DEFAULT_MIN_TRENDBARS = 3  # Minimum bars to confirm trend
    DEFAULT_MIN_STRENGTH = 0.3  # Minimum trend strength
    DEFAULT_MAX_SPREAD_POINTS = 30  # Maximum spread for entry

    def __init__(
        self,
        pair: str,
        min_trendbars: Optional[int] = None,
        min_strength: Optional[float] = None,
        max_spread: Optional[float] = None
    ):
        """
        Initialize swing rules for a specific pair.

        Args:
            pair: Trading pair symbol
            min_trendbars: Minimum bars to confirm trend (default: 3)
            min_strength: Minimum trend strength (default: 0.3)
            max_spread: Maximum spread in points (default: 30)

        Note:
            No external calls on init.
            No state persistence.
        """
        self.pair = pair
        self.min_trendbars = min_trendbars or self.DEFAULT_MIN_TRENDBARS
        self.min_strength = min_strength or self.DEFAULT_MIN_STRENGTH
        self.max_spread = max_spread or self.DEFAULT_MAX_SPREAD_POINTS

    def validate_entry(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate if entry conditions are met for swing trading.

        Args:
            market_data: Market data dict containing:
                - bid: Current bid price
                - ask: Current ask price
                - spread: Spread in points
                - ohlc_data: OHLC history for trend analysis

        Returns:
            Validation result containing:
            - valid: Boolean indicating if conditions met
            - reason: Human-readable reason
            - confidence: Confidence score (0-1)
            - signals: Dict of signal components

        Swing Entry Logic:
        1. Spread must be reasonable
        2. Clear trend must exist
        3. Trend must have sufficient strength
        4. Market structure must be valid

        Note:
            Pure function - no side effects.
            Deterministic output for same input.
        """
        # Extract basic data
        bid = market_data.get("bid", 0)
        ask = market_data.get("ask", 0)
        spread = market_data.get("spread", 0)

        # Check spread
        spread_ok = self._check_spread(spread)

        # Analyze trend
        ohlc_data = market_data.get("ohlc_data", [])
        trend_analysis = self._analyze_trend(ohlc_data)

        # Validate trend
        trend_ok = self._validate_trend(trend_analysis)

        # Check structure
        structure_ok = self._check_structure(ohlc_data)

        # Overall validity
        valid = spread_ok and trend_ok and structure_ok

        # Build reason
        reasons = []
        if not spread_ok:
            reasons.append(f"Spread too high: {spread} > {self.max_spread}")
        if not trend_ok:
            reasons.append(f"No clear trend: {trend_analysis.get('trend', 'unknown')}")
        if not structure_ok:
            reasons.append("Market structure invalid (choppy)")

        if valid:
            trend = trend_analysis.get("trend", "unknown")
            reasons.append(f"Clear {trend} trend established (swing setup valid)")

        # Calculate confidence
        confidence = self._calculate_confidence(
            spread_ok=spread_ok,
            trend_ok=trend_ok,
            structure_ok=structure_ok,
            trend_strength=trend_analysis.get("strength", 0)
        )

        return {
            "valid": valid,
            "reason": "; ".join(reasons),
            "confidence": confidence,
            "signals": {
                "spread_ok": spread_ok,
                "trend_ok": trend_ok,
                "structure_ok": structure_ok,
                "trend": trend_analysis.get("trend", "unknown"),
                "trend_strength": trend_analysis.get("strength", 0)
            }
        }

    def _check_spread(self, spread: float) -> bool:
        """
        Check if spread is within tolerance.

        Args:
            spread: Spread in points

        Returns:
            True if spread acceptable

        Note:
            Swing tolerates higher spreads than scalper.
        """
        return spread <= self.max_spread

    def _analyze_trend(self, ohlc_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze trend from OHLC data.

        Args:
            ohlc_data: List of OHLC candles (most recent first)

        Returns:
            Trend analysis containing:
            - trend: "bullish", "bearish", or "ranging"
            - strength: Trend strength (0-1)
            - duration: Number of bars confirming trend
        """
        if not ohlc_data or len(ohlc_data) < self.min_trendbars:
            return {
                "trend": "ranging",
                "strength": 0.0,
                "duration": 0
            }

        # Use recent candles for trend detection
        recent = ohlc_data[:min(20, len(ohlc_data))]

        # Calculate moving averages
        closes = [candle.get("close", 0) for candle in recent]

        if len(closes) < self.min_trendbars:
            return {
                "trend": "ranging",
                "strength": 0.0,
                "duration": 0
            }

        # Short MA (fast)
        short_ma = sum(closes[:5]) / 5 if len(closes) >= 5 else closes[0]

        # Long MA (slow)
        long_ma = sum(closes) / len(closes)

        # Determine trend based on MA position
        if short_ma > long_ma * 1.002:
            trend = "bullish"
            # Strength based on MA separation
            strength = min((short_ma / long_ma - 1.0) * 500, 1.0)
        elif short_ma < long_ma * 0.998:
            trend = "bearish"
            strength = min((long_ma / short_ma - 1.0) * 500, 1.0)
        else:
            trend = "ranging"
            strength = 0.0

        # Calculate trend duration (consecutive bars in same direction)
        duration = self._calculate_trend_duration(closes, trend)

        return {
            "trend": trend,
            "strength": max(strength, 0.0),
            "duration": duration
        }

    def _calculate_trend_duration(self, closes: List[float], trend: str) -> int:
        """
        Calculate how many consecutive bars support the trend.

        Args:
            closes: List of close prices
            trend: Current trend direction

        Returns:
            Number of bars confirming trend
        """
        if len(closes) < 2:
            return 0

        duration = 0
        for i in range(len(closes) - 1):
            if trend == "bullish":
                if closes[i] >= closes[i + 1]:
                    duration += 1
                else:
                    break
            elif trend == "bearish":
                if closes[i] <= closes[i + 1]:
                    duration += 1
                else:
                    break
            else:
                break

        return duration

    def _validate_trend(self, trend_analysis: Dict[str, Any]) -> bool:
        """
        Validate if trend is strong enough for swing entry.

        Args:
            trend_analysis: Trend analysis result

        Returns:
            True if trend valid for swing trading

        Swing Trend Requirements:
        - Not ranging
        - Strength above minimum threshold
        - Sufficient duration
        """
        trend = trend_analysis.get("trend", "ranging")
        strength = trend_analysis.get("strength", 0)
        duration = trend_analysis.get("duration", 0)

        # Must be directional (not ranging)
        if trend == "ranging":
            return False

        # Must have minimum strength
        if strength < self.min_strength:
            return False

        # Must have minimum duration
        if duration < self.min_trendbars:
            return False

        return True

    def _check_structure(self, ohlc_data: List[Dict[str, Any]]) -> bool:
        """
        Check if market structure is valid (not too choppy).

        Args:
            ohlc_data: List of OHLC candles

        Returns:
            True if structure is valid

        Structure Check:
        - Not too many overlapping candles
        - Reasonable price ranges
        """
        if not ohlc_data or len(ohlc_data) < 5:
            return True  # Can't determine, assume OK

        recent = ohlc_data[:min(10, len(ohlc_data))]

        # Check for choppy market (overlapping ranges)
        overlaps = 0
        for i in range(len(recent) - 1):
            curr_high = recent[i].get("high", 0)
            curr_low = recent[i].get("low", 0)
            next_high = recent[i + 1].get("high", 0)
            next_low = recent[i + 1].get("low", 0)

            # Check if candles overlap significantly
            if (curr_high >= next_low) and (curr_low <= next_high):
                overlaps += 1

        # If too many overlaps, market is choppy
        overlap_ratio = overlaps / len(recent)
        return overlap_ratio < 0.7  # Allow some overlap, but not excessive

    def _calculate_confidence(
        self,
        spread_ok: bool,
        trend_ok: bool,
        structure_ok: bool,
        trend_strength: float
    ) -> float:
        """
        Calculate confidence score for entry signal.

        Args:
            spread_ok: Is spread within tolerance
            trend_ok: Is trend valid
            structure_ok: Is market structure valid
            trend_strength: Trend strength (0-1)

        Returns:
            Confidence score (0-1)

        Confidence Logic:
        - Base: 0.3
        - +0.3 if spread OK
        - +0.2 if trend OK
        - +0.2 if structure OK
        - Scaled by trend strength
        """
        confidence = 0.3

        if spread_ok:
            confidence += 0.3

        if trend_ok:
            confidence += 0.2 * trend_strength

        if structure_ok:
            confidence += 0.2

        return min(max(confidence, 0.0), 1.0)

    def calculate_exit(self, position: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate exit parameters for swing position.

        Args:
            position: Position information containing:
                - entry_price: Entry price
                - direction: "BUY" or "SELL"
                - current_price: Current market price

        Returns:
            Exit parameters containing:
            - take_profit: TP price level
            - stop_loss: SL price level
            - risk_reward: Risk/reward ratio

        Swing Exit Logic:
        - Wider stops than scalper
        - Larger targets (multi-day holds)
        - Risk/reward >= 2.0

        Note:
            Pure calculation - no side effects.
        """
        entry_price = position.get("entry_price", 0)
        direction = position.get("direction", "BUY")
        current_price = position.get("current_price", entry_price)

        # Default pip value
        pip_size = 0.01 if "USD" in self.pair else 0.0001

        # Swing targets (in pips)
        # Larger than scalper (longer holds)
        if direction == "BUY":
            tp_price = entry_price + (50 * pip_size)  # 50 pips target
            sl_price = entry_price - (25 * pip_size)   # 25 pips stop
        else:  # SELL
            tp_price = entry_price - (50 * pip_size)  # 50 pips target
            sl_price = entry_price + (25 * pip_size)   # 25 pips stop

        # Calculate risk/reward
        if direction == "BUY":
            risk = entry_price - sl_price
            reward = tp_price - entry_price
        else:
            risk = sl_price - entry_price
            reward = entry_price - tp_price

        risk_reward = abs(reward / risk) if risk > 0 else 2.0

        return {
            "take_profit": tp_price,
            "stop_loss": sl_price,
            "risk_reward": risk_reward,
            "target_pips": 50,
            "stop_pips": 25
        }

    def detect_support_resistance(
        self,
        ohlc_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Detect support and resistance levels.

        Args:
            ohlc_data: List of OHLC candles

        Returns:
            Dict with:
            - support: Support price level
            - resistance: Resistance price level
            - strength: Level strength (0-1)

        Note:
            Simplified implementation for Phase 4.
            Will be enhanced in later phases.
        """
        if not ohlc_data or len(ohlc_data) < 10:
            return {
                "support": 0,
                "resistance": 0,
                "strength": 0
            }

        # Use recent candles
        recent = ohlc_data[:min(50, len(ohlc_data))]

        # Find recent lows (support) and highs (resistance)
        lows = [candle.get("low", 0) for candle in recent]
        highs = [candle.get("high", 0) for candle in recent]

        # Simple approach: min of lows, max of highs
        support = min(lows)
        resistance = max(highs)

        # Strength based on how many times level was tested
        # (simplified - just use proximity to current price)
        current_price = ohlc_data[0].get("close", 0)

        dist_to_support = abs(current_price - support) / current_price
        dist_to_resistance = abs(resistance - current_price) / current_price

        # Closer levels are stronger
        strength = 1.0 - min(dist_to_support, dist_to_resistance) * 100

        return {
            "support": support,
            "resistance": resistance,
            "strength": max(strength, 0.0)
        }
