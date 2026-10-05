def evaluate_routing_rules(utterance: str = "", current_module: str = "") -> dict:
    """Evaluates intent classification and suggested routing module.
    
    Conversational pacing: Determine the best department to route the caller.

    Returns:
        dict: Tool response data or agent_action error message.
    """
    try:
        utt = str(utterance).lower()
        if any(k in utt for k in ["mfa", "two-factor", "2fa", "password", "reset", "secure", "login", "suspend", "restore", "account"]):
            route = "M7"
        elif any(k in utt for k in ["tech", "repair", "troubleshoot", "outage", "internet", "slow", "sim", "puk", "device"]):
            route = "M4"
        elif any(k in utt for k in ["plan", "upgrade", "order", "addon", "streaming", "extender"]):
            route = "M5"
        elif any(k in utt for k in ["appoint", "technician", "ticket", "reschedule", "visit"]):
            route = "M6"
        else:
            route = "M3"

        return {
            "route": route,
            "confidence": 0.95,
            "requires_auth": True
        }
    except Exception as e:
        return {"agent_action": f"Error evaluating routing: {e}"}
