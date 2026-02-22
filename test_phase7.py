#!/usr/bin/env python
"""
Phase 7 Implementation Tests

Tests all Phase 7 components:
- ZAiClient
- PromptBuilder
- DecisionSchema
- LLMCache
"""

import sys
sys.path.insert(0, '.')

print('=' * 60)
print('PHASE 7 IMPLEMENTATION TESTS')
print('=' * 60)

# Test 1: Import LLM components
print('\n[TEST 1] Import LLM components...')
try:
    from llm import ZAiClient, PromptBuilder, DecisionSchema, LLMCache
    print('  PASS: All LLM components imported')
except Exception as e:
    print(f'  FAIL: {e}')
    sys.exit(1)

# Test 2: Initialize DecisionSchema
print('\n[TEST 2] Initialize DecisionSchema...')
try:
    schema = DecisionSchema()
    print('  PASS: DecisionSchema initialized')
except Exception as e:
    print(f'  FAIL: {e}')
    sys.exit(1)

# Test 3: Validate advisory response schema
print('\n[TEST 3] Validate advisory response schema...')
try:
    # Valid response
    valid_response = {
        'explanation': 'Test explanation',
        'bias_detected': 'none',
        'confidence_suggestion': 'hold',
        'risk_notes': 'No risks',
        'actionability': 'informational_only'
    }

    is_valid, error, sanitized = schema.validate_advisory_response(valid_response)
    if is_valid:
        print('  PASS: Valid response accepted')
    else:
        print(f'  FAIL: {error}')
        sys.exit(1)

    # Invalid response (wrong actionability)
    invalid_response = {
        'explanation': 'Test',
        'bias_detected': 'none',
        'confidence_suggestion': 'hold',
        'risk_notes': 'Test',
        'actionability': 'executable'  # WRONG!
    }

    is_valid, error, _ = schema.validate_advisory_response(invalid_response)
    if not is_valid:
        print('  PASS: Invalid actionability rejected')
    else:
        print('  FAIL: Invalid actionability should be rejected')
        sys.exit(1)

