"""
Backtest Engine - Phase 8 Implementation

Responsibilities:
- Drive the backtest loop
- For each candle: build context, call strategy, simulate execution
- Respect strategy frequency (scalper vs swing)
- No scheduling logic reuse from Phase 2
- Write results to backtest.jsonl
- Update aggregate snapshots

This module orchestrates the complete backtesting workflow.

PHASE 8 CONSTRAINTS:
- NO MT5 calls
- NO live trading
- Sequential candle processing only
- Reuse Phase 4 strategy unchanged
- Reuse Phase 5 validation unchanged
- Write to backtest.jsonl only
"""

import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime

from backtest.data_loader import CandleDataLoader
from backtest.executor import BacktestExecutor
from aggregator.updater import AggregatorUpdater
from strategy.scalper.decision import ScalperDecisionEngine
from strategy.swing.decision import SwingDecisionEngine


logger = logging.getLogger(__name__)


class BacktestEngine:
    """
    Main backtest engine orchestrator.

    Drives the complete backtesting workflow:
    1. Load historical candles
    2. For each candle:
       - Build market context
       - Call strategy decision (Phase 4)
       - Validate decision (Phase 5)
       - Simulate execution
       - Update knowledge and aggregates
    3. Finalize and report results

    No MT5 connection required.
    No live trading.
    """

    def __init__(
        self,
        pair: str,
        strategy: str = "scalper",
        data_file: Optional[Path] = None,
        pairs_dir: Optional[Path] = None
    ):
        """
        Initialize backtest engine.

        Args:
            pair: Trading pair symbol (e.g., "XAUUSDm")
            strategy: Strategy to use ("scalper" or "swing")
            data_file: Path to historical data file
            pairs_dir: Base pairs directory path

        Note:
            No data loading on init.
            Call run() to execute backtest.
        """
        self.pair = pair
        self.strategy_name = strategy

        # Data loader
        self.data_file = data_file
        self.loader = None

        # Strategy engine (reuse Phase 4)
        if strategy == "scalper":
            self.strategy = ScalperDecisionEngine(pair)
        elif strategy == "swing":
            self.strategy = SwingDecisionEngine(pair)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

        # Backtest executor
        self.executor = BacktestExecutor(pair)

        # Aggregator updater (reuse Phase 6)
        self.aggregator = AggregatorUpdater(pair, pairs_dir)

        # Backtest state
        self.candle_count = 0
        self.trade_count = 0
        self.last_decision_time: Optional[str] = None

        # Frequency control (respect strategy intervals)
        self.strategy_intervals = {
            "scalper": 2,   # 2 seconds (simulated as candles)
            "swing": 60     # 60 seconds (simulated as candles)
        }
        self.candles_since_last_decision = 0

    def run(self, data_file: Optional[Path] = None) -> Dict[str, Any]:
        """
        Run the complete backtest.

        Args:
            data_file: Optional override for data file path

        Returns:
            Backtest results dict with structure:
            {
                "pair": str,
                "strategy": str,
                "candles_processed": int,
                "trades_executed": int,
                "final_balance": float,
                "total_pnl": float,
                "win_rate": float,
                "start_time": str,
                "end_time": str
            }

        Raises:
            FileNotFoundError: If data file not found
            InvalidCandleError: If candle data is invalid

        Note:
            Sequential processing only.
            No parallel execution.
        """
        # Load data
        data_file = data_file or self.data_file
        if not data_file:
            raise ValueError("No data file specified")

        self.loader = CandleDataLoader(data_file)

        logger.info(f"[BACKTEST] Starting backtest for {self.pair}")
        logger.info(f"[BACKTEST] Strategy: {self.strategy_name}")
        logger.info(f"[BACKTEST] Data file: {data_file}")

        # Initialize
        start_time = datetime.now().isoformat()
        self.candle_count = 0
        self.trade_count = 0
        self.candles_since_last_decision = 0

        # Process candles sequentially
        for candle in self.loader.candles():
            self._process_candle(candle)
            self.candle_count += 1

            # Progress logging every 100 candles
            if self.candle_count % 100 == 0:
                logger.info(
                    f"[BACKTEST] Processed {self.candle_count} candles, "
                    f"{self.trade_count} trades"
                )

        # Close remaining positions
        self._close_all_positions()

        # Generate results
        end_time = datetime.now().isoformat()
        results = self._generate_results(start_time, end_time)

        logger.info(f"[BACKTEST] Backtest complete:")
        logger.info(f"  Candles: {results['candles_processed']}")
        logger.info(f"  Trades: {results['trades_executed']}")
        logger.info(f"  Final PnL: {results['total_pnl']:.2f}")
        logger.info(f"  Win Rate: {results['win_rate']:.2%}")

        return results

    def _process_candle(self, candle: Dict[str, Any]):
        """
        Process a single candle.

        Args:
            candle: OHLC candle dict

        Workflow:
        1. Check SL/TP on existing positions
        2. Update strategy frequency counter
        3. If due for decision: call strategy
        4. If valid decision: execute order
        5. Update knowledge and aggregates
        """
        timestamp = candle["timestamp"]

        # Step 1: Check SL/TP on existing positions
        closed_trades = self.executor.check_sl_tp(candle, timestamp)

        for trade in closed_trades:
            self._log_trade_outcome(trade)
            self.trade_count += 1

        # Step 2: Update frequency counter
        interval = self.strategy_intervals[self.strategy_name]
        self.candles_since_last_decision += 1

        # Step 3: Check if due for decision
        if self.candles_since_last_decision < interval:
            return  # Not time yet

        # Reset counter
        self.candles_since_last_decision = 0

        # Step 4: Build market context
        market_data = self._build_market_context(candle)

        # Step 5: Call strategy (reuse Phase 4)
        try:
            decision = self.strategy.evaluate(market_data)
        except Exception as e:
            logger.error(f"[BACKTEST] Strategy error: {e}")
            return

        # Step 6: Validate decision (reuse Phase 5)
        is_valid, error_msg = self.executor.validate_decision(decision)

        if not is_valid:
            logger.warning(f"[BACKTEST] Invalid decision: {error_msg}")
            return

        # Step 7: Check for HOLD
        if decision["decision"] == "HOLD":
            # Log HOLD decision
            self._log_decision(decision, mode="backtest")
            return

        # Step 8: Execute order (simulated)
        execution_result = self._execute_decision(decision, candle, timestamp)

        if execution_result and execution_result.get("success"):
            # Step 9: Log decision to knowledge
            self._log_decision(decision, mode="backtest")
            self.trade_count += 1

    def _build_market_context(self, candle: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build market context for strategy evaluation.

        Args:
            candle: Current OHLC candle

        Returns:
            Market data dict with structure expected by Phase 4 strategies:
            {
                "bid": float,
                "ask": float,
                "spread": float,
                "ohlc_data": List[Dict]  # Recent candles for trend analysis
            }

        Note:
            Simplified - uses candle close as bid/ask (no spread).
            TODO: Add historical candle buffer for trend analysis.
        """
        close_price = candle["close"]

        # Simplified - no spread in backtest
        market_data = {
            "bid": close_price,
            "ask": close_price,
            "spread": 0.0,
            "ohlc_data": [candle]  # TODO: Maintain candle history
        }

        return market_data

    def _execute_decision(
        self,
        decision: Dict[str, Any],
        candle: Dict[str, Any],
        timestamp: str
    ) -> Optional[Dict[str, Any]]:
        """
        Execute a trading decision.

        Args:
            decision: Decision dict from Phase 4 strategy
            candle: Current OHLC candle
            timestamp: Current timestamp

        Returns:
            Execution result dict, or None if not executed

        Note:
            Delegates to BacktestExecutor.
            Routes to market or pending order execution.
        """
        entry_type = decision.get("entry_type", "none")

        if entry_type == "market":
            # Market order - fill immediately
            return self.executor.execute_market_order(decision, candle, timestamp)

        elif entry_type == "pending":
            # Pending order - check if fills
            result = self.executor.execute_pending_order(decision, candle, timestamp)
            if result:
                return result
            else:
                # Pending order didn't fill - log decision anyway
                self._log_decision(decision, mode="backtest")
                return None

        else:
            # entry_type == "none" or HOLD
            return None

    def _log_decision(self, decision: Dict[str, Any], mode: str = "backtest"):
        """
        Log trading decision to knowledge.

        Args:
            decision: Decision dict from Phase 4
            mode: "backtest" or "live"

        Note:
            Delegates to AggregatorUpdater (Phase 6).
            Writes to backtest.jsonl.
        """
        try:
            entry = self.aggregator.log_decision(decision, mode=mode)
            logger.debug(
                f"[BACKTEST] Logged decision: {decision['decision']} {self.pair}"
            )
        except Exception as e:
            logger.error(f"[BACKTEST] Failed to log decision: {e}")

    def _log_trade_outcome(self, trade_result: Dict[str, Any]):
        """
        Log resolved trade outcome to knowledge.

        Args:
            trade_result: Trade result dict from BacktestExecutor

        Note:
            Delegates to AggregatorUpdater (Phase 6).
            Writes outcome to backtest.jsonl.
            Updates aggregate snapshot.
        """
        try:
            # Extract original decision
            decision = trade_result.get("decision", {})

            # Log outcome
            self.aggregator.log_outcome(
                original_entry=decision,
                result=trade_result["result"],
                pnl=trade_result["pnl"],
                duration_sec=trade_result["duration_sec"],
                mode="backtest"
            )

            logger.info(
                f"[BACKTEST] Logged outcome: {trade_result['result']} "
                f"PnL: {trade_result['pnl']:.2f}"
            )
        except Exception as e:
            logger.error(f"[BACKTEST] Failed to log outcome: {e}")

    def _close_all_positions(self):
        """
        Close all remaining open positions at end of backtest.

        Note:
            Uses last candle close price for exit.
            Logs all outcomes to knowledge.
        """
        # TODO: Need to track last candle for this
        # For now, just close with placeholder
        open_positions = self.executor.get_open_positions()

        if not open_positions:
            return

        logger.warning(
            f"[BACKTEST] Closing {len(open_positions)} open positions "
            f"at end of backtest"
        )

        # TODO: Implement proper close at last candle
        for position in open_positions:
            ticket = position["ticket"]
            logger.warning(f"[BACKTEST] Position {ticket} still open - TODO")

    def _generate_results(
        self,
        start_time: str,
        end_time: str
    ) -> Dict[str, Any]:
        """
        Generate backtest results summary.

        Args:
            start_time: Backtest start timestamp
            end_time: Backtest end timestamp

        Returns:
            Results summary dict
        """
        # Get aggregate statistics
        stats = self.aggregator.get_statistics()

        return {
            "pair": self.pair,
            "strategy": self.strategy_name,
            "candles_processed": self.candle_count,
            "trades_executed": self.trade_count,
            "final_balance": self.executor.get_balance(),
            "total_pnl": self.executor.get_balance() - self.executor.initial_balance,
            "win_rate": stats.get("win_rate", 0.0),
            "start_time": start_time,
            "end_time": end_time
        }


# =============================================================================
# Convenience Functions
# =============================================================================

def run_backtest(
    pair: str,
    strategy: str,
    data_file: Path,
    pairs_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Convenience function to run a backtest.

    Args:
        pair: Trading pair symbol
        strategy: Strategy name ("scalper" or "swing")
        data_file: Path to historical data file
        pairs_dir: Optional pairs directory path

    Returns:
        Backtest results dict

    Usage:
        results = run_backtest(
            pair="XAUUSDm",
            strategy="scalper",
            data_file=Path("data/XAUUSDm_h1.json")
        )
    """
    engine = BacktestEngine(pair, strategy, data_file, pairs_dir)
    return engine.run()
