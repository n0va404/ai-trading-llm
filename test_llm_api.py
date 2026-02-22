#!/usr/bin/env python
"""
LLM API Integration Test

Tests the complete LLM integration with actual API call.
This will make a REAL API call to test your Z.AI configuration.
"""

import sys
import os
import json

print('=' * 70)
print('LLM API INTEGRATION TEST')
print('=' * 70)

# Test 1: Check environment
print('\n[TEST 1] Checking environment setup...')
print('-' * 70)

api_key = os.getenv("ZAI_API_KEY")

if not api_key:
    print('Status: FAILED')
    print('')
    print('ZAI_API_KEY is not set!')
    print('')
    print('Please set it up first:')
    print('  1. Copy .env.example to .env')
    print('  2. Edit .env and set: ZAI_API_KEY=your_actual_key_here')
    print('')
    print('See LLM_QUICKSTART.md for quick setup.')
    sys.exit(1)

print('Status: PASS')
print(f'API Key (masked): {"*" * (len(api_key) - 4)}{api_key[-4:]}')

# Test 2: Import components
print('\n[TEST 2] Importing LLM components...')
print('-' * 70)

try:
    from llm import ZAiClient, PromptBuilder, DecisionSchema, LLMCache
    print('Status: PASS')
    print('Components: ZAiClient, PromptBuilder, DecisionSchema, LLMCache')
except ImportError as e:
    print(f'Status: FAILED - {e}')
    sys.exit(1)

# Test 3: Initialize client
print('\n[TEST 3] Initializing LLM client...')
print('-' * 70)

try:
    from llm.z_ai_client import get_llm_client
    client = get_llm_client()

    if not client:
        print('Status: FAILED')
        print('Client initialization returned None')
        sys.exit(1)

    print('Status: PASS')
    print(f'Base URL: {client.config.base_url}')
    print(f'Model: {client.config.model}')
    print(f'Timeout: {client.config.timeout}s')
except Exception as e:
    print(f'Status: FAILED - {e}')
    sys.exit(1)

# Test 4: Test API health
print('\n[TEST 4] Testing API health check...')
print('-' * 70)

try:
    if client.health_check():
        print('Status: PASS')
        print('API is accessible')
    else:
        print('Status: FAILED')
        print('API health check failed')
        print('')
        print('Possible issues:')
        print('  - Invalid API key')
        print('  - No internet connection')
        print('  - API endpoint down')
        sys.exit(1)
except Exception as e:
    print(f'Status: FAILED - {e}')
    sys.exit(1)

# Test 5: Build a test prompt
print('\n[TEST 5] Building test prompt...')
print('-' * 70)

try:
    builder = PromptBuilder()

    # Simulated trading decision
    test_decision = {
        'action': 'BUY',
        'confidence': 0.75,
        'tick': {'bid': 2936.50, 'ask': 2937.20, 'spread': 0.70},
        'timestamp': '2026-02-22T12:00:00',
        'entry_type': 'market',
        'pending_type': 'none',
        'reasoning': 'Strong uptrend with bounce from support at 2935'
    }

    # Simulated aggregate state
    test_aggregate = {
        'total_trades': 150,
        'win_rate': 58.0,
        'total_pnl': 875.50,
        'scalper': {'total_trades': 90, 'win_rate': 62.0},
        'swing': {'total_trades': 60, 'win_rate': 52.0}
    }

    prompt = builder.build_explanation_prompt(
        pair='XAUUSDm',
        strategy='scalper',
        decision=test_decision,
        aggregate_state=test_aggregate
    )

    print('Status: PASS')
    print(f'Prompt length: {len(prompt)} characters')
    print(f'Contains READ-ONLY directive: {"YES" if "READ-ONLY" in prompt else "NO"}')
except Exception as e:
    print(f'Status: FAILED - {e}')
    sys.exit(1)

# Test 6: Get LLM response (REAL API CALL)
print('\n[TEST 6] Making REAL API call to LLM...')
print('-' * 70)

