def place_service_order(cirn: str = "", plan_id: str = "", address: str = "", idempotency_key: str = "") -> dict:
    """Submits a confirmed service addition or upgrade order.
    
    Conversational pacing: Submit the confirmed service order.

    Returns:
        dict: Tool response data or agent_action error message.
    """
    try:
        plan_str = str(plan_id).lower()
        if "stream" in plan_str or "addon" in plan_str:
            fee = 15.00 if "pass" in plan_str else 25.00
            order_num = "STR-40912"
        elif "mob" in plan_str or "unlimited" in plan_str:
            fee = 65.00 if "plus" in plan_str else 85.00
            order_num = "MOB-77215"
        elif "premier" in plan_str:
            fee = 70.00
            order_num = "TV-90812"
        else:
            fee = 45.00
            order_num = "TV-90812"

        return {
            "order_id": "ORD-11029",
            "order_number": order_num,
            "status": "confirmed",
            "delivery_eta_iso": "2026-10-05T12:00:00Z",
            "monthly_fee": fee,
            "currency": "USD"
        }
    except Exception as e:
        return {"agent_action": f"Error placing order: {e}"}
