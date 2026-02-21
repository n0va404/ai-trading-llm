# Market Data Layer - Quick Reference

## Phase 3 Usage Guide

---

## Basic Setup

```python
from execution.mt5_bridge import MT5BridgeClient
from data.market.cache import MarketCache
from data.market.puller import MarketPuller

# Create components
mt5 = MT5BridgeClient()
cache = MarketCache()
puller = MarketPuller(
    pair="XAUUSDm",
    mt5_bridge=mt5,
    cache=cache,
    default_ttl=1.0  # 1 second default TTL
)
```

---

## Fetching Data

### Get Current Tick

```python
# Get current tick (uses default TTL)
tick = puller.get_tick()

print(f"Bid: {tick['bid']}")
print(f"Ask: {tick['ask']}")
print(f"Spread: {tick['spread']}")
print(f"Timestamp: {tick['timestamp']}")
```

**Cache Behavior:**
- First call: Fetches from MT5 (cache miss)
- Second call (within 1s): Returns cached data
- After 1s: Fetches fresh data from MT5

### Get Multiple Ticks

```python
# Get last 10 ticks
ticks = puller.get_ticks(count=10)

for tick in ticks:
    print(f"{tick['time']}: Bid={tick['bid']} Ask={tick['ask']}")
```

### Get OHLC Bars

```python
# Get 100 H1 candles
ohlc = puller.get_ohlc(timeframe=60, bars=100)

# Get 50 H4 candles
ohlc = puller.get_ohlc(timeframe=240, bars=50)

# Get 20 Daily candles
ohlc = puller.get_ohlc(timeframe=1440, bars=20)

for candle in ohlc:
    print(f"{candle['time']}: O={candle['open']} H={candle['high']} "
          f"L={candle['low']} C={candle['close']}")
```

---

## Custom TTL

### Use Short TTL for Scalping

```python
# 0.5 second TTL for fast-moving scalping
tick = puller.get_tick(ttl=0.5)
```

### Use Long TTL for Swing Data

```python
# 60 second TTL for swing trading (slower changes)
tick = puller.get_tick(ttl=60.0)

# 300 second TTL for OHLC historical data
ohlc = puller.get_ohlc(timeframe=1440, bars=20, ttl=300.0)
```

---

## Direct Cache Access

### Check Cache Validity

```python
# Check if cache is valid
if cache.is_valid(("XAUUSDm", "tick"), ttl=1.0):
    print("Cache is valid (fresh)")
else:
    print("Cache is expired or missing")
```

### Get Cache Age

```python
# Check how old cached data is
age = cache.get_age(("XAUUSDm", "tick"))
print(f"Cache age: {age:.2f} seconds")
```

### Manual Cache Invalidation

```python
# Invalidate specific cache entry
cache.invalidate(("XAUUSDm", "tick"))

# Next get_tick() will fetch from MT5
tick = puller.get_tick()
```

### Clear All Cache

```python
# Clear all cached data
cache.clear()

# Useful for testing or reset
```

---

## Force Refresh

### Bypass Cache

```python
# Force refresh from MT5 (bypasses TTL)
puller.refresh_cache()

# Next call will use refreshed data
tick = puller.get_tick()
```

---

## Convenience Methods

### Get Current Prices

```python
# Get bid/ask/spread in one call
prices = puller.get_current_prices()

print(f"Bid: {prices['bid']}")
print(f"Ask: {prices['ask']}")
print(f"Spread: {prices['spread']}")
print(f"Timestamp: {prices['timestamp']}")
```

### Legacy Methods (Phase 0)

```python
# These methods maintain Phase 0 compatibility

# Get bid only
bid = cache.get_bid("XAUUSDm", ttl=1.0)

# Get ask only
ask = cache.get_ask("XAUUSDm", ttl=1.0)

# Get spread only
spread = cache.get_spread("XAUUSDm", ttl=1.0)
```

---

## Multiple Symbols

### Create Puller per Symbol

```python
symbols = ["XAUUSDm", "EURUSDm", "GBPUSDm"]

mt5 = MT5BridgeClient()
cache = MarketCache()

# Create puller for each symbol (pair isolation)
pullers = {
    symbol: MarketPuller(symbol, mt5, cache)
    for symbol in symbols
}

# Fetch data for each symbol
for symbol, puller in pullers.items():
    tick = puller.get_tick()
    print(f"{symbol}: Bid={tick['bid']}")
```

---

## Testing with Mock MT5

