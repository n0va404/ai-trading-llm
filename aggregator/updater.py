"""
Aggregator Updater - Phase 6 Implementation

Responsibilities:
- Append new JSONL entries
- Trigger aggregate update
- Handle file I/O safely
- Prepare data for LLM and backtest

This module is called by execution layer after trade resolution.
It does NOT make trading decisions or execute trades.

PHASE 6 CONSTRAINTS:
- No LLM calls
- No strategy logic
- No trade execution
- No market data fetching
- No auto-promotion
- Incremental updates (no full-history scans)
"""

import json
import time
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import threading

from aggregator.state import AggregateStateManager


logger = logging.getLogger(__name__)


def aggregator_update_job():
    """
    Job function to update aggregates for all pairs.

    This is called by the scheduler (Phase 2) every aggregator_update_interval.

    Phase 6 Implementation:
    - For each pair with new knowledge: update aggregate

    Note:
        In Phase 6, this is a placeholder.
        Actual integration with execution layer will be added in future phases.

    TODO: Load enabled pairs from config/pairs.yaml
    TODO: Check for new knowledge entries
    TODO: Update aggregates for pairs with new entries
    """
    # TODO: Implement actual job logic
    # This will be implemented when we have:
    # 1. Config loading mechanism
    # 2. Knowledge file monitoring
    # 3. Integration with execution layer

    raise NotImplementedError("aggregator_update_job not yet implemented - needs execution layer integration")


