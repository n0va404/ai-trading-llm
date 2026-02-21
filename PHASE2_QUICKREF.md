# Scheduler Quick Reference - Phase 2

## Usage Guide and Examples

---

## Basic Setup

```python
from scheduler.job_manager import JobManager

# Create scheduler instance
manager = JobManager()

# Register all jobs (loads from config/job_cycles.yaml)
manager.register_all_jobs()

# Start scheduler
manager.start()
```

---

## Execution Models

### Model 1: External Loop (Recommended)

```python
import time

manager = JobManager()
manager.register_all_jobs()
manager.start()

try:
    while True:
        # Execute due jobs
        manager.run_pending()

        # Do other work or sleep
        time.sleep(0.1)

finally:
    manager.stop()
```

### Model 2: Controlled Ticks (Testing)

```python
import time

manager = JobManager()
manager.register_all_jobs()
manager.start()

# Start time
current_time = time.time()

# Simulate 10 seconds
for _ in range(10):
    # Execute jobs
    manager.run_pending(current_time)

    # Advance time
    current_time += 1

manager.stop()
```

### Model 3: Single Tick (On-Demand)

```python
manager = JobManager()
manager.register_all_jobs()
manager.start()

# Execute due jobs once
manager.run_pending()

# Check stats
stats = manager.get_stats()
print(f"Jobs executed: {stats['jobs_executed']}")

manager.stop()
```

---

## Job Information

### List All Jobs

```python
manager = JobManager()
manager.register_all_jobs()

# Get job names
jobs = manager.registry.get_all_job_names()
for job in jobs:
    print(job)

# Output:
# market_data_pull
# account_sync
# scalper_decision
# swing_decision
# news_pull
# aggregator_update
# knowledge_backup
```

### Get Job Details

```python
manager = JobManager()
manager.register_all_jobs()

# Get info for specific job
info = manager.get_job_info("market_data_pull")

print(f"Name: {info['name']}")
print(f"Interval: {info['interval']}s")
print(f"Next run: {info['next_run']}")
print(f"Last run: {info['last_run']}")
```

### Check Job Status

```python
manager = JobManager()
manager.register_all_jobs()

# Get status of all jobs
status = manager.status()
for job_name, job_status in status.items():
    print(f"{job_name}: {job_status}")
```

---

## Scheduler Statistics

### Get Statistics

```python
manager = JobManager()
manager.register_all_jobs()
manager.start()

# Run some jobs...
manager.run_pending()

# Get stats
stats = manager.get_stats()
print(f"Jobs registered: {stats['jobs_registered']}")
print(f"Jobs executed: {stats['jobs_executed']}")
print(f"Jobs failed: {stats['jobs_failed']}")
print(f"Is running: {stats['is_running']}")
```

### Reset Statistics

```python
manager = JobManager()
manager.register_all_jobs()
manager.start()

# Run some jobs...
manager.run_pending()

# Reset counters
manager.reset_stats()

# Stats now zero
stats = manager.get_stats()
assert stats['jobs_executed'] == 0
```

---

## Timer Usage

### Direct Timer Usage

```python
from scheduler.timer import JobTimer
import time

# Create timer for 5-second interval
timer = JobTimer(interval=5)

# Check if should run (never run, so yes)
if timer.should_run():
    print("Job is due!")

# Mark as run
timer.mark_run()

# Check again (just ran, so no)
if timer.should_run():
    print("Job is due!")
else:
    print("Job not due yet")

# Get time until next run
seconds = timer.time_until_next()
print(f"Next run in: {seconds}s")
```

### TimerRegistry Usage

```python
from scheduler.timer import TimerRegistry

# Create registry
registry = TimerRegistry()

# Register timers
registry.register("job_a", interval=1)
registry.register("job_b", interval=5)
registry.register("job_c", interval=10)

# Check specific job
if registry.should_run("job_a"):
    print("Job A is due")
    registry.mark_run("job_a")

# List all jobs
jobs = registry.get_all_job_names()
print(f"Registered jobs: {jobs}")
```

---

## Job Registry Usage

### Load Config

```python
from scheduler.job_registry import JobRegistry, load_interval

# Method 1: Load via registry
registry = JobRegistry()
config = registry.load_config()

print(f"Market data interval: {config['market_data_pull_interval']}s")

# Method 2: Load single interval
interval = load_interval("market_data_pull_interval")
print(f"Market data interval: {interval}s")
```

### Register Custom Job

```python
from scheduler.job_registry import JobRegistry

registry = JobRegistry()
registry.load_config()

# Define job function
def my_custom_job():
    print("Custom job executed!")

# Register with interval from config
registry.register_from_config("market_data_pull", my_custom_job)

# Or register with custom interval
registry.register_job(
    name="my_job",
    func=my_custom_job,
    interval=30,
    description="My custom job"
)
```

---

## Error Handling

### Job Execution Errors

