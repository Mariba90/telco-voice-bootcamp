def add_technician_note(appointment_id: str = "APT-8821", note: str = "") -> dict:
    """Attaches a note or gate/access instructions for the dispatched or en-route technician.
    
    Conversational pacing: Attach a note for your technician.

    Returns:
        dict: Tool response data or agent_action error message.
    """
    try:
        return {
            "status": "note_attached",
            "appointment_id": appointment_id,
            "note": note,
            "confirmation": "Note successfully delivered to technician dispatch system."
        }
    except Exception as e:
        return {"agent_action": f"Error attaching technician note: {e}"}

