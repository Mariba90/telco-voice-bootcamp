def fetch_active_appointments(cirn: str = "") -> dict:
    """Retrieves scheduled technician visits and their dispatch status.
    
    Conversational pacing: Lookup scheduled technician appointments.

    Returns:
        dict: Tool response data or agent_action error message.
    """
    try:
        return {
            "appointments": [
                {
                    "id": "APT-8821",
                    "service_type": "internet",
                    "description": "Internet repair service",
                    "date": "2026-10-02",
                    "window": "08:00 - 12:00",
                    "timezone": "America/New_York",
                    "dispatch_status": "en_route",
                    "notes": ""
                },
                {
                    "id": "APT-8822",
                    "service_type": "tv",
                    "description": "TV installation service",
                    "date": "2026-10-03",
                    "window": "13:00 - 17:00",
                    "timezone": "America/New_York",
                    "dispatch_status": "scheduled",
                    "notes": ""
                }
            ]
        }
    except Exception as e:
        return {"agent_action": f"Error fetching appointments: {e}"}
