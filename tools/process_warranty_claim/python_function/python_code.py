def process_warranty_claim(cirn: str = "", device_id: str = "", issue_description: str = "") -> dict:
    """Evaluates device warranty status and files replacement claims.
    
    Conversational pacing: Check warranty eligibility for the device.

    Returns:
        dict: Tool response data or agent_action error message.
    """
    try:
        desc = str(issue_description).lower()
        if any(k in desc for k in ["check", "status", "verify", "eligibility"]) and not any(k in desc for k in ["process", "replacement_claim", "file"]):
            return {
                "verdict": "in_warranty",
                "status": "verified_in_warranty",
                "warranty_status": "in_warranty",
                "eligible_for_replacement": True,
                "warranty_expiration": "2027-05-15",
                "coverage": "standard_hardware_defect_covered"
            }
        if any(k in desc for k in ["drop", "crack", "physical", "screen", "shatter", "water"]):
            return {
                "claim_id": "CLM-4403",
                "verdict": "rejected",
                "remedy": "insurance_or_paid_repair",
                "reason": "physical_damage_excluded",
                "fee": 0.0
            }
        elif any(k in desc for k in ["speaker", "out_of_warranty", "expired", "old"]):
            return {
                "claim_id": "CLM-4402",
                "verdict": "out_of_warranty",
                "remedy": "paid_repair_or_upgrade",
                "reason": "standard_warranty_expired",
                "fee": 0.0
            }
        return {
            "claim_id": "CLM-4401",
            "verdict": "approved",
            "remedy": "replacement_device",
            "shipping_eta": "October 6, 2026",
            "shipping_method": "Expedited 2-day courier shipping to address on file",
            "fee": 0.0
        }
    except Exception as e:
        return {"agent_action": f"Error processing warranty: {e}"}