class AggregatorUpdater:
    """
    Aggregator updater for a single trading pair.

    Each pair has its own aggregator instance for isolation.

    Responsibilities:
    - Append knowledge entries to JSONL files
    - Update aggregate snapshot incrementally
    - Prepare data for LLM (future)
    """

    # Knowledge file types
    KNOWLEDGE_BACKTEST = "backtest.jsonl"
    KNOWLEDGE_LIVE = "live.jsonl"
    KNOWLEDGE_PROMOTED = "promoted.jsonl"

    def __init__(
        self,
        pair: str,
        pairs_dir: Optional[Path] = None,
        state_manager: Optional[AggregateStateManager] = None
    ):
        """
        Initialize aggregator updater for a specific pair.

        Args:
            pair: Trading pair symbol
            pairs_dir: Base pairs directory path
            state_manager: Optional AggregateStateManager (creates new if None)

        Note:
            No data loading on init.
            No side effects.
        """
        self.pair = pair
        if pairs_dir is None:
            pairs_dir = Path(__file__).parent.parent / "pairs"

        self.pairs_dir = pairs_dir / pair
        self.state_manager = state_manager or AggregateStateManager(pair, pairs_dir)

        # Knowledge file paths
        self.knowledge_dir = self.pairs_dir / "knowledge"
        self.backtest_path = self.knowledge_dir / self.KNOWLEDGE_BACKTEST
        self.live_path = self.knowledge_dir / self.KNOWLEDGE_LIVE
        self.promoted_path = self.knowledge_dir / self.KNOWLEDGE_PROMOTED

        # Thread safety for concurrent writes
        self._lock = threading.Lock()

    def log_decision(
        self,
        decision: Dict[str, Any],
        mode: str = "live"
    ) -> Dict[str, Any]:
        """
        Log a trading decision to knowledge.

        Args:
            decision: Decision dict from Phase 4 strategy
            mode: "live" or "backtest"

        Returns:
            Knowledge entry dict that was logged

        Raises:
            ValueError: If mode is invalid
            IOError: If JSONL write fails

        Note:
            Creates entry with result="unknown" (outcome not yet known).
            Entry will be updated when trade resolves.
        """
        # Validate mode
        if mode not in ["live", "backtest"]:
            raise ValueError(f"Invalid mode: {mode}")

        # Determine file path
        if mode == "live":
            file_path = self.live_path
        else:
            file_path = self.backtest_path

        # Create knowledge entry
        entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "strategy": decision.get("strategy", "unknown"),
            "symbol": decision.get("symbol", self.pair),
            "decision": decision.get("decision", "HOLD"),
            "entry_type": decision.get("entry_type", "none"),
            "pending_type": decision.get("pending_type", "none"),
            "confidence": decision.get("confidence", 0.0),
            "result": "unknown",  # Will be updated on resolution
            "pnl": 0.0,  # Will be updated on resolution
            "duration_sec": 0,  # Will be updated on resolution
            "reason": decision.get("reason", ""),
            "context": decision.get("context", {})
        }

        # Append to JSONL file
        self._append_entry(file_path, entry)

        # Update aggregate
        self._update_aggregate(entry)

        logger.info(f"Logged {mode} decision: {decision['decision']} {self.pair}")

        return entry

    def log_outcome(
        self,
        original_entry: Dict[str, Any],
        result: str,
        pnl: float,
        duration_sec: float,
        mode: str = "live"
    ):
        """
        Update knowledge entry with trade outcome.

        Args:
            original_entry: Original knowledge entry (from log_decision)
            result: "win", "loss", or "breakeven"
            pnl: Profit/loss in account currency
            duration_sec: Trade duration in seconds
            mode: "live" or "backtest"

        Raises:
            ValueError: If result is invalid
            IOError: If file update fails

        Note:
            This appends a NEW entry with the outcome.
            Original entry is NOT modified (append-only).
        """
        # Validate result
        if result not in ["win", "loss", "breakeven"]:
            raise ValueError(f"Invalid result: {result}")

        # Create outcome entry
        outcome_entry = original_entry.copy()
        outcome_entry["result"] = result
        outcome_entry["pnl"] = pnl
        outcome_entry["duration_sec"] = duration_sec
        outcome_entry["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%S")

        # Determine file path
        if mode == "live":
            file_path = self.live_path
        else:
            file_path = self.backtest_path

        # Append outcome to JSONL file
        self._append_entry(file_path, outcome_entry)

        # Update aggregate with outcome
        self._update_aggregate(outcome_entry)

        logger.info(f"Logged {mode} outcome: {result} {self.pair} (PnL: {pnl:.2f})")

    def _append_entry(self, file_path: Path, entry: Dict[str, Any]):
        """
        Append entry to JSONL file.

        Args:
            file_path: Path to JSONL file
            entry: Entry dict to append

        Raises:
            IOError: If write fails

        Note:
            Thread-safe operation.
            File is append-only (no overwrite).
        """
        with self._lock:
            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Append as JSONL
            with open(file_path, 'a') as f:
                json.dump(entry, f)
                f.write('\n')  # Newline after each entry

    def _update_aggregate(self, entry: Dict[str, Any]):
        """
        Update aggregate snapshot incrementally from new entry.

        Args:
            entry: Knowledge entry

        Note:
            O(1) operation - doesn't scan full history.
            Atomic write to snapshot file.
        """
        with self._lock:
            # Load current snapshot
            current = self.state_manager.load()

            # Compute updated snapshot
            updated = self.state_manager.compute_incremental(current, entry)

            # Save updated snapshot
            self.state_manager.save(updated)

    def get_aggregate(self) -> Dict[str, Any]:
        """
        Get current aggregate snapshot.

        Returns:
            Aggregate snapshot dict

        Note:
            O(1) read operation.
        """
        return self.state_manager.load()

    def get_recent_knowledge(
        self,
        mode: str = "live",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get recent knowledge entries.

        Args:
            mode: "live" or "backtest"
            limit: Maximum number of entries to return

        Returns:
            List of knowledge entries (most recent first)

        Note:
            Reads from END of file and reverses.
            This is O(limit) not O(history size).
        """
        # Determine file path
        if mode == "live":
            file_path = self.live_path
        else:
            file_path = self.backtest_path

        if not file_path.exists():
            return []

        # Read last N lines
        entries = []
        with open(file_path, 'r') as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line))
                    if len(entries) >= limit:
                        break

        # Reverse to get most recent first
        entries.reverse()
        return entries

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get current statistics from aggregate.

        Returns:
            Dict with:
            - total_trades: Total number of trades
            - win_rate: Overall win rate
            - avg_pnl: Average PnL
            - scalper_trades: Scalper trade count
            - swing_trades: Swing trade count

        Note:
            O(1) operation - reads snapshot only.
        """
        snapshot = self.get_aggregate()
        return {
            "total_trades": snapshot["total_trades"],
            "win_rate": snapshot["win_rate"],
            "avg_pnl": snapshot["avg_pnl"],
            "scalper_trades": snapshot["scalper"]["trades"],
            "swing_trades": snapshot["swing"]["trades"]
        }

    def get_path(self, knowledge_type: str = "live") -> Path:
        """
        Get path to knowledge file.

        Args:
            knowledge_type: "live", "backtest", or "promoted"

        Returns:
            Path to knowledge file

        Raises:
            ValueError: If knowledge_type is invalid
        """
        if knowledge_type == "live":
            return self.live_path
        elif knowledge_type == "backtest":
            return self.backtest_path
        elif knowledge_type == "promoted":
            return self.promoted_path
        else:
            raise ValueError(f"Invalid knowledge type: {knowledge_type}")

    def promote_entry(
        self,
        entry: Dict[str, Any],
        reason: str
    ):
        """
        Promote a knowledge entry to promoted.jsonl.

        Args:
            entry: Knowledge entry to promote
            reason: Reason for promotion

        Raises:
            IOError: If write fails

        Note:
            For Phase 6, this is a placeholder.
            Actual promotion logic will be added in Phase 9.
        """
        # TODO: Implement promotion logic in Phase 9
        # This will be called by LLM or heuristic in later phases

        # Add promotion metadata
        promoted_entry = entry.copy()
        promoted_entry["promoted_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        promoted_entry["promotion_reason"] = reason

        # Append to promoted.jsonl
        self._append_entry(self.promoted_path, promoted_entry)

        logger.info(f"Promoted entry: {entry.get('timestamp')} - {reason}")
