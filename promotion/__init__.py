"""
Knowledge Promotion Engine - Phase 9 Implementation

This package provides conservative knowledge promotion:
- Read backtest knowledge
- Evaluate statistical quality
- Promote ONLY robust patterns
- Write to promoted.jsonl (separate from backtest/live)
- Never pollutes existing knowledge

PHASE 9 CONSTRAINTS:
- NO modification of backtest.jsonl
- NO modification of live.jsonl
- NO LLM calls
- NO strategy logic
- Conservative thresholds only
- Pattern-based promotion (not individual trades)
"""

from promotion.promoter import KnowledgePromoter, PromotionError
from promotion.config import PromotionConfig
from promotion.pattern_analyzer import PatternAnalyzer

__all__ = [
    "KnowledgePromoter",
    "PromotionConfig",
    "PatternAnalyzer",
    "PromotionError"
]
