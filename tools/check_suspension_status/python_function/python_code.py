def check_suspension_status(cirn: str = "", service_id: str = "", check_type: str = "") -> dict:
    """Checks the suspension state and reason for a line of service.
    
    Conversational pacing: Check line suspension status and outstanding balance.

    Args:
        cirn: Customer identifier reference number.
        service_id: Service or line identifier, or check context ('check_active', 'lost_stolen', etc.).
        check_type: Optional check context ('check_active', 'lost_stolen', 'non_payment').

    Returns:
        dict: Tool response data or agent_action error message.
    """
    try:
        combined = f"{service_id} {check_type}".lower()
        if any(w in combined for w in ["active", "check", "verify", "functional", "is_active"]):
            return {
                "is_suspended": False,
                "status": "active",
                "reason": "none",
                "amount_due": 0.0,
                "currency": "USD",
                "summary": "Service is currently active and fully functional."
            }
        if any(w in combined for w in ["lost", "stolen", "found"]):
            return {
                "is_suspended": True,
                "status": "suspended",
                "reason": "lost_stolen",
                "amount_due": 0.0,
                "currency": "USD",
                "summary": "Line was suspended due to lost or stolen device. No outstanding balance owed."
            }
        return {
            "is_suspended": True,
            "status": "suspended",
            "reason": "non_payment",
            "amount_due": 89.50,
            "currency": "USD",
            "summary": "Line is suspended for non-payment with an outstanding balance of $89.50."
        }
    except Exception as e:
        return {"agent_action": f"Error checking suspension: {e}"}

