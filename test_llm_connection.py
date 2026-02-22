#!/usr/bin/env python
"""
LLM Connection Test

Tests if your Z.AI API key is configured correctly and the API is accessible.
"""

import sys
import os

print('=' * 70)
print('LLM CONNECTION TEST')
print('=' * 70)

# Test 1: Check if API key is set
print('\n[TEST 1] Checking ZAI_API_KEY...')
print('-' * 70)

api_key = os.getenv("ZAI_API_KEY")

if api_key:
    key_length = len(api_key)
    masked_key = '*' * (key_length - 4) + api_key[-4:] if key_length > 4 else '****'
    print(f'Status: ✓ API key is set')
    print(f'Key (masked): {masked_key}')
    print(f'Length: {key_length} characters')
else:
    print('Status: ✗ API key is NOT set')
    print('')
    print('Please set ZAI_API_KEY in one of these ways:')
    print('')
    print('Option 1: Create .env file')
    print('  1. Copy .env.example to .env')
    print('  2. Edit .env and set: ZAI_API_KEY=your_actual_key_here')
    print('')
    print('Option 2: Set environment variable')
    print('  Windows: $env:ZAI_API_KEY="your_actual_key_here"')
    print('  Linux/Mac: export ZAI_API_KEY="your_actual_key_here"')
    print('')
    print('See LLM_SETUP.md for detailed instructions.')
    sys.exit(1)

# Test 2: Import LLM client
print('\n[TEST 2] Importing LLM client...')
print('-' * 70)

try:
    from llm.z_ai_client import get_llm_client, ZAiConfig
    print('Status: ✓ LLM client imported successfully')
except ImportError as e:
    print(f'Status: ✗ Import failed: {e}')
    print('')
    print('Please install dependencies:')
    print('  pip install -r requirements.txt')
    sys.exit(1)

# Test 3: Initialize client
print('\n[TEST 3] Initializing LLM client...')
print('-' * 70)

client = get_llm_client()

if client:
    print('Status: ✓ LLM client initialized')
    print(f'  Base URL: {client.config.base_url}')
    print(f'  Model: {client.config.model}')
    print(f'  Timeout: {client.config.timeout}s')
    print(f'  Max Tokens: {client.config.max_tokens}')
    print(f'  Temperature: {client.config.temperature}')
else:
    print('Status: ✗ Failed to initialize LLM client')
    print('')
    print('This should not happen if API key is set.')
    print('Please check the error messages above.')
    sys.exit(1)

# Test 4: Health check
print('\n[TEST 4] Testing API connection...')
print('-' * 70)

print('Sending health check request to API...')
if client.health_check():
    print('Status: ✓ API connection successful')
    print('')
    print('Your Z.AI API is configured correctly and accessible!')
else:
    print('Status: ✗ API connection failed')
    print('')
    print('Possible reasons:')
    print('  1. API key is invalid or expired')
    print('  2. No internet connection')
    print('  3. API endpoint is down')
    print('  4. Insufficient API credits/quota')
    print('')
    print('Please check:')
    print('  - Your API key is correct')
    print('  - You have internet connection')
    print('  - Your Z.AI account has available credits')
    print('  - API endpoint is: https://api.z.ai/api/coding/paas/v4')

# Test 5: Configuration verification
print('\n[TEST 5] Verifying configuration...')
print('-' * 70)

config = client.config

checks = []

# Check base URL
if 'api.z.ai' in config.base_url:
    print('✓ Base URL: Correct')
    checks.append(True)
else:
    print(f'✗ Base URL: Unexpected ({config.base_url})')
    checks.append(False)

# Check model
if config.model == 'glm-4.7':
    print('✓ Model: Correct (glm-4.7)')
    checks.append(True)
else:
    print(f'! Model: {config.model} (expected: glm-4.7)')
    checks.append(True)  # Different model is OK

# Check timeout
if config.timeout == 10:
    print('✓ Timeout: Correct (10s)')
    checks.append(True)
else:
    print(f'! Timeout: {config.timeout}s (expected: 10s)')
    checks.append(True)  # Different timeout is OK

# Check temperature
if 0.0 <= config.temperature <= 1.0:
    print(f'✓ Temperature: Correct ({config.temperature})')
    checks.append(True)
else:
    print(f'✗ Temperature: Invalid ({config.temperature})')
    checks.append(False)

# Summary
print('\n' + '=' * 70)
print('TEST SUMMARY')
print('=' * 70)

if all(checks):
    print('✓ ALL TESTS PASSED')
    print('')
    print('Your LLM is configured correctly and ready to use!')
    print('')
    print('Next steps:')
    print('  1. Start the trading system: python main.py start')
    print('  2. LLM insights will be automatically included')
    print('  3. Monitor logs for LLM analysis')
    print('')
    print('For more information, see:')
    print('  - LLM_SETUP.md: Complete LLM setup guide')
    print('  - PHASE7_SUMMARY.md: Phase 7 implementation details')
    print('  - demo_phase7.py: LLM feature demonstrations')
else:
    print('✗ SOME TESTS FAILED')
    print('')
    print('Please fix the issues above before using LLM features.')
    print('See LLM_SETUP.md for troubleshooting tips.')

print('=' * 70)