except Exception as e:
    print(f'  FAIL: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: PromptBuilder
print('\n[TEST 4] PromptBuilder functionality...')
try:
    builder = PromptBuilder()

    # Test decision context
    decision = {
        'action': 'BUY',
        'confidence': 0.75,
        'tick': {'bid': 2936.50, 'ask': 2937.20},
        'timestamp': '2026-02-22T12:00:00',
        'entry_type': 'market',
        'pending_type': 'none',
        'reasoning': 'Test reasoning'
    }

    aggregate = {
        'total_trades': 100,
        'win_rate': 55.0,
        'total_pnl': 500.0,
        'scalper': {'total_trades': 60, 'win_rate': 58.0},
        'swing': {'total_trades': 40, 'win_rate': 52.0}
    }

    prompt = builder.build_explanation_prompt(
        pair='XAUUSDm',
        strategy='scalper',
        decision=decision,
        aggregate_state=aggregate
    )

    if 'READ-ONLY' in prompt and 'informational_only' in prompt:
        print('  PASS: Prompt contains system directive')
    else:
        print('  FAIL: Prompt missing system directive')
        sys.exit(1)

    if len(prompt) > 500:
        print('  PASS: Prompt is substantial (>= 500 chars)')
    else:
        print('  FAIL: Prompt too short')
        sys.exit(1)

except Exception as e:
    print(f'  FAIL: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: LLMCache
print('\n[TEST 5] LLMCache functionality...')
try:
    cache = LLMCache(max_size=10, ttl=60)

    # Test set and get
    test_prompt = 'Test prompt for caching'
    test_response = {'test': 'response'}

    cache.set(test_prompt, test_response)
    cached = cache.get(test_prompt)

    if cached == test_response:
        print('  PASS: Cache set and get working')
    else:
        print('  FAIL: Cache not returning correct value')
        sys.exit(1)

    # Test cache miss
    cache.clear()
    cached = cache.get(test_prompt)

    if cached is None:
        print('  PASS: Cache miss returns None')
    else:
        print('  FAIL: Cache should return None after clear')
        sys.exit(1)

except Exception as e:
    print(f'  FAIL: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 6: ZAiClient without API key
print('\n[TEST 6] ZAiClient without API key...')
try:
    # Make sure no API key is set
    import os
    original_key = os.environ.get('ZAI_API_KEY')
    if original_key:
        del os.environ['ZAI_API_KEY']

    from llm.z_ai_client import get_llm_client

    client = get_llm_client()

    if client is None:
        print('  PASS: Returns None when no API key')
    else:
        print('  FAIL: Should return None without API key')
        sys.exit(1)

    # Restore original key if it existed
    if original_key:
        os.environ['ZAI_API_KEY'] = original_key

except Exception as e:
    print(f'  FAIL: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 7: Prompt builder batch analysis
print('\n[TEST 7] PromptBuilder batch analysis...')
try:
    decisions = [
        {'action': 'BUY', 'confidence': 0.75},
        {'action': 'SELL', 'confidence': 0.60},
        {'action': 'HOLD', 'confidence': 0.30}
    ]

    prompt = builder.build_batch_analysis_prompt(
        pair='XAUUSDm',
        decisions=decisions,
        aggregate_state=aggregate
    )

    if 'Batch Decision Review' in prompt:
        print('  PASS: Batch prompt contains correct header')
    else:
        print('  FAIL: Batch prompt missing header')
        sys.exit(1)

    if 'BUY' in prompt and 'SELL' in prompt and 'HOLD' in prompt:
        print('  PASS: Batch prompt contains all decisions')
    else:
        print('  FAIL: Batch prompt missing decisions')
        sys.exit(1)

except Exception as e:
    print(f'  FAIL: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 8: Schema validation for all bias types
print('\n[TEST 8] Schema validation for all bias types...')
try:
    valid_biases = ['none', 'recency', 'loss_aversion', 'overconfidence', 'pattern_failing']

    for bias in valid_biases:
        response = {
            'explanation': 'Test',
            'bias_detected': bias,
            'confidence_suggestion': 'hold',
            'risk_notes': 'Test',
            'actionability': 'informational_only'
        }

        is_valid, error, _ = schema.validate_advisory_response(response)
        if not is_valid:
            print(f'  FAIL: Valid bias {bias} rejected: {error}')
            sys.exit(1)

    print(f'  PASS: All {len(valid_biases)} bias types accepted')

except Exception as e:
    print(f'  FAIL: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 9: Cache LRU eviction
print('\n[TEST 9] Cache LRU eviction...')
try:
    cache = LLMCache(max_size=3, ttl=60)

    # Fill cache
    cache.set('prompt1', {'data': 1})
    cache.set('prompt2', {'data': 2})
    cache.set('prompt3', {'data': 3})

    # All should be there
    if cache.get('prompt1') and cache.get('prompt2') and cache.get('prompt3'):
        print('  PASS: Cache holds 3 entries')
    else:
        print('  FAIL: Cache should hold 3 entries')
        sys.exit(1)

    # Add 4th entry (triggers eviction)
    cache.set('prompt4', {'data': 4})

    # Count entries - should still be 3
    entries = sum(1 for p in ['prompt1', 'prompt2', 'prompt3', 'prompt4'] if cache.get(p))

    if entries == 3:
        print('  PASS: LRU eviction working (max 3 entries maintained)')
    else:
        print(f'  FAIL: Expected 3 entries, got {entries}')
        sys.exit(1)

except Exception as e:
    print(f'  FAIL: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 10: Performance review prompt
print('\n[TEST 10] Performance review prompt...')
try:
    prompt = builder.build_performance_review_prompt(
        pair='XAUUSDm',
        aggregate_state=aggregate,
        drawdown=7.5,
        win_rate=52.0
    )

    if 'Performance Review' in prompt:
        print('  PASS: Performance review contains correct header')
    else:
        print('  FAIL: Performance review missing header')
        sys.exit(1)

    if '7.50' in prompt and '52.00' in prompt:
        print('  PASS: Metrics included in prompt')
    else:
        print('  FAIL: Metrics missing from prompt')
        sys.exit(1)

except Exception as e:
    print(f'  FAIL: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)

print('\n' + '=' * 60)
print('ALL TESTS PASSED')
print('=' * 60)
print('\nPhase 7 Implementation Summary:')
print('  - ZAiClient: HTTP client for Z.AI API')
print('  - PromptBuilder: Context-rich prompts')
print('  - DecisionSchema: Fixed JSON output validation')
print('  - LLMCache: TTL-based caching')
print('  - All components: READ-ONLY and ADVISORY ONLY')
print('  - LLM failure does NOT block trading')
print('  - Works without ZAI_API_KEY (optional)')
