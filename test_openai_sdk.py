#!/usr/bin/env python
"""
Quick test for Z.AI API using OpenAI SDK
"""

import os
from openai import OpenAI

print('=' * 70)
print('Z.AI API TEST - OpenAI SDK')
print('=' * 70)

# Check API key
api_key = os.getenv("ZAI_API_KEY")

if not api_key:
    print('\nERROR: ZAI_API_KEY not set!')
    print('')
    print('Please set it in .env file:')
    print('  ZAI_API_KEY=your_actual_key_here')
    print('')
    print('Then run: python test_openai_sdk.py')
    exit(1)

print(f'\nAPI Key (masked): {"*" * (len(api_key) - 4)}{api_key[-4:]}')

# Initialize client
print('\nInitializing OpenAI SDK client...')
client = OpenAI(
    api_key=api_key,
    base_url="https://api.z.ai/api/coding/paas/v4",
)

print('Client initialized!')
print(f'Base URL: https://api.z.ai/api/coding/paas/v4')
print(f'Model: glm-4.7')

# Test API call
print('\nSending test request to Z.AI...')
print('Asking LLM to write a short fairy tale...')

try:
    completion = client.chat.completions.create(
        model="glm-4.7",
        messages=[
            {"role": "system", "content": "You are a smart and creative novelist"},
            {
                "role": "user",
                "content": "Please write a short fairy tale story as a fairy tale master",
            },
        ],
        max_tokens=500,
        temperature=0.7,
    )

    print('\n' + '=' * 70)
    print('RESPONSE FROM Z.AI (glm-4.7):')
    print('=' * 70)
    print('')
    print(completion.choices[0].message.content)
    print('')
    print('=' * 70)
    print('SUCCESS! Your Z.AI API is working perfectly!')
    print('=' * 70)

except Exception as e:
    print(f'\nERROR: {e}')
    print('')
    print('Possible issues:')
    print('  1. Invalid API key')
    print('  2. No internet connection')
    print('  3. API endpoint is down')
    print('  4. Insufficient API credits')
    print('')
    print('Please check your Z.AI dashboard.')
    exit(1)
