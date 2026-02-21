"""
Job Manager - Phase 2 Implementation

Responsibilities:
- Load job_cycles.yaml
- Register jobs from JobRegistry
- Evaluate which jobs are due
- Invoke registered job callables

This is the central scheduler for the entire system.
It does NOT contain any trading logic - only job orchestration.

PHASE 2 CONSTRAINTS:
- No knowledge of what the job does
- Treat jobs as opaque callables
- Support safe start / stop
- No infinite loops
- No threads
- No async
"""

import time
import logging
from typing import Dict, List, Optional, Callable
from pathlib import Path

from scheduler.timer import TimerRegistry
from scheduler.job_registry import JobRegistry


# Configure logging for scheduler
logger = logging.getLogger(__name__)


class JobExecutionError(Exception):
    """Raised when a job callable raises an exception."""
    pass


class JobManager:
    """
    Central job scheduler for the Synaptrix system.

    Manages all scheduled jobs:
    - Market data pulling
    - Account syncing
    - Strategy decision cycles (scalper, swing)
    - News pulling
    - Aggregation updates

    This scheduler does NOT own the main loop.
    It is driven by external calls to run_pending().
    """

    def __init__(
        self,
        registry: Optional[JobRegistry] = None,
        timer_registry: Optional[TimerRegistry] = None
    ):
        """
        Initialize the JobManager.

        Args:
            registry: Optional JobRegistry instance (creates new if None)
            timer_registry: Optional TimerRegistry instance (creates new if None)

        Note:
            Scheduler starts in STOPPED state.
            Call start() to enable job execution.
            No jobs are registered until register_all_jobs() is called.
        """
        self.registry = registry or JobRegistry()
        self.timer_registry = timer_registry or TimerRegistry()
        self._running = False
        self._jobs_executed = 0
        self._jobs_failed = 0
        self._last_tick: Optional[float] = None

    def register_all_jobs(self):
        """
        Register all jobs from registry and timer registry.

        This loads jobs from config/job_cycles.yaml and registers them.

        Raises:
            FileNotFoundError: If config file not found
            KeyError: If config keys are invalid

        Note:
            In Phase 2, all jobs use placeholder functions.
            Actual implementations will be added in later phases.
        """
        from scheduler.job_registry import register_phase2_jobs

        # Register jobs with placeholder functions
        register_phase2_jobs(self.registry)

        # Register timers for each job
        for job_name in self.registry.get_all_job_names():
            interval = self.registry.get_job_interval(job_name)
            self.timer_registry.register(job_name, interval)

        logger.info(
            f"Registered {len(self.registry.get_all_job_names())} jobs"
        )

    def start(self):
        """
        Start the scheduler.

        Enables job execution.
        Scheduler must be started before run_pending() will execute jobs.

        Note:
            This does NOT start an automatic loop.
            The scheduler is driven by external calls to run_pending().
        """
        if self._running:
            logger.warning("Scheduler already started")
            return

        self._running = True
        self._last_tick = None
        logger.info("Scheduler started")

    def stop(self):
        """
        Stop the scheduler.

        Disables job execution.
        Pending jobs will not execute after stop().

        Note:
            This is a graceful stop.
            Currently running jobs (if any) are not interrupted.
        """
        if not self._running:
            logger.warning("Scheduler already stopped")
            return

        self._running = False
        logger.info(
            f"Scheduler stopped. "
            f"Jobs executed: {self._jobs_executed}, "
            f"Jobs failed: {self._jobs_failed}"
        )

    def is_running(self) -> bool:
        """
        Check if scheduler is running.

        Returns:
            True if scheduler is in RUNNING state
        """
        return self._running

    def run_pending(self, current_time: Optional[float] = None):
        """
        Check all jobs and execute those that are due.

        This is the MAIN ENTRY POINT for the scheduler.
        Called by external loop (e.g., main.py) on each tick.

        Args:
            current_time: Optional Unix timestamp (uses time.time() if None)

        Execution Model:
        1. Check if scheduler is running
        2. For each registered job:
           - Check if timer says it's due
           - If due: execute job function
           - Catch and log any exceptions
           - Mark job as run in timer

        Note:
            This method does NOT sleep or block.
            It returns immediately after checking all jobs.
        """
        # Must be started to execute jobs
        if not self._running:
            return

        now = current_time if current_time is not None else time.time()
        self._last_tick = now

        # Check each job
        for job_name in self.timer_registry.get_all_job_names():
            try:
                # Check if job is due
                if self.timer_registry.should_run(job_name, now):
                    self._execute_job(job_name, now)
            except Exception as e:
                # Timer error - log but continue checking other jobs
                logger.error(
                    f"Timer error for job '{job_name}': {e}",
                    exc_info=True
                )
                self._jobs_failed += 1

    def _execute_job(self, job_name: str, current_time: float):
        """
        Execute a single job.

        Args:
            job_name: Name of job to execute
            current_time: Current Unix timestamp

        Raises:
            JobExecutionError: If job raises an exception

        Note:
            Job exceptions are caught, logged, and re-raised.
            The scheduler continues processing other jobs.
        """
        if not self.registry.is_job_registered(job_name):
            logger.error(f"Job '{job_name}' not in registry")
            self._jobs_failed += 1
            return

        try:
            # Get job function
            job_func = self.registry.get_job_func(job_name)

            # Execute job
            logger.debug(f"Executing job: {job_name}")
            job_func()

            # Mark as run
            self.timer_registry.mark_run(job_name, current_time)
            self._jobs_executed += 1

            logger.debug(f"Job completed: {job_name}")

        except Exception as e:
            # Job failed - log but don't crash scheduler
            logger.error(
                f"Job '{job_name}' failed: {e}",
                exc_info=True
            )

            # Still mark as run to avoid rapid retry
            self.timer_registry.mark_run(job_name, current_time)
            self._jobs_failed += 1

            raise JobExecutionError(
                f"Job '{job_name}' failed: {e}"
            ) from e

    def status(self) -> Dict[str, str]:
        """
        Get status of all registered jobs.

        Returns:
            Dict mapping job names to status strings

        Status values:
        - "RUNNING": Job executed successfully
        - "FAILED": Job failed on last execution
        - "PENDING": Job waiting to run
        - "DISABLED": Job disabled in registry
        """
        status_dict = {}

        for job_name in self.registry.get_all_job_names():
            # TODO: Add proper job status tracking
            # For now, all jobs are PENDING
            status_dict[job_name] = "PENDING"

        return status_dict

    def get_stats(self) -> Dict[str, int]:
        """
        Get scheduler statistics.

        Returns:
            Dict with:
            - jobs_registered: Number of registered jobs
            - jobs_executed: Total jobs executed
            - jobs_failed: Total jobs failed
            - is_running: 1 if running, 0 if stopped
        """
        return {
            "jobs_registered": len(self.registry.get_all_job_names()),
            "jobs_executed": self._jobs_executed,
            "jobs_failed": self._jobs_failed,
            "is_running": 1 if self._running else 0
        }

    def get_job_info(self, job_name: str) -> Dict[str, any]:
        """
        Get detailed information about a specific job.

        Args:
            job_name: Job identifier

        Returns:
            Dict with:
            - name: Job name
            - interval: Interval in seconds
            - description: Job description
            - enabled: Whether job is enabled
            - last_run: Unix timestamp of last run (or None)
            - next_run: Unix timestamp of next run

        Raises:
            KeyError: If job not found
        """
        if not self.registry.is_job_registered(job_name):
            raise KeyError(f"Job '{job_name}' not found")

        timer = self.timer_registry.get_timer(job_name)
        interval = self.registry.get_job_interval(job_name)

        return {
            "name": job_name,
            "interval": interval,
            "description": job_name,  # TODO: Get from registry
            "enabled": True,  # TODO: Get from registry
            "last_run": timer.last_run,
            "next_run": timer.next_run()
        }

    def reset_stats(self):
        """
        Reset scheduler statistics.

        Resets execution and failure counters.
        Useful for testing or monitoring reset.
        """
        self._jobs_executed = 0
        self._jobs_failed = 0
