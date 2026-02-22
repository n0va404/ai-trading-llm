# 🚀 Synaptrix AI Trading System - Complete Setup Tutorial

**Version:** 1.0.0
**Last Updated:** 2026-02-22
**Status:** Production-Ready

---

## 📋 TABLE OF CONTENTS

1. [Prerequisites](#prerequisites)
2. [API Keys Setup](#api-keys-setup)
3. [MT5 Bridge Setup](#mt5-bridge-setup)
4. [Project Installation](#project-installation)
5. [Configuration](#configuration)
6. [Initial Setup](#initial-setup)
7. [Running the System](#running-the-system)
8. [Verification](#verification)
9. [Troubleshooting](#troubleshooting)
10. [Next Steps](#next-steps)

---

## 1. PREREQUISITES

### Required Software

- **Python 3.7+** (Recommended: Python 3.12)
- **MetaTrader 5** (MT5) terminal
- **Git** (for cloning repository)
- **Text Editor** (VS Code, PyCharm, etc.)

### Hardware Requirements

- **RAM:** 4GB minimum, 8GB recommended
- **Disk:** 500MB free space
- **Network:** Stable internet connection

---

## 2. API KEYS SETUP

### 2.1 Z.AI API Key (Optional - Phase 7 Skipped)

> **NOTE:** Phase 7 (LLM Integration) was SKIPPED in this project.
> The system does NOT require any API keys to function.
> Skip this section unless you plan to add LLM features later.

If you want to add Z.AI API later:

1. Visit: https://z.ai/
2. Sign up for an account
3. Navigate to API Keys section
4. Generate new API key
5. Copy the key

### 2.2 Brave Search API Key (Optional - For News)

> **NOTE:** Phase 2 registered a news_pull job, but Phase 3 implementation was placeholder.
> The system works WITHOUT news data.
> Skip this section unless you plan to implement news features.

If you want to add news features later:

1. Visit: https://brave.com/search/api/
2. Sign up for Brave Search API
3. Generate new API key
4. Copy the key

### 2.3 Environment Variables

You don't need to set any environment variables for this project!

All configuration is done via YAML files in the `config/` directory.

---

## 3. MT5 BRIDGE SETUP

The MT5 Bridge is the connection between the trading system and MetaTrader 5.

### 3.1 Install MT5

1. Download MetaTrader 5 from your broker
2. Install MT5 on your computer
3. Open MT5 and log in to your trading account

### 3.2 Enable RemoteControlEA

The MT5 Bridge requires an Expert Advisor (EA) called **RemoteControlEA**.

#### Option A: Use Pre-built RemoteControlEA (Recommended)

1. Download RemoteControlEA from:
   - https://github.com/n0va404/mt5-remote-control
   - OR compile from source

2. Copy RemoteControlEA.ex4 to your MT5 Experts folder:
   ```
   C:\Users\YourName\AppData\Roaming\MetaQuotes\Terminal\YourBroker\MQL5\Experts\
   ```

3. Open MT5
4. Go to **Tools → Options → Expert Advisors**
5. Check "Allow automated trading"
6. Check "Allow DLL imports"
7. Click OK

#### Option B: Compile RemoteControlEA

1. Open MetaEditor in MT5
2. Open the RemoteControlEA source code
3. Compile the EA (Press F7)
4. It will be auto-loaded into Experts folder

### 3.3 Configure ZeroMQ in RemoteControlEA

1. Open MT5
2. Navigate to **Navigator → Expert Advisors**
3. Find **RemoteControlEA**
4. Drag and drop it onto a chart (any pair, any timeframe)
5. Click on the EA icon on the chart
6. Click **Inputs** button
7. Configure:
   - **ZMQ Port:** 5555 (default, matches our system)
   - **ZMQ Host:** localhost (if MT5 is on same machine)
8. Click OK
9. Click **AutoTrading** button to enable EA

### 3.4 Verify MT5 Bridge Connection

The MT5 Bridge should now be listening on port 5555 for ZeroMQ connections.

---

## 4. PROJECT INSTALLATION

### 4.1 Clone Repository

```bash
# Clone the repository
git clone git@github.com:n0va404/ai-trading-llm.git
cd ai-trading-llm
```

### 4.2 Install Python Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4.3 Create requirements.txt

Create `requirements.txt` in the project root:

```txt
# Web Framework (for MT5 Bridge)
flask>=2.0.0
flask-cors>=4.0.0
pyzmq>=25.0.0

# HTTP Client
requests>=2.28.0

# YAML Parser
pyyaml>=6.0
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 5. CONFIGURATION

### 5.1 Configuration Files Explained

All configuration is in the `config/` directory:

```
config/
├── pairs.yaml         # Trading pairs to enable
├── risk.yaml          # Risk management limits
├── runtime.yaml       # System mode (backtest/paper/live)
└── job_cycles.yaml   # Job execution intervals
```

### 5.2 Configure Trading Pairs

Edit `config/pairs.yaml`:

```yaml
pairs:
  - XAUUSDm  # Gold vs US Dollar
  - EURUSDm  # Euro vs US Dollar
  # - GBPUSDm  # British Pound vs US Dollar
  # - USDJPYm  # US Dollar vs Japanese Yen
```

**IMPORTANT:** Only enable pairs that:
- Your broker supports
- You want to trade
- Are available in your MT5 terminal

### 5.3 Configure Risk Limits

Edit `config/risk.yaml`:

```yaml
max_capital_risk_per_trade: 2.0  # 2% of account balance per trade
max_total_exposure: 10.0           # 10% of account balance max
max_concurrent_trades: 5
daily_loss_limit: 5.0             # 5% daily loss limit
max_stop_loss_pips: 0
max_take_profit_pips: 0
min_risk_reward_ratio: 1.5
```

**ADJUST THESE VALUES BASED ON YOUR RISK TOLERANCE!**

### 5.4 Configure Runtime Mode

Edit `config/runtime.yaml`:

```yaml
mode: paper  # Options: backtest, paper, live
log_level: INFO
verbose: false
log_decisions: true
log_errors: true
timezone: UTC
```

**Modes Explained:**
- **backtest:** No real trades, for testing only
- **paper:** Real market data, but simulated trades (PAPER TRADING)
- **live:** Real trades with real money (LIVE TRADING)

**START WITH PAPER MODE FIRST!**

### 5.5 Configure Job Intervals

Edit `config/job_cycles.yaml`:

```yaml
market_data_pull_interval: 1      # 1 second
account_sync_interval: 5          # 5 seconds
scalper_decision_interval: 2      # 2 seconds
swing_decision_interval: 60       # 60 seconds (1 minute)
news_pull_interval: 300           # 5 minutes (not implemented yet)
aggregator_update_interval: 10    # 10 seconds
knowledge_backup_interval: 3600   # 1 hour (not implemented yet)
```

**DO NOT CHANGE THESE unless you know what you're doing!**

---

## 6. INITIAL SETUP

### 6.1 Initialize Pair Directories

```bash
python main.py init
```

This will create directory structure for each enabled pair:

```
pairs/
├── XAUUSDm/
│   ├── knowledge/           # JSONL knowledge files
│   ├── aggregate/           # Aggregate snapshots
│   └── state/               # Pair state
└── EURUSDm/
    ├── knowledge/
    ├── aggregate/
    └── state/
```

### 6.2 Verify Setup

```bash
python main.py status
```

Expected output:

```
Synaptrix AI Trading System - Status

Runtime Mode: paper
Enabled Pairs: ['XAUUSDm', 'EURUSDm']

System Status: STOPPED
```

---

## 7. RUNNING THE SYSTEM

### 7.1 Start the MT5 Bridge Server

The MT5 Bridge is a Flask server that connects HTTP requests to MT5 via ZeroMQ.

#### Option A: Run Manually (Development)

```bash
python -m execution.mt5_bridge
```

Expected output:

```
============================================================
MT5 Remote Control - HTTP Bridge
============================================================
ZeroMQ:  tcp://localhost:5555
HTTP:    http://0.0.0.0:8080
Auth:    Disabled
============================================================
[MT5 Bridge] Connected to MT5 at tcp://localhost:5555

Starting HTTP server on 0.0.0.0:8080
   Try: curl http://localhost:8080/ping
============================================================
```

#### Option B: Run as Background Service (Production)

**Windows:**
```bash
start /B python -m execution.mt5_bridge > mt5_bridge.log 2>&1
```

**Linux/Mac:**
```bash
python -m execution.mt5_bridge > mt5_bridge.log 2>&1 &
```

The bridge server will now run in the background.

### 7.2 Verify MT5 Bridge is Running

Open your browser and go to:
```
http://localhost:8080
```

You should see API documentation.

Or test with curl:
```bash
curl http://localhost:8080/ping
```

Expected response:
```json
{
  "success": true,
  "data": {
    "ping": "pong"
  },
  "connected": true
}
```

### 7.3 Start the Trading System

```bash
python main.py start
```

Expected output:

```
============================================================
SYNAPTRIX AI TRADING SYSTEM - INITIALIZING
============================================================
Runtime Mode: paper
Enabled Pairs: ['XAUUSDm', 'EURUSDm']

[INIT] Initializing MT5 Bridge...
  MT5 Bridge: CONNECTED
  Base URL: http://localhost:8080
[INIT] Initializing Order Validator...
  Order Validator: READY
[INIT] Initializing 2 trading pairs...
  Pair: XAUUSDm
    Cache, Puller, Strategies, Aggregator, Router: OK
  Pair: EURUSDm
    Cache, Puller, Strategies, Aggregator, Router: OK
[INIT] Initializing Job Scheduler...
[INIT] Registering jobs...
  Registered 10 jobs
  Job Scheduler: READY
  Jobs registered: 10

============================================================
INITIALIZATION COMPLETE
============================================================

============================================================
SYNAPTRIX AI TRADING SYSTEM - RUNNING
============================================================
Press Ctrl+C to stop

[MARKET_DATA] XAUUSDm: XAUUSDm Bid=2936.50 Ask=2937.20
[SCALPER] XAUUSDm: HOLD (confidence: 0.30)
[MARKET_DATA] EURUSDm: EURUSDm Bid=1.0850 Ask=1.0853
[SWING] EURUSDm: HOLD (confidence: 0.40)
[ACCOUNT] Balance: 10000.00 Equity: 10000.00 Margin: 0.00
...
```

### 7.4 Stop the System

Press `Ctrl+C` in the terminal where the system is running.

Or run:
```bash
python main.py stop
```

---

## 8. VERIFICATION

### 8.1 Check System Status

```bash
python main.py status
```

### 8.2 Check Knowledge Files

```bash
# List knowledge files
ls pairs/XAUUSDm/knowledge/

# You should see:
# backtest.jsonl  - Backtest results
# live.jsonl       - Live trading decisions (will be created)
# promoted.jsonl   - Promoted patterns (will be created)
```

### 8.3 Check Aggregate Snapshots

```bash
# View aggregate snapshot
cat pairs/XAUUSDm/aggregate/snapshot.json
```

---

## 9. TROUBLESHOOTING

### 9.1 MT5 Bridge Not Connecting

**Problem:** `Failed to connect to MT5`

**Solutions:**
1. Verify MT5 is running
2. Verify RemoteControlEA is attached to a chart
3. Verify AutoTrading is enabled
4. Check ZMQ port matches (default: 5555)
5. Check Windows Firewall (allow port 5555)

### 9.2 Python Import Errors

**Problem:** `ModuleNotFoundError: No module named 'xxx'`

**Solutions:**
1. Activate virtual environment
2. Install dependencies: `pip install -r requirements.txt`
3. Check Python version (3.7+ required)

### 9.3 Permission Denied Errors

**Problem:** Cannot create directories

**Solutions:**
1. Run terminal as Administrator
2. Check folder permissions
3. Ensure write access to project directory

### 9.4 MT5 Bridge Port Already in Use

**Problem:** `Address already in use`

**Solutions:**
1. Kill existing process using port 8080:
   ```bash
   # Windows:
   netstat -ano | findstr :8080
   taskkill /F /PID <PID>

   # Linux/Mac:
   lsof -ti:8080 | xargs kill -9
   ```

### 9.5 System Not Starting

**Problem:** Startup fails or crashes

**Solutions:**
1. Check logs in terminal output
2. Verify all config files exist
3. Verify MT5 Bridge is running first
4. Check `config/pairs.yaml` has enabled pairs
5. Run with `verbose: true` in `config/runtime.yaml`

### 9.6 No Trades Being Executed

**Problem:** System running but no trades

**Solutions:**
1. Check if mode is "backtest" or "paper" (not "live")
2. Check strategy confidence thresholds
3. Check market data is being received
4. Review logs for HOLD decisions
5. Verify risk limits aren't preventing trades

---

## 10. NEXT STEPS

### 10.1 Start with Paper Trading

**IMPORTANT! Do NOT start with live trading!**

1. Set `mode: paper` in `config/runtime.yaml`
2. Run the system for at least 1 week
3. Monitor performance metrics
4. Verify strategies are profitable
5. Check risk management is working

### 10.2 Run Backtests

```bash
python -c "
from backtest.engine import run_backtest
from pathlib import Path

results = run_backtest(
    pair='XAUUSDm',
    strategy='scalper',
    data_file=Path('data/historical/XAUUSDm_m1_sample.json')
)
print(f'Candles: {results[\"candles_processed\"]}')
print(f'Trades: {results[\"trades_executed\"]}')
print(f'PnL: {results[\"total_pnl\"]:.2f}')
"
```

### 10.3 Promote Knowledge Patterns

```bash
python -c "
from promotion import KnowledgePromoter, PromotionConfig

# Promote with conservative thresholds
config = PromotionConfig.conservative()
promoter = KnowledgePromoter('XAUUSDm', config=config)

result = promoter.promote()
print(f'Promoted: {result[\"promoted\"]} patterns')
"
```

### 10.4 Go Live (Only After Successful Paper Trading!)

1. Change `mode: live` in `config/runtime.yaml`
2. Reduce risk limits if needed
3. Start with small position sizes
4. Monitor closely for first week
5. Keep detailed logs

---

## 📁 COMPLETE FILE STRUCTURE

```
ai-trading-llm/
├── main.py                          # ✅ Live Trading Orchestrator
├── requirements.txt                 # Python dependencies
├── LICENSE                          # MIT License
│
├── config/                         # Configuration files
│   ├── pairs.yaml                # Trading pairs
│   ├── risk.yaml                 # Risk limits
│   ├── runtime.yaml              # System mode
│   └── job_cycles.yaml           # Job intervals
│
├── scheduler/                      # ✅ Phase 2: Job Cycle Engine
│   ├── __init__.py
│   ├── job_manager.py             # Job scheduler
│   ├── job_registry.py           # Job registry
│   └── timer.py                  # Job timing
│
├── execution/                      # ✅ Phase 1 & 5: MT5 Bridge + Execution
│   ├── mt5_bridge.py             # MT5 HTTP client + Flask server
│   ├── validator.py              # Order validation
│   └── order_router.py           # Order routing
│
├── data/                          # ✅ Phase 3: Market Data Layer
│   └── market/
│       ├── cache.py               # TTL-based cache
│       └── puller.py              # Cache-first data puller
│
├── strategy/                      # ✅ Phase 4: Strategy Core
│   ├── scalper/
│   │   ├── rules.py              # Scalper trading rules
│   │   └── decision.py           # Scalper decision engine
│   └── swing/
│       ├── rules.py              # Swing trading rules
│       └── decision.py           # Swing decision engine
│
├── aggregator/                   # ✅ Phase 6: Knowledge System
│   ├── state.py                  # Aggregate state manager
│   └── updater.py                # Knowledge updater
│
├── backtest/                      # ✅ Phase 8: Backtest Engine
│   ├── data_loader.py            # Historical data loader
│   ├── executor.py               # Simulated execution
│   └── engine.py                 # Backtest orchestrator
│
├── promotion/                     # ✅ Phase 9: Knowledge Promotion
│   ├── config.py                 # Promotion thresholds
│   ├── pattern_analyzer.py      # Pattern analysis
│   └── promoter.py               # Promotion engine
│
├── pairs/                         # Pair-specific data
│   ├── XAUUSDm/
│   │   ├── knowledge/
│   │   │   ├── backtest.jsonl
│   │   │   ├── live.jsonl
│   │   │   └── promoted.jsonl
│   │   ├── aggregate/
│   │   │   └── snapshot.json
│   │   └── state/
│   └── SAMPLE_PAIR/               # Template
│
├── data/                          # Historical data
│   └── historical/
│       └── XAUUSDm_m1_sample.jsonl
│
└── logs/                          # Decision and error logs
    ├── decisions/
    └── errors/
```

---

## 🎯 QUICK START CHEAT SHEET

```bash
# 1. Clone and setup
git clone git@github.com:n0va404/ai-trading-llm.git
cd ai-trading-llm
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# 2. Configure
# Edit config/pairs.yaml - enable your trading pairs

# 3. Initialize
python main.py init

# 4. Start MT5 Bridge (separate terminal)
python -m execution.mt5_bridge

# 5. Start trading system
python main.py start

# 6. Stop (Ctrl+C)
```

---

## 📞 SUPPORT

### Documentation Files

- `README.md` - Project overview
- `QUICKSETUP.md` - This file
- `PROJECT_COMPLETION.md` - Final project summary

### Phase Documentation

- `PHASE1_SUMMARY.md` - MT5 Bridge details
- `PHASE2_SUMMARY.md` - Scheduler details
- `PHASE3_SUMMARY.md` - Market data details
- `PHASE4_SUMMARY.md` - Strategy details
- `PHASE5_SUMMARY.md` - Execution details
- `PHASE6_SUMMARY.md` - Knowledge system details
- `PHASE8_SUMMARY.md` - Backtest details
- `PHASE9_SUMMARY.md` - Promotion details
- `PHASE10_SUMMARY.md` - Orchestrator details

### Quick Reference Guides

- `PHASE1_QUICKREF.md` - MT5 Bridge API
- `PHASE2_QUICKREF.md` - Scheduler usage
- `PHASE8_QUICKREF.md` - Backtesting guide
- `PHASE9_QUICKREF.md` - Promotion guide

---

## ⚠️ IMPORTANT REMINDERS

1. **START WITH PAPER TRADING MODE** - Not live!
2. **MT5 BRIDGE MUST BE RUNNING** - Start it first!
3. **REMOTECONTOROLEA MUST BE ACTIVE** - Attach to chart in MT5!
4. **RISK MANAGEMENT IS CRITICAL** - Set appropriate limits!
5. **MONITOR THE SYSTEM** - Check logs regularly!

---

## 🎉 YOU'RE READY TO GO!

The Synaptrix AI Trading System is now fully configured and ready to run.

**Next Step:** Start with paper trading and monitor performance!

```bash
python main.py start
```

---

**End of Quick Setup Tutorial**

For more information, see individual phase documentation files.

**Happy Trading!** 🚀
