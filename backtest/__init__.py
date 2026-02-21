"""
Backtest Engine - Phase 8 Implementation

This package provides historical backtesting capabilities:
- Load historical OHLC data
- Reuse Phase 4 strategy logic
- Reuse Phase 5 execution validation
- Simulate order fills
- Write results to backtest.jsonl
- Update aggregate snapshots

PHASE 8 CONSTRAINTS:
- NO MT5 calls
- NO live trading
- NO future data leakage
- Sequential processing only
- Deterministic behavior
"""

from backtest.data_loader import CandleDataLoader
from backtest.executor import BacktestExecutor
from backtest.engine import BacktestEngine

__all__ = [
    "CandleDataLoader",
    "BacktestExecutor",
    "BacktestEngine"
]
