"""
Synaptrix AI Trading System - Main Entry Point

This is the universal entry point for the entire system.
Responsibilities:
- Initialize configuration
- Setup scheduler with registered jobs
- Provide CLI interface for starting/stopping the system

This file does NOT contain any trading logic.
It only orchestrates the startup and shutdown sequences.
"""

import sys
from pathlib import Path

# TODO: Add imports when modules are implemented
# from scheduler.job_manager import JobManager
# from config import load_all_configs


def main():
    """
    Main entry point for the Synaptrix trading system.

    Usage:
        python main.py [command]

    Commands:
        start   - Start the scheduler and all registered jobs
        stop    - Gracefully stop the system
        status  - Show system status
        init    - Initialize pair directories from config
    """
    if len(sys.argv) < 2:
        print("Usage: python main.py [start|stop|status|init]")
        sys.exit(1)

    command = sys.argv[1]

    if command == "start":
        print("Starting Synaptrix AI Trading System...")
        # TODO: Initialize and start JobManager
        # TODO: Load configuration from config/
        # TODO: Validate pair directories exist
        raise NotImplementedError("Start command not yet implemented")

    elif command == "stop":
        print("Stopping Synaptrix AI Trading System...")
        # TODO: Signal JobManager to stop
        raise NotImplementedError("Stop command not yet implemented")

    elif command == "status":
        print("Synaptrix AI Trading System Status")
        # TODO: Query JobManager for status
        raise NotImplementedError("Status command not yet implemented")

    elif command == "init":
        print("Initializing pair directories...")
        # TODO: Create pair directories from config/pairs.yaml
        raise NotImplementedError("Init command not yet implemented")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
