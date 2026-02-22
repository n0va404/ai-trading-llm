"""
Synaptrix AI Trading System - Main Entry Point

PHASE 10: Live Trading Orchestrator

This is the production control layer that orchestrates all phases
into a safe, deterministic live trading flow.

Responsibilities:
- Load configuration from config/
- Initialize scheduler (Phase 2)
- Instantiate MT5 bridge client (Phase 1)
- Register jobs for market data, decisions, execution, knowledge
- Orchestrate decision flow: data -> strategy -> validate -> execute -> log
- Safety checks, error handling, observability

PHASE 10 CONSTRAINTS:
- NO modification of earlier phase logic
- NO bypassing scheduler
- NO executing trades outside validator
- NO overriding strategy decisions
- NO LLM calls
- NO async/threading
- NO auto-optimization
"""

import sys
import time
import logging
import signal
import os
from pathlib import Path

# Load environment variables from .env file (if exists)
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        logging.info(f"Loaded environment variables from {env_path}")
except ImportError:
    # python-dotenv not installed - will use system environment variables
    pass
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml

# Phase imports
from scheduler.job_manager import JobManager
from execution.mt5_bridge import MT5BridgeClient
from execution.order_router import OrderRouter
from execution.validator import OrderValidator

from data.market.cache import MarketCache
from data.market.puller import MarketPuller

from strategy.scalper.decision import ScalperDecisionEngine
from strategy.swing.decision import SwingDecisionEngine

from aggregator.updater import AggregatorUpdater


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)-5s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


# ============================================================================
# GLOBAL STATE (for signal handling)
# ============================================================================

_job_manager: Optional[JobManager] = None
_running = False


# ============================================================================
# CONFIGURATION
# ============================================================================

class SystemConfig:
    """
    System configuration loader.

    Loads all config files from config/ directory.
    """

    def __init__(self, base_dir: Optional[Path] = None):
        """
        Initialize system config.

        Args:
            base_dir: Base directory (default: project root)
        """
        if base_dir is None:
            base_dir = Path(__file__).parent

        self.config_dir = base_dir / "config"
        self.pairs_dir = base_dir / "pairs"

        # Configs
        self.pairs_config: Dict[str, Any] = {}
        self.job_cycles_config: Dict[str, Any] = {}
        self.runtime_config: Dict[str, Any] = {}
        self.risk_config: Dict[str, Any] = {}

    def load_all(self):
        """Load all configuration files."""
        logger.info("Loading configuration files...")

        self.pairs_config = self._load_config("pairs.yaml")
        self.job_cycles_config = self._load_config("job_cycles.yaml")
        self.runtime_config = self._load_config("runtime.yaml")
        self.risk_config = self._load_config("risk.yaml")

        logger.info("Configuration loaded successfully")

    def _load_config(self, filename: str) -> Dict[str, Any]:
        """Load a single config file."""
        config_path = self.config_dir / filename

        if not config_path.exists():
            logger.warning(f"Config file not found: {filename}")
            return {}

        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def get_enabled_pairs(self) -> List[str]:
        """Get list of enabled trading pairs."""
        pairs = self.pairs_config.get("pairs", [])
        return pairs if isinstance(pairs, list) else []

    def get_runtime_mode(self) -> str:
        """Get runtime mode (backtest, paper, live)."""
        return self.runtime_config.get("mode", "paper")

    def is_live_mode(self) -> bool:
        """Check if running in live mode."""
        return self.get_runtime_mode() == "live"


# ============================================================================
# ORCHESTRATOR STATE
# ============================================================================

