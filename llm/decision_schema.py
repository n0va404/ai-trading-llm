"""
Decision Schema - Phase 7

JSON schema for LLM advisory responses.
Enforces "actionability": "informational_only" constraint.

Architecture:
- Fixed output schema (locked fields)
- Actionability field (informational_only)
- Validation helper methods
- NO execution logic
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


# Fixed JSON schema for LLM advisory responses
ADVISORY_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "explanation": {
            "type": "string",
            "description": "Why the decision makes sense (or doesn't)"
        },
        "bias_detected": {
            "type": "string",
            "enum": ["none", "recency", "loss_aversion", "overconfidence", "pattern_failing"],
            "description": "Bias detected in recent patterns"
        },
        "confidence_suggestion": {
            "type": "string",
            "enum": ["increase", "decrease", "hold"],
            "description": "Suggested confidence adjustment"
        },
        "risk_notes": {
            "type": "string",
            "description": "Risk factors to monitor"
        },
        "actionability": {
            "type": "string",
            "enum": ["informational_only"],
            "description": "LOCKED FIELD - Must be informational_only"
        }
    },
    "required": [
        "explanation",
        "bias_detected",
        "confidence_suggestion",
        "risk_notes",
        "actionability"
    ],
    "additionalProperties": False
}


class DecisionSchema:
    """
    Validator for LLM advisory responses.

    **CRITICAL:** Enforces "actionability": "informational_only" constraint.
    """

    def __init__(self):
        """Initialize decision schema validator."""
        self.schema = ADVISORY_RESPONSE_SCHEMA

    def validate_advisory_response(
        self,
        response: Dict[str, Any]
    ) -> tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Validate LLM advisory response against schema.

        Args:
            response: LLM response dictionary

        Returns:
            Tuple of (is_valid, error_message, sanitized_response)
        """
        # Check required fields
        required_fields = [
            "explanation",
            "bias_detected",
            "confidence_suggestion",
            "risk_notes",
            "actionability"
        ]

        for field in required_fields:
            if field not in response:
                return False, f"Missing required field: {field}", {}

        # Check actionability is locked
        if response["actionability"] != "informational_only":
            logger.error(
                f"[LLM] INVALID actionability: {response['actionability']}"
            )
            return False, "actionability must be 'informational_only'", {}

        # Check bias_detected enum
        valid_biases = [
            "none",
            "recency",
            "loss_aversion",
            "overconfidence",
            "pattern_failing"
        ]
        if response["bias_detected"] not in valid_biases:
            return False, f"Invalid bias_detected: {response['bias_detected']}", {}

        # Check confidence_suggestion enum
        valid_suggestions = ["increase", "decrease", "hold"]
        if response["confidence_suggestion"] not in valid_suggestions:
            return False, f"Invalid confidence_suggestion: {response['confidence_suggestion']}", {}

        # Sanitize response (remove extra fields)
        sanitized = {
            "explanation": response["explanation"],
            "bias_detected": response["bias_detected"],
            "confidence_suggestion": response["confidence_suggestion"],
            "risk_notes": response["risk_notes"],
            "actionability": "informational_only"  # Force lock
        }

        logger.info("[LLM] Advisory response validated")
        return True, None, sanitized

    def get_schema(self) -> Dict[str, Any]:
        """
        Get the advisory response JSON schema.

        Returns:
            JSON schema dictionary
        """
        return self.schema
