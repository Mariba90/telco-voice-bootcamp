def send_authentication_otp(cirn: str = "", channel: str = "sms") -> dict:
    """Dispatches a 6-digit one-time passcode to the verified on-file contact number.
    
    Conversational pacing: Inform the customer you are sending a verification code to their phone.

    Returns:
        dict: Tool response data or agent_action error message.
    """
    try:
        challenge_id = "CHG-FAIL-OTP" if "FAIL" in str(cirn) else "CHG-9921"
        return {
            "challenge_id": challenge_id,
            "sent": True,
            "valid_minutes": 5,
            "destination_masked": "***-***-1234"
        }
    except Exception as e:
        return {"agent_action": f"Error sending OTP: {e}"}