class OrchestratorState:
    """
    Live trading orchestrator state.

    Manages all system components for live trading.
    """

    def __init__(self, config: SystemConfig):
        """
        Initialize orchestrator state.

        Args:
            config: System configuration
        """
        self.config = config
        self.enabled_pairs = config.get_enabled_pairs()

        # Phase 1: MT5 Bridge
        self.mt5_bridge: Optional[MT5BridgeClient] = None

        # Phase 2: Scheduler
        self.job_manager: Optional[JobManager] = None

        # Per-pair components
        self.market_caches: Dict[str, MarketCache] = {}
        self.market_pullers: Dict[str, MarketPuller] = {}
        self.scalper_engines: Dict[str, ScalperDecisionEngine] = {}
        self.swing_engines: Dict[str, SwingDecisionEngine] = {}
        self.aggregators: Dict[str, AggregatorUpdater] = {}
        self.order_routers: Dict[str, OrderRouter] = {}

        # Execution components (shared)
        self.validator: Optional[OrderValidator] = None

        # Safety state
        self.mt5_error_count = 0
        self.max_mt5_errors = 5
        self.trading_paused = False

    def initialize(self) -> bool:
        """
        Initialize all system components.

        Returns:
            True if initialization successful, False otherwise

        Raises:
            Exception: If critical initialization fails
        """
        logger.info("=" * 60)
        logger.info("SYNAPTRIX AI TRADING SYSTEM - INITIALIZING")
        logger.info("=" * 60)
        logger.info(f"Runtime Mode: {self.config.get_runtime_mode()}")
        logger.info(f"Enabled Pairs: {self.enabled_pairs}")
        logger.info("")

        try:
            # Step 1: Initialize MT5 Bridge (Phase 1)
            if not self._init_mt5_bridge():
                return False

            # Step 2: Initialize validator (Phase 5)
            if not self._init_validator():
                return False

            # Step 3: Initialize LLM client (Phase 7 - Optional)
            if not self._init_llm_client():
                return False

            # Step 4: Initialize per-pair components
            if not self._init_per_pair_components():
                return False

            # Step 5: Initialize scheduler (Phase 2)
            if not self._init_scheduler():
                return False

            logger.info("")
            logger.info("=" * 60)
            logger.info("INITIALIZATION COMPLETE")
            logger.info("=" * 60)

            return True

        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            return False

    def _init_mt5_bridge(self) -> bool:
        """Initialize MT5 Bridge client."""
        logger.info("[INIT] Initializing MT5 Bridge...")

        try:
            self.mt5_bridge = MT5BridgeClient()

            # Health check
            health = self.mt5_bridge.health_check()

            if health.get("status") != "healthy":
                logger.error(f"MT5 Bridge health check failed: {health}")
                return False

            logger.info(f"  MT5 Bridge: CONNECTED")
            logger.info(f"  Base URL: {self.mt5_bridge.base_url}")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize MT5 Bridge: {e}")
            return False

    def _init_validator(self) -> bool:
        """Initialize order validator."""
        logger.info("[INIT] Initializing Order Validator...")

        try:
            self.validator = OrderValidator(
                risk_config=self.config.risk_config,
                pairs_config=self.config.pairs_config
            )
            logger.info("  Order Validator: READY")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize validator: {e}")
            return False

    def _init_llm_client(self) -> bool:
        """Initialize LLM client (optional)."""
        logger.info("[INIT] Initializing LLM Client...")

        try:
            from llm.z_ai_client import get_llm_client
            self.llm_client = get_llm_client()

            if self.llm_client:
                logger.info(f"  LLM Client: READY")
                logger.info(f"  Model: {self.llm_client.config.model}")
                logger.info(f"  API: {self.llm_client.config.base_url}")
            else:
                logger.info("  LLM Client: DISABLED (no API key)")
                logger.info("  System will trade without LLM analysis")

            return True

        except Exception as e:
            logger.warning(f"Failed to initialize LLM client: {e}")
            logger.info("  Continuing without LLM analysis...")
            self.llm_client = None
            return True  # LLM is optional, so don't fail

    def _init_per_pair_components(self) -> bool:
        """Initialize per-pair components."""
        logger.info(f"[INIT] Initializing {len(self.enabled_pairs)} trading pairs...")

        for pair in self.enabled_pairs:
            logger.info(f"  Pair: {pair}")

            # Market cache (Phase 3)
            cache = MarketCache()
            self.market_caches[pair] = cache

            # Market puller (Phase 3)
            puller = MarketPuller(
                pair=pair,
                mt5_bridge=self.mt5_bridge,
                cache=cache,
                default_ttl=1.0
            )
            self.market_pullers[pair] = puller

            # Scalper engine (Phase 4)
            scalper = ScalperDecisionEngine(pair)
            self.scalper_engines[pair] = scalper

            # Swing engine (Phase 4)
            swing = SwingDecisionEngine(pair)
            self.swing_engines[pair] = swing

            # Aggregator (Phase 6)
            aggregator = AggregatorUpdater(pair, self.config.pairs_dir)
            self.aggregators[pair] = aggregator

            # Order router (Phase 5)
            router = OrderRouter(
                mt5_bridge=self.mt5_bridge,
                validator=self.validator
            )
            self.order_routers[pair] = router

            logger.info(f"    Cache, Puller, Strategies, Aggregator, Router: OK")

        return True

    def _init_scheduler(self) -> bool:
        """Initialize job scheduler."""
        logger.info("[INIT] Initializing Job Scheduler...")

        try:
            self.job_manager = JobManager()

            # Register all jobs
            self._register_jobs()

            # Start scheduler
            self.job_manager.start()

            logger.info("  Job Scheduler: READY")
            logger.info(f"  Jobs registered: {len(self.job_manager.registry.get_all_job_names())}")

            return True

        except Exception as e:
            logger.error(f"Failed to initialize scheduler: {e}")
            return False

    def _register_jobs(self):
        """Register all jobs with the scheduler."""
        logger.info("[INIT] Registering jobs...")

        # Market data refresh job (all pairs)
        for pair in self.enabled_pairs:
            self.job_manager.registry.register_job(
                f"market_data_{pair}",
                self._make_market_data_job(pair),
                interval=self.config.job_cycles_config.get("market_data_pull_interval", 1)
            )

        # Scalper decision jobs
        for pair in self.enabled_pairs:
            self.job_manager.registry.register_job(
                f"scalper_decision_{pair}",
                self._make_scalper_decision_job(pair),
                interval=self.config.job_cycles_config.get("scalper_decision_interval", 2)
            )

        # Swing decision jobs
        for pair in self.enabled_pairs:
            self.job_manager.registry.register_job(
                f"swing_decision_{pair}",
                self._make_swing_decision_job(pair),
                interval=self.config.job_cycles_config.get("swing_decision_interval", 60)
            )

        # Account sync job
        self.job_manager.registry.register_job(
            "account_sync",
            self._make_account_sync_job(),
            interval=self.config.job_cycles_config.get("account_sync_interval", 5)
        )

        # Register all jobs in timer registry
        for job_name in self.job_manager.registry.get_all_job_names():
            interval = self.job_manager.registry.get_job_interval(job_name)
            self.job_manager.timer_registry.register(job_name, interval)

        logger.info(f"  Registered {len(self.job_manager.registry.get_all_job_names())} jobs")

    def _make_market_data_job(self, pair: str):
        """Create market data refresh job function."""
        def job():
            try:
                puller = self.market_pullers[pair]
                tick = puller.get_tick()
                logger.debug(f"[MARKET_DATA] {pair}: {tick.get('symbol')} Bid={tick.get('bid')} Ask={tick.get('ask')}")
                self.mt5_error_count = 0  # Reset error count on success
            except Exception as e:
                self._handle_mt5_error(f"Market data fetch failed for {pair}", e)
        return job

    def _make_scalper_decision_job(self, pair: str):
        """Create scalper decision job function."""
        def job():
            if self.trading_paused:
                logger.warning(f"[SCALPER] {pair}: Trading paused")
                return

            try:
                # Get market data
                puller = self.market_pullers[pair]
                tick = puller.get_tick()

                # Get REAL OHLC data from MT5 Bridge
                # Use 1-minute timeframe (M1) for scalping
                ohlc_response = self.mt5_bridge.get_ohlc(
                    symbol=pair,
                    timeframe="M1",  # 1 minute
                    count=100  # Last 100 candles
                )

                # Extract OHLC data from response
                ohlc_data = ohlc_response.get('data', [])

                # Build market context
                bid = tick.get("bid", 0)
                ask = tick.get("ask", 0)

                market_data = {
                    "bid": bid,
                    "ask": ask,
                    "spread": tick.get("spread", 0),
                    "ohlc_data": ohlc_data  # REAL data from MT5
                }

                # Get decision from strategy (Phase 4)
                engine = self.scalper_engines[pair]
                decision = engine.evaluate(market_data)

                # Log decision
                logger.info(
                    f"[SCALPER] {pair}: {decision['decision']} "
                    f"(confidence: {decision['confidence']:.2f}) "
                    f"[OHLC: {len(ohlc_data)} M1 candles]"
                )

                # LLM Analysis (Phase 7) - Get insights
                if self.llm_client:
                    try:
                        from llm import PromptBuilder, DecisionSchema
                        builder = PromptBuilder()
                        schema = DecisionSchema()

                        # Build prompt for LLM
                        aggregate = self.aggregators[pair].get_snapshot()
                        prompt = builder.build_explanation_prompt(
                            pair=pair,
                            strategy="scalper",
                            decision={
                                "action": decision["decision"],
                                "confidence": decision["confidence"],
                                "tick": tick,
                                "timestamp": tick.get("timestamp", ""),
                                "entry_type": "market",
                                "pending_type": "none",
                                "reasoning": decision.get("reason", "")
                            },
                            aggregate_state=aggregate
                        )

                        # Get LLM analysis
                        llm_response = self.llm_client.get_completion(
                            prompt=prompt,
                            response_schema=schema.get_schema()
                        )

                        # Validate and log LLM insights
                        is_valid, error, sanitized = schema.validate_advisory_response(llm_response)
                        if is_valid:
                            logger.info(f"[LLM] {pair} Analysis:")
                            logger.info(f"  Explanation: {sanitized['explanation']}")
                            logger.info(f"  Bias: {sanitized['bias_detected']}")
                            logger.info(f"  Confidence: {sanitized['confidence_suggestion']}")
                            logger.info(f"  Risk: {sanitized['risk_notes']}")
                    except Exception as llm_error:
                        logger.warning(f"[LLM] {pair} Analysis failed: {llm_error}")
                        # Continue trading even if LLM fails

                # Execute if not HOLD
                if decision["decision"] != "HOLD":
                    self._execute_decision(pair, decision)

            except Exception as e:
                logger.error(f"[SCALPER] {pair}: Decision failed: {e}")

        return job

    def _make_swing_decision_job(self, pair: str):
        """Create swing decision job function."""
        def job():
            if self.trading_paused:
                logger.warning(f"[SWING] {pair}: Trading paused")
                return

            try:
                # Get market data
                puller = self.market_pullers[pair]
                tick = puller.get_tick()

                # Get REAL OHLC data from MT5 Bridge
                # Use 5-minute timeframe (M5) for swing trading
                ohlc_response = self.mt5_bridge.get_ohlc(
                    symbol=pair,
                    timeframe="M5",  # 5 minute
                    count=100  # Last 100 candles
                )

                # Extract OHLC data from response
                ohlc_data = ohlc_response.get('data', [])

                # Build market context
                bid = tick.get("bid", 0)
                ask = tick.get("ask", 0)

                market_data = {
                    "bid": bid,
                    "ask": ask,
                    "spread": tick.get("spread", 0),
                    "ohlc_data": ohlc_data  # REAL data from MT5
                }

                # Get decision from strategy (Phase 4)
                engine = self.swing_engines[pair]
                decision = engine.evaluate(market_data)

                # Log decision
                logger.info(
                    f"[SWING] {pair}: {decision['decision']} "
                    f"(confidence: {decision['confidence']:.2f}) "
                    f"[OHLC: {len(ohlc_data)} M5 candles]"
                )

                # LLM Analysis (Phase 7) - Get insights
                if self.llm_client:
                    try:
                        from llm import PromptBuilder, DecisionSchema
                        builder = PromptBuilder()
                        schema = DecisionSchema()

                        # Build prompt for LLM
                        aggregate = self.aggregators[pair].get_snapshot()
                        prompt = builder.build_explanation_prompt(
                            pair=pair,
                            strategy="swing",
                            decision={
                                "action": decision["decision"],
                                "confidence": decision["confidence"],
                                "tick": tick,
                                "timestamp": tick.get("timestamp", ""),
                                "entry_type": "market",
                                "pending_type": "none",
                                "reasoning": decision.get("reasoning", "")
                            },
                            aggregate_state=aggregate
                        )

                        # Get LLM analysis
                        llm_response = self.llm_client.get_completion(
                            prompt=prompt,
                            response_schema=schema.get_schema()
                        )

                        # Validate and log LLM insights
                        is_valid, error, sanitized = schema.validate_advisory_response(llm_response)
                        if is_valid:
                            logger.info(f"[LLM] {pair} Analysis:")
                            logger.info(f"  Explanation: {sanitized['explanation']}")
                            logger.info(f"  Bias: {sanitized['bias_detected']}")
                            logger.info(f"  Confidence: {sanitized['confidence_suggestion']}")
                            logger.info(f"  Risk: {sanitized['risk_notes']}")
                    except Exception as llm_error:
                        logger.warning(f"[LLM] {pair} Analysis failed: {llm_error}")
                        # Continue trading even if LLM fails

                # Execute if not HOLD
                if decision["decision"] != "HOLD":
                    self._execute_decision(pair, decision)

            except Exception as e:
                logger.error(f"[SWING] {pair}: Decision failed: {e}")

        return job

    def _make_account_sync_job(self):
        """Create account sync job function."""
        def job():
            try:
                response = self.mt5_bridge.get_account()

                # Account data is nested under "account" key
                account_data = response.get('account', {})
                if not account_data:
                    # Fallback: try response directly
                    account_data = response

                # Extract values with defaults
                balance = account_data.get('balance', 0) or 0
                equity = account_data.get('equity', 0) or 0
                margin = account_data.get('margin', 0) or 0
                profit = account_data.get('profit', 0) or 0
                free_margin = account_data.get('freemargin', 0) or 0
                leverage = account_data.get('leverage', 0) or 0

                # Log account info
                logger.info(
                    f"[ACCOUNT] Balance: {balance:.2f} | "
                    f"Equity: {equity:.2f} | "
                    f"Margin: {margin:.2f} | "
                    f"Profit: {profit:.2f} | "
                    f"FreeMargin: {free_margin:.2f} | "
                    f"Leverage: {leverage}"
                )

                self.mt5_error_count = 0  # Reset error count on success
            except Exception as e:
                self._handle_mt5_error("Account sync failed", e)
        return job

    def _execute_decision(self, pair: str, decision: Dict[str, Any]):
        """
        Execute a trading decision.

        Args:
            pair: Trading pair
            decision: Decision dict from Phase 4 strategy
        """
        try:
            # Get order router
            router = self.order_routers[pair]

            # Execute decision (Phase 5)
            result = router.execute_decision(decision)

            if result.get("executed"):
                order_id = result.get("order_id")
                logger.info(f"[EXECUTION] {pair}: Order executed {order_id}")

                # Log to knowledge (Phase 6)
                aggregator = self.aggregators[pair]
                aggregator.log_decision(decision, mode="live")

            else:
                reason = result.get("reason", "Unknown")
                logger.debug(f"[EXECUTION] {pair}: Not executed - {reason}")

        except Exception as e:
            logger.error(f"[EXECUTION] {pair}: Execution failed: {e}")

    def _handle_mt5_error(self, context: str, error: Exception):
        """
        Handle MT5 errors with safety checks.

        Args:
            context: Error context description
            error: The exception that occurred
        """
        self.mt5_error_count += 1

        logger.error(f"[MT5_ERROR] ({self.mt5_error_count}/{self.max_mt5_errors}) {context}: {error}")

        if self.mt5_error_count >= self.max_mt5_errors:
            logger.critical("Max MT5 errors reached - PAUSING TRADING")
            self.trading_paused = True

    def shutdown(self):
        """Shutdown all components gracefully."""
        logger.info("=" * 60)
        logger.info("SHUTTING DOWN SYNAPTRIX AI TRADING SYSTEM")
        logger.info("=" * 60)

        if self.job_manager:
            logger.info("Stopping Job Scheduler...")
            self.job_manager.stop()

        logger.info("Shutdown complete")


