"""
Job Registry - Phase 2 Implementation

Responsibilities:
- Maintain a registry of job names
- Map job names → callable placeholders
- No actual job logic

This module serves as the central registry for all system jobs.
It does NOT execute jobs - only defines and registers them.

PHASE 2 CONSTRAINTS:
- Jobs are symbolic at this phase
- Actual execution logic will be injected in later phases
- No network calls
- No MT5 calls
- No trading logic
"""

from typing import Callable, Dict, Any, Optional
import yaml
from pathlib import Path


# Placeholder job functions for Phase 2
# These will be replaced with actual implementations in later phases

def _placeholder_job(job_name: str):
    """
    Placeholder job function for Phase 2.

    In Phase 2, jobs are symbolic - they don't do anything yet.
    This placeholder exists to satisfy the callable requirement.

    Args:
        job_name: Name of the job being executed

    Note:
        This will be replaced with actual job functions in later phases.
    """
    # TODO: Replace with actual job implementations in Phase 3+
    pass


class JobRegistry:
    """
    Registry for maintaining job definitions and their intervals.

    Jobs are mapped to callable functions.
    In Phase 2, all jobs use placeholder functions.
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the job registry.

        Args:
            config_path: Optional path to job_cycles.yaml
                        (defaults to config/job_cycles.yaml)

        Note:
            No jobs are registered until load_config() is called.
        """
        if config_path is None:
            # Default path relative to project root
            config_path = Path(__file__).parent.parent / "config" / "job_cycles.yaml"

        self.config_path = config_path
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self._config: Dict[str, int] = {}

    def load_config(self) -> Dict[str, int]:
        """
        Load job intervals from config/job_cycles.yaml.

        Returns:
            Dictionary mapping job config keys to interval values

        Raises:
            FileNotFoundError: If config file not found
            yaml.YAMLError: If config file is invalid

        Note:
            This reads the config but does NOT register jobs yet.
            Call register_jobs() to actually register jobs.
        """
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Job cycles config not found: {self.config_path}"
            )

        with open(self.config_path, 'r') as f:
            self._config = yaml.safe_load(f)

        return self._config

    def register_job(
        self,
        name: str,
        func: Callable,
        interval: int,
        description: Optional[str] = None
    ):
        """
        Register a single job.

        Args:
            name: Unique job identifier
            func: Callable to execute on each cycle
            interval: Seconds between executions
            description: Optional human-readable description

        Note:
            If a job with this name already exists, it will be replaced.
        """
        self.jobs[name] = {
            "func": func,
            "interval": interval,
            "description": description or name,
            "enabled": True
        }

    def register_from_config(self, job_name: str, func: Callable):
        """
        Register a job using interval from config.

        Args:
            job_name: Name of job (must match config key)
            func: Callable to execute on each cycle

        Raises:
            KeyError: If job_name not found in config
            ValueError: If config not loaded yet

        Note:
            The job_name should match the config key name.
            Example: "market_data_pull_interval" -> job should be named "market_data_pull"
        """
        if not self._config:
            raise ValueError(
                "Config not loaded. Call load_config() first."
            )

        # Convert job_name to config key
        # Example: "market_data_pull" -> "market_data_pull_interval"
        config_key = f"{job_name}_interval"

        if config_key not in self._config:
            raise KeyError(
                f"Job '{job_name}' not found in config. "
                f"Looking for key: {config_key}"
            )

        interval = self._config[config_key]
        self.register_job(job_name, func, interval)

    def get_job_func(self, name: str) -> Callable:
        """
        Get the callable function for a job.

        Args:
            name: Job identifier

        Returns:
            Callable function

        Raises:
            KeyError: If job not registered
        """
        if name not in self.jobs:
            raise KeyError(f"Job '{name}' not registered")

        return self.jobs[name]["func"]

    def get_job_interval(self, name: str) -> int:
        """
        Get the interval for a job.

        Args:
            name: Job identifier

        Returns:
            Interval in seconds

        Raises:
            KeyError: If job not registered
        """
        if name not in self.jobs:
            raise KeyError(f"Job '{name}' not registered")

        return self.jobs[name]["interval"]

    def get_all_job_names(self) -> list[str]:
        """
        Get list of all registered job names.

        Returns:
            List of job identifiers
        """
        return list(self.jobs.keys())

    def is_job_registered(self, name: str) -> bool:
        """
        Check if a job is registered.

        Args:
            name: Job identifier

        Returns:
            True if job exists in registry
        """
        return name in self.jobs


def register_phase2_jobs(registry: JobRegistry):
    """
    Register Phase 2 placeholder jobs.

    In Phase 2, jobs are symbolic - they use placeholder functions.
    Actual job implementations will be added in later phases.

    Args:
        registry: JobRegistry instance to populate

    Jobs registered:
    - market_data_pull
    - account_sync
    - scalper_decision
    - swing_decision
    - news_pull
    - aggregator_update
    - knowledge_backup

    Note:
        All jobs use _placeholder_job function in Phase 2.
    """
    # Load config first
    config = registry.load_config()

    # Register jobs with placeholder functions
    # Each job gets its interval from config

    # Market data pull: fetch current prices
    registry.register_from_config(
        "market_data_pull",
        lambda: _placeholder_job("market_data_pull")
    )

    # Account sync: sync account state
    registry.register_from_config(
        "account_sync",
        lambda: _placeholder_job("account_sync")
    )

    # Scalper decision: evaluate scalper opportunities
    registry.register_from_config(
        "scalper_decision",
        lambda: _placeholder_job("scalper_decision")
    )

    # Swing decision: evaluate swing opportunities
    registry.register_from_config(
        "swing_decision",
        lambda: _placeholder_job("swing_decision")
    )

    # News pull: fetch news updates
    registry.register_from_config(
        "news_pull",
        lambda: _placeholder_job("news_pull")
    )

    # Aggregator update: update pair aggregates
    registry.register_from_config(
        "aggregator_update",
        lambda: _placeholder_job("aggregator_update")
    )

    # Knowledge backup: backup knowledge files
    registry.register_from_config(
        "knowledge_backup",
        lambda: _placeholder_job("knowledge_backup")
    )


def load_interval(key: str, config_path: Optional[Path] = None) -> int:
    """
    Load a single job interval from config.

    Args:
        key: Configuration key (e.g., "market_data_pull_interval")
        config_path: Optional path to job_cycles.yaml

    Returns:
        Interval in seconds

    Raises:
        FileNotFoundError: If config file not found
        KeyError: If key not found in config

    Example:
        >>> interval = load_interval("market_data_pull_interval")
        >>> print(interval)
        1
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config" / "job_cycles.yaml"

    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    if key not in config:
        raise KeyError(f"Key '{key}' not found in {config_path}")

    return config[key]
