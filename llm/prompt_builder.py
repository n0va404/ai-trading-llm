"""
Prompt Builder - Phase 7

Builds minimal, context-rich prompts for LLM analysis.
LLM is ADVISORY ONLY - prompts emphasize READ-ONLY analysis.

Architecture:
- Minimal prompts (reduce token usage)
- Structured context (market, state, knowledge)
- Fixed output schema constraints
- NO decision-making prompts (analysis only)
"""

import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class PromptBuilder:
    """
    Build minimal, context-rich prompts for LLM analysis.

    **CRITICAL:** This builds ANALYSIS prompts only.
    - NO decision-making prompts
    - NO action recommendations
    - READ-ONLY analysis only
    """

    # System directive (enforces advisory-only behavior)
    SYSTEM_DIRECTIVE = """
You are a READ-ONLY trading analyst for the Synaptrix AI Trading System.

**CRITICAL CONSTRAINTS:**
1. You provide ANALYSIS and EXPLANATION only
2. You DO NOT make trading decisions
3. Your output is INFORMATIONAL ONLY
4. You DO NOT recommend actions
5. Trading decisions are made by rule-based strategies

**Your Role:**
- Explain WHY decisions were made
- Identify potential biases in patterns
- Suggest confidence adjustments (informational)
- Note risk factors (informational)
- Provide behavioral insights

**Output Format:**
Return a JSON object with:
- explanation: Why the decision makes sense (or doesn't)
- bias_detected: Any bias in recent patterns (none/recency/loss_aversion/overconfidence)
- confidence_suggestion: Suggested confidence adjustment (increase/decrease/hold)
- risk_notes: Any risk factors to monitor
- actionability: MUST be "informational_only" (locked field)
"""

    def build_explanation_prompt(
        self,
        pair: str,
        strategy: str,
        decision: Dict[str, Any],
        aggregate_state: Dict[str, Any],
        recent_knowledge: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Build prompt for decision explanation.

        Args:
            pair: Trading pair symbol
            strategy: Strategy name (scalper/swing)
            decision: Trading decision dict (8-key schema)
            aggregate_state: Aggregate state snapshot
            recent_knowledge: Optional recent knowledge entries

        Returns:
            Formatted prompt string
        """
        # Build context sections
        market_section = self._format_market_context(decision)
        decision_section = self._format_decision_context(decision)
        aggregate_section = self._format_aggregate_context(aggregate_state)
        knowledge_section = self._format_knowledge_context(recent_knowledge)

        # Combine into prompt
        prompt = f"""{self.SYSTEM_DIRECTIVE}

**Trading Pair:** {pair}
**Strategy:** {strategy}

{market_section}

{decision_section}

{aggregate_section}

{knowledge_section}

**Task:** Explain this trading decision. Identify any biases. Suggest confidence adjustments. Note risk factors.
**REMEMBER:** Your output is INFORMATIONAL ONLY. Return JSON with actionability="informational_only".
"""
        return prompt

    def build_batch_analysis_prompt(
        self,
        pair: str,
        decisions: List[Dict[str, Any]],
        aggregate_state: Dict[str, Any]
    ) -> str:
        """
        Build prompt for batch decision analysis.

        Args:
            pair: Trading pair symbol
            decisions: List of recent decisions (max 10)
            aggregate_state: Aggregate state snapshot

        Returns:
            Formatted prompt string
        """
        # Format decisions
        decision_lines = []
        for i, dec in enumerate(decisions[:10], 1):
            decision_lines.append(
                f"Decision {i}: {dec['action']} (confidence: {dec['confidence']:.2f})"
            )

        decisions_text = "\n".join(decision_lines)

        prompt = f"""{self.SYSTEM_DIRECTIVE}

**Trading Pair:** {pair}
**Analysis Type:** Batch Decision Review

**Recent Decisions (Last {len(decisions)}):**
{decisions_text}

{self._format_aggregate_context(aggregate_state)}

**Task:** Analyze this batch of decisions for patterns, biases, and consistency. Provide behavioral insights.
**REMEMBER:** Your output is INFORMATIONAL ONLY. Return JSON with actionability="informational_only".
"""
        return prompt

    def build_performance_review_prompt(
        self,
        pair: str,
        aggregate_state: Dict[str, Any],
        drawdown: float,
        win_rate: float
    ) -> str:
        """
        Build prompt for performance review.

        Args:
            pair: Trading pair symbol
            aggregate_state: Aggregate state snapshot
            drawdown: Current drawdown percentage
            win_rate: Current win rate percentage

        Returns:
            Formatted prompt string
        """
        prompt = f"""{self.SYSTEM_DIRECTIVE}

**Trading Pair:** {pair}
**Analysis Type:** Performance Review

**Current Metrics:**
- Win Rate: {win_rate:.2f}%
- Drawdown: {drawdown:.2f}%

{self._format_aggregate_context(aggregate_state)}

**Task:** Review performance. Identify concerning patterns. Suggest risk management considerations.
**REMEMBER:** Your output is INFORMATIONAL ONLY. Return JSON with actionability="informational_only".
"""
        return prompt

    def _format_market_context(self, decision: Dict[str, Any]) -> str:
        """Format market data from decision."""
        tick = decision.get("tick", {})
        return f"""**Market Context:**
- Bid: {tick.get('bid', 'N/A')}
- Ask: {tick.get('ask', 'N/A')}
- Spread: {tick.get('ask', 0) - tick.get('bid', 0):.5f}
- Time: {decision.get('timestamp', 'N/A')}"""

    def _format_decision_context(self, decision: Dict[str, Any]) -> str:
        """Format decision data."""
        return f"""**Decision:**
- Action: {decision.get('action', 'N/A')}
- Confidence: {decision.get('confidence', 0):.2f}
- Entry Type: {decision.get('entry_type', 'N/A')}
- Reasoning: {decision.get('reasoning', 'N/A')}"""

    def _format_aggregate_context(self, state: Dict[str, Any]) -> str:
        """Format aggregate state context."""
        total_trades = state.get("total_trades", 0)
        win_rate = state.get("win_rate", 0)
        total_pnl = state.get("total_pnl", 0)

        # Strategy-specific stats
        scalper = state.get("scalper", {})
        swing = state.get("swing", {})

        return f"""**Performance Aggregate:**
- Total Trades: {total_trades}
- Win Rate: {win_rate:.2f}%
- Total PnL: {total_pnl:.2f}

**Scalper Stats:**
- Trades: {scalper.get('total_trades', 0)}
- Win Rate: {scalper.get('win_rate', 0):.2f}%

**Swing Stats:**
- Trades: {swing.get('total_trades', 0)}
- Win Rate: {swing.get('win_rate', 0):.2f}%"""

    def _format_knowledge_context(
        self,
        knowledge: Optional[List[Dict[str, Any]]]
    ) -> str:
        """Format recent knowledge context."""
        if not knowledge:
            return "**Recent Knowledge:** None available"

        lines = ["**Recent Knowledge:**"]
        for entry in knowledge[:5]:  # Max 5 entries
            action = entry.get("action", "N/A")
            result = entry.get("result", "unknown")
            reasoning = entry.get("reasoning", "N/A")
            lines.append(f"- {action} -> {result}: {reasoning}")

        return "\n".join(lines)