# ============================================================================
# GLOBAL ORCHESTRATOR INSTANCE
# ============================================================================

_orchestrator: Optional[OrchestratorState] = None


# ============================================================================
# SIGNAL HANDLERS
# ============================================================================

def signal_handler(signum, frame):
    """Handle interrupt signals for graceful shutdown."""
    global _running, _orchestrator

    logger.info(f"Received signal {signum} - shutting down...")
    _running = False

    if _orchestrator:
        _orchestrator.shutdown()

    sys.exit(0)


# ============================================================================
# COMMANDS
# ============================================================================

def cmd_init(config: SystemConfig):
    """Initialize pair directories."""
    pairs = config.get_enabled_pairs()

    if not pairs:
        logger.warning("No pairs enabled in config/pairs.yaml")
        return

    logger.info(f"Initializing directories for {len(pairs)} pairs...")

    for pair in pairs:
        pair_dir = config.pairs_dir / pair

        # Create subdirectories
        (pair_dir / "knowledge").mkdir(parents=True, exist_ok=True)
        (pair_dir / "aggregate").mkdir(parents=True, exist_ok=True)
        (pair_dir / "state").mkdir(parents=True, exist_ok=True)

        logger.info(f"  Created: {pair_dir}")

    logger.info("Initialization complete")


