def submit_diagnostic_step(session_id: str = "", step_number: int = 1, caller_response: str = "") -> dict:
    """Submits the result of a diagnostic troubleshooting step.
    
    Conversational pacing: Process the diagnostic step outcome.

    Returns:
        dict: Tool response data or agent_action error message.
    """
    try:
        return {
            "status": "resolved",
            "next_step": "",
            "resolution_summary": "TV signal restored successfully after cable reseat."
        }
    except Exception as e:
        return {"agent_action": f"Error submitting diagnostic step: {e}"}