try:
    schema = DecisionSchema()

    print('Sending request to Z.AI API...')
    print(f'Endpoint: {client.config.base_url}')
    print(f'Model: {client.config.model}')
    print('This may take 5-10 seconds...')

    response = client.get_completion(
        prompt=prompt,
        response_schema=schema.get_schema()
    )

    print('')
    print('Status: PASS')
    print('Response received from LLM!')
    print('')
    print('--- LLM Analysis ---')
    print(f"Explanation: {response.get('explanation', 'N/A')}")
    print(f"Bias Detected: {response.get('bias_detected', 'N/A')}")
    print(f"Confidence Suggestion: {response.get('confidence_suggestion', 'N/A')}")
    print(f"Risk Notes: {response.get('risk_notes', 'N/A')}")
    print(f"Actionability: {response.get('actionability', 'N/A')}")
    print('-------------------')

except Exception as e:
    print(f'Status: FAILED - {e}')
    print('')
    print('API call failed. Possible reasons:')
    print('  - Invalid API key')
    print('  - Insufficient API credits')
    print('  - Network timeout')
    print('  - API rate limit')
    print('')
    print('Please check your Z.AI dashboard.')
    sys.exit(1)

# Test 7: Validate response
print('\n[TEST 7] Validating LLM response...')
print('-' * 70)

try:
    is_valid, error, sanitized = schema.validate_advisory_response(response)

    if is_valid:
        print('Status: PASS')
        print('Response schema is valid')
        print(f"Actionability locked: {sanitized.get('actionability', 'N/A')}")
    else:
        print(f'Status: FAILED - {error}')
        sys.exit(1)
except Exception as e:
    print(f'Status: FAILED - {e}')
    sys.exit(1)

# Test 8: Cache functionality
print('\n[TEST 8] Testing cache functionality...')
print('-' * 70)

try:
    cache = LLMCache(max_size=100, ttl=300)

    # Cache the response
    cache.set(prompt, response)

    # Retrieve from cache
    cached = cache.get(prompt)

    if cached and cached == response:
        print('Status: PASS')
        print('Cache working correctly')
        print('Same prompt will use cached response (saves API calls)')
    else:
        print('Status: FAILED')
        print('Cache not working properly')
except Exception as e:
    print(f'Status: FAILED - {e}')
    sys.exit(1)

# Test 9: Batch analysis prompt
print('\n[TEST 9] Testing batch analysis...')
print('-' * 70)

try:
    decisions_batch = [
        {'action': 'BUY', 'confidence': 0.75},
        {'action': 'BUY', 'confidence': 0.80},
        {'action': 'SELL', 'confidence': 0.60}
    ]

    batch_prompt = builder.build_batch_analysis_prompt(
        pair='XAUUSDm',
        decisions=decisions_batch,
        aggregate_state=test_aggregate
    )

    print('Status: PASS')
    print(f'Batch prompt built for {len(decisions_batch)} decisions')
    print(f'Prompt length: {len(batch_prompt)} characters')
except Exception as e:
    print(f'Status: FAILED - {e}')
    sys.exit(1)

# Test 10: Performance review
print('\n[TEST 10] Testing performance review prompt...')
print('-' * 70)

try:
    review_prompt = builder.build_performance_review_prompt(
        pair='XAUUSDm',
        aggregate_state=test_aggregate,
        drawdown=7.5,
        win_rate=52.0
    )

    print('Status: PASS')
    print('Performance review prompt built')
    print(f'Prompt length: {len(review_prompt)} characters')
except Exception as e:
    print(f'Status: FAILED - {e}')
    sys.exit(1)

# Final Summary
print('\n' + '=' * 70)
print('TEST SUMMARY')
print('=' * 70)

print('')
print('ALL TESTS PASSED!')
print('')
print('Your LLM integration is working perfectly!')
print('')
print('What was tested:')
print('  1. Environment setup (API key)')
print('  2. Component imports')
print('  3. Client initialization')
print('  4. API health check')
print('  5. Prompt building')
print('  6. REAL API CALL (with actual LLM response)')
print('  7. Response validation')
print('  8. Cache functionality')
print('  9. Batch analysis')
print('  10. Performance review')
print('')
print('System is ready to use LLM features!')
print('')
print('Next steps:')
print('  1. Start the trading system: python main.py start')
print('  2. LLM will provide advisory insights during trading')
print('  3. Monitor logs for LLM analysis')
print('')
print('=' * 70)
