# Project TODO & Lifecycle Checklist: Telco Voice Central

**Target GCP App:** `projects/gcp-i-and-d-practitioners/locations/us/apps/maryam-telco-voice-central`  
**Display Name:** `Maryam - Telco Voice Central`  
**Local App Directory:** `c:\Users\mbagheri\Downloads\GECX\telco-voice-central`  
**Spec References:** [PRD.md](PRD.md) · [EVAL-PLAN-Telco-Voice-Central.md](EVAL-PLAN-Telco-Voice-Central.md)

---

## 7-Gate Lifecycle Checklist

- [x] **Step 1: Gather Requirements (Gate 1)**
  - Comprehensive PRD established in [PRD.md](PRD.md).
  - 20 Behavioral Requirements mapped (`BR-TV-001` through `BR-TV-020`).
  - 12 Verbatim Compliance Keys identified (recording notice, legal disclosures, handoffs, empathy protocol).
  - 11 Standardized Reason Codes specified for all handoff and termination paths.
  - 7 Core Customer Journeys (CUJs) defined and weighted by real call volume:
    - CUJ-1: Password reset (15%)
    - CUJ-2: Billing dispute, auto-eligible (25%)
    - CUJ-3: Tech support, TV no signal (30%)
    - CUJ-4: Appointment reschedule (10%)
    - CUJ-5: Sales, add TV (15%)
    - CUJ-6: Restore from non-payment (5%)
    - CUJ-7: Secondary-language tech fallback (subset of CUJ-3)

- [x] **Step 2: TDD + User Approval (Gate 2)**
  - Agent topology designed: Hierarchical architecture with 1 root dispatcher (`root_agent`) and 5 specialized child agents (`account_agent`, `appointments_agent`, `billing_agent`, `sales_agent`, `tech_support_agent`).
  - 34 Tool contracts defined with input schemas, output structures, and `mock_mode` support.
  - Pre-model callback pattern designed for deterministic legal disclosure and recording notice playback.
  - Naming constraints approved (`Maryam - Telco Voice Central` / `maryam-telco-voice-central`).

- [x] **Step 3: Scaffold App (Gate 3)**
  - Application manifests scaffolded: [app.json](app.json), [gecx-config.json](gecx-config.json).
  - Agents scaffolded with instructions and routing rules:
    - `agents/root_agent/`
    - `agents/account_agent/`
    - `agents/appointments_agent/`
    - `agents/billing_agent/`
    - `agents/sales_agent/`
    - `agents/tech_support_agent/`
  - 34 tools implemented under `tools/` with mock capabilities and error handling.
  - `before_model_callback` implemented in [handle_legal_notice.py](agents/root_agent/callbacks/handle_legal_notice.py).

- [x] **Step 4: Lint Clean (Gate 4)**
  - Platform variable conflict resolved (`current_date` removed from `variableDeclarations` as it is automatically populated by CES).
  - Callback signature verified against platform standard: `def before_model_callback(callback_context: CallbackContext, llm_request: LlmRequest) -> Optional[LlmResponse]`.
  - Static lint verification via `cxas lint --app-dir .` passed with **0 errors, 0 warnings**.

- [x] **Step 5: Generate Evals — one eval-writer dispatch per type (Gate 5)**
  - [x] Multi-layer eval plan defined in [EVAL-PLAN-Telco-Voice-Central.md](EVAL-PLAN-Telco-Voice-Central.md), 100% aligned with [PRD.md](PRD.md).
  - [x] Generated modular evals across all 4 eval types (83 eval manifests total, passing `cxas lint` with 0 errors, 0 warnings):
    - [x] Type A: **Simulations** (75 files in [evals/simulations/](evals/simulations/)) — **The complete 70 public benchmark evaluations** from `Day 1 - greenfield_agent_public_evals.md` + 5 P0 hard safety/compliance edge cases (`sim__hard_01_blocklist_deflection` through `sim__hard_05_interrupted_recording_notice_replay`).
    - [x] Type B: **Goldens** (7 files in [evals/goldens/](evals/goldens/)) — 7 deterministic turn-by-turn golden conversations with exact tool call assertions.
    - [x] Type C: **Tool Tests** ([evals/tool_tests/cuj_tool_tests.yaml](evals/tool_tests/cuj_tool_tests.yaml)) — Tool contract unit tests checking output envelopes and error handling.
    - [x] Type D: **Callback Tests** ([evals/callback_tests/test_before_model_callback.py](evals/callback_tests/test_before_model_callback.py)) — Unit tests for legal notice barge-in suppression and replay callbacks (passed 3/3 tests).
  - [x] Static lint verification via `cxas lint` validated all **83 eval files** (0 errors, 0 warnings).


- [/] **Step 6: Push + Verify (Gate 6)**
  - [x] Initial application push executed to `projects/gcp-i-and-d-practitioners/locations/us/apps/maryam-telco-voice-central`.
  - [x] Verified app presence in `cxas apps list`.
  - [ ] Push generated evaluation suites via `cxas push-eval` / platform eval runner.
  - [ ] Verify evals are successfully registered and visible in the app.

- [ ] **Step 7: Self-Grade Against Evals and Close Every Gap (Gate 7)**
  - [ ] Run baseline evaluation suite across CUJ-1 through CUJ-7.
  - [ ] Measure pass rates against Gate standards:
    - P0 Scenarios: 100% pass (zero tolerance on safety, compliance, PII, auth).
    - P1 Scenarios: ≥90% pass.
    - Volume-weighted pass rate: ≥90%.
  - [ ] Triage and fix any failing edge cases or routing discrepancies.
  - [ ] Declare production readiness once all gates are met.
