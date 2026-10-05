def execute_adjustment(decision_id: str = "", idempotency_key: str = "", billing_account: str = "", charge_id: str = "", amount: float = 0.0, operation_type: str = "statement_credit") -> dict:
    """Commits an authorized statement credit or refund to the billing system.
    
    Conversational pacing: Tell the customer you are processing the authorized credit adjustment.

    Returns:
        dict: Tool response data or agent_action error message.
    """
    try:
        return {
            "operation_id": "OP-ADJ-551",
            "status": "succeeded",
            "amount": 14.50,
            "currency": "USD",
            "operation_type": "statement_credit",
            "posting_timeframe": "1 to 2 billing cycles"
        }
    except Exception as e:
        return {"agent_action": f"Error executing adjustment: {e}"}
