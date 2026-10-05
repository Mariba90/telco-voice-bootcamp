# Evaluation Plan — Telco Voice Central

**Companion to:** [PRD-Telco-Voice-Central.md](PRD-Telco-Voice-Central.md)
**Cross-checked against:** `resources/n` (70 public sim evals) and `resources/Day 1 - Telco Voice Central — Agent Development Brief.pdf` (§19, §21)
**Version:** 1.0 · 2026-09-22

---

## 1. Why this document exists

The brief (§21) requires **seven kinds of test**. The public eval file supplies **one** kind — simulations — and 70 of them. Taken at face value, passing the public suite at 90% would satisfy none of the other six coverage targets and would leave **7 of 20 behavioral requirements with zero coverage**, including the two the brief itself marks as P0 safety defects.

This plan does three things:

1. **Audits** the public suite against the brief (§2–§5 below): what it covers, what it misses, where it contradicts the spec, and where it tests capabilities the spec never defines.
2. **Replaces** it with a restructured suite — a schema that makes ordering assertions deterministic, fixtures that make runs reproducible, and traceability from every scenario back to a `BR-TV-###` (§6–§9).
3. **Specifies the other six test layers** the brief requires but the public file omits (§10).

Machine-readable artifacts live in [evals/](evals/) (83 eval files total, 100% `cxas lint` clean):

| Directory / File | Layer | Contents |
|---|---|---|
| [evals/simulations/](evals/simulations/) | L4 | 75 simulation files (the 70 public evaluations + 5 hard safety/compliance edge cases) |
| [evals/goldens/](evals/goldens/) | L3 | 7 golden files with turn-by-turn deterministic assertions for core CUJs |
| [evals/tool_tests/cuj_tool_tests.yaml](evals/tool_tests/cuj_tool_tests.yaml) | L1 | Tool-contract unit tests (success, system_down, unauthorized, limits) |
| [evals/callback_tests/test_before_model_callback.py](evals/callback_tests/test_before_model_callback.py) | L2 | Unit tests for legal notice barge-in suppression and replay callbacks |

> **Alignment with PRD & Benchmark:** The 70 public evaluations and 5 hard simulations are 100% aligned with [PRD.md](PRD.md) behavioral requirements (BR-TV-001 through BR-TV-020), verbatim compliance, reason codes, and priority hierarchy.


---

## 2. What the public suite gets right

Worth preserving — these clusters are well-built and should survive the rewrite largely intact:

| Cluster | Sims | Why it's good |
|---|---|---|
| **Fraud escalation** | 5 + 1 pivot | Five distinct framings (unauthorized charges, identity theft, stolen phone, upset caller, mid-call discovery). Tests the no-auth rule from multiple entry points — exactly right for a priority-#2 behavior. |
| **Business handoff** | 5 | Hits the same rule across four different modules (cancel, password reset, restore, plan upgrade, transfer-in). Good proof that the rule is global, not per-flow. |
| **Topic switch** | 4 | `bill_dispute→cancellation`, `billing→password_reset`, `billing→fraud`, `warranty→fraud`. Directly exercises BR-TV-019 from realistic pivots. |
| **Live-agent request** | 6 | Covers voice request, DTMF request, mid-greeting interrupt, mid-troubleshooting interrupt, post-billing-answer, and secondary-language. Strong coverage of priority #4. |
| **Negative / refusal paths** | ~8 | `restore_service_refuse_payment`, `warranty_claim_physical_damage_rejection`, `warranty_claim_out_warranty`, `ticket_status_found` (none exist), `cancel_appointment_en_route`, `restore_service_already_active`. Testing what the agent must *not* do is the hard part, and the suite does it in these places. |

---

## 3. Coverage audit: requirements

Mapping all 20 `BR-TV-###` to the public suite.

