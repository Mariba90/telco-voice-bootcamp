def send_sms_notification(cirn: str = "", sms_type: str = "Public", template_name: str = "", payload_data: str = "") -> dict:
    """Dispatches an SMS notification template (receipt, appointment details, etc.) to on-file contact.
    
    Conversational pacing: Send confirmation text message to caller.

    Returns:
        dict: Tool response data or agent_action error message.
    """
    try:
        return {
            "message_id": "MSG-9921",
            "status": "dispatched"
        }
    except Exception as e:
        return {"agent_action": f"Error sending SMS: {e}"}
