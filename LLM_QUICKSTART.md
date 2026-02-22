# LLM Quick Setup Card

## Where to Put Your API Key

### FILE TO EDIT: `.env` (in project root)

```
ZAI_API_KEY=your_actual_api_key_here
```

---

## Quick Setup (3 Steps)

### 1. Copy the template
```bash
cp .env.example .env
```

### 2. Edit .env file
```bash
# Windows
notepad .env

# Linux/Mac
nano .env
```

### 3. Replace the placeholder
```
ZAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Save and close!**

---

## Test Your Setup

```bash
python test_llm_connection.py
```

Expected output:
```
✓ ALL TESTS PASSED
Your LLM is configured correctly and ready to use!
```

---

## Configuration (Already Set in Code)

✓ **API Endpoint:** `https://api.z.ai/api/coding/paas/v4`
✓ **Model:** `glm-4.7`
✓ **Timeout:** 10 seconds
✓ **Temperature:** 0.3

**You don't need to change these!**

---

## What If It Doesn't Work?

### Problem: API key not found
**Solution:** Make sure `.env` file exists in project root

### Problem: Connection failed
**Solution:**
1. Check API key is correct
2. Check internet connection
3. Verify API credits at z.ai

### Problem: Module not found
**Solution:**
```bash
pip install python-dotenv
```

---

## Need More Help?

See **LLM_SETUP.md** for detailed instructions.

---

**That's it! Your LLM is ready to help the system evolve! 🚀**
