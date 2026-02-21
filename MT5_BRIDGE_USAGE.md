# MT5 Bridge - Usage Guide

## Overview

The `execution/mt5_bridge.py` module now provides TWO components:

1. **Flask HTTP Server** - Bridges HTTP requests to ZeroMQ for MT5
2. **MT5BridgeClient** - Python client for making HTTP requests to the bridge

This is based on your working `mt5_bridge_worked.py` and maintains compatibility with the existing system.

---

## Quick Start

### Step 1: Start the Bridge Server

**Requirements:**
- MT5 terminal running with RemoteControlEA loaded
- ZeroMQ enabled in RemoteControlEA (port 5555)
- Python installed with: `pip install pyzmq flask flask-cors requests`

**Start the server:**
```bash
cd D:\1Computer\1AI\Sandbox\ai-trading-llm
python -m execution.mt5_bridge
```

You should see:
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

### Step 2: Use the Client in Your Code

```python
from execution.mt5_bridge import MT5BridgeClient

# Create client
client = MT5BridgeClient()

# Get current tick data
tick = client.get_tick("XAUUSDm")
print(f"Bid: {tick['bid']}, Ask: {tick['ask']}")

# Get account info
account = client.get_account()
print(f"Balance: {account['balance']}, Equity: {account['equity']}")

# Get open positions
positions = client.get_positions()
for pos in positions:
    print(f"Position {pos['ticket']}: {pos['symbol']} {pos['lots']} lots")
```

---

## Available API Endpoints

### Market Data

```python
# Get current tick
tick = client.get_tick("XAUUSDm")

# Get last N ticks
ticks = client.get_ticks("XAUUSDm", count=10)

# Get OHLC data
ohlc = client.get_ohlc("XAUUSDm", timeframe=60, bars=100)
# timeframe: 1=M1, 5=M5, 15=M15, 30=M30, 60=H1, 240=H4, 1440=D1
```

### Account State

```python
# Get account information
account = client.get_account()

# Get open positions
positions = client.get_positions()

# Get pending orders
orders = client.get_orders()
```

### Trade Execution

```python
# Place market order (0=BUY, 1=SELL)
result = client.place_order({
    "symbol": "XAUUSDm",
    "type": 0,  # BUY
    "volume": 0.01,
    "price": 0,  # 0 for market orders
    "sl": 2924.50,  # optional
    "tp": 2954.50,  # optional
    "comment": "AI Generated Trade"
})

# Place pending order
result = client.place_pending_order({
    "symbol": "XAUUSDm",
    "type": "BUY_LIMIT",  # or 2
    "volume": 0.01,
    "price": 2930.00,
    "sl": 2924.50,
    "tp": 2954.50,
    "comment": "AI Pending Trade"
})
```

### System Health

```python
# Check bridge and MT5 connection
health = client.health_check()
# Returns: {"status": "healthy", "mt5_connection": true, "timestamp": "..."}
```

---

## HTTP API Reference (curl examples)

```bash
# Health check
curl http://localhost:8080/health

# Get tick data
curl http://localhost:8080/tick/XAUUSDm

# Get account info
curl http://localhost:8080/account

# Get positions
curl http://localhost:8080/positions

# Place market order
curl -X POST http://localhost:8080/place \
  -H "Content-Type: application/json" \
  -d '{"symbol":"XAUUSDm","type":0,"volume":0.01,"price":0}'

# Place pending order
curl -X POST http://localhost:8080/pending \
  -H "Content-Type: application/json" \
  -d '{"symbol":"XAUUSDm","type":"BUY_LIMIT","volume":0.01,"price":2930}'
```

---

## Configuration

Edit the variables at the top of `execution/mt5_bridge.py`:

```python
# ZeroMQ connection settings
ZMQ_HOST = "localhost"      # MT5 machine IP
ZMQ_PORT = 5555             # Must match RemoteControlEA
ZMQ_TIMEOUT = 5000          # milliseconds

# HTTP server settings
HTTP_HOST = "0.0.0.0"       # Listen on all interfaces
HTTP_PORT = 8080            # HTTP port

# Security (optional)
API_KEY = None              # Set to string for API key auth
ALLOWED_IPS = ["192.168.1.0/24", "127.0.0.1"]
```

---

## Integration with Existing System

The new `mt5_bridge.py` maintains **full backward compatibility**:

```python
# Option 1: Use new client (recommended)
from execution.mt5_bridge import MT5BridgeClient
client = MT5BridgeClient()

# Option 2: Use old wrapper (still works)
from execution.mt5_bridge import MT5Bridge
bridge = MT5Bridge()
# Same interface as Phase 0
```

---

## Troubleshooting

### Bridge won't connect to MT5

1. **Check MT5 is running** with RemoteControlEA loaded
2. **Check ZeroMQ port** - Default is 5555, must match RemoteControlEA setting
3. **Check firewall** - Ensure port 5555 is not blocked

### Client can't reach bridge

1. **Check bridge is running** - Visit http://localhost:8080/ in browser
2. **Check HTTP port** - Default is 8080
3. **Check base_url** - Client defaults to `http://localhost:8080`

### Timeout errors

1. **Increase timeout** when creating client:
   ```python
   client = MT5BridgeClient(timeout=10)  # 10 seconds
   ```
2. **Check ZMQ_TIMEOUT** in bridge server configuration

---

## Files

- **Bridge Server & Client**: `execution/mt5_bridge.py`
- **Working Reference**: `execution/mt5_bridge_worked.py` (your original)
- **This Guide**: `MT5_BRIDGE_USAGE.md`

---

## Summary

✅ Bridge server can be started with: `python -m execution.mt5_bridge`
✅ Client can be imported and used in Python code
✅ All 9 required API methods implemented
✅ Full backward compatibility with Phase 0
✅ Based on your working `mt5_bridge_worked.py`

The system is now ready to connect to MT5!
