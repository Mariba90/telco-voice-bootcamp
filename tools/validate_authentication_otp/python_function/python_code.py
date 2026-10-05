_otp_failures = {}

def validate_authentication_otp(challenge_id: str = "", code: str = "") -> dict:
    """Validates the 6-digit OTP code provided by the caller.
    
    Conversational pacing: Let the customer know you are verifying the security code.

    Returns:
        dict: Tool response data or agent_action error message.
    """
    try:
        clean_code = str(code).strip()
        key = str(challenge_id).strip() or "default"
        
        is_repeated = len(clean_code) == 6 and len(set(clean_code)) == 1
        is_known_fail = clean_code in [
            "000000", "111111", "222222", "333333", "444444", "555555",
            "666666", "777777", "888888", "999999", "000001", "123123",
            "0000", "1111", "9999", "wrong", "fail", "invalid"
        ]
        is_fail_challenge = "FAIL" in key.upper()
        is_invalid_format = len(clean_code) != 6 or not clean_code.isdigit()
        
        if is_fail_challenge or is_repeated or is_known_fail or is_invalid_format:
            _otp_failures[key] = _otp_failures.get(key, 0) + 1
            fails = _otp_failures[key]
            attempts_left = max(0, 3 - fails)
            return {
                "auth_status": "Fail",
                "attempts_remaining": attempts_left,
                "agent_action": "Invalid OTP code entered."
            }
            
        return {
            "auth_status": "Pass",
            "attempts_remaining": 3,
            "authenticated_account_id": "ACC-9821"
        }
    except Exception as e:
        return {"agent_action": f"Error validating OTP: {e}"}

