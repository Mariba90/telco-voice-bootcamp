def execute_live_agent_handover(reason_code: str = "", summary: str = "", sanitized_context: str = "") -> dict:
    """Transfers the caller to a human specialist with allowlisted session context.
    
    Conversational pacing: Connect the caller to a live customer service specialist.

    Returns:
        dict: Tool response data or agent_action error message.
    """
    try:
        if "fraud" in str(reason_code).lower():
            queue = "fraud"
        elif "secondary_language" in str(reason_code).lower() or "spanish" in str(reason_code).lower():
            queue = "spanish_support"
        else:
            queue = "general_support"
        return {
            "handover_id": "HND-1002",
            "queue": queue,
            "status": "handover_accepted"
        }
    except Exception as e:
        return {"agent_action": f"Error executing handoff: {e}"}
