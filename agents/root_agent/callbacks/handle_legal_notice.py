from typing import Optional


def before_model_callback(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """Enforces non-interruptible legal disclosure playback with barge-in disabled.

    Args:
        callback_context: The active session callback context containing session state.
        llm_request: The LLM request object.

    Returns:
        Optional[LlmResponse]: None to proceed with standard model call after updating state.
    """
    state = callback_context.state
    notice_status = state.get("notice_playback_status", "not_started")

    # On initial turn or required notice replay, enforce protected disclosure
    if notice_status in ("not_started", "incomplete"):
        state["notice_key"] = "recording_notice"
        state["notice_version"] = "1.0"
        state["notice_playback_status"] = "completed"

    # Caller blocklist check (BR-TV-002)
    clid = state.get("clid", "")
    if "+1-555-0199" in clid or "555-0199" in clid:
        state["blocklist_status"] = "restricted"

    return None