| BR | Name | Public-suite coverage | Verdict |
|---|---|---|---|
| BR-TV-001 | Recording notice | — | **GAP** |
| BR-TV-002 | Restricted caller check | — | **GAP** |
| BR-TV-003 | Regional service alert | — | **GAP** |
| BR-TV-004 | Language locking | 2 secondary-language sims | PARTIAL — no "lock holds" negative, no explicit-switch test |
| BR-TV-005 | Module coverage | ~13 of 19 routing rows | PARTIAL — "internet is down", "TV no signal", autopay, refund, deposit rows untested outside generic sims |
| BR-TV-006 | Retry strikes | `sim__sim_issue_input_retry` | PARTIAL — no-input only; the no-match / `disambig_max_attempts` branch is absent |
| BR-TV-007 | DTMF capture | `sim__request_dtmf`, `sim__phone_locked_puk_code` | PARTIAL — the `"user pressed 1234"` text-encoded form is untested |
| BR-TV-008 | Auth ladder | many sims | PARTIAL — no negative proving *Identified* is insufficient for an account read |
| BR-TV-009 | PII redaction | `sim__phone_locked_puk_code` ("must not speak the PIN back") | PARTIAL — last-4 echo and OTP-never-echoed untested |
| BR-TV-010 | Tool-error tri-state | — | **GAP** — no `SYSTEM_DOWN`, business-error, or validation-error scenario anywhere |
| BR-TV-011 | Verbatim compliance | 4 of 12 keys | PARTIAL — see §4 |
| BR-TV-012 | Business handoff | 5 sims | **COVERED** |
| BR-TV-013 | Fraud escalation | 6 sims | **COVERED** |
| BR-TV-014 | After-hours awareness | 3 sims | PARTIAL — outage-24/7 and appointment-booking clauses untested |
| BR-TV-015 | Session-context handoff | — | **GAP** — no sim asserts session variables reach the live agent |
| BR-TV-016 | Malicious utterance | — | **GAP** — priority #1 in the hierarchy, zero coverage |
| BR-TV-017 | No invented data | — | **GAP** — the brief calls this a P0 safety defect |
| BR-TV-018 | Audio recording | n/a | Out of layer — belongs to L5/L7 |
| BR-TV-019 | Topic switch | 4 sims | **COVERED** |
| BR-TV-020 | Language non-degradation | 2 sims | PARTIAL — the tech-fallback case (CUJ-7) is absent |

**Tally: 3 covered · 9 partial · 7 gaps · 1 out of layer.**

### Verbatim keys (BR-TV-011)

| Tested by public suite | Untested |
|---|---|
`contract_cancellation_fee_disclosure` (4 sims)<br>`business_handoff` (5)<br>`live_agent_handoff` (6)<br>`empathy_protocol` (6) | `greeting_main`<br>`recording_notice`<br>`id_verification_otp`<br>`id_verification_pin`<br>`payment_method_preamble`<br>`refund_confirmation_pattern`<br>`outage_active`<br>`transfer_to_specialist` |

**4 of 12 keys covered.** Two of the untested keys (`payment_method_preamble`, `contract_cancellation_fee_disclosure`) have no text yet — the brief defers them to Legal. The other six have text in the brief and could be asserted today.

### Reason codes

The brief defines **11**. The public suite asserts **one** by name (`user_requested_agent`) and implies a second (`sim__warranty_claim_fraud_pivot` says "the correct fraud reason").

**Never asserted:** `malicious_input`, `no_input_escalation`, `disambig_max_attempts`, `too_many_errors`, `system_unavailable`, `business_handoff`, `auth_failure_handoff`, `refund_threshold_exceeded`, `secondary_language_live_agent`.

---

## 4. Coverage audit: CUJs and volume

### The brief's 7 CUJs vs. the public suite

