def fetch_recent_bills(billing_account: str = "") -> dict:
    """Fetches recent statements, balances, and itemized charges for an authenticated account.
    
    Conversational pacing: Let the customer know you are pulling up their recent billing statements.

    Returns:
        dict: Tool response data or agent_action error message.
    """
    try:
        return {
            "bills": [
                {
                    "bill_id": "BILL-2026-09",
                    "date": "2026-09-15",
                    "total_amount": 89.50,
                    "currency": "USD",
                    "due_date": "2026-10-05",
                    "line_items": [
                        {"id": "CHG-101", "description": "Gigabit Fiber Internet", "amount": 75.00},
                        {"id": "CHG-102", "description": "Late Fee / Surcharge", "amount": 14.50}
                    ]
                }
            ]
        }
    except Exception as e:
        return {"agent_action": f"Error fetching bills: {e}"}
