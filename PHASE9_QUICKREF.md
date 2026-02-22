# Phase 9 - Knowledge Promotion: Quick Reference

## Overview

Phase 9 implements a **conservative knowledge promotion engine** that:
- Reads backtest knowledge from Phase 8
- Groups trades by context patterns
- Evaluates statistical quality
- Promotes ONLY robust patterns to promoted.jsonl
- Never modifies existing knowledge files

---

## Quick Start

### Analyze Backtest Patterns

```python
from promotion import KnowledgePromoter, PromotionConfig

# Create promoter
config = PromotionConfig.moderate()
promoter = KnowledgePromoter("XAUUSDm", config=config)

# Analyze without promoting
analysis = promoter.analyze()

print(f"Total patterns: {analysis['total_patterns']}")
print(f"Promotable: {analysis['promotable_patterns']}")
```

### Promote Patterns

```python
# Promote patterns that meet thresholds
result = promoter.promote()

print(f"Promoted: {result['promoted']} patterns")
print(f"Skipped: {result['skipped']} (duplicates)")
```

---

## Configuration Presets

### Conservative (Production Live Trading)
```python
config = PromotionConfig.conservative()
# 60% win rate, 50+ trades, 5% max drawdown
```

### Moderate (Paper Trading - Default)
```python
config = PromotionConfig.moderate()
# 55% win rate, 20+ trades, 10% max drawdown
```

### Permissive (Development Only)
```python
config = PromotionConfig.permissive()
# 50% win rate, 10+ trades, 15% max drawdown
```

---

## Promotion Criteria

A pattern is promoted ONLY if it meets:

1. **Sample size** ≥ min_sample_size (20 default)
2. **Win rate** ≥ min_win_rate (55% default)
3. **Avg PnL** ≥ min_avg_pnl (2.0 default)
4. **Max drawdown** ≤ max_drawdown_pct (10% default)
5. **Confidence score** ≥ min_confidence_score (0.7 default)
6. **Consistency** ≥ min_consistency_score (0.6 default)

---

## Confidence Score

Weighted average of 6 factors:

| Factor | Weight | Description |
|--------|--------|-------------|
| Sample size | 15% | More trades = higher score |
| Win rate | 25% | Higher win rate = higher score |
| Avg PnL | 20% | Positive PnL = higher score |
| Consistency | 20% | Consistent across time = higher score |
| Drawdown | 10% | Lower drawdown = higher score |
| Profit factor | 10% | Higher ratio = higher score |

---

## Output Format

### promoted.jsonl

Each entry represents a **pattern** (not a single trade):

```json
{
  "symbol": "XAUUSDm",
  "strategy": "scalper",
  "context_signature": {
    "timeframe": "M1",
    "volatility_state": "normal",
    "trend_state": "bullish"
  },
  "stats": {
    "sample_size": 30,
    "win_rate": 0.667,
    "avg_pnl": 17.40,
    "max_drawdown": 45.0,
    "profit_factor": 2.15
  },
  "confidence_score": 0.76,
  "promotion_reason": "Sample size: 30 trades; Win rate: 66.7%; Avg PnL: 17.40; Consistency: 70.0%; Confidence: 75.7%",
  "created_at": "2026-02-22T12:00:00"
}
```

---

## Idempotent Promotion

```python
# Run promotion multiple times
result1 = promoter.promote()
result2 = promoter.promote()

# Same patterns not promoted twice
# Existing signatures tracked automatically
```

---

## Files

- `promotion/__init__.py` - Package exports
- `promotion/config.py` - Configuration presets
- `promotion/pattern_analyzer.py` - Statistical analysis
- `promotion/promoter.py` - Promotion orchestrator

---

## Integration

### Phase 6: Knowledge System
- Reads from `pairs/<PAIR>/knowledge/backtest.jsonl`
- Writes to `pairs/<PAIR>/knowledge/promoted.jsonl`

### Phase 8: Backtest Engine
- Consumes Phase 8 output (backtest.jsonl)
- Analyzes backtest trades

---

## Testing

```python
# Test with permissive config
config = PromotionConfig.permissive()
promoter = KnowledgePromoter("XAUUSDm", config=config)
result = promoter.promote()

# View promoted patterns
promoted = promoter.get_promoted_patterns()
for p in promoted:
    print(f"{p['strategy']} {p['context_signature']}")
    print(f"  Confidence: {p['confidence_score']:.2f}")
    print(f"  Stats: {p['stats']['sample_size']} trades, {p['stats']['win_rate']:.1%}")
```

---

## Constraints

✅ **NO modification of backtest.jsonl**
✅ **NO modification of live.jsonl**
✅ **NO LLM calls**
✅ **NO strategy logic**
✅ **Conservative thresholds only**

---

## Status

✅ **Phase 9 Complete**

- 4 files created (~900 LOC)
- 21 functions implemented
- 5/5 tests passed
- Idempotent promotion verified
- Ready for Phase 10 (Live Trading)