```python
class MockMT5Bridge:
    """Mock MT5 Bridge for testing"""
    def get_tick(self, symbol):
        return {
            'symbol': symbol,
            'bid': 2936.12,
            'ask': 2936.87,
            'spread': 0.75
        }

# Use mock instead of real MT5 Bridge
mt5 = MockMT5Bridge()
cache = MarketCache()
puller = MarketPuller("XAUUSDm", mt5, cache)

# Test without real MT5 connection
tick = puller.get_tick()
assert tick['bid'] == 2936.12
```

---

## Time Injection (Testing)

```python
import time

# Inject specific time for testing
test_time = 1000.0

# Cache data at specific time
cache.set_tick("XAUUSDm", tick_data, current_time=test_time)

# Check validity at specific time
is_valid = cache.is_valid(
    ("XAUUSDm", "tick"),
    ttl=1.0,
    current_time=test_time + 0.5
)
assert is_valid == True  # 0.5s old, TTL is 1s
```

---

## Cache Monitoring

### Get Cache Size

```python
# Number of entries in cache
size = cache.size()
print(f"Cache entries: {size}")
```

### Inspect Cache Contents

```python
# Check if specific key exists
key = ("XAUUSDm", "tick")
if key in cache._cache:
    entry = cache._cache[key]
    print(f"Timestamp: {entry['timestamp']}")
    print(f"Data: {entry['data']}")
```

---

## Common Patterns

### Pattern 1: Cache as Primary

```python
# Use cache as primary data source
# Fall back to MT5 only if cache expired

def get_price_with_fallback(symbol, ttl=1.0):
    tick = puller.get_tick(ttl=ttl)
    if tick is not None:
        return tick['bid']

    # Cache expired, fetch fresh
    tick = puller.refresh_cache()
    return tick['bid']
```

### Pattern 2: Periodic Refresh

```python
# Refresh cache periodically (e.g., every 5 seconds)

import time

while True:
    puller.refresh_cache()
    time.sleep(5)
```

### Pattern 3: Multiple Timeframes

```python
# Fetch different timeframes with appropriate TTLs

# Fast scalping data (fast refresh)
tick_1s = puller.get_tick(ttl=1.0)

# Medium-term data (slower refresh)
ohlc_h1 = puller.get_ohlc(timeframe=60, bars=100, ttl=10.0)

# Long-term data (very slow refresh)
ohlc_d1 = puller.get_ohlc(timeframe=1440, bars=20, ttl=60.0)
```

---

## Performance Tips

### 1. Use Appropriate TTL

```python
# BAD: Too short (excessive MT5 calls)
tick = puller.get_tick(ttl=0.001)

# GOOD: Balanced (cache hit >90%)
tick = puller.get_tick(ttl=1.0)
```

### 2. Reuse Puller Instances

```python
# BAD: Create new puller each time (loses cache)
def get_tick():
    puller = MarketPuller("XAUUSDm", mt5, cache)
    return puller.get_tick()

# GOOD: Reuse puller (keeps cache)
puller = MarketPuller("XAUUSDm", mt5, cache)
def get_tick():
    return puller.get_tick()
```

### 3. Batch Operations

```python
# BAD: Multiple cache lookups
for _ in range(100):
    tick = puller.get_tick()

# GOOD: Cache hit reduces MT5 calls
# First call: MT5 fetch
# Next 99 calls: Cache hit (if within TTL)
```

---

## Important Notes

1. **Thread-Safe**
   - Cache uses threading.Lock
   - Safe to use from multiple threads
   - No race conditions

2. **No Auto-Refresh**
   - Cache does NOT auto-refresh
   - Caller decides when to fetch
   - Prevents unexpected MT5 calls

3. **TTL is Optional**
   - ttl=None means no expiry check
   - Data returned as long as it exists
   - Useful for historical data

4. **Cache Key Structure**
   - Explicit tuple keys
   - No magic strings
   - Type-safe

5. **Dependency Injection**
   - MT5BridgeClient is injected
   - No module-level imports
   - Testable with mocks

---

## Troubleshooting

### Problem: Always hits MT5

**Solution:** Check TTL value
```python
# TTL too short = always expired
tick = puller.get_tick(ttl=0.001)  # BAD

# Use reasonable TTL
tick = puller.get_tick(ttl=1.0)  # GOOD
```

### Problem: Stale Data

**Solution:** Force refresh
```python
# Bypass cache and get fresh data
puller.refresh_cache()
tick = puller.get_tick()
```

### Problem: Cache Growing Too Large

**Solution:** Periodic cleanup
```python
# Clear all cache
cache.clear()

# Or invalidate specific entries
cache.invalidate(("XAUUSDm", "tick"))
```

---

**Phase 3 - Market Data Layer**