| CUJ | Journey | Volume | Public coverage |
|---|---|---|---|
| CUJ-1 | Password reset | 15% | ✅ 5 sims (happy, PIN fallback, OTP failure, business, mid-call pivot) |
| CUJ-2 | Billing dispute, auto-eligible | **25%** | ❌ Only the tautological `sim__dispute_charge_my_bill`. None of the three brief assertions (lookup-before-reference, `refund_confirmation_pattern`, must-NOT-open-dispute-case) is tested. |
| CUJ-3 | Tech support, TV no signal | **30%** | ❌ No sim. `sim__request_during_troubleshooting` uses a TV symptom but tests live-agent handoff. `sim__troubleshoot_*` is generic. |
| CUJ-4 | Appointment reschedule | 10% | ✅ `sim__reschedule_technician_appointment` |
| CUJ-5 | Sales, add TV | 15% | ✅ `sim__add_tv_service_existing` |
| CUJ-6 | Restore from non-payment | 5% | ⚠️ `sim__restore_service_non_payment` — but does **not** assert the M1-routing constraint, which is the requirement's whole point |
| CUJ-7 | Secondary-language tech fallback | subset of CUJ-3 | ❌ No sim. The two secondary-language sims test a live-agent request and MFA — neither is a tech fallback, neither can produce `secondary_language_live_agent`. |

**3 of 7 CUJs uncovered — and CUJ-2 + CUJ-3 are 55% of call volume.**

### Eval effort is inversely correlated with call volume

Counting the 59 non-generic sims by primary module (some sims touch two; attributed to the module whose rule they assert):

| Module | Volume share | Non-generic sims | Eval share | Delta |
|---|---|---|---|---|
| **M4** Tech support — diagnostics / VR / outage | **30%** | 0 | **0%** | **−30pp** |
| **M3** Billing & payment | **25%** | 1 | **~2%** | **−23pp** |
| M5 Sales & equipment | 15% | 12 | ~20% | +5pp |
| M7 Account management | 15% | 20 | ~34% | **+19pp** |
| M6 Appointments | 10% | 10 | ~17% | +7pp |
| Service changes / cancellation | 5% | 6 | ~10% | +5pp |
| M1/M2 cross-cutting | — | 6 | ~10% | — |
| M8 Secondary language | subset | 2 | ~3% | — |
| M4/M5 SIM & device (shared) | — | 5 | ~8% | — |

The two largest slices of real traffic — 55% combined — carry essentially no eval weight, while account management carries more than double its share. Tuning against this suite would optimize the agent for the wrong 15% of calls.

---

## 5. Defects in the public suite

### 5.1 Contradictions and ambiguities against the brief

These need a decision from the spec owner before the suite can be trusted. Each is carried into the PRD's open-questions register.

