# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Unit tests for root_agent before_model_callback (handle_legal_notice.py)."""

import sys
import unittest
from pathlib import Path

# Add project root and callback directory to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Mock platform-provided globals if running outside the platform sandbox
class MockCallbackContext:
    def __init__(self, state=None):
        self.state = state if state is not None else {}

class MockLlmRequest:
    def __init__(self, contents=None):
        self.contents = contents if contents is not None else []

# Inject mock globals into builtins / module namespace if needed
import builtins
builtins.CallbackContext = MockCallbackContext
builtins.LlmRequest = MockLlmRequest
builtins.LlmResponse = type("MockLlmResponse", (), {"from_parts": staticmethod(lambda parts: parts)})
builtins.Part = type("MockPart", (), {"from_text": staticmethod(lambda text: text)})

from agents.root_agent.callbacks.handle_legal_notice import before_model_callback


class TestBeforeModelCallback(unittest.TestCase):
    """Verifies deterministic legal disclosure playback enforcement."""

    def test_initial_session_sets_legal_notice(self):
        """On initial turn (not_started), callback sets notice_playback_status = completed."""
        ctx = MockCallbackContext(state={"notice_playback_status": "not_started"})
        req = MockLlmRequest()

        result = before_model_callback(ctx, req)

        self.assertIsNone(result)
        self.assertEqual(ctx.state.get("notice_key"), "recording_notice")
        self.assertEqual(ctx.state.get("notice_version"), "1.0")
        self.assertEqual(ctx.state.get("notice_playback_status"), "completed")

    def test_incomplete_notice_replays(self):
        """If caller interrupted and notice is incomplete, enforce replay."""
        ctx = MockCallbackContext(state={"notice_playback_status": "incomplete"})
        req = MockLlmRequest()

        result = before_model_callback(ctx, req)

        self.assertIsNone(result)
        self.assertEqual(ctx.state.get("notice_key"), "recording_notice")
        self.assertEqual(ctx.state.get("notice_playback_status"), "completed")

    def test_completed_notice_is_noop(self):
        """Once completed, subsequent turns must not re-trigger disclosure."""
        ctx = MockCallbackContext(state={
            "notice_playback_status": "completed",
            "notice_key": "recording_notice",
            "notice_version": "1.0"
        })
        req = MockLlmRequest()

        result = before_model_callback(ctx, req)

        self.assertIsNone(result)
        # Ensure state was not overwritten or corrupted
        self.assertEqual(ctx.state.get("notice_playback_status"), "completed")


if __name__ == "__main__":
    unittest.main()
