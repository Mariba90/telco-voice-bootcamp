def lookup_ticket_status(ticket_id: str = "", service_type: str = "") -> dict:
    """Checks the status and latest update on an existing support or dispute ticket.
    
    Conversational pacing: Lookup ticket progress and latest updates.

    Returns:
        dict: Tool response data or agent_action error message.
    """
    try:
        # If no specific ticket ID is provided or if looking up general tickets
        if not ticket_id or ticket_id.lower() in ["none", "unknown", "any", "all", "check"]:
            if service_type and "tv" in service_type.lower():
                return {
                    "ticket_id": "TCK-TV-4402",
                    "service_type": "tv",
                    "state": "open",
                    "last_update": "2026-10-01",
                    "summary": "TV service pixelation review in progress."
                }
            return {
                "tickets": [],
                "status": "no_tickets_found",
                "summary": "No active support or dispute tickets found for this account."
            }
        
        return {
            "ticket_id": ticket_id,
            "state": "open",
            "last_update": "2026-09-30",
            "summary": "Technician review in progress."
        }
    except Exception as e:
        return {"agent_action": f"Error looking up ticket: {e}"}
