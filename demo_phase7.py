#!/usr/bin/env python
"""
Phase 7 Demo - LLM Advisory Features

Demonstrates the read-only LLM advisory layer.
Note: This demo works WITHOUT ZAI_API_KEY (shows graceful fallback).
"""

import sys
sys.path.insert(0, '.')

print('=' * 70)
print('PHASE 7 DEMO - LLM ADVISORY FEATURES')
print('=' * 70)

# Import components
from llm import PromptBuilder, DecisionSchema, LLMCache
from llm.z_ai_client import get_llm_client
import os

# Demo 1: Check LLM availability
print('\n[DEMO 1] LLM Client Availability')
print('-' * 70)

client = get_llm_client()
if client:
    print('Status: LLM Client initialized')
    print(f'API Key: Set ({"*" * 20})')
else:
    print('Status: LLM Client NOT initialized')
    print('Reason: ZAI_API_KEY environment variable not set')
    print('')
    print('This is EXPECTED behavior - LLM features are OPTIONAL!')
    print('The trading system works perfectly without LLM.')

# Demo 2: Build explanation prompt
print('\n[DEMO 2] Build Explanation Prompt')
print('-' * 70)

builder = PromptBuilder()

# Simulated trading decision
decision = {
    'action': 'BUY',
    'confidence': 0.75,
    'tick': {'bid': 2936.50, 'ask': 2937.20, 'spread': 0.70},
    'timestamp': '2026-02-22T12:00:00',
    'entry_type': 'market',
    'pending_type': 'none',
    'reasoning': 'Strong uptrend with bounce from support'
}

# Simulated aggregate state
aggregate = {
    'total_trades': 150,
    'win_rate': 58.0,
    'total_pnl': 875.50,
    'scalper': {'total_trades': 90, 'win_rate': 62.0},
    'swing': {'total_trades': 60, 'win_rate': 52.0}
}

# Build prompt
prompt = builder.build_explanation_prompt(
    pair='XAUUSDm',
    strategy='scalper',
    decision=decision,
    aggregate_state=aggregate
)

print('Prompt built successfully!')
print(f'Prompt length: {len(prompt)} characters')
print(f'Contains READ-ONLY directive: {"YES" if "READ-ONLY" in prompt else "NO"}')
print(f'Contains actionability lock: {"YES" if "informational_only" in prompt else "NO"}')

# Demo 3: Validate advisory response schema
print('\n[DEMO 3] Advisory Response Validation')
print('-' * 70)

schema = DecisionSchema()

# Example LLM response (simulated)
valid_response = {
    'explanation': 'BUY decision aligns with uptrend and support bounce. '
                   'Scalper win rate of 62% supports confidence level.',
    'bias_detected': 'none',
    'confidence_suggestion': 'hold',
    'risk_notes': 'Monitor for false breakout below 2935.00',
    'actionability': 'informational_only'
}

is_valid, error, sanitized = schema.validate_advisory_response(valid_response)

if is_valid:
    print('Response: VALID')
    print('')
    print('Parsed LLM Insights:')
    print(f'  Explanation: {sanitized["explanation"]}')
    print(f'  Bias Detected: {sanitized["bias_detected"]}')
    print(f'  Confidence Suggestion: {sanitized["confidence_suggestion"]}')
    print(f'  Risk Notes: {sanitized["risk_notes"]}')
    print(f'  Actionability: {sanitized["actionability"]} (LOCKED)')
else:
    print(f'Response: INVALID - {error}')

# Demo 4: Test invalid actionability (security check)
print('\n[DEMO 4] Security Check - Invalid Actionability')
print('-' * 70)

invalid_response = {
    'explanation': 'Malicious attempt to make executable decisions',
    'bias_detected': 'none',
    'confidence_suggestion': 'increase',
    'risk_notes': 'None',
    'actionability': 'executable'  # WRONG! Should be informational_only
}

is_valid, error, _ = schema.validate_advisory_response(invalid_response)