def cmd_start(config: SystemConfig):
    """Start the live trading orchestrator."""
    global _orchestrator, _running

    # Check runtime mode
    if not config.is_live_mode():
        logger.warning(f"Runtime mode is '{config.get_runtime_mode()}', not 'live'")
        logger.warning("No actual orders will be executed")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            logger.info("Aborted")
            return

    # Initialize orchestrator
    _orchestrator = OrchestratorState(config)

    if not _orchestrator.initialize():
        logger.error("Initialization failed - aborting startup")
        return

    # Start main loop
    _running = True
    logger.info("")
    logger.info("=" * 60)
    logger.info("SYNAPTRIX AI TRADING SYSTEM - RUNNING")
    logger.info("=" * 60)
    logger.info("Press Ctrl+C to stop")
    logger.info("")

    try:
        # Main loop: drive scheduler
        while _running:
            # Run pending jobs
            _orchestrator.job_manager.run_pending()

            # Small sleep to prevent busy-waiting
            time.sleep(0.1)

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        _orchestrator.shutdown()


def cmd_stop():
    """Stop the running system."""
    logger.info("Stop command - send SIGINT to process")
    logger.info("Or press Ctrl+C if running in foreground")


def cmd_status(config: SystemConfig):
    """Show system status."""
    logger.info("Synaptrix AI Trading System - Status")
    logger.info("")
    logger.info(f"Runtime Mode: {config.get_runtime_mode()}")
    logger.info(f"Enabled Pairs: {config.get_enabled_pairs()}")
    logger.info("")
    logger.info("System Status: " + ("RUNNING" if _running else "STOPPED"))


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python main.py [start|stop|status|init]")
        sys.exit(1)

    command = sys.argv[1]

    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Load configuration
    config = SystemConfig()
    config.load_all()

    # Route command
    if command == "init":
        cmd_init(config)

    elif command == "start":
        cmd_start(config)

    elif command == "stop":
        cmd_stop()

    elif command == "status":
        cmd_status(config)

    else:
        print(f"Unknown command: {command}")
        print("Available commands: start, stop, status, init")
        sys.exit(1)


if __name__ == "__main__":
    main()
