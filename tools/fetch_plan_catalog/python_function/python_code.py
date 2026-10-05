def fetch_plan_catalog(lob: str = "tv", customer_type: str = "Existing") -> dict:
    """Fetches 2 to 3 comparable plans and packages matching customer criteria.
    
    Conversational pacing: Pull up plan options and pricing catalog.

    Returns:
        dict: Tool response data or agent_action error message.
    """
    try:
        lob_lower = str(lob).lower()
        if any(k in lob_lower for k in ["stream", "addon", "add-on"]):
            plans = [
                {
                    "id": "ADDON-STREAM-PASS",
                    "name": "Stream Pass",
                    "price": 15.00,
                    "currency": "USD",
                    "key_features": ["Popular streaming apps included", "HD streaming", "No contract"]
                },
                {
                    "id": "ADDON-STREAM-PLUS",
                    "name": "Stream Plus",
                    "price": 25.00,
                    "currency": "USD",
                    "key_features": ["Premium streaming bundle", "4K Ultra HD", "Multiple concurrent streams"]
                }
            ]
        elif any(k in lob_lower for k in ["mobile", "mobility", "cellular", "data", "phone"]):
            plans = [
                {
                    "id": "PLAN-MOB-PLUS",
                    "name": "Unlimited Plus",
                    "price": 65.00,
                    "currency": "USD",
                    "key_features": ["50GB high-speed data", "Unlimited talk and text", "5G access"]
                },
                {
                    "id": "PLAN-MOB-PREMIUM",
                    "name": "Unlimited Premium",
                    "price": 85.00,
                    "currency": "USD",
                    "key_features": ["Unlimited high-speed data", "15GB mobile hotspot", "Ultra Wideband 5G"]
                }
            ]
        else:
            plans = [
                {
                    "id": "PLAN-TV-ESSENTIAL",
                    "name": "TV Essentials",
                    "price": 45.00,
                    "currency": "USD",
                    "key_features": ["75+ channels", "HD streaming", "1 Stream Box included"]
                },
                {
                    "id": "PLAN-TV-PREMIER",
                    "name": "TV Premier",
                    "price": 70.00,
                    "currency": "USD",
                    "key_features": ["140+ channels", "4K streaming", "Cloud DVR included"]
                }
            ]
        return {
            "plans": plans
        }
    except Exception as e:
        return {"agent_action": f"Error fetching catalog: {e}"}
