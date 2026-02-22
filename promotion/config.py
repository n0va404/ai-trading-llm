"""
Promotion Configuration - Phase 9 Implementation

Conservative thresholds for knowledge promotion.

These thresholds control WHAT knowledge gets promoted from backtest
to the promoted.jsonl knowledge set.

PHASE 9 CONSTRAINTS:
- Conservative by default
- Configurable
- NOT hardcoded in business logic
"""

from typing import Dict, Any
from dataclasses import dataclass, field


@dataclass
class PromotionConfig:
    """
    Configuration for knowledge promotion thresholds.

    All thresholds are conservative to ensure only robust patterns
    are promoted to live trading consideration.
    """

    # Minimum sample size (number of trades in pattern)
    min_sample_size: int = 20

    # Minimum win rate (0.0 - 1.0)
    min_win_rate: float = 0.55

    # Minimum average PnL (must be positive)
    min_avg_pnl: float = 0.0

    # Maximum acceptable drawdown (as percentage of bankroll)
    max_drawdown_pct: float = 10.0

    # Minimum confidence score (0.0 - 1.0)
    min_confidence_score: float = 0.7

    # Minimum consistency score (pattern appears across time segments)
    min_consistency_score: float = 0.6

    # Maximum number of patterns to promote per pair
    max_promoted_patterns: int = 50

    # Time segmentation: number of segments to test for consistency
    consistency_segments: int = 3

    @classmethod
    def conservative(cls) -> "PromotionConfig":
        """
        Create ultra-conservative configuration.

        Use this for production live trading.
        Only the most robust patterns survive.
        """
        return cls(
            min_sample_size=50,
            min_win_rate=0.60,
            min_avg_pnl=5.0,
            max_drawdown_pct=5.0,
            min_confidence_score=0.85,
            min_consistency_score=0.75,
            max_promoted_patterns=20
        )

    @classmethod
    def moderate(cls) -> "PromotionConfig":
        """
        Create moderate configuration.

        Use this for paper trading or testing.
        More permissive than conservative.
        """
        return cls(
            min_sample_size=30,
            min_win_rate=0.55,
            min_avg_pnl=2.0,
            max_drawdown_pct=8.0,
            min_confidence_score=0.70,
            min_consistency_score=0.65,
            max_promoted_patterns=30
        )

    @classmethod
    def permissive(cls) -> "PromotionConfig":
        """
        Create permissive configuration.

        Use this for development and experimentation.
        WARNING: Not suitable for live trading.
        """
        return cls(
            min_sample_size=10,
            min_win_rate=0.50,
            min_avg_pnl=0.0,
            max_drawdown_pct=15.0,
            min_confidence_score=0.50,
            min_consistency_score=0.50,
            max_promoted_patterns=100
        )

    def validate(self) -> None:
        """
        Validate configuration values.

        Raises:
            ValueError: If configuration is invalid
        """
        if self.min_sample_size < 1:
            raise ValueError("min_sample_size must be >= 1")

        if not 0.0 <= self.min_win_rate <= 1.0:
            raise ValueError("min_win_rate must be in [0.0, 1.0]")

        if self.min_avg_pnl < 0:
            raise ValueError("min_avg_pnl must be >= 0")

        if self.max_drawdown_pct < 0:
            raise ValueError("max_drawdown_pct must be >= 0")

        if not 0.0 <= self.min_confidence_score <= 1.0:
            raise ValueError("min_confidence_score must be in [0.0, 1.0]")

        if not 0.0 <= self.min_consistency_score <= 1.0:
            raise ValueError("min_consistency_score must be in [0.0, 1.0]")

        if self.max_promoted_patterns < 1:
            raise ValueError("max_promoted_patterns must be >= 1")

        if self.consistency_segments < 2:
            raise ValueError("consistency_segments must be >= 2")

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.

        Returns:
            Config dict
        """
        return {
            "min_sample_size": self.min_sample_size,
            "min_win_rate": self.min_win_rate,
            "min_avg_pnl": self.min_avg_pnl,
            "max_drawdown_pct": self.max_drawdown_pct,
            "min_confidence_score": self.min_confidence_score,
            "min_consistency_score": self.min_consistency_score,
            "max_promoted_patterns": self.max_promoted_patterns,
            "consistency_segments": self.consistency_segments
        }

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "PromotionConfig":
        """
        Create configuration from dictionary.

        Args:
            config_dict: Configuration dict

        Returns:
            PromotionConfig instance
        """
        return cls(
            min_sample_size=config_dict.get("min_sample_size", 20),
            min_win_rate=config_dict.get("min_win_rate", 0.55),
            min_avg_pnl=config_dict.get("min_avg_pnl", 0.0),
            max_drawdown_pct=config_dict.get("max_drawdown_pct", 10.0),
            min_confidence_score=config_dict.get("min_confidence_score", 0.7),
            min_consistency_score=config_dict.get("min_consistency_score", 0.6),
            max_promoted_patterns=config_dict.get("max_promoted_patterns", 50),
            consistency_segments=config_dict.get("consistency_segments", 3)
        )