```python
from scheduler.job_manager import JobManager, JobExecutionError

manager = JobManager()
manager.register_all_jobs()
manager.start()

try:
    manager.run_pending()
except JobExecutionError as e:
    print(f"Job failed: {e}")
    # Scheduler continues running

# Check stats
stats = manager.get_stats()
if stats['jobs_failed'] > 0:
    print(f"{stats['jobs_failed']} jobs failed")
```

### Missing Config

```python
from scheduler.job_registry import JobRegistry

registry = JobRegistry()

try:
    # This will raise FileNotFoundError if config missing
    config = registry.load_config()
except FileNotFoundError as e:
    print(f"Config error: {e}")
```

### Invalid Job Name

```python
from scheduler.timer import TimerRegistry

registry = TimerRegistry()
registry.register("my_job", interval=5)

try:
    # This will raise KeyError
    registry.should_run("nonexistent_job")
except KeyError as e:
    print(f"Job not found: {e}")
```

---

## Testing Patterns

### Mock Time for Testing

```python
from scheduler.job_manager import JobManager
import time

manager = JobManager()
manager.register_all_jobs()
manager.start()

# Start at known time
mock_time = 1000.0

# First tick - all jobs run
manager.run_pending(mock_time)
assert manager.get_stats()['jobs_executed'] == 7

# Advance 1 second - only 1s jobs run
mock_time += 1
manager.run_pending(mock_time)

# Advance 5 seconds - 1s and 5s jobs run
mock_time += 5
manager.run_pending(mock_time)
```

### Test Job Execution Order

```python
execution_order = []

def job_a():
    execution_order.append("A")

def job_b():
    execution_order.append("B")

manager = JobManager()
manager.registry.register_job("a", job_a, interval=1)
manager.registry.register_job("b", job_b, interval=1)
manager.timer_registry.register("a", interval=1)
manager.timer_registry.register("b", interval=1)
manager.start()

manager.run_pending()

# Jobs execute in registration order
assert execution_order == ["A", "B"]
```

---

## Configuration

### job_cycles.yaml Structure

```yaml
# Job intervals in seconds
market_data_pull_interval: 1
account_sync_interval: 5
scalper_decision_interval: 2
swing_decision_interval: 60
news_pull_interval: 300
aggregator_update_interval: 10
knowledge_backup_interval: 3600
```

### Adding New Job

1. Add to `config/job_cycles.yaml`:
```yaml
my_new_job_interval: 15  # 15 seconds
```

2. Register in `job_registry.py`:
```python
registry.register_from_config(
    "my_new_job",
    lambda: _placeholder_job("my_new_job")
)
```

3. Scheduler will automatically use configured interval

---

## Best Practices

### 1. Always Start Scheduler

```python
manager = JobManager()
manager.register_all_jobs()

# Always call start() before run_pending()
manager.start()

# Now run_pending() will execute jobs
manager.run_pending()
```

### 2. Always Stop Scheduler

```python
manager = JobManager()
manager.register_all_jobs()
manager.start()

try:
    # Main loop
    while True:
        manager.run_pending()
        time.sleep(0.1)
finally:
    # Always clean shutdown
    manager.stop()
```

### 3. Check Stats for Monitoring

```python
# Periodically check stats
stats = manager.get_stats()

if stats['jobs_failed'] > 0:
    # Alert or log
    print(f"WARNING: {stats['jobs_failed']} jobs failed")

if stats['jobs_executed'] == 0:
    print("WARNING: No jobs executed recently")
```

### 4. Use Time Injection for Testing

```python
# Don't use time.time() in tests
# Inject known time instead

current_time = 1000.0
manager.run_pending(current_time)

# Predictable results
```

---

## Common Patterns

### Wait for Specific Job

```python
import time

manager = JobManager()
manager.register_all_jobs()
manager.start()

# Wait for news_pull job (300s interval)
# This checks every second
while True:
    manager.run_pending()

    info = manager.get_job_info("news_pull")
    last_run = info['last_run']

    if last_run is not None:
        break

    time.sleep(1)

print("News pull job executed!")
```

### Run Scheduler for Fixed Duration

```python
import time

manager = JobManager()
manager.register_all_jobs()
manager.start()

# Run for 60 seconds
start_time = time.time()
while time.time() - start_time < 60:
    manager.run_pending()
    time.sleep(0.1)

manager.stop()

print(f"Jobs executed: {manager.get_stats()['jobs_executed']}")
```

---

## Important Notes

1. **Scheduler is Single-Threaded**
   - Jobs run sequentially, not in parallel
   - Long-running jobs block other jobs
   - Keep jobs short and fast

2. **External Tick Model**
   - Scheduler does NOT sleep or block
   - run_pending() returns immediately
   - Caller controls the loop

3. **Job Errors Don't Crash Scheduler**
   - Job exceptions are caught and logged
   - Scheduler continues with other jobs
   - Failed jobs are marked as run (prevents rapid retry)

4. **First Run Executes All Jobs**
   - Jobs with `last_run = None` are due
   - First tick will execute all registered jobs
   - This is by design

5. **Time is Deterministic**
   - `current_time` can be injected
   - Useful for testing
   - No hidden time calls

---

**Phase 2 - Job Cycle Engine**
