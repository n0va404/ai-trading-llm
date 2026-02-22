# LLM Setup Guide for Synaptrix AI Trading System

## Overview

The LLM (Large Language Model) integration provides **read-only advisory insights** for your trading system. It's designed to help the system evolve by:
- Explaining trading decisions
- Detecting biases in patterns
- Suggesting confidence adjustments
- Identifying risk factors

**IMPORTANT:** The LLM is **READ-ONLY and ADVISORY ONLY**. It cannot make trading decisions or modify strategy behavior.

---

## Step 1: Get Your Z.AI API Key

1. Visit https://z.ai/
2. Sign up for an account
3. Navigate to API Keys section
4. Generate a new API key
5. Copy the API key

---

## Step 2: Configure API Key

### Option A: Using .env File (Recommended)

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit the `.env` file:
```bash
# Windows (Notepad)
notepad .env

# Linux/Mac (nano)
nano .env
```

3. Replace `your_zai_api_key_here` with your actual API key:
```bash
ZAI_API_KEY=your_actual_api_key_here
```

4. Save and close the file

### Option B: Using System Environment Variables

**Windows (PowerShell):**
```powershell
$env:ZAI_API_KEY="your_actual_api_key_here"
```

**Windows (Command Prompt):**
```cmd
set ZAI_API_KEY=your_actual_api_key_here
```

**Linux/Mac:**
```bash
export ZAI_API_KEY="your_actual_api_key_here"
```

**Permanent Setup (Linux/Mac):**
Add to your `~/.bashrc` or `~/.zshrc`:
```bash
echo 'export ZAI_API_KEY="your_actual_api_key_here"' >> ~/.bashrc
source ~/.bashrc
```

**Permanent Setup (Windows):**
1. Press `Win + R`
2. Type `sysdm.cpl` and press Enter
3. Go to **Advanced** tab
4. Click **Environment Variables**
5. Under **User variables**, click **New**
6. Variable name: `ZAI_API_KEY`
7. Variable value: your actual API key
8. Click **OK** to save

---

## Step 3: Install Dependencies

```bash
pip install python-dotenv
```

Or install all requirements:
```bash
pip install -r requirements.txt
```

---

## Step 4: Verify LLM Setup

Run the LLM test to verify everything is working:

```bash
python test_phase7.py
```

Expected output:
```
[TEST 6] ZAiClient without API key...
  FAIL: Should return None without API key
```

If you see this **FAIL**, it means your API key is **NOT** set yet.

After setting the API key, run the demo:
```bash
python demo_phase7.py
```

Expected output:
```
[DEMO 1] LLM Client Availability
Status: LLM Client initialized
API Key: Set (********************)
```

---

## Step 5: Test LLM Connection

Create a test file `test_llm_connection.py`:

```python
from llm.z_ai_client import get_llm_client
import os

# Check if API key is set
if os.getenv("ZAI_API_KEY"):
    print("✓ ZAI_API_KEY is set")
else:
    print("✗ ZAI_API_KEY is NOT set")
    print("  Please set ZAI_API_KEY in .env file or environment variables")
    exit(1)

# Initialize client
client = get_llm_client()

if client:
    print("✓ LLM Client initialized successfully")
    print(f"  Base URL: {client.config.base_url}")
    print(f"  Model: {client.config.model}")
    print(f"  Timeout: {client.config.timeout}s")
else:
    print("✗ Failed to initialize LLM Client")
    exit(1)

# Test health check
print("\nTesting API connection...")
if client.health_check():
    print("✓ API connection successful")
else:
    print("✗ API connection failed")
    print("  Please check your API key and internet connection")
```

Run the test:
```bash
python test_llm_connection.py
```

---

## Configuration Details

### API Configuration (Already Set in Code)

The following configuration is **already set** in `llm/z_ai_client.py`:

```python
@dataclass
class ZAiConfig:
    api_key: str
    base_url: str = "https://api.z.ai/api/coding/paas/v4"  # ✓ Set
    model: str = "glm-4.7"  # ✓ Set
    timeout: int = 10  # seconds
    max_tokens: int = 1000
    temperature: float = 0.3
```

**You don't need to change these values.** Just set your API key.

---

## Troubleshooting

### Problem: "ZAI_API_KEY not set"

**Solution:**
1. Check if `.env` file exists in project root
2. Verify API key is correctly set in `.env`
3. Try setting it as system environment variable

### Problem: "LLM connection failed"

**Solution:**
1. Verify API key is correct
2. Check internet connection
3. Confirm API endpoint is accessible: `https://api.z.ai/api/coding/paas/v4`
4. Check if you have API credits/quota remaining

### Problem: "ModuleNotFoundError: No module named 'dotenv'"

**Solution:**
```bash
pip install python-dotenv
```

---

## Security Best Practices

1. **NEVER commit `.env` to git**
   - `.env` is already in `.gitignore`
   - Only commit `.env.example`

2. **Keep your API key secret**
   - Don't share it publicly
   - Don't post it in forums/chats

3. **Monitor API usage**
   - Check your Z.AI dashboard regularly
   - Set up usage alerts if available

4. **Rotate API keys periodically**
   - Generate new keys every few months
   - Revoke old keys

---

## What the LLM Provides

Once configured, the LLM will provide:

### 1. Decision Explanations
```
"BUY decision aligns with uptrend and support bounce.
Scalper win rate of 62% supports confidence level."
```

### 2. Bias Detection
- `none` - No bias detected
- `recency` - Overweighting recent events
- `loss_aversion` - Fear of losses affecting decisions
- `overconfidence` - Confidence not matched by results
- `pattern_failing` - Recent pattern not working

### 3. Confidence Adjustment Suggestions
- `increase` - Pattern is strong
- `decrease` - Pattern is weak
- `hold` - Confidence level is appropriate

### 4. Risk Notes
```
"Monitor for false breakout below 2935.00"
```

---

## Next Steps

After setting up the LLM:

1. **Run the system in paper mode first**
   ```bash
   python main.py start
   ```

2. **Monitor LLM insights**
   - Check logs for LLM analysis
   - Review bias detection alerts
   - Evaluate confidence suggestions

3. **Gradually increase reliance**
   - Start with informational only
   - Monitor accuracy of insights
   - Adjust over time

4. **Keep learning**
   - LLM helps identify patterns
   - Use insights to refine strategies
   - System evolves with experience

---

## Summary

**To enable LLM features:**

1. ✅ Get API key from https://z.ai/
2. ✅ Set `ZAI_API_KEY` in `.env` file
3. ✅ Install dependencies: `pip install python-dotenv`
4. ✅ Verify setup: `python test_phase7.py`

**That's it!** The system will automatically use LLM features when the API key is configured.

---

**Questions?**
- Check the main README.md
- Review PHASE7_SUMMARY.md for implementation details
- Run demo_phase7.py to see LLM features in action

**Happy Trading! 🚀**
