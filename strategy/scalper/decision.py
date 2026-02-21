"""
Scalper Strategy Decision

Responsibilities:
- Make scalper trading decisions
- Coordinate between rules, LLM, and execution
- Update pair knowledge with decisions

This module is a job function - called by the scheduler on interval.
It combines rules + LLM reasoning to make decisions.
"""

from typing import Dict, Any, Optional


# TODO: Import when implemented
# from strategy.scalper.rules import ScalperRules
# from llm.z_ai_client import ZAIClient
# from execution.order_router import OrderRouter


def scalper_decision_job():
    """
    Job function to evaluate scalper opportunities for all pairs.

    This is called by the scheduler every scalper_decision_interval seconds.

    TODO: Implement scalper decision cycle
    TODO: Load enabled pairs from config/pairs.yaml
    TODO: For each pair:
    TODO:   - Load pair state
    TODO:   - Fetch market data from cache
    TODO:   - Evaluate rules
    TODO:   - If valid, prompt LLM for decision
    TODO:   - Execute decision via OrderRouter
    TODO:   - Update pair knowledge
    """
    raise NotImplementedError("scalper_decision_job not yet implemented")


class ScalperDecisionEngine:
    """
    Decision engine for scalper strategy.

    Each pair has its own decision engine for isolation.
    """

    def __init__(self, pair: str, rules: ScalperRules, llm_client, order_router):
        """
        Initialize scalper decision engine for a specific pair.

        Args:
            pair: Trading pair symbol
            rules: ScalperRules instance
            llm_client: LLM client for reasoning
            order_router: Order router for execution

        TODO: Implement initialization
        """
        self.pair = pair
        self.rules = rules
        self.llm_client = llm_client
        self.order_router = order_router
        raise NotImplementedError("ScalperDecisionEngine.__init__ not yet implemented")

    def evaluate(self) -> Optional[Dict[str, Any]]:
        """
        Evaluate and execute scalper opportunity.

        Returns:
            Decision result or None if no action taken

        TODO: Implement evaluation flow:
        TODO: 1. Validate entry conditions via rules
        TODO: 2. If valid, build LLM prompt
        TODO: 3. Get LLM decision
        TODO: 4. Validate decision
        TODO: 5. Execute via order_router
        TODO: 6. Log to knowledge
        """
        raise NotImplementedError("evaluate not yet implemented")

    def _build_prompt(self, market_data: Dict[str, Any], pair_state: Dict[str, Any]) -> str:
        """
        Build LLM prompt for scalper decision.

        Args:
            market_data: Current market data
            pair_state: Current pair state

        Returns:
            Prompt string for LLM

        TODO: Implement prompt building
        TODO: Include market context
        TODO: Include pair state
        TODO: Include recent performance
        """
        raise NotImplementedError("_build_prompt not yet implemented")
