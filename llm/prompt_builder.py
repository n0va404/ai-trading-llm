"""
Prompt Builder

Responsibilities:
- Build structured prompts for LLM
- Include relevant context (market, state, knowledge)
- Ensure prompt consistency across strategies

This module creates prompts - it does NOT call the LLM.
Actual LLM calls are made by z_ai_client.
"""

from typing import Dict, Any, List, Optional


class PromptBuilder:
    """
    Builder for structured LLM prompts.

    Ensures consistent prompt format across all strategies.
    """

    def __init__(self, strategy_type: str):
        """
        Initialize prompt builder for a strategy type.

        Args:
            strategy_type: 'scalper' or 'swing'

        TODO: Load strategy-specific prompt templates
        """
        self.strategy_type = strategy_type
        raise NotImplementedError("PromptBuilder.__init__ not yet implemented")

    def build_decision_prompt(
        self,
        pair: str,
        market_data: Dict[str, Any],
        pair_state: Dict[str, Any],
        knowledge: List[Dict[str, Any]]
    ) -> str:
        """
        Build prompt for trading decision.

        Args:
            pair: Trading pair symbol
            market_data: Current market data
            pair_state: Current pair state
            knowledge: Recent knowledge entries for context

        Returns:
            Formatted prompt string

        TODO: Implement prompt building
        TODO: Include system directive
        TODO: Include market context
        TODO: Include recent history from knowledge
        """
        raise NotImplementedError("build_decision_prompt not yet implemented")

    def build_reflection_prompt(
        self,
        pair: str,
        trade_result: Dict[str, Any],
        original_decision: Dict[str, Any]
    ) -> str:
        """
        Build prompt for trade reflection/learning.

        Args:
            pair: Trading pair symbol
            trade_result: Trade outcome data
            original_decision: Original decision that led to trade

        Returns:
            Formatted prompt string

        TODO: Implement reflection prompt building
        TODO: Include trade outcome
        TODO: Include original reasoning
        TODO: Ask for lessons learned
        """
        raise NotImplementedError("build_reflection_prompt not yet implemented")

    def _format_market_context(self, market_data: Dict[str, Any]) -> str:
        """
        Format market data for prompt inclusion.

        Args:
            market_data: Market data dictionary

        Returns:
            Formatted string

        TODO: Implement market formatting
        """
        raise NotImplementedError("_format_market_context not yet implemented")

    def _format_knowledge_context(self, knowledge: List[Dict[str, Any]]) -> str:
        """
        Format knowledge entries for prompt inclusion.

        Args:
            knowledge: List of knowledge entries

        Returns:
            Formatted string

        TODO: Implement knowledge formatting
        TODO: Prioritize recent and relevant entries
        """
        raise NotImplementedError("_format_knowledge_context not yet implemented")
