"""
Aggregate State Manager - Phase 6 Implementation

Responsibilities:
- Maintain aggregate computation logic
- Calculate statistics from knowledge entries
- O(1) snapshot reads
- Deterministic behavior

This module handles aggregate state I/O and computation.
It does NOT fetch data or execute trades.

PHASE 6 CONSTRAINTS:
- No LLM calls
- No strategy logic
- No trade execution
- No market data fetching
- No auto-promotion
- Deterministic computation
"""

import json
import time
from typing import Dict, Any, Optional, List
from pathlib import Path
import threading


class AggregateStateManager:
    """
    Manager for aggregate state persistence and computation.

    Handles:
    - Reading aggregate snapshot from disk
    - Computing statistics incrementally
    - Writing snapshot to disk
    - O(1) read operations

    Aggregate is derived incrementally - never requires full history scan.
    """

    def __init__(self, pair: str, pairs_dir: Optional[Path] = None):
        """
        Initialize aggregate state manager for a specific pair.

        Args:
            pair: Trading pair symbol
            pairs_dir: Base pairs directory path

        Note:
            No data loading on init.
            Use load() to read from disk.
        """
        self.pair = pair
        if pairs_dir is None:
            pairs_dir = Path(__file__).parent.parent / "pairs"
        self.aggregate_path = pairs_dir / pair / "aggregate" / "snapshot.json"

        # Thread safety for concurrent updates
        self._lock = threading.Lock()

    def load(self) -> Dict[str, Any]:
        """
        Load aggregate snapshot from disk.

        Returns:
            Aggregate snapshot dict with structure:
            {
                "symbol": str,
                "total_trades": int,
                "win_rate": float,
                "avg_pnl": float,
                "scalper": {"trades": int, "win_rate": float, "avg_pnl": float},
                "swing": {"trades": int, "win_rate": float, "avg_pnl": float},
                "last_updated": ISO-8601 timestamp
            }

        Returns empty snapshot if file doesn't exist.

        Note:
            O(1) operation - reads only the snapshot file.
            Does NOT scan entire knowledge files.
        """
        with self._lock:
            if not self.aggregate_path.exists():
                return self._create_empty_snapshot()

            try:
                with open(self.aggregate_path, 'r') as f:
                    snapshot = json.load(f)
                return snapshot
            except (json.JSONDecodeError, IOError) as e:
                # Corrupt file - return empty
                return self._create_empty_snapshot()

    def save(self, snapshot: Dict[str, Any]):
        """
        Save aggregate snapshot to disk.

        Args:
            snapshot: Aggregate snapshot dict

        Raises:
            IOError: If write fails

        Note:
            Atomic write operation.
            Overwrites existing snapshot.
        """
        with self._lock:
            # Ensure directory exists
            self.aggregate_path.parent.mkdir(parents=True, exist_ok=True)

            # Atomic write: write to temp file, then rename
            temp_path = self.aggregate_path.with_suffix('.tmp')
            with open(temp_path, 'w') as f:
                json.dump(snapshot, f, indent=2)

            # Atomic rename
            temp_path.replace(self.aggregate_path)

    def create_empty(self) -> Dict[str, Any]:
        """
        Create empty snapshot (convenience method).

        Returns:
            Empty aggregate snapshot

        Note:
            This is a convenience wrapper around _create_empty_snapshot().
        """
        return self._create_empty_snapshot()

    def _create_empty_snapshot(self) -> Dict[str, Any]:
        """
        Create empty aggregate snapshot.

        Returns:
            Empty snapshot with zero-initialized counters.
        """
        return {
            "symbol": self.pair,
            "total_trades": 0,
            "win_rate": 0.0,
            "avg_pnl": 0.0,
            "scalper": {
                "trades": 0,
                "win_rate": 0.0,
                "avg_pnl": 0.0
            },
            "swing": {
                "trades": 0,
                "win_rate": 0.0,
                "avg_pnl": 0.0
            },
            "last_updated": None
        }

    def compute_incremental(
        self,
        current_snapshot: Dict[str, Any],
        new_entry: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compute updated snapshot incrementally from new entry.

        Args:
            current_snapshot: Current aggregate snapshot
            new_entry: New knowledge entry from JSONL

        Returns:
            Updated snapshot

        Note:
            O(1) operation - only processes new entry.
            Does NOT read entire history.
            Pure computation - no side effects except calculation.
        """
        # Create new snapshot (copy)
        updated = current_snapshot.copy()

        # Update total trades
        updated["total_trades"] += 1

        # Update strategy-specific stats
        strategy = new_entry.get("strategy", "scalper")
        if strategy in ["scalper", "swing"]:
            strategy_stats = updated[strategy]
            strategy_stats["trades"] += 1

            # Update win rate if result known
            result = new_entry.get("result", "unknown")
            if result in ["win", "loss", "breakeven"]:
                if result == "win":
                    wins = strategy_stats.get("wins", 0) + 1
                    total = strategy_stats["trades"]
                    strategy_stats["win_rate"] = wins / total if total > 0 else 0.0
                    strategy_stats["wins"] = wins
                elif result == "loss":
                    wins = strategy_stats.get("wins", 0)
                    total = strategy_stats["trades"]
                    strategy_stats["win_rate"] = wins / total if total > 0 else 0.0
                    # No need to track losses separately for win rate
                # breakeven doesn't affect win rate

            # Update avg PnL
            pnl = new_entry.get("pnl", 0.0)
            current_avg = strategy_stats.get("avg_pnl", 0.0)
            total = strategy_stats["trades"]

            # Incremental average
            if total > 0:
                updated_avg = (current_avg * (total - 1) + pnl) / total
                strategy_stats["avg_pnl"] = updated_avg

        # Update overall stats
        updated["win_rate"] = self._compute_overall_win_rate(updated)
        updated["avg_pnl"] = self._compute_overall_avg_pnl(updated)

        # Update timestamp
        updated["last_updated"] = time.strftime("%Y-%m-%dT%H:%M:%S")

        return updated

    def _compute_overall_win_rate(self, snapshot: Dict[str, Any]) -> float:
        """
        Compute overall win rate across all strategies.

        Args:
            snapshot: Aggregate snapshot

        Returns:
            Overall win rate (0-1)
        """
        total_wins = 0
        total_trades = 0

        for strategy in ["scalper", "swing"]:
            strategy_stats = snapshot.get(strategy, {})
            wins = int(strategy_stats.get("wins", 0))
            trades = strategy_stats.get("trades", 0)
            total_wins += wins
            total_trades += trades

        if total_trades > 0:
            return total_wins / total_trades
        return 0.0

    def _compute_overall_avg_pnl(self, snapshot: Dict[str, Any]) -> float:
        """
        Compute overall average PnL across all strategies.

        Args:
            snapshot: Aggregate snapshot

        Returns:
            Average PnL
        """
        total_pnl = 0.0
        total_trades = 0

        for strategy in ["scalper", "swing"]:
            strategy_stats = snapshot.get(strategy, {})
            avg_pnl = strategy_stats.get("avg_pnl", 0.0)
            trades = strategy_stats.get("trades", 0)

            total_pnl += avg_pnl * trades
            total_trades += trades

        if total_trades > 0:
            return total_pnl / total_trades
        return 0.0

    def exists(self) -> bool:
        """
        Check if aggregate snapshot exists.

        Returns:
            True if snapshot file exists
        """
        return self.aggregate_path.exists()

    def get_path(self) -> Path:
        """
        Get the path to the aggregate snapshot file.

        Returns:
            Path object for snapshot file
        """
        return self.aggregate_path
