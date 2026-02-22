"""
LLM Integration Layer - Phase 7

This module provides read-only, advisory LLM services for the Synaptrix AI Trading System.

**CRITICAL:** This layer is READ-ONLY and ADVISORY ONLY.
- LLM outputs are NON-BINDING
- LLM insights are INFORMATIONAL ONLY
- Trading decisions are made by Phase 4 strategies
- LLM failure MUST NOT block trading

Usage:
    from llm import ZAiClient, PromptBuilder, DecisionSchema, LLMCache

    # Initialize client
    client = ZAiClient(api_key="your_api_key")

    # Build prompt
    builder = PromptBuilder()
    prompt = builder.build_explanation_prompt(
        pair="XAUUSDm",
        strategy="scalper",
        decision=decision_dict,
        aggregate_state=state_dict
    )

    # Get LLM response (with caching)
    response = client.get_completion(prompt)

    # Validate response schema
    schema = DecisionSchema()
    validated = schema.validate_advisory_response(response)
"""

from llm.z_ai_client import ZAiClient
from llm.prompt_builder import PromptBuilder
from llm.decision_schema import DecisionSchema
from llm.cache import LLMCache

__all__ = [
    "ZAiClient",
    "PromptBuilder",
    "DecisionSchema",
    "LLMCache"
]
