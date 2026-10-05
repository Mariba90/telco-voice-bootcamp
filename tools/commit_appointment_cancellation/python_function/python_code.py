def commit_appointment_cancellation(appointment_id: str = "", reason: str = "", idempotency_key: str = "") -> dict:
    """Cancels a scheduled appointment after caller confirmation.
    
    Conversational pacing: Process appointment cancellation.

    Returns:
        dict: Tool response data or agent_action error message.
    """
    try:
        return {
            "cancelled": True,
            "appointment_id": appointment_id,
            "confirmation_code": "CNL-2201"
        }
    except Exception as e:
        return {"agent_action": f"Error cancelling appointment: {e}"}
