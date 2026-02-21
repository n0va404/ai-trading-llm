"""
Timer Utility - Phase 2 Implementation

Responsibilities:
- Track current time
- Calculate elapsed time
- Determine if a job is due

This is a utility module for the scheduler.
It does NOT execute any jobs - only timing calculations.

PHASE 2 CONSTRAINTS:
- No sleep loops
- No threads
- No async
- Deterministic logic only
- No external API calls
"""

import time
from typing import Dict, Optional


class JobTimer:
    """
    Timer for tracking job execution schedules.

    Each job has its own timer instance.
    """

    def __init__(self, interval: int):
        """
        Initialize a job timer.

        Args:
            interval: Seconds between job executions

        Note:
            Timer starts in "never run" state.
            First call to should_run() will return True.
        """
        self.interval = interval
        self.last_run: Optional[float] = None

    def should_run(self, current_time: Optional[float] = None) -> bool:
        """
        Check if job should run based on elapsed time.

        Args:
            current_time: Optional Unix timestamp (uses time.time() if None)

        Returns:
            True if interval has elapsed since last run (or never run)

        Note:
            If never run (last_run is None), returns True.
        """
        now = current_time if current_time is not None else time.time()

        # Never run before - should run now
        if self.last_run is None:
            return True

        # Check if interval has elapsed
        elapsed = now - self.last_run
        return elapsed >= self.interval

    def mark_run(self, current_time: Optional[float] = None):
        """
        Mark the job as having run now.

        Args:
            current_time: Optional Unix timestamp (uses time.time() if None)
        """
        self.last_run = current_time if current_time is not None else time.time()

    def next_run(self, current_time: Optional[float] = None) -> float:
        """
        Calculate the Unix timestamp of next scheduled run.

        Args:
            current_time: Optional Unix timestamp (uses time.time() if None)

        Returns:
            Unix timestamp of next run

        Note:
            If never run, returns current_time + interval.
        """
        now = current_time if current_time is not None else time.time()

        if self.last_run is None:
            return now + self.interval

        return self.last_run + self.interval

    def time_until_next(self, current_time: Optional[float] = None) -> float:
        """
        Calculate seconds until next scheduled run.

        Args:
            current_time: Optional Unix timestamp (uses time.time() if None)

        Returns:
            Seconds until next run (can be 0 or negative if due)

        Note:
            Useful for display purposes, not for scheduling.
        """
        now = current_time if current_time is not None else time.time()
        next_time = self.next_run(now)
        return max(0, next_time - now)


class TimerRegistry:
    """
    Registry for managing multiple job timers.

    Each job has its own timer tracked by name.
    """

    def __init__(self):
        """
        Initialize the timer registry.

        Creates empty registry.
        No timers are registered until register() is called.
        """
        self.timers: Dict[str, JobTimer] = {}

    def register(self, name: str, interval: int):
        """
        Register a new timer for a job.

        Args:
            name: Unique job identifier
            interval: Seconds between executions

        Note:
            If a timer with this name already exists, it will be replaced.
        """
        self.timers[name] = JobTimer(interval)

    def should_run(self, name: str, current_time: Optional[float] = None) -> bool:
        """
        Check if a specific job should run.

        Args:
            name: Job identifier
            current_time: Optional Unix timestamp

        Returns:
            True if the job's interval has elapsed

        Raises:
            KeyError: If job name not registered
        """
        if name not in self.timers:
            raise KeyError(f"Job '{name}' not registered in timer registry")

        return self.timers[name].should_run(current_time)

    def mark_run(self, name: str, current_time: Optional[float] = None):
        """
        Mark a specific job as having run.

        Args:
            name: Job identifier
            current_time: Optional Unix timestamp

        Raises:
            KeyError: If job name not registered
        """
        if name not in self.timers:
            raise KeyError(f"Job '{name}' not registered in timer registry")

        self.timers[name].mark_run(current_time)

    def get_timer(self, name: str) -> JobTimer:
        """
        Get the timer for a specific job.

        Args:
            name: Job identifier

        Returns:
            JobTimer instance

        Raises:
            KeyError: If job name not registered
        """
        if name not in self.timers:
            raise KeyError(f"Job '{name}' not registered in timer registry")

        return self.timers[name]

    def get_all_job_names(self) -> list[str]:
        """
        Get list of all registered job names.

        Returns:
            List of job identifiers
        """
        return list(self.timers.keys())

    def clear(self):
        """
        Clear all timers from registry.

        Useful for testing or reset scenarios.
        """
        self.timers.clear()
