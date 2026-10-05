_pin_failures = {}

def validate_authentication_pin(cirn: str = "", pin: str = "") -> dict:
    """Validates the 4-digit security PIN captured from native phone keypad input.
    
    Conversational pacing: Tell the caller you are verifying their PIN.

    Returns:
        dict: Tool response data or agent_action error message.
    """
    try:
        clean_pin = str(pin).strip()
        key = cirn or "default"
        
        is_repeated = len(clean_pin) == 4 and len(set(clean_pin)) == 1
        is_known_fail = clean_pin in [
            "0000", "1111", "2222", "3333", "4444", "5555",
            "6666", "7777", "8888", "9999", "0001", "1212",
            "wrong", "fail", "invalid"
        ]
        
        if is_repeated or is_known_fail or len(clean_pin) != 4 or not clean_pin.isdigit():
            _pin_failures[key] = _pin_failures.get(key, 0) + 1
            fails = _pin_failures[key]
            attempts_left = max(0, 3 - fails)
            return {
                "auth_status": "Fail",
                "attempts_remaining": attempts_left,
                "agent_action": "Invalid PIN entered."
            }

        return {
            "auth_status": "Pass",
            "attempts_remaining": 3,
            "authenticated_account_id": "ACC-9821"
        }
    except Exception as e:
        return {"agent_action": f"Error validating PIN: {e}"}