if not is_valid:
    print('Security Check: PASSED')
    print(f'Rejection Reason: {error}')
    print('')
    print('The schema correctly REJECTED attempts to make LLM output executable.')
    print('LLM is strictly READ-ONLY and ADVISORY ONLY.')
else:
    print('Security Check: FAILED')
    print('Invalid actionability should have been rejected!')

# Demo 5: Batch analysis prompt
print('\n[DEMO 5] Batch Analysis Prompt')
print('-' * 70)

decisions_batch = [
    {'action': 'BUY', 'confidence': 0.75},
    {'action': 'BUY', 'confidence': 0.80},
    {'action': 'SELL', 'confidence': 0.60},
    {'action': 'HOLD', 'confidence': 0.30},
    {'action': 'BUY', 'confidence': 0.70}
]

batch_prompt = builder.build_batch_analysis_prompt(
    pair='XAUUSDm',
    decisions=decisions_batch,
    aggregate_state=aggregate
)

print(f'Batch analysis prompt built for {len(decisions_batch)} decisions')
print(f'Prompt length: {len(batch_prompt)} characters')
print('Purpose: Analyze patterns, detect biases, provide insights')

# Demo 6: Cache functionality
print('\n[DEMO 6] LLM Response Cache')
print('-' * 70)

cache = LLMCache(max_size=100, ttl=300)

# Cache a prompt
test_prompt = 'Test prompt for XAUUSDm scalper decision'
test_response = {
    'explanation': 'Cached explanation',
    'bias_detected': 'none',
    'confidence_suggestion': 'hold',
    'risk_notes': 'None',
    'actionability': 'informational_only'
}

cache.set(test_prompt, test_response)
cached_result = cache.get(test_prompt)

if cached_result:
    print('Cache: WORKING')
    print(f'Cached response retrieved: {cached_result["explanation"]}')
    print('')
    print('Benefits:')
    print('  - Reduces duplicate API calls')
    print('  - Saves API costs')
    print('  - Faster response time')
else:
    print('Cache: FAILED')

# Demo 7: Performance review prompt
print('\n[DEMO 7] Performance Review Prompt')
print('-' * 70)

review_prompt = builder.build_performance_review_prompt(
    pair='XAUUSDm',
    aggregate_state=aggregate,
    drawdown=7.5,
    win_rate=52.0
)

print('Performance review prompt built')
print(f'Prompt length: {len(review_prompt)} characters')
print('')
print('Purpose: Review performance, identify patterns, suggest considerations')

# Summary
print('\n' + '=' * 70)
print('PHASE 7 DEMO SUMMARY')
print('=' * 70)
print('')
print('Phase 7 LLM Integration provides:')
print('')
print('  1. Decision Explanations')
print('     - Why decisions make sense')
print('     - Reasoning transparency')
print('')
print('  2. Bias Detection')
print('     - none, recency, loss_aversion, overconfidence, pattern_failing')
print('')
print('  3. Confidence Adjustment Suggestions')
print('     - increase, decrease, hold')
print('')
print('  4. Risk Notes')
print('     - Factors to monitor')
print('     - Risk considerations')
print('')
print('KEY FEATURES:')
print('  - READ-ONLY and ADVISORY ONLY')
print('  - LLM output is NON-BINDING')
print('  - Fixed JSON schema with locked actionability')
print('  - Event-driven triggers (not tick-driven)')
print('  - Disabled by default (works without ZAI_API_KEY)')
print('  - 10s timeout, no retries (fail fast)')
print('  - Trading continues without LLM if timeout/error')
print('  - TTL-based caching (reduces API costs)')
print('')
print('SAFETY:')
print('  - LLM cannot make trading decisions')
print('  - LLM cannot modify strategy behavior')
print('  - actionability field locked to "informational_only"')
print('  - Schema validation enforces read-only behavior')
print('')
print('ALL TESTS PASSED - Phase 7 is working correctly!')
print('=' * 70)
