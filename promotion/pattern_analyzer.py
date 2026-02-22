"""
Pattern Analyzer - Phase 9 Implementation

Responsibilities:
- Group backtest trades by context signature
- Compute statistics per pattern
- Calculate consistency across time segments
- Generate confidence scores

This module analyzes patterns in backtest knowledge for promotion.

PHASE 9 CONSTRAINTS:
- NO modification of backtest data
- NO LLM calls
- Pure statistical analysis
- Deterministic output
"""

import logging
from typing import Dict, Any, List, Tuple
from datetime import datetime
from collections import defaultdict
import hashlib
import json


logger = logging.getLogger(__name__)


class PatternAnalyzer:
    """
    Analyzer for trading patterns in backtest knowledge.

    Groups trades by context signature and computes statistics
    to determine which patterns are robust enough for promotion.
    """

    def __init__(self, pair: str):
        """
        Initialize pattern analyzer.

        Args:
            pair: Trading pair symbol
        """
        self.pair = pair

    def analyze_patterns(
        self,
        backtest_entries: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Analyze backtest entries to find patterns.

        Args:
            backtest_entries: List of backtest knowledge entries

        Returns:
            Dict mapping pattern signatures to pattern statistics:
            {
                "pattern_signature": {
                    "symbol": "XAUUSDm",
                    "strategy": "scalper",
                    "context_signature": {...},
                    "trades": [...],
                    "stats": {...},
                    "time_segments": {...}
                }
            }

        Note:
            Groups entries by context_signature.
            Computes statistics per group.
            Checks consistency across time segments.
        """
        # Group by context signature
        patterns = self._group_by_context(backtest_entries)

        # Compute statistics for each pattern
        for signature, pattern in patterns.items():
            pattern["stats"] = self._compute_stats(pattern["trades"])
            pattern["time_segments"] = self._analyze_time_segments(
                pattern["trades"]
            )

        return patterns

    def _group_by_context(
        self,
        entries: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Group entries by context signature.

        Args:
            entries: Backtest knowledge entries

        Returns:
            Dict mapping signatures to pattern data

        Note:
            Context signature = (strategy, timeframe, volatility, trend)
        """
        patterns = {}

        for entry in entries:
            # Extract context
            context = entry.get("context", {})
            strategy = entry.get("strategy", "unknown")

            # Create signature
            signature = self._create_signature(strategy, context)

            # Initialize pattern if needed
            if signature not in patterns:
                patterns[signature] = {
                    "symbol": entry.get("symbol", self.pair),
                    "strategy": strategy,
                    "context_signature": {
                        "timeframe": context.get("timeframe", "unknown"),
                        "volatility_state": context.get("volatility_state", "unknown"),
                        "trend_state": context.get("trend_state", "unknown")
                    },
                    "trades": []
                }

            # Add trade to pattern
            patterns[signature]["trades"].append(entry)

        return patterns

    def _create_signature(self, strategy: str, context: Dict[str, Any]) -> str:
        """
        Create unique signature for a pattern.

        Args:
            strategy: Strategy name
            context: Trade context dict

        Returns:
            Signature string (hash)

        Note:
            Signature is deterministic for same context.
            Used for idempotent promotion (no duplicates).
        """
        # Extract key fields
        timeframe = context.get("timeframe", "unknown")
        volatility = context.get("volatility_state", "unknown")
        trend = context.get("trend_state", "unknown")

        # Create signature string
        sig_str = f"{strategy}|{timeframe}|{volatility}|{trend}"

        # Hash for consistency
        sig_hash = hashlib.md5(sig_str.encode()).hexdigest()[:8]

        return f"{sig_str}_{sig_hash}"

    def _compute_stats(self, trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compute statistics for a pattern.

        Args:
            trades: List of trades in pattern

        Returns:
            Statistics dict with structure:
            {
                "sample_size": int,
                "win_rate": float,
                "avg_pnl": float,
                "total_pnl": float,
                "max_drawdown": float,
                "max_consecutive_losses": int,
                "profit_factor": float
            }
        """
        if not trades:
            return {
                "sample_size": 0,
                "win_rate": 0.0,
                "avg_pnl": 0.0,
                "total_pnl": 0.0,
                "max_drawdown": 0.0,
                "max_consecutive_losses": 0,
                "profit_factor": 0.0
            }

        # Filter only resolved trades (have result)
        resolved = [t for t in trades if t.get("result") in ["win", "loss", "breakeven"]]

        if not resolved:
            return {
                "sample_size": 0,
                "win_rate": 0.0,
                "avg_pnl": 0.0,
                "total_pnl": 0.0,
                "max_drawdown": 0.0,
                "max_consecutive_losses": 0,
                "profit_factor": 0.0
            }

        sample_size = len(resolved)

        # Count wins/losses
        wins = [t for t in resolved if t["result"] == "win"]
        losses = [t for t in resolved if t["result"] == "loss"]

        win_rate = len(wins) / sample_size if sample_size > 0 else 0.0

        # Calculate PnL stats
        total_pnl = sum(t.get("pnl", 0.0) for t in resolved)
        avg_pnl = total_pnl / sample_size if sample_size > 0 else 0.0

        gross_profit = sum(t.get("pnl", 0.0) for t in wins)
        gross_loss = abs(sum(t.get("pnl", 0.0) for t in losses))

        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0.0

        # Calculate drawdown
        cumulative = 0.0
        peak = 0.0
        max_drawdown = 0.0

        for trade in resolved:
            pnl = trade.get("pnl", 0.0)
            cumulative += pnl

            if cumulative > peak:
                peak = cumulative

            drawdown = peak - cumulative
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        # Calculate max consecutive losses
        max_consecutive_losses = 0
        current_streak = 0

        for trade in resolved:
            if trade["result"] == "loss":
                current_streak += 1
                max_consecutive_losses = max(max_consecutive_losses, current_streak)
            else:
                current_streak = 0

        return {
            "sample_size": sample_size,
            "win_rate": win_rate,
            "avg_pnl": avg_pnl,
            "total_pnl": total_pnl,
            "max_drawdown": max_drawdown,
            "max_consecutive_losses": max_consecutive_losses,
            "profit_factor": profit_factor,
            "gross_profit": gross_profit,
            "gross_loss": gross_loss
        }

    def _analyze_time_segments(
        self,
        trades: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze pattern consistency across time segments.

        Args:
            trades: List of trades in pattern

        Returns:
            Time segment analysis dict with structure:
            {
                "segments": [
                    {"segment_id": 0, "win_rate": float, "sample_size": int},
                    ...
                ],
                "consistency_score": float,
                "min_win_rate": float,
                "max_win_rate": float
            }

        Note:
            Divides trades into N time segments.
            Checks if pattern performs consistently across segments.
        """
        # Filter resolved trades
        resolved = [t for t in trades if t.get("result") in ["win", "loss", "breakeven"]]

        if not resolved:
            return {
                "segments": [],
                "consistency_score": 0.0,
                "min_win_rate": 0.0,
                "max_win_rate": 0.0
            }

        # Sort by timestamp
        sorted_trades = sorted(
            resolved,
            key=lambda t: t.get("timestamp", "")
        )

        # Divide into segments
        num_segments = 3  # TODO: Make configurable
        segment_size = max(1, len(sorted_trades) // num_segments)

        segments = []

        for i in range(num_segments):
            start_idx = i * segment_size
            end_idx = start_idx + segment_size if i < num_segments - 1 else len(sorted_trades)

            segment_trades = sorted_trades[start_idx:end_idx]

            if not segment_trades:
                continue

            # Compute segment stats
            wins = sum(1 for t in segment_trades if t["result"] == "win")
            win_rate = wins / len(segment_trades)

            segments.append({
                "segment_id": i,
                "win_rate": win_rate,
                "sample_size": len(segment_trades)
            })

        # Calculate consistency score
        if segments:
            win_rates = [s["win_rate"] for s in segments]
            min_win_rate = min(win_rates)
            max_win_rate = max(win_rates)

            # Consistency = how close win rates are across segments
            # Range from 0 (inconsistent) to 1 (perfectly consistent)
            range_size = max_win_rate - min_win_rate
            consistency_score = max(0.0, 1.0 - range_size)
        else:
            consistency_score = 0.0
            min_win_rate = 0.0
            max_win_rate = 0.0

        return {
            "segments": segments,
            "consistency_score": consistency_score,
            "min_win_rate": min_win_rate,
            "max_win_rate": max_win_rate
        }

    def calculate_confidence_score(
        self,
        pattern: Dict[str, Any],
        config: Any  # PromotionConfig
    ) -> float:
        """
        Calculate overall confidence score for a pattern.

        Args:
            pattern: Pattern dict with stats and time_segments
            config: PromotionConfig with thresholds

        Returns:
            Confidence score in [0.0, 1.0]

        Note:
            Combines multiple factors:
            - Sample size (more is better)
            - Win rate (higher is better)
            - Avg PnL (positive is better)
            - Consistency (more consistent is better)
            - Drawdown (lower is better)
        """
        stats = pattern.get("stats", {})
        segments = pattern.get("time_segments", {})

        # Extract metrics
        sample_size = stats.get("sample_size", 0)
        win_rate = stats.get("win_rate", 0.0)
        avg_pnl = stats.get("avg_pnl", 0.0)
        max_drawdown = stats.get("max_drawdown", 0.0)
        consistency_score = segments.get("consistency_score", 0.0)
        profit_factor = stats.get("profit_factor", 0.0)

        # Normalize each factor to [0, 1]
        # 1. Sample size: saturates at min_sample_size * 3
        min_samples = config.min_sample_size
        sample_score = min(1.0, sample_size / (min_samples * 3))

        # 2. Win rate: already in [0, 1]
        win_rate_score = win_rate

        # 3. Avg PnL: normalize by threshold (clamped)
        # Positive PnL gets score, negative gets 0
        pnl_threshold = max(1.0, config.min_avg_pnl)
        pnl_score = max(0.0, min(1.0, avg_pnl / pnl_threshold))

        # 4. Consistency: already in [0, 1]
        consistency_score_value = consistency_score

        # 5. Drawdown: invert (lower is better)
        # Normalize by max_drawdown_pct
        max_dd_pct = config.max_drawdown_pct
        if max_dd_pct > 0:
            drawdown_penalty = min(1.0, max_drawdown / max_dd_pct)
            drawdown_score = 1.0 - drawdown_penalty
        else:
            drawdown_score = 1.0 if max_drawdown == 0 else 0.0

        # 6. Profit factor: normalize (1.0 = breakeven, 2.0 = good)
        profit_factor_score = min(1.0, (profit_factor - 1.0) / 2.0)
        profit_factor_score = max(0.0, profit_factor_score)

        # Weighted average (adjust weights as needed)
        weights = {
            "sample": 0.15,
            "win_rate": 0.25,
            "pnl": 0.20,
            "consistency": 0.20,
            "drawdown": 0.10,
            "profit_factor": 0.10
        }

        confidence = (
            weights["sample"] * sample_score +
            weights["win_rate"] * win_rate_score +
            weights["pnl"] * pnl_score +
            weights["consistency"] * consistency_score_value +
            weights["drawdown"] * drawdown_score +
            weights["profit_factor"] * profit_factor_score
        )

        return max(0.0, min(1.0, confidence))
