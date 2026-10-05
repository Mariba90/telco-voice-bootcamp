def evaluate_adjustment_eligibility(billing_account: str = "", charge_id: str = "", requested_amount: float = 0.0) -> dict:
    """Authoritatively evaluates if a charge qualifies for a statement credit or refund.
    
    Conversational pacing: Check backend authorization for fee credit eligibility.

    Returns:
        dict: Tool response data or agent_action error message.
    """
    try:
        return {
            "decision_id": "DEC-8812",
            "verdict": "eligible",
            "operation_type": "statement_credit",
            "allowed_amount": 14.50,
            "currency": "USD",
            "caller_safe_reason": "One-time courtesy adjustment for unexpected fee",
            "valid_until_iso": "2026-10-01T00:00:00Z"
        }
    except Exception as e:
        return {"agent_action": f"Error evaluating adjustment: {e}"}
