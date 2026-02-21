# MT5 Bridge Client - Quick Reference

## Phase 1 Implementation

---

## Usage Examples

### Basic Setup

```python
from execution.mt5_bridge import MT5BridgeClient

# Initialize client (no connection yet)
client = MT5BridgeClient(
    base_url="http://localhost:8080",  # Optional, default is localhost:8080
    timeout=5                          # Optional, default is 5 seconds
)
```

---

## System & Health

### Health Check

```python
try:
    health = client.health_check()
    print(f"Status: {health['status']}")
    print(f"MT5 Connected: {health['mt5_connection']}")
except MT5BridgeConnectionError as e:
    print(f"Connection failed: {e}")
except MT5BridgeResponseError as e:
    print(f"MT5 error: {e}")
```

---

## Market Data

### Get Current Tick

```python
tick = client.get_tick("XAUUSDm")
# Returns:
# {
#     "symbol": "XAUUSDm",
#     "bid": 2936.12,
#     "ask": 2936.87,
#     "spread": 0.75,
#     "timestamp": "2026-02-19T13:00:00.000000"
# }
```

### Get Last N Ticks

```python
ticks = client.get_ticks("XAUUSDm", count=50)
# Returns list of tick dicts (most recent first)
for tick in ticks:
    print(f"{tick['time']}: Bid={tick['bid']} Ask={tick['ask']}")
```

### Get OHLC Candles

```python
# Get 100 H1 candles
candles = client.get_ohlc("XAUUSDm", timeframe=60, bars=100)

# Get 50 H4 candles
candles = client.get_ohlc("EURUSDm", timeframe=240, bars=50)

# Get 20 Daily candles
candles = client.get_ohlc("GBPUSDm", timeframe=1440, bars=20)

# Returns list of candle dicts (most recent first)
for candle in candles:
    print(f"{candle['time']}: O={candle['open']} H={candle['high']} "
          f"L={candle['low']} C={candle['close']}")
```

**Timeframe Values:**
- `1` - M1 (1 minute)
- `5` - M5 (5 minutes)
- `15` - M15 (15 minutes)
- `30` - M30 (30 minutes)
- `60` - H1 (1 hour)
- `240` - H4 (4 hours)
- `1440` - D1 (Daily)

---

## Account State

### Get Account Info

```python
account = client.get_account()
# Returns:
# {
#     "login": 12345678,
#     "server": "MetaQuotes-Demo",
#     "balance": 10000.00,
#     "equity": 10000.00,
#     "margin": 0.00,
#     "free_margin": 10000.00,
#     "leverage": 100,
#     "currency": "USD"
# }
```

### Get Open Positions

```python
positions = client.get_positions()
# Returns list of position dicts
for pos in positions:
    print(f"Ticket: {pos['ticket']}")
    print(f"Symbol: {pos['symbol']}")
    print(f"Type: {'BUY' if pos['type'] == 0 else 'SELL'}")
    print(f"Lots: {pos['lots']}")
    print(f"Profit: {pos['profit']}")
```

### Get Pending Orders

```python
orders = client.get_orders()
# Returns list of order dicts
for order in orders:
    print(f"Ticket: {order['ticket']}")
    print(f"Symbol: {order['symbol']}")
    print(f"Type: {order['type']}")
    print(f"Price: {order['price']}")
```

---

## Trade Execution

### Place Market Order

```python
payload = {
    "symbol": "XAUUSDm",
    "type": 0,        # 0=BUY, 1=SELL
    "volume": 0.01,
    "price": 0,       # 0 for market orders
    "sl": 2924.50,    # Optional
    "tp": 2954.50,    # Optional
    "comment": "My Trade"  # Optional
}

result = client.place_order(payload)
# Returns:
# {
#     "success": true,
#     "ticket": 123456,
#     "message": "Order placed successfully"
# }
```

### Place Pending Order

```python
payload = {
    "symbol": "XAUUSDm",
    "type": "BUY_LIMIT",  # or 2
    "volume": 0.01,
    "price": 2930.00,
    "sl": 2924.50,        # Optional
    "tp": 2954.50,        # Optional
    "comment": "Pending Trade"  # Optional
}

result = client.place_pending_order(payload)
# Returns:
# {
#     "success": true,
#     "ticket": 123457,
#     "message": "Pending order placed"
# }
```

**Order Types:**
- `"BUY_LIMIT"` or `2`
- `"SELL_LIMIT"` or `3`
- `"BUY_STOP"` or `4`
- `"SELL_STOP"` or `5`

---

## Error Handling

### Exception Hierarchy

```python
from execution.mt5_bridge import (
    MT5BridgeClient,
    MT5BridgeError,
    MT5BridgeConnectionError,
    MT5BridgeResponseError
)

client = MT5BridgeClient()

try:
    tick = client.get_tick("XAUUSDm")
except MT5BridgeConnectionError as e:
    # HTTP request failed (network error, timeout, etc.)
    print(f"Connection error: {e}")
except MT5BridgeResponseError as e:
    # MT5 Bridge returned success=False
    print(f"MT5 error: {e}")
except MT5BridgeError as e:
    # Generic MT5 Bridge error
    print(f"Bridge error: {e}")
```

---

## Phase 0 Compatibility

If you have existing Phase 0 code using `MT5Bridge`:

```python
from execution.mt5_bridge import MT5Bridge

# This still works (backward compatible)
bridge = MT5Bridge()

# Phase 0 interface
account = bridge.get_account_info()
tick = bridge.get_market_data("XAUUSDm")
positions = bridge.get_open_positions()

# Place market order (Phase 0 style)
result = bridge.place_market_order(
    pair="XAUUSDm",
    action="BUY",
    lots=0.01,
    stop_loss=2924.50,
    take_profit=2954.50
)
```

**Recommendation:** New code should use `MT5BridgeClient` directly.

---

## Testing Without MT5 Running

```python
# This will raise MT5BridgeConnectionError
# but won't crash on import
from execution.mt5_bridge import MT5BridgeClient

client = MT5BridgeClient()
# No connection yet - safe

try:
    tick = client.get_tick("XAUUSDm")
except MT5BridgeConnectionError:
    print("MT5 Bridge not running - expected in testing")
```

---

## Important Notes

1. **No Validation:** Client does NOT validate payload structure. MT5 Bridge will validate and return errors if payload is invalid.

2. **No Retries:** Failed requests raise exceptions immediately. No automatic retries.

3. **No Caching:** Every call makes a fresh HTTP request. No response caching.

4. **Stateless:** Client does NOT store any state between calls.

5. **Thread-Safe:** Each request is independent. Safe to use from multiple threads.

---

## Common Patterns

### Check MT5 Connection

```python
def is_mt5_connected(client):
    try:
        health = client.health_check()
        return health.get("mt5_connection", False)
    except MT5BridgeConnectionError:
        return False
```

### Get Symbol Price

```python
def get_current_price(client, symbol):
    tick = client.get_tick(symbol)
    return {
        "bid": tick["bid"],
        "ask": tick["ask"],
        "spread": tick["spread"]
    }
```

### Place Buy Order

```python
def place_buy(client, symbol, lots, sl=None, tp=None):
    payload = {
        "symbol": symbol,
        "type": 0,  # BUY
        "volume": lots,
        "price": 0
    }
    if sl:
        payload["sl"] = sl
    if tp:
        payload["tp"] = tp
    return client.place_order(payload)
```

---

## MT5 Bridge API Documentation

For full API details, see:
`kairos_core/docs/MT5_BRIDGE_API.md`

---

**Phase 1 - Implementation Complete**
