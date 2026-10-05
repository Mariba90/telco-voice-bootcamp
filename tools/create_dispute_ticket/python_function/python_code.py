def create_dispute_ticket(billing_account: str = "", charge_id: str = "", reason: str = "", notes: str = "") -> dict:
    """Opens a formal billing dispute ticket for an itemized charge.
    
    Conversational pacing: Inform the customer you are filing a billing dispute ticket.

    Returns:
        dict: Tool response data or agent_action error message.
    """
    try:
        return {
            "ticket_id": "DSP-4412",
            "eta_business_days": 3,
            "status": "open"
        }
    except Exception as e:
        return {"agent_action": f"Error creating dispute: {e}"}
