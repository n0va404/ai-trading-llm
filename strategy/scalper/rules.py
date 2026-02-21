"""
Scalper Strategy Rules - Phase 4 Implementation

Responsibilities:
- Define scalping-specific trading rules
- Validate trade conditions for scalper
- Calculate entry/exit parameters for scalping
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


class ScalperRules:
    """
    Scalping strategy rules definition.

    Scalping is high-frequency trading with:
    - Short holding periods (seconds to minutes)
    - Small profit targets
    - Tight stop losses
    - High volume leverage
    - MUST prefer action over HOLD
    """

    # Scalper-specific thresholds
    DEFAULT_MAX_SPREAD_POINTS = 50  # Maximum spread for entry
    DEFAULT_MIN_VOLATILITY = 0.0001  # Minimum volatility for valid setup
    DEFAULT_MAX_VOLATILITY = 0.01    # Maximum volatility (anomaly detection)

    def __init__(
        self,
        pair: str,
        max_spread: Optional[float] = None,
        min_volatility: Optional[float] = None,
        max_volatility: Optional[float] = None
    ):
        """
        Initialize scalper rules for a specific pair.

        Args:
            pair: Trading pair symbol
            max_spread: Maximum spread in points (default: 50)
            min_volatility: Minimum volatility for setup (default: 0.0001)
            max_volatility: Maximum volatility before anomaly (default: 0.01)

        Note:
            No external calls on init.
            No state persistence.
        """
        self.pair = pair
        self.max_spread = max_spread or self.DEFAULT_MAX_SPREAD_POINTS
        self.min_volatility = min_volatility or self.DEFAULT_MIN_VOLATILITY
        self.max_volatility = max_volatility or self.DEFAULT_MAX_VOLATILITY

    def validate_entry(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate if entry conditions are met for scalping.

        Args:
            market_data: Market data dict containing:
                - bid: Current bid price
                - ask: Current ask price
                - spread: Spread in points
                - Optional: ohlc_data for volatility calculation

        Returns:
            Validation result containing:
            - valid: Boolean indicating if conditions met
            - reason: Human-readable reason
            - confidence: Confidence score (0-1)
            - signals: Dict of signal components

        Scalper Entry Logic:
        1. Spread must be within tolerance
        2. Volatility must be within acceptable range
        3. Market must be active (no anomalies)

        Note:
            Pure function - no side effects.
            Deterministic output for same input.
        """
        # Extract basic data
        bid = market_data.get("bid", 0)
        ask = market_data.get("ask", 0)
        spread = market_data.get("spread", 0)

        # Calculate signals
        spread_ok = self._check_spread(spread)
        volatility_data = self._calculate_volatility(market_data)
        volatility_ok = (
            self.min_volatility <= volatility_data["volatility"] <= self.max_volatility
        )

        # Overall validity
        valid = spread_ok and volatility_ok

        # Build reason
        reasons = []
        if not spread_ok:
            reasons.append(f"Spread too high: {spread} > {self.max_spread}")
        if not volatility_ok:
            if volatility_data["volatility"] < self.min_volatility:
                reasons.append("Volatility too low (no movement)")
            else:
                reasons.append("Volatility anomaly (too high)")

        if valid:
            reasons.append("Market conditions favorable for scalping")

        # Calculate confidence
        confidence = self._calculate_confidence(
            spread_ok=spread_ok,
            volatility_ok=volatility_ok,
            spread=spread,
            volatility=volatility_data["volatility"]
        )

        return {
            "valid": valid,
            "reason": "; ".join(reasons),
            "confidence": confidence,
            "signals": {
                "spread_ok": spread_ok,
                "volatility_ok": volatility_ok,
                "volatility_value": volatility_data["volatility"],
                "spread_value": spread
            }
        }

    def _check_spread(self, spread: float) -> bool:
        """
        Check if spread is within tolerance.

        Args:
            spread: Spread in points

        Returns:
            True if spread acceptable
        """
        return spread <= self.max_spread

    def _calculate_volatility(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate market volatility from OHLC data.

        Args:
            market_data: Market data dict (may contain OHLC history)

        Returns:
            Dict with:
            - volatility: Calculated volatility (0-1 range)
            - method: Method used (range or default)

        Note:
            If OHLC data not available, returns default volatility.
        """
        # Check if OHLC data available
        ohlc_data = market_data.get("ohlc_data")
        if ohlc_data and len(ohlc_data) > 1:
            # Calculate volatility from recent candles
            # Use simple range-based calculation
            recent_candles = ohlc_data[:min(10, len(ohlc_data))]

            ranges = []
            for candle in recent_candles:
                high = candle.get("high", candle.get("close", 0))
                low = candle.get("low", candle.get("close", 0))
                if high > 0 and low > 0:
                    rng = (high - low) / low  # Normalized range
                    ranges.append(rng)

            if ranges:
                volatility = sum(ranges) / len(ranges)
                # Normalize to 0-1 range (typical forex range)
                volatility = min(volatility * 100, 1.0)
                return {"volatility": volatility, "method": "range"}

        # Default volatility if no OHLC data
        return {"volatility": 0.001, "method": "default"}

    def _calculate_confidence(
        self,
        spread_ok: bool,
        volatility_ok: bool,
        spread: float,
        volatility: float
    ) -> float:
        """
        Calculate confidence score for entry signal.

        Args:
            spread_ok: Is spread within tolerance
            volatility_ok: Is volatility within range
            spread: Current spread value
            volatility: Current volatility value

        Returns:
            Confidence score (0-1)

        Confidence Logic:
        - Base: 0.5
        - +0.3 if spread good
        - +0.2 if volatility optimal
        - Scaled by how good the values are
        """
        confidence = 0.5

        if spread_ok:
            # Bonus for good spread (up to 0.3)
            spread_ratio = 1.0 - (spread / self.max_spread)
            confidence += 0.3 * spread_ratio

        if volatility_ok:
            # Bonus for optimal volatility (up to 0.2)
            # Optimal is middle of range
            mid_vol = (self.min_volatility + self.max_volatility) / 2
            vol_diff = abs(volatility - mid_vol) / mid_vol
            confidence += 0.2 * (1.0 - min(vol_diff, 1.0))

        return min(max(confidence, 0.0), 1.0)

    def calculate_exit(self, position: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate exit parameters for scalping position.

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

        Scalper Exit Logic:
        - Tight stops (close to entry)
        - Small targets (quick profits)
        - Risk/reward >= 1.5

        Note:
            Pure calculation - no side effects.
        """
        entry_price = position.get("entry_price", 0)
        direction = position.get("direction", "BUY")
        current_price = position.get("current_price", entry_price)

        # Default pip value (will be pair-specific in production)
        pip_size = 0.01 if "USD" in self.pair else 0.0001

        # Scalper targets (in pips)
        # These are simplified - will be more sophisticated in production
        if direction == "BUY":
            tp_price = entry_price + (10 * pip_size)  # 10 pips target
            sl_price = entry_price - (7 * pip_size)   # 7 pips stop
        else:  # SELL
            tp_price = entry_price - (10 * pip_size)  # 10 pips target
            sl_price = entry_price + (7 * pip_size)   # 7 pips stop

        # Calculate risk/reward
        if direction == "BUY":
            risk = entry_price - sl_price
            reward = tp_price - entry_price
        else:
            risk = sl_price - entry_price
            reward = entry_price - tp_price

        risk_reward = abs(reward / risk) if risk > 0 else 1.5

        return {
            "take_profit": tp_price,
            "stop_loss": sl_price,
            "risk_reward": risk_reward,
            "target_pips": 10,
            "stop_pips": 7
        }

    def analyze_trend(self, ohlc_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze trend from OHLC data.

        Args:
            ohlc_data: List of OHLC candles (most recent first)

        Returns:
            Trend analysis containing:
            - trend: "bullish", "bearish", or "ranging"
            - strength: Trend strength (0-1)
            - momentum: Momentum indicator (0-1)

        Note:
            Simplified trend analysis for Phase 4.
            Will be enhanced in later phases.
        """
        if not ohlc_data or len(ohlc_data) < 3:
            return {
                "trend": "ranging",
                "strength": 0.0,
                "momentum": 0.5
            }

        # Use recent candles for trend detection
        recent = ohlc_data[:min(10, len(ohlc_data))]

        # Calculate simple moving average comparison
        closes = [candle.get("close", 0) for candle in recent]
        if len(closes) < 2:
            return {
                "trend": "ranging",
                "strength": 0.0,
                "momentum": 0.5
            }

        # Simple trend detection: current vs average
        avg_close = sum(closes) / len(closes)
        current_close = closes[0]

        # Calculate momentum (recent vs older)
        if len(closes) >= 5:
            recent_avg = sum(closes[:3]) / 3
            older_avg = sum(closes[3:6]) / 3 if len(closes) >= 6 else recent_avg
            momentum = (recent_avg - older_avg) / older_avg if older_avg > 0 else 0
            momentum = max(min(momentum * 100, 1.0), -1.0)  # Normalize to -1 to 1
            momentum = (momentum + 1) / 2  # Convert to 0-1
        else:
            momentum = 0.5

        # Determine trend
        if current_close > avg_close * 1.001:
            trend = "bullish"
            strength = min((current_close / avg_close - 1.0) * 1000, 1.0)
        elif current_close < avg_close * 0.999:
            trend = "bearish"
            strength = min((avg_close / current_close - 1.0) * 1000, 1.0)
        else:
            trend = "ranging"
            strength = 0.0

        return {
            "trend": trend,
            "strength": min(strength, 1.0),
            "momentum": momentum
        }
