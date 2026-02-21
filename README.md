# Synaptrix AI Trading System

## Project Status

**Current Phase:** Phase 2 - Job Cycle Engine (Scheduler) ✅

**Completed Phases:**
- ✅ Phase 0: Project Skeleton
- ✅ Phase 1: MT5 HTTP Bridge Integration
- ✅ Phase 2: Job Cycle Engine (Scheduler)

### Architecture Principles

1. **Pair Isolation** - Each trading pair has its own state, knowledge, and aggregate
2. **Job-Cycle Driven** - Scheduler-driven execution, NOT infinite loops
3. **Knowledge System** - JSONL-based append-only knowledge storage
4. **No Global Mutable State** - All state is pair-isolated

### Project Structure

```
ai-trading-llm/
├── main.py                 # Universal entry point
├── config/                 # Configuration files (YAML)
├── scheduler/              # Job scheduler and timer
├── data/                   # Data pullers and caches
├── strategy/               # Trading strategies (scalper, swing)
├── llm/                    # LLM client and prompt builder
├── execution/              # Order execution and validation
├── aggregator/             # Aggregate state management
├── pairs/                  # Pair-specific data (isolated)
├── logs/                   # Decision and error logs
└── utils/                  # Utility functions
```

### What's Implemented (Phase 0)

✅ Complete folder structure
✅ Configuration file schemas (pairs.yaml, risk.yaml, runtime.yaml, job_cycles.yaml)
✅ Module interface contracts with clear docstrings
✅ Pair isolation structure (SAMPLE_PAIR template)
✅ Knowledge system structure (JSONL files)

### What's Implemented (Phase 1)

✅ MT5BridgeClient - Stateless HTTP client for MT5 Bridge API
✅ All 9 required MT5 Bridge API methods:
  - `health_check()` - System health monitoring
  - `get_tick()`, `get_ticks()`, `get_ohlc()` - Market data
  - `get_account()`, `get_positions()`, `get_orders()` - Account state
  - `place_order()`, `place_pending_order()` - Trade execution
✅ Exception hierarchy (ConnectionError, ResponseError)
✅ Phase 0 backward compatibility maintained
✅ NO trading logic, NO caching, NO retries (pure transport adapter)

### What's Implemented (Phase 2)

✅ JobTimer - Per-job timing tracking
✅ TimerRegistry - Multi-job timer management
✅ JobRegistry - Job definitions and config loading
✅ JobManager - Central scheduler orchestrator
✅ External tick model (no infinite loops)
✅ All 7 jobs registered from config/job_cycles.yaml
✅ Clean start/stop mechanism
✅ Comprehensive error handling
✅ Zero MT5 imports (clean separation)
✅ Zero business logic (pure scheduler)

**Registered Jobs:**
- `market_data_pull` (1s) - Fetch current prices
- `account_sync` (5s) - Sync account state
- `scalper_decision` (2s) - Evaluate scalper opportunities
- `swing_decision` (60s) - Evaluate swing opportunities
- `news_pull` (300s) - Fetch news updates
- `aggregator_update` (10s) - Update pair aggregates
- `knowledge_backup` (3600s) - Backup knowledge files

### What's NOT Implemented Yet

❌ Actual job implementations (Phase 2: placeholders only)
❌ Trading decision logic
❌ Strategy execution
❌ Data layer implementation (pullers, sync with actual MT5 calls)
❌ LLM integration
❌ Order routing and validation logic

### Next Steps

After Phase 2 completion:
1. Implement data layer (market puller, account sync, news puller)
2. Implement execution layer (order_router, validator)
3. Implement strategy rules and decision engines
4. Implement LLM integration
5. Implement knowledge management

### Quick Start

```bash
# Initialize pair directories
python main.py init

# Start the system (scheduler)
python main.py start

# Check system status
python main.py status

# Stop the system
python main.py stop
```

### Configuration

Edit files in `config/` before running:
- `config/pairs.yaml` - Enable trading pairs
- `config/risk.yaml` - Set risk limits
- `config/runtime.yaml` - Set mode (backtest/paper/live)
- `config/job_cycles.yaml` - Configure job intervals

### Environment Variables

Required:
- `ZAI_API_KEY` - Z.AI API key for LLM
- `BRAVE_API_KEY` - Brave Search API key for news

### Documentation

- [README.md](README.md) - This file
- [PHASE0_SUMMARY.md](PHASE0_SUMMARY.md) - Phase 0 completion details
- [PHASE1_SUMMARY.md](PHASE1_SUMMARY.md) - Phase 1 completion details
- [PHASE1_QUICKREF.md](PHASE1_QUICKREF.md) - MT5 Bridge client usage guide
- [PHASE1_OVERVIEW.md](PHASE1_OVERVIEW.md) - Phase 1 comprehensive overview
- [PHASE2_SUMMARY.md](PHASE2_SUMMARY.md) - Phase 2 completion details
- [PHASE2_QUICKREF.md](PHASE2_QUICKREF.md) - Scheduler usage guide

### License

MIT License - See LICENSE file for details
