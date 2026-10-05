def process_bill_payment(billing_account: str = "", amount: float = 0.0, payment_token: str = "", idempotency_key: str = "") -> dict:
    """Executes a bill payment against the account using tokenized payment info.
    
    Conversational pacing: Inform the customer you are submitting their payment.

    Returns:
        dict: Tool response data or agent_action error message.
    """
    try:
        return {
            "payment_id": "PMT-7721",
            "status": "succeeded",
            "authorization_code": "AUTH-441",
            "amount": amount,
            "currency": "USD",
            "new_balance": 0.0
        }
    except Exception as e:
        return {"agent_action": f"Error processing payment: {e}"}
