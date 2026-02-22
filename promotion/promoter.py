"""
Knowledge Promoter - Phase 9 Implementation

Responsibilities:
- Read backtest knowledge from backtest.jsonl
- Analyze patterns using PatternAnalyzer
- Filter patterns by configurable thresholds
- Promote ONLY robust patterns to promoted.jsonl
- Idempotent (no duplicate promotions)
- Conservative by default

This module is the knowledge gatekeeper for the system.

PHASE 9 CONSTRAINTS:
- NO modification of backtest.jsonl
- NO modification of live.jsonl
- NO LLM calls
- NO strategy logic
- Conservative thresholds only
"""

import json
import logging
from typing import Dict, Any, List, Optional, Set
from pathlib import Path
from datetime import datetime
import threading

from promotion.pattern_analyzer import PatternAnalyzer
from promotion.config import PromotionConfig


logger = logging.getLogger(__name__)


class PromotionError(Exception):
    """Raised when promotion fails."""
    pass


class KnowledgePromoter:
    """
    Conservative knowledge promotion engine.

    Reads backtest knowledge, analyzes patterns, and promotes
    only robust patterns to the promoted knowledge set.

    Rules:
    - promoted.jsonl is append-only
    - No duplicate promotions (idempotent)
    - Conservative thresholds enforced
    - Clear audit trail
    """

    def __init__(
        self,
        pair: str,
        config: Optional[PromotionConfig] = None,
        pairs_dir: Optional[Path] = None
    ):
        """
        Initialize knowledge promoter.

        Args:
            pair: Trading pair symbol
            config: PromotionConfig (uses moderate defaults if None)
            pairs_dir: Base pairs directory path

        Note:
            No data loading on init.
            Call analyze() or promote() to execute.
        """
        self.pair = pair

        if pairs_dir is None:
            pairs_dir = Path(__file__).parent.parent / "pairs"

        self.pairs_dir = pairs_dir / pair
        self.config = config or PromotionConfig.moderate()

        # Paths
        self.backtest_path = self.pairs_dir / "knowledge" / "backtest.jsonl"
        self.promoted_path = self.pairs_dir / "knowledge" / "promoted.jsonl"

        # Thread safety
        self._lock = threading.Lock()

        # Track existing promotions for idempotency
        self._existing_signatures: Set[str] = set()

        # Analyzer
        self.analyzer = PatternAnalyzer(pair)

    def analyze(self) -> Dict[str, Any]:
        """
        Analyze backtest knowledge and find promotable patterns.

        Returns:
            Analysis results dict with structure:
            {
                "pair": str,
                "total_patterns": int,
                "promotable_patterns": int,
                "patterns": {
                    "signature": {
                        "stats": {...},
                        "confidence_score": float,
                        "meets_thresholds": bool
                    }
                }
            }

        Raises:
            FileNotFoundError: If backtest.jsonl doesn't exist
            PromotionError: If analysis fails

        Note:
            Does NOT write to promoted.jsonl.
            Call promote() to actually promote patterns.
        """
        # Load backtest knowledge
        backtest_entries = self._load_backtest_knowledge()

        if not backtest_entries:
            logger.warning(f"[PROMOTION] No backtest entries found for {self.pair}")
            return {
                "pair": self.pair,
                "total_patterns": 0,
                "promotable_patterns": 0,
                "patterns": {}
            }

        # Analyze patterns
        patterns = self.analyzer.analyze_patterns(backtest_entries)

        # Evaluate each pattern
        results = {}

        for signature, pattern in patterns.items():
            stats = pattern.get("stats", {})
            segments = pattern.get("time_segments", {})

            # Calculate confidence score
            confidence = self.analyzer.calculate_confidence_score(
                pattern, self.config
            )

            # Check if meets thresholds
            meets_thresholds = self._check_thresholds(
                stats, segments, confidence
            )

            results[signature] = {
                "stats": stats,
                "time_segments": segments,
                "confidence_score": confidence,
                "meets_thresholds": meets_thresholds,
                "context": pattern.get("context_signature", {}),
                "strategy": pattern.get("strategy", "unknown")
            }

        # Count promotable patterns
        promotable = sum(
            1 for p in results.values()
            if p["meets_thresholds"]
        )

        return {
            "pair": self.pair,
            "total_patterns": len(results),
            "promotable_patterns": promotable,
            "patterns": results
        }

    def promote(
        self,
        max_patterns: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Promote patterns that meet thresholds to promoted.jsonl.

        Args:
            max_patterns: Maximum number of patterns to promote
                        (uses config.max_promoted_patterns if None)

        Returns:
            Promotion results dict with structure:
            {
                "pair": str,
                "analyzed": int,
                "promoted": int,
                "skipped": int,
                "promoted_signatures": List[str],
                "timestamp": str
            }

        Raises:
            FileNotFoundError: If backtest.jsonl doesn't exist
            PromotionError: If promotion fails

        Note:
            Append-only write to promoted.jsonl.
            Idempotent (no duplicate promotions).
        """
        with self._lock:
            # Analyze patterns
            analysis = self.analyze()

            # Load existing promotions
            self._load_existing_promotions()

            # Filter promotable patterns
            promotable = [
                (sig, pattern)
                for sig, pattern in analysis["patterns"].items()
                if pattern["meets_thresholds"]
            ]

            # Sort by confidence score (highest first)
            promotable.sort(
                key=lambda x: x[1]["confidence_score"],
                reverse=True
            )

            # Apply max patterns limit
            limit = max_patterns or self.config.max_promoted_patterns
            promotable = promotable[:limit]

            # Promote each pattern
            promoted_count = 0
            skipped_count = 0
            promoted_signatures = []

            for signature, pattern_data in promotable:
                # Skip if already promoted
                if signature in self._existing_signatures:
                    skipped_count += 1
                    logger.info(
                        f"[PROMOTION] Skipping {signature} - already promoted"
                    )
                    continue

                # Create promoted entry
                entry = self._create_promoted_entry(signature, pattern_data)

                # Append to promoted.jsonl
                self._append_promoted_entry(entry)

                # Track
                promoted_count += 1
                promoted_signatures.append(signature)
                self._existing_signatures.add(signature)

                logger.info(
                    f"[PROMOTION] Promoted {signature} "
                    f"(confidence: {pattern_data['confidence_score']:.2f})"
                )

            return {
                "pair": self.pair,
                "analyzed": analysis["total_patterns"],
                "promoted": promoted_count,
                "skipped": skipped_count,
                "promoted_signatures": promoted_signatures,
                "timestamp": datetime.now().isoformat()
            }

    def _load_backtest_knowledge(self) -> List[Dict[str, Any]]:
        """
        Load backtest knowledge from backtest.jsonl.

        Returns:
            List of backtest knowledge entries

        Raises:
            FileNotFoundError: If backtest.jsonl doesn't exist
        """
        if not self.backtest_path.exists():
            raise FileNotFoundError(
                f"Backtest knowledge not found: {self.backtest_path}"
            )

        entries = []

        with open(self.backtest_path, 'r') as f:
            for line in f:
                if not line.strip():
                    continue

                try:
                    entry = json.loads(line.strip())
                    entries.append(entry)
                except json.JSONDecodeError as e:
                    logger.error(f"[PROMOTION] Invalid JSON in backtest.jsonl: {e}")
                    continue

        logger.info(f"[PROMOTION] Loaded {len(entries)} backtest entries")
        return entries

    def _load_existing_promotions(self):
        """
        Load existing promoted signatures for idempotency.

        Note:
            Reads promoted.jsonl to extract existing signatures.
            Prevents duplicate promotions.
        """
        self._existing_signatures.clear()

        if not self.promoted_path.exists():
            return

        with open(self.promoted_path, 'r') as f:
            for line in f:
                if not line.strip():
                    continue

                try:
                    entry = json.loads(line.strip())
                    # Extract signature from context
                    context = entry.get("context_signature", {})
                    strategy = entry.get("strategy", "unknown")

                    # Reconstruct signature
                    sig = self.analyzer._create_signature(strategy, context)
                    self._existing_signatures.add(sig)

                except json.JSONDecodeError:
                    continue

        logger.info(
            f"[PROMOTION] Found {len(self._existing_signatures)} "
            f"existing promotions"
        )

    def _check_thresholds(
        self,
        stats: Dict[str, Any],
        segments: Dict[str, Any],
        confidence: float
    ) -> bool:
        """
        Check if pattern meets all promotion thresholds.

        Args:
            stats: Pattern statistics
            segments: Time segment analysis
            confidence: Confidence score

        Returns:
            True if pattern meets all thresholds
        """
        # Sample size check
        if stats["sample_size"] < self.config.min_sample_size:
            return False

        # Win rate check
        if stats["win_rate"] < self.config.min_win_rate:
            return False

        # Avg PnL check
        if stats["avg_pnl"] < self.config.min_avg_pnl:
            return False

        # Drawdown check
        # Convert percentage to absolute value
        # Assume initial bankroll of 10000
        bankroll = 10000.0
        max_dd_allowed = bankroll * (self.config.max_drawdown_pct / 100.0)

        if stats["max_drawdown"] > max_dd_allowed:
            return False

        # Confidence score check
        if confidence < self.config.min_confidence_score:
            return False

        # Consistency check
        consistency = segments.get("consistency_score", 0.0)
        if consistency < self.config.min_consistency_score:
            return False

        return True

    def _create_promoted_entry(
        self,
        signature: str,
        pattern_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create promoted knowledge entry.

        Args:
            signature: Pattern signature
            pattern_data: Pattern analysis results

        Returns:
            Promoted entry dict matching Phase 9 schema
        """
        stats = pattern_data["stats"]
        segments = pattern_data["time_segments"]
        context = pattern_data["context"]

        # Generate promotion reason
        reason = self._generate_promotion_reason(stats, segments, pattern_data)

        return {
            "symbol": self.pair,
            "strategy": pattern_data["strategy"],
            "context_signature": context,
            "stats": {
                "sample_size": stats["sample_size"],
                "win_rate": stats["win_rate"],
                "avg_pnl": stats["avg_pnl"],
                "max_drawdown": stats["max_drawdown"],
                "profit_factor": stats.get("profit_factor", 0.0)
            },
            "confidence_score": pattern_data["confidence_score"],
            "promotion_reason": reason,
            "created_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        }

    def _generate_promotion_reason(
        self,
        stats: Dict[str, Any],
        segments: Dict[str, Any],
        pattern_data: Dict[str, Any]
    ) -> str:
        """
        Generate human-readable promotion reason.

        Args:
            stats: Pattern statistics
            segments: Time segment analysis
            pattern_data: Full pattern data

        Returns:
            Human-readable explanation
        """
        reasons = []

        # Sample size
        sample_size = stats["sample_size"]
        reasons.append(f"Sample size: {sample_size} trades")

        # Win rate
        win_rate = stats["win_rate"]
        reasons.append(f"Win rate: {win_rate:.1%}")

        # Avg PnL
        avg_pnl = stats["avg_pnl"]
        reasons.append(f"Avg PnL: {avg_pnl:.2f}")

        # Consistency
        consistency = segments.get("consistency_score", 0.0)
        reasons.append(f"Consistency: {consistency:.1%}")

        # Confidence
        confidence = pattern_data["confidence_score"]
        reasons.append(f"Confidence: {confidence:.1%}")

        # Combine
        return "; ".join(reasons)

    def _append_promoted_entry(self, entry: Dict[str, Any]):
        """
        Append promoted entry to promoted.jsonl.

        Args:
            entry: Promoted entry dict

        Raises:
            PromotionError: If write fails

        Note:
            Atomic append operation.
            Thread-safe.
        """
        try:
            # Ensure directory exists
            self.promoted_path.parent.mkdir(parents=True, exist_ok=True)

            # Append to file
            with open(self.promoted_path, 'a') as f:
                json.dump(entry, f)
                f.write('\n')

        except IOError as e:
            raise PromotionError(f"Failed to write promoted entry: {e}")

    def get_promoted_patterns(self) -> List[Dict[str, Any]]:
        """
        Get all promoted patterns.

        Returns:
            List of promoted pattern entries

        Note:
            Reads from promoted.jsonl.
        """
        if not self.promoted_path.exists():
            return []

        patterns = []

        with open(self.promoted_path, 'r') as f:
            for line in f:
                if not line.strip():
                    continue

                try:
                    entry = json.loads(line.strip())
                    patterns.append(entry)
                except json.JSONDecodeError:
                    continue

        return patterns
