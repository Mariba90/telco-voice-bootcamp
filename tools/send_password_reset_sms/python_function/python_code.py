def send_password_reset_sms(cirn: str = "") -> dict:
    """Dispatches a secure one-time password reset link with 30-minute validity to the on-file phone.
    
    Conversational pacing: Send password reset link to customer on-file phone number.

    Returns:
        dict: Tool response data or agent_action error message.
    """
    try:
        return {
            "sent": True,
            "valid_minutes": 30,
            "destination_masked": "***-***-1234"
        }
    except Exception as e:
        return {"agent_action": f"Error sending password reset: {e}"}
