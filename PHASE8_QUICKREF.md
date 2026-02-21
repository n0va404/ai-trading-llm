# Phase 8 - Backtest Engine: Quick Reference

## Overview

Phase 8 implements a **deterministic backtest engine** that:
- Replays historical market data step-by-step
- Reuses Phase 4 strategy logic unchanged
- Reuses Phase 5 validation unchanged
- Simulates order fills (no MT5)
- Writes results to `backtest.jsonl`
- Updates aggregate snapshots

---

## Quick Start

### Run a Backtest

```python
from backtest.engine import run_backtest
from pathlib import Path

results = run_backtest(
    pair="XAUUSDm",
    strategy="scalper",  # or "swing"
    data_file=Path("data/historical/XAUUSDm_m1.json")
)

print(f"Candles: {results['candles_processed']}")
print(f"Trades: {results['trades_executed']}")
print(f"PnL: {results['total_pnl']:.2f}")
print(f"Win Rate: {results['win_rate']:.2%}")
```

---

## Components

### 1. CandleDataLoader

```python
from backtest.data_loader import CandleDataLoader

loader = CandleDataLoader(Path("data/historical/XAUUSDm_m1.jsonl"))

# Iterate candles sequentially
for candle in loader.candles():
    print(f"{candle['timestamp']}: O={candle['open']} C={candle['close']}")
```

**Features:**
- JSONL and JSON array support
- OHLCV validation
- Sequential iteration only

### 2. BacktestExecutor

```python
from backtest.executor import BacktestExecutor

executor = BacktestExecutor(pair="XAUUSDm")

# Validate decision (Phase 5)
is_valid, error = executor.validate_decision(decision)

# Execute market order
result = executor.execute_market_order(decision, candle, timestamp)

# Execute pending order
result = executor.execute_pending_order(decision, candle, timestamp)

# Check SL/TP
closed = executor.check_sl_tp(candle, timestamp)

# Get balance
balance = executor.get_balance()
```

### 3. BacktestEngine

```python
from backtest.engine import BacktestEngine

engine = BacktestEngine(
    pair="XAUUSDm",
    strategy="scalper",
    data_file=Path("data/historical/XAUUSDm_m1.json")
)

results = engine.run()
```

---

## Historical Data Format

### JSONL (Recommended)

```json
{"timestamp": "2026-02-21T10:00:00", "open": 2934.50, "high": 2940.20, "low": 2930.10, "close": 2936.12, "volume": 150}
{"timestamp": "2026-02-21T10:01:00", "open": 2936.12, "high": 2941.50, "low": 2934.00, "close": 2938.75, "volume": 120}
```

### Required Fields

- `timestamp`: ISO-8601 string
- `open`, `high`, `low`, `close`: Numeric prices
- `volume`: Non-negative integer

---

## Execution Simulation

### Market Orders
- Fill at candle **OPEN** price
- No slippage (simplified)

### Pending Orders
- Fill if price touched during candle
- BUY_LIMIT/SELL_STOP: Fill if `low <= price`
- SELL_LIMIT/BUY_STOP: Fill if `high >= price`

### Stop Loss / Take Profit
- Check if candle high/low touched levels
- TP priority over SL
- Fill at SL/TP price

---

## Output

### backtest.jsonl

Results written to: `pairs/<PAIR>/knowledge/backtest.jsonl`

Format matches Phase 6 schema exactly:
```json
{"timestamp": "...", "strategy": "scalper", "symbol": "XAUUSDm", "decision": "BUY", "confidence": 0.8, "entry_type": "market", "pending_type": "none", "result": "win", "pnl": 30.50, "duration_sec": 120, "reason": "...", "context": {...}}
```

### Aggregate Snapshot

Updated incrementally (Phase 6):
- Total trades
- Win rate
- Avg PnL
- Per-strategy stats

---

## Constraints

✅ **NO MT5 calls**
✅ **NO live trading**
✅ **NO future data leakage**
✅ **Sequential processing only**
✅ **Deterministic behavior**

---

## Integration

### Phase 4: Strategy
```python
# Reused unchanged
from strategy.scalper.decision import ScalperDecisionEngine
from strategy.swing.decision import SwingDecisionEngine
```

### Phase 5: Validation
```python
# Reused unchanged
from execution.validator import OrderValidator
```

### Phase 6: Knowledge
```python
# Reused unchanged
from aggregator.updater import AggregatorUpdater
aggregator.log_decision(decision, mode="backtest")
```

---

## Testing

```bash
cd D:\1Computer\1AI\Sandbox\ai-trading-llm
python -c "
from backtest.engine import run_backtest
from pathlib import Path

results = run_backtest(
    pair='XAUUSDm',
    strategy='scalper',
    data_file=Path('data/historical/XAUUSDm_m1_sample.jsonl')
)
print(f'Candles: {results[\"candles_processed\"]}')
print(f'Trades: {results[\"trades_executed\"]}')
"
```

---

## Files

- `backtest/__init__.py` - Package exports
- `backtest/data_loader.py` - Historical data loader
- `backtest/executor.py` - Simulated execution
- `backtest/engine.py` - Backtest orchestrator
- `data/historical/XAUUSDm_m1_sample.jsonl` - Sample data

---

## Status

✅ **Phase 8 Complete**

- 3 files created (~950 LOC)
- 27 functions implemented
- 4/4 tests passed
- No changes to Phases 0-6
- Ready for Phase 9 (Knowledge Promotion)