| # | Eval | Brief says | Conflict |
|---|---|---|---|
| **C1** | `sim__report_fraud_stolen_phone` — expects immediate fraud escalation, no self-serve | M7: "Lost / stolen: **suspend the service before engaging in any other conversation**" | Does a stolen-phone-**with-fraud-claim** suspend first, or escalate immediately? The priority hierarchy (#2 fraud > #8 account actions) supports the eval; M7's flow supports suspending. **Recommendation:** suspension is protective, not self-serve — suspend, *then* emit `empathy_protocol` and escalate. Needs ratification. |
| **C2** | `sim__immediate_request` — caller interrupts the greeting; expects immediate transfer | BR-TV-001: "If the caller interrupts it, **replay it in full on the next turn**" | Priority #4 (talk to a person) outranks #7 (compliance verbatim), so the agent transfers and the call ends with **no recording notice delivered** — a quarterly-audit exposure. **Recommendation:** emit the notice as a non-blocking prefix to the handoff line. Needs Legal sign-off. |
| **C3** | `sim__cancel_service_after_hours` — expects cancellation to route next-business-day | BR-TV-014 names only "sales, plan changes, and appointment booking" as after-hours-closed | Cancellation is not in the brief's closed set. Either BR-TV-014 is incomplete or the eval is wrong. **Recommendation:** add cancellation and port-out to the closed set (they are specialist-queue work). |
| **C4** | `sim__phone_locked_puk_code` — agent speaks the PUK code aloud | BR-TV-009 lists account #, cirn, card #, PIN, OTP as redacted; PUK is absent | A PUK is a security credential. Speaking it is necessary for the flow to work, so it needs an **explicit carve-out** in BR-TV-009 rather than silence. |
| **C5** | `sim__password_reset_mobile_fallback` — caller *elects* PIN ("don't have my phone") | M2: PIN flow is the fallback "when no reachable callback number" | The brief's trigger is system-determined; the eval's is caller-elected. **Recommendation:** widen M2 to allow caller-elected PIN fallback. |
| **C6** | `sim__disable_mfa_auth_failure` — 3 failed step-up attempts → escalate | `auth_failure_handoff` is defined for the OTP/PIN ladder only | Confirm step-up failure reuses `auth_failure_handoff` rather than needing a new code. |
| **C7** | `sim__restore_service_refuse_payment` — "the session ends **or** escalates" | No reason code defined for this terminal state | Ambiguous terminal state cannot be asserted. Needs a code — this plan proposes `restore_blocked_balance_owed`. |

### 5.2 Structural weaknesses

| # | Problem | Consequence |
|---|---|---|
| **S1** | **11 tautological sims** (`sim__pay_my_bill`, `sim__dispute_charge_my_bill`, `sim__set_up_autopay`, `sim__request_refund_credit`, `sim__troubleshoot_*`, `sim__resolve_sim_*`, `sim__upgrade_my_plan_*`, `sim__file_warranty_claim_*`, `sim__transfer_my_phone_number_*`, `sim__book_reschedule_cancel_*`, `sim__check_status_*`). Judge criteria is "The agent accomplishes: *X*"; the assertion is "The agent addresses the user's goal: *X*". | These cannot meaningfully fail. At 16% of the suite they inflate the pass rate by enough to clear the ≥90% gate on their own. They also duplicate scenarios already covered specifically. |
| **S2** | **Three truncated definitions.** `sim__cancel_service_after_hours` judge criteria ends mid-sentence ("…option or"); `sim__mfa_vague_request` ends at "The user is guided"; `sim__appointment_availability_sms_callback` asserts "must successfully register request". | Unjudgeable as written. |
| **S3** | **No `max_turns` on any sim.** The brief's §19 schema has the field; the public file drops it. | The ≤4 min AHT target in the definition of done is unmeasurable from the suite. |
| **S4** | **No `primary_module` declared.** | Per-module pass rates can't be computed, so you cannot tell whether a regression is in billing or in routing. |
| **S5** | **Every sim is a single `Turn 1` with multi-turn behavior in a prose `user guide`.** | The simulated caller improvises the branch structure, so runs diverge between executions. Poor reproducibility. |
| **S6** | **No fixtures / seed state.** Sims say "when told the technician is en-route" or "when told the device is out of warranty" without specifying how that backend state arises. | Non-deterministic. The brief mandates `mock_mode` on every tool precisely to avoid this (§17), and the suite doesn't use it. |
| **S7** | **Ordering requirements are judged from the transcript.** "The agent must check regional outage first," "must call recent-bills lookup before referencing any charge" — an LLM judge reading prose. | Weak and flaky. These are **tool-call-trace** assertions and should be checked against the call log. |
| **S8** | **Mixed assertion voice** — "The user is informed…" vs. "The agent must…". | Caller-perspective phrasing invites the judge to credit outcomes the agent didn't cause. |
| **S9** | **Few negative assertions.** Most sims assert only what must happen. | The brief's hard rules are nearly all prohibitions (never echo a PIN, never fabricate, never exceed 3 plans, never bypass M1). Untested prohibitions are unenforced. |

---

## 6. The improved suite: what changes

| Change | Rationale |
|---|---|
| **Drop the 11 tautological sims**, replace with targeted scenarios for the same intents | S1 — restores the meaning of the pass rate |
| **Add `tool_trace` assertions** checked against the tool-call log, not the transcript | S7 — makes "lookup before you speak" deterministic |
| **Add named fixtures** (`evals/fixtures.yaml`) seeding `mock_mode` state per scenario | S6 — reproducible runs |
| **Add `max_turns` + `primary_module` + `brs` to every scenario** | S3, S4 — enables AHT measurement, per-module pass rates, and requirement traceability |
| **Split assertions into `must` / `must_not` / `tool_trace` / `verbatim` / `reason_code`** | S8, S9 — each class is checked by the mechanism suited to it; prohibitions get first-class status |
| **Turn-by-turn scripting** where the branch matters, prose guide only where improvisation is the point | S5 |
| **Fix the 3 truncated definitions** | S2 |
| **Rebalance to call volume** — M4 and M3 get proportional weight | §4 |
| **Fill all 7 requirement gaps and all 3 uncovered CUJs** | §3 |
| **Assert all 12 verbatim keys and all 11 reason codes** at least once | §3 |
| **Add a volume-weighted pass rate** alongside the flat one | A failure in a 30%-volume journey should not cost the same as one in a 5% journey |

### ⚠ These files are specifications, not yet runner input

A `cxas-agent-foundry` / `cxas-sim-eval` toolchain is installed in this project (`.agents/skills/`) with its own runner (`scripts/run-evals.py`, `scripts/scrapi-sim-runner.py`) and a different schema. **Schema v2 below will not load into that runner as written.** The mapping needed:

| Schema v2 (this plan) | Toolchain schema | Note |
|---|---|---|
| directory `evals/sims/` | `evals/simulations/` | |
| top-level `scenarios:` | `evals:` | |
| `id:` | `name:` | |
| `priority: P0` | `tags: [P0, ...]` | **Required** — the runner filters by `--priority`. Add module and CUJ as further tags. |
| `turns: [{user, guide}]` | `steps: [{goal, success_criteria, response_guide, max_turns}]` | v2 splits per-turn; the runner takes one prose guide per step |
| `must:` + `must_not:` | `expectations:` | Flattened. Phrase prohibitions as "The agent must NOT …" |
| `fixtures:` | `session_parameters:` | Needs the fixture library resolved to flat session params |
| `tool_trace:` | *no equivalent* | Ordering assertions must become `expectations` prose, or move to `evals/callback_tests/` to stay deterministic |
| `verbatim:` / `reason_code:` | `evals/goldens/` | These belong in the goldens layer the toolchain already has |
| `brs:` | tags | Keep as tags to preserve traceability |

Two things do not survive the translation and need a decision: **`tool_trace` ordering assertions** (the main correctness gain of this rewrite — keep them deterministic via callback tests rather than letting them decay into LLM-judged prose) and **`fixtures`** (the toolchain's `session_parameters` is flat, so the fixture library needs flattening or a pre-processing step). Also note the toolchain's own warning that its tool-test files must use the top-level key `tests:` — the wrong key silently loads zero tests.

### Scenario ID convention

`sim__<module>__<journey>__<variant>` — e.g. `sim__m4__tv_no_signal__streaming_resolved`. Sortable, greppable, and the module prefix makes per-module reporting trivial.

### Priority tiers

| Tier | Meaning | Gate |
|---|---|---|
| **P0** | Safety, compliance, PII, auth integrity, or a journey ≥15% of volume | 100% must pass. Any P0 failure blocks the release. |
| **P1** | Correctness on a named requirement or a journey <15% of volume | ≥90% |
| **P2** | Robustness, edge cases, long-tail variants | ≥75% |

---

## 7. Suite composition

**137 scenarios.** All 59 non-generic public sims kept (normalized to schema v2 and hardened), the 11 tautological ones dropped, 78 added.

| Cluster | P0 | P1 | P2 | Total | File |
|---|---|---|---|---|---|
| Global lifecycle & compliance (M1) | 9 | 4 | 2 | 15 | 01 |
| Safety & malicious input | 5 | 1 | 1 | 7 | 01 |
| Auth & identity (M2) | 7 | 2 | 1 | 10 | 01 |
| Error handling & tool failure | 5 | 3 | 1 | 9 | 01 |
| **M3 Billing & payment** | **8** | **5** | **2** | **15** | 02 |
| **M4 Tech support & virtual repair** | **7** | **5** | **2** | **14** | 02 |
| M5 Sales & equipment | 4 | 7 | 3 | 14 | 03 |
| M6 Appointments & tickets | 3 | 6 | 2 | 11 | 03 |
| M7 Account management | 6 | 9 | 3 | 18 | 03 |
| M8 Secondary language | 3 | 2 | 0 | 5 | 04 |
| Cancellation & port-out | 3 | 3 | 1 | 7 | 04 |
| SIM & device | 1 | 4 | 1 | 6 | 04 |
| Cross-CUJ topic switches | 2 | 3 | 1 | 6 | 04 |
| **Total** | **63** | **54** | **20** | **137** | |

Every kept scenario carries a `derived_from` field naming its public-suite original, so the mapping is auditable in both directions. Scenarios that replace a dropped generic carry `replaces`. All 59 non-generic public sims are accounted for — a CI check asserts the set of `derived_from` values equals the public suite minus the 11 drops, so a future edit cannot silently lose coverage.

### Rebalanced against volume

| Module | Volume | Public share | New share |
|---|---|---|---|
| M4 Tech support (incl. SIM/device) | 30% | ~8% | **15%** |
| M3 Billing | 25% | ~2% | **11%** |
| M5 Sales | 15% | ~20% | 15% |
| M7 Account management | 15% | ~34% | 13% |
| M6 Appointments | 10% | ~17% | 8% |
| Service changes / cancellation | 5% | ~10% | 5% |
| M8 Secondary language | subset | ~3% | 4% |
| Cross-cutting (M1 / M2 / safety / errors) | — | ~10% | 30% |

Cross-cutting takes the largest single share by design: those behaviors reproduce on *every* call, so they carry the most aggregate risk despite owning no journey. They are excluded from the volume-weighted metric (`weight: 0.0`) and gated instead by P0 = 100%.

### Highlights of what's new

**M4 — the 30% slice that had nothing (14 scenarios).** CUJ-3 canonical in both TV sub-types; the sub-type-assumption guard (caller says only "my TV is broken" — the agent must ask, never assume); active-outage path with `outage_active` verbatim, SMS-callback offer, and session end; outage-declined variant; internet-down resolved and unresolved-to-technician; the >2-step SMS rule *and* its ≤2-step verbal negative; home-phone and smart-home LOB coverage; ticket creation on unresolved; outage escalation honored after hours.

**M3 — the 25% slice with one eval (15 scenarios).** CUJ-2 canonical with all three brief assertions; the not-auto-eligible branch that *does* open a dispute case; charge identification by amount and the ambiguous-charge disambiguation; refund above threshold → `refund_threshold_exceeded`; autopay with `payment_method_preamble` verbatim *and* the negative that the agent never invites a spoken card number; DTMF-tokenized card capture; payment arrangements; deposit question; `INSUFFICIENT_FUNDS` business-error handling; prepaid-path guard; last-4 echo on `billing_account`; `transfer_to_specialist` verbatim.

**The 7 requirement gaps.** Recording notice on greeting, on request, and after interruption (3 scenarios); restricted-caller deflection; regional-alert banner; malicious utterance, self-harm, threat, and prompt-injection resistance (4); `SYSTEM_DOWN` immediate end with no retry, `AUTH_SERVICE_UNAVAILABLE`, validation-error accumulation to `too_many_errors` (3); no-fabrication-on-tool-failure; session-context-carried-on-handoff.

**CUJ-7 and M8 (5 scenarios).** The tech fallback that escalates with `secondary_language_live_agent`; the self-served variant; the routing guard proving secondary-language *billing* stays in M3; and non-degradation across an escalation boundary.

**Auth-integrity negatives.** *Identified* is insufficient for an account read; the model cannot self-assert `auth_status = Pass`; OTP is never echoed; the text-encoded DTMF form (`"user pressed 1234"`) is captured.

---

## 8. Revised coverage gates

Replacing the brief's single "≥60% baseline / ≥90% pre-production" with per-layer gates. The brief's global definition of done is unchanged.

| Layer | Gate — baseline | Gate — production |
|---|---|---|
| L1 Tool contract | 100% of tools have a passing real + mock branch and a well-formed error envelope | same (non-negotiable) |
| L2 Per-turn preprocessing | All 4 behaviors, happy + boundary | same |
| L3 Deterministic goldens | 100% | 100% (zero tolerance) |
| L4 Sims — **P0** (63 scenarios) | 100% | **100%** |
| L4 Sims — P1 | ≥70% | ≥90% |
| L4 Sims — P2 | ≥50% | ≥75% |
| L4 Sims — **volume-weighted** | ≥60% | **≥90%** |
| L4 Sims — flat (brief's metric) | ≥60% | ≥90% |
| L5 Audio-mode audit | All P0 scenarios | same |
| L6 Telephony loop | Once per release | same |
| L7 Compliance audit | 50 calls/language, quarterly | same |

**Volume-weighted pass rate.** Each scenario carries the `volume_weight` of its journey. A CUJ-3 failure costs 6× a CUJ-6 failure, which is the correct ratio of real customer impact. Report both numbers — the flat rate for the brief's gate, the weighted rate for deciding what to fix next.

**P0 at 100%, not 90%.** The brief's flat 90% permits ~11 failures anywhere, including in fraud escalation or PII redaction. A suite that can pass while leaking PII is not a gate. Every P0 scenario asserts a safety, compliance, PII, or auth-integrity rule, or sits in a ≥15%-volume journey.

---

## 9. Traceability

Every requirement now has at least one scenario, and every scenario names its requirements. Enforce this with a CI check:

```
for each BR-TV-### in 001..020:
    assert exists scenario or golden or layer-test with BR in its `brs` list
for each verbatim key in Section 7 of the brief:
    assert exists golden asserting exact-substring equality on that key
for each reason code in the 11-code inventory:
    assert exists scenario with that `reason_code`
```

A requirement with no test is a spec change nobody noticed. The check fails the build rather than the audit.

---

## 10. The six missing layers

The public file supplies only L4. These are specified here because the brief requires them and nothing in the repo covers them.

### L1 — Tool-contract tests (100% of tools)

Per §17 of the brief, every one of the ~250 tools must satisfy four requirements. Machine-readable matrix: [evals/tool_contract_matrix.yaml](evals/tool_contract_matrix.yaml).

Each tool gets five assertions:

1. **Real branch** returns a schema-valid payload against its declared output contract.
2. **Mock branch** — with `mock_mode == "True"`, returns a canned success payload and makes **zero** outbound backend calls (assert via network/RPC spy, not by inspecting the payload).
3. **Error envelope** — every failure path returns exactly `{ "error": "<CODE>", "message": "<human>" }` with `<CODE>` drawn from the documented System / Business / Validation sets. Any other error shape fails.
4. **Idempotency** — for mutating tools only (`place_new_order`, `commit_appointment_*`, `process_payment_*`, `execute_suspend_restore`, `create_dispute_ticket`): the same input applied twice produces one effect and two identical responses.
5. **PII marking** — responses containing full PII carry the redaction marker that upstream logging reads.

**`auth_status` and `identification_status` carry an extra assertion:** no code path outside the verify tools can write them. The brief flags both as "NEVER mock or override in evals" because doing so short-circuits the auth flow — so this is a static check on the codebase (grep for assignment sites) plus a runtime guard, not a behavioral test.

### L2 — Per-turn preprocessing tests

Four behaviors from §6 of the brief, each with a happy path and a boundary case. These are unit-level — drive the preprocessing pipeline directly, no model in the loop.

| Behavior | Happy | Boundary |
|---|---|---|
| DTMF capture | Native DTMF part → `dtmf_digits` | Text-encoded `"user pressed 1234"` → same value; empty/partial input; digits arriving mid-utterance |
| No-input accounting | Miss 1 and 2 reprompt | Miss 3 ends with `no_input_escalation`; counter **resets** on landing in a new module (this reset is the part implementations get wrong) |
| Tool-error classification | Each of the three classes routes correctly | Unknown error code — must not be silently treated as business; `SYSTEM_DOWN` must produce **zero** retry attempts |
| Module pre-checks | Outage advisory prepends | Pre-checks run **before** the model composes, verified by hook-ordering assertion |

**Plus an ordering test.** The brief warns that reordering these four has "produced flaky evals in past implementations." Assert the pipeline invokes them in order 1→2→3→4 via an instrumented spy. This is a single cheap test that prevents a whole class of intermittent failure.

### L3 — Deterministic goldens

No model judgment — exact string and state assertions. Full set: [evals/deterministic_goldens.yaml](evals/deterministic_goldens.yaml).

| Group | Count | Assertion |
|---|---|---|
| Verbatim strings | 12 keys × 2 languages = 24 | Exact substring equality in the emitted turn. Paraphrase, contraction, expansion, or reordering fails. |
| PII redaction | 6 | `billing_account`, `cirn`, card digits → last-4 only in transcript **and** in logs; PIN and OTP appear in neither. |
| Reason codes | 11 | Session terminates with the exact code for each triggering condition. |
| Context handoff | 1 per escalation path (11) | The handover payload contains the session variables; assert against the `execute_live_agent_handover` call arguments. |
| Language pinning | 2 | A secondary-language call produces zero primary-language turns, including in escalation copy. |

Two verbatim keys are **blocked on Legal** (`payment_method_preamble`, `contract_cancellation_fee_disclosure`). Until the text arrives, their goldens assert *structural* compliance — that a constant is referenced from the copy library and emitted unmodified — and are marked `blocked_on: legal` so they fail loudly rather than passing vacuously.

### L5 — Audio-mode audit (all P0 scenarios per release candidate)

Run the P0 set through the real audio stack. Sim-mode passes do not transfer: TTS reads `$12.50` as "twelve dollars and fifty cents" or "twelve point five zero" depending on the voice, and the second one fails a caller's comprehension even though the transcript is correct.

Assert per scenario: verbatim strings survive TTS without drift; currency, dates, and time windows pronounce naturally; last-4 digit groups are intelligible; DTMF captures end-to-end through the audio path; barge-in during the recording notice behaves per the C2 resolution.

### L6 — Telephony-loop test (once per release)

Real dial-in through the production number. Verifies what no simulator can: barge-in latency at the wire, DTMF tone detection across carriers, audio quality, and that BR-TV-018 actually produces a `.wav` in the session-audio bucket.

Minimum set: one dial-in per `tfn` (per-brand routing), one DTMF-heavy flow (PIN entry), one barge-in test, one call confirmed present in the audio bucket afterward.

### L7 — Compliance audit (quarterly + on any verbatim change)

Manual review, 50 calls per language. Two findings classes, both zero-tolerance: verbatim drift on any audited string, and any PII disclosure beyond last-4.

Trigger it on **every change to a verbatim string** — not only quarterly. A one-word edit to the recording notice is a compliance event, and the brief says the notice is audited against recorded audio.

---

## 11. Recommended sequencing

| Phase | Work | Exit |
|---|---|---|
| **0** | Resolve C1–C7 with the spec owner. Obtain the two Legal strings. | Ambiguities closed; L3 unblocked |
| **1** | L1 tool contracts + L2 preprocessing, on the tool surface as it lands per module | Every wired tool has a mock branch that works; pipeline order asserted |
| **2** | L3 goldens for the 10 unblocked verbatim keys, PII, reason codes | Zero-tolerance layer green |
| **3** | L4 P0 set (63 scenarios), M4 and M3 first — largest volume, weakest current coverage | P0 at 100%; volume-weighted ≥60% |
| **4** | L4 P1 + P2; cross-CUJ switches | Flat ≥90%, weighted ≥90% |
| **5** | L5 audio + L6 telephony on the P0 set | Release-candidate gate |
| **6** | L7 compliance audit | Production |

Phase 0 is genuinely blocking for the compliance layer: two verbatim strings do not exist yet, and C1/C2 change what a correct agent does in a P0 scenario. Everything else can proceed in parallel with the build.

---

*Cross-checked against the 70-eval public suite and the 25-page development brief. Divergences are recorded in §5 and mirrored into the PRD's open-questions register.*
