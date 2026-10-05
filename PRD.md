# Telco Voice Central — Agent Development Brief

Functional specification and capability inventory for the engineers who will build the voice agent.

| Document field | Value |
|---|---|
| Version | Consolidated draft 1.0 |
| Date | 2026-09-30 |
| Baseline | `Day 1 - Telco Voice Central — Agent Development Brief.pdf`, 25 pages |
| Structure | The original 21 sections, eight modules, seven example journeys, and BR-TV-001 through BR-TV-020 are retained. |
| Additional inputs | Business lead's answers supplied with this request; `PRD-ADDENDUM-Telco-Voice-Central-2026-09-29.md`; the earlier gap review. |
| Status | Implementation specification with explicitly proposed assumptions and client-owned release dependencies. No client approval, backend availability, or Legal approval is implied by this draft. |

Build a production voice agent that answers a consumer telco's main customer-service line and resolves the six most common contact reasons: billing questions, technical support, sales and equipment, appointment management, account management, and service changes. Resolution may be self-contained or a clean escalation to a live representative with the necessary session context.

**How to read this document.** This specifies behavior, data, back-office capabilities, and acceptance criteria. Engineers choose the architecture. A module is a functional capability area, not a required agent, class, or process. Internal composition remains an engineering choice; authentication, disclosures, transaction ordering, and handoff outcomes are observable requirements.

**How additions are identified.** Existing scope is retained and clarified in place. **Lead guidance** identifies what the business lead actually answered. **Assumption A-xx** identifies a proposed decision where the answers were incomplete or the original brief conflicted with itself. The register in Section 21 identifies the owner and what must be supplied or approved. These assumptions are the deterministic behavior for development and evaluation; the affected production capability remains disabled until its listed dependencies are accepted. A tested handoff fallback does not count as completing a self-service feature.

**Precedence.** Explicit business-lead guidance is incorporated in this draft. It does not constitute approval of unanswered client policies. Where a rule here changes the original brief or earlier addendum, the local clarification and assumption label state the operative rule. The earlier addendum and evaluation plan are supporting evidence, not independent instructions that can override this file. In particular, area-code-only language selection, replay-based handling of normal notice interruptions, primary-language fallback on a supported secondary-language call, and automatic test exclusions are not carried forward as approved requirements.

**Source references.** The platform language and voice-control statements were checked on 2026-09-30 against [CX Agent Studio languages](https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/reference/language), [voice/audio callback patterns](https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/best-practices), and [system tools](https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/tool/system). These references describe platform capabilities, not the client's language scope or security policy.

## Section 1 — Global Behavioral Requirements

These behaviors apply across all turns and modules.

- **Recording notice — BR-TV-001.** Deliver the approved `recording_notice` at call opening and repeat it verbatim if the caller asks about recording. The applicable regional and language variant comes from approved configuration. Delivery and playback completion are separate audit events.
- **Language locking — BR-TV-004.** Detect the first meaningful caller utterance using platform language detection and respond in the selected, supported language. Retain that choice until the caller explicitly requests a different language. Section 3 defines the initial audio before caller input; Section 15 defines unsupported languages and language-specific capability gaps.
- **PII redaction — BR-TV-009.** Speak account numbers, customer reference numbers, and approved masked card references only as their last four characters. Never echo PINs, OTPs, reset links, or other credentials. Section 5 defines the treatment of state, logs, transcripts, and handoffs.
- **Malicious utterances and safety — BR-TV-016.** Evaluate every caller turn. Malicious requests and credible threats, distress, self-harm signals, ordinary anger, quoted speech, and fraud reports are distinct categories with the outcomes in Section 20. A fraud report or an angry tone alone must not cause disconnection.
- **Retry strikes — BR-TV-006.** Three consecutive no-input events in the same module or three unresolved clarification attempts in one disambiguation episode cause a live handoff. Authentication has its own call-wide attempt limit. Counter resets are defined in Section 16.
- **After hours — BR-TV-014.** Fraud and outage handoff destinations must support 24/7 routing. Sales, plan-change, and appointment specialist availability comes from the platform. Successful automated service may continue after hours; the closed-queue outcome is defined in Section 8.
- **No invented data — BR-TV-017.** Statements about an account, eligibility, availability, an action's completion, amounts, dates, and follow-up commitments require a successful authoritative result. Caller statements are search inputs, not backend facts.
- **Business accounts — BR-TV-012.** Once the resolved account is identified as a business account, stop self-service and hand off using the business path, unless a higher-priority safety or fraud event applies.

**Lead guidance: language.** Author agent instructions in English. Platform language detection can support multilingual interaction; available languages differ between voice and chat and must be verified for the selected deployment. The client chooses the languages in scope. Automatic detection does not authorize automatic translation of locked compliance text.

**Lead guidance: mandatory notices.** Use a deterministic callback to disable barge-in for legal-notice playback. Repeated replay is not the normal strategy for handling caller interruption. Scope this protection to the necessary disclosure and restore ordinary interruption afterward. In the CXAS implementation, this is enforced via `root_agent`'s `beforeModelCallbacks` (`handle_legal_notice.py`), managing `notice_playback_status` and suppressing barge-in during disclosure playback.

## Section 2 — Capability Modules Overview

| ID | Module | Purpose | CUJs owned |
|---|---|---|---|
| M1 | Session Lifecycle & Routing | Greeting, identity capture, language, intent, routing, handoff, and close | Entry and exit for all CUJs |
| M2 | Authentication & Identity | OTP/PIN verification, account-bound authentication, failure escalation | Precondition for authenticated CUJs |
| M3 | Billing & Payment | Bills, adjustments, disputes, payments, autopay, refunds, arrangements, deposits | CUJ-2 and payment portion of CUJ-6 |
| M4 | Technical Support & Virtual Repair | Outage lookup, subtype clarification, repair, troubleshooting, tickets | CUJ-3 |
| M5 | Sales & Equipment | Coverage, catalog, orders, warranty, returns, SIM and transfer-in requests | CUJ-5 |
| M6 | Appointment & Ticket Management | Availability, booking, rescheduling, cancellation, visit and ticket status | CUJ-4 |
| M7 | Account Management | Password reset, MFA, fraud, profile, registration, suspension/restoration, cancellation/port-out | CUJ-1 and account portion of CUJ-6 |
| M8 | Secondary Language Fallback | Supported-language technical help when M4 lacks approved localized coverage | CUJ-7 |

Modules may be combined or split internally. Cross-module routing through M1 is a logical routing requirement; it does not require separate deployed agents.

| Approximate call-volume distribution | Share |
|---|---:|
| Technical support | 30% |
| Billing | 25% |
| Sales | 15% |
| Account management | 15% |
| Appointments | 10% |
| Service changes, including restoration | 5% |

CUJ-7 is a subset of technical support, not additional volume. The percentages guide prioritization; they are not a substitute for production measurement.

**Launch scope clarification — Assumption A-10.** Every listed intent must be recognized. Recognition, human referral, and completion by the agent are separate capabilities. Section 17 records the proposed launch treatment and prerequisites. No tool is assumed available merely because it appears in this document. Missing capability contracts result in a controlled handoff, and any resulting reduction from promised launch scope requires product approval.

## Section 3 — Call Lifecycle Requirements

The opening sequence preserves the restricted-caller and alert checks while defining what can happen before the caller speaks.

1. Load the dialed number's approved brand, default language, legal-notice variant, supported-language set, and handoff configuration.
2. Check the incoming caller against the restricted-caller capability before any greeting. Do not use caller ID as proof of identity.
3. Determine whether a trusted pre-call service-region attribute exists. If it does, check the public regional advisory. If it does not, omit a region-specific advisory and resolve the service region later; never announce that there is no outage based on missing region data.
4. Emit `recording_notice` with barge-in disabled, followed by any applicable approved advisory and `greeting_main`. Only the disclosure needs protected playback unless another approved mandatory disclosure follows.
5. For a restricted caller, emit the opening notice and approved deflection instead of the greeting, then disconnect. This is an added assumption about notice coverage, not an approved regional legal conclusion.
6. Capture the first meaningful caller utterance, establish language under the rules below, and capture any intent already supplied. Do not ask the caller to restate a clear intent.
7. Resolve identity and authenticate only when required for the chosen action. Fraud and explicit human requests do not require identity capture first.

**Opening language — Assumption A-01.** Before caller speech, use a trusted channel-provided language preference if it belongs to the client's supported set; otherwise use the dialed number's configured default language. Do not infer a definitive language from an area code. English is the authoring language, not an automatic production default. A development-only English fixture may be used with synthetic data.

After the first clear caller utterance, use the detected supported language and lock it. If it differs from the initial language, replay the approved recording notice once in the corrected language before account work; give a short localized transition rather than repeating the full greeting. A caller who already states an intent need not repeat it. This startup correction is an explicit exception to the original literal prohibition on any mixed-language transcript. After the lock, a switch requires the caller's explicit request. If detection is uncertain, ask one language-selection question using approved configuration; do not guess from a short word, a name, or background speech.

**Pre-call region — Assumption A-02.** The authoritative pre-call region is a trusted service-region attribute supplied by the client's telephony/routing integration. Caller area code and current physical location are not substitutes for the account's service region. A missing pre-call region is a normal state. After identity/authentication, the selected service address from the account backend supplies `region` for account-specific outage and coverage work. Conflicting regions are resolved in favor of that selected service. Applicable legal notices must be available through channel configuration even when service region is unknown.

**Notice playback — Lead guidance; failure behavior under A-06.** Generate the protected response from a callback (`agents/root_agent/callbacks/handle_legal_notice.py`) using the supported voice control with barge-in disabled on disclosure turns, and test it through the actual telephone integration. Do not assume speech during disabled barge-in is captured, queued, or understood. Process only caller input the platform actually delivers; if necessary ask for the request after the disclosure. Verify playback completion via `notice_playback_status` before a dependent action. A disconnect during playback is recorded as `caller_disconnected` with an incomplete notice, not as successful disclosure. An unexpected playback failure stops dependent work and invokes the configured platform fallback; it must not produce an unlimited replay loop. An explicit later request about recording still causes a full replay.

Blocklist, opening notice, and configured fallback availability are production prerequisites. A missing blocklist integration must not silently behave as “not blocked”; route the call through the client's tested legacy intake. The public regional alert can be omitted when region is unavailable, but a known-region alert service failure must be recorded and must not be reported as a clear result. See A-02 and Section 17.

## Section 4 — Intent Coverage & Routing Table

The table retains all original routing rows. Authentication means verification for the selected account and authorization for the specific service/action, not simply knowledge of an account number.

| Representative utterance | Route | Authentication and operative clarification |
|---|---|---|
| “my bill is wrong” / “dispute a charge” | M3 | Authenticated before bill read or adjustment |
| “I want to pay my bill” | M3 | Authenticated; secure payment capture and approved disclosure |
| “set up autopay” | M3 | Authenticated; approved preamble before payment-method access |
| “refund” / “credit back” | M3 | Authenticated; backend eligibility and transaction-type decision |
| “internet is down” / “no service” | M4 | Authenticated for account-specific technical work; distinguish from public pre-call alert |
| “TV says no signal” | M4 | Authenticated; TV subtype required before TV diagnostics |
| “SIM not working” / “phone locked” | M4 | Authenticated; clarify diagnosis versus SIM replacement, PUK, or carrier unlock |
| “I want to add TV” / “new plan” / “upgrade” | M5 | Public coverage/catalog allowed without authentication; account-specific quotes and all billed changes require authentication |
| “my phone is defective” / “warranty” | M5 | Authenticated; warranty decision comes from backend |
| “transfer my number in” | M5 | Authenticated for existing account; proposed launch treatment is human handoff |
| “book a technician” / “reschedule my appointment” | M6 | Authenticated |
| “where is my technician” / “ticket status” | M6 | Authenticated |
| “forgot my password” / “reset login” | M7 | **A-03:** Authenticated before dispatch; supersedes the original “Identified only” exception |
| “disable two-factor” / “enable MFA” | M7 | Authenticated plus approved step-up; human handoff while the step-up contract is unavailable |
| “someone used my account” / “fraud” | M7 | Empathy and immediate fraud handoff; no new authentication or self-service |
| “restore my suspended service” | M7 | Authenticated; non-payment travels M7 → M1 → M3 → M1 → M7 |
| “cancel my service” / “port out my number” | M7 | Authenticated; proposed launch treatment is human handoff; mandatory disclosure must precede any future automated cancellation |
| Supported secondary-language technical query beyond M4 coverage | M8 via M1 | Same authentication as M4; retain language |
| “I want to talk to a person” | Human handoff | No authentication prerequisite; mandatory opening playback completes first |

**Disambiguation requirements.** Ask one targeted question at a time, not a menu recital. “Three attempts on the same turn” in the original means three unresolved attempts over one clarification episode, with a caller response between questions. A repetition request is not a no-match. Keep a resolved intent during identity capture. If the caller gives two intents, acknowledge both, handle the higher-priority one first, and check the remaining intent before closing. A terminal safety or fraud event ends self-service rather than returning to the second intent.

**Topic switch — A-09.** Reclassify and route through M1 without greeting or authenticating again when the same account's verification remains valid. Switching the target account invalidates authentication. Switching topics does not cancel a submitted transaction; the operation rules in Section 16 determine whether it can be stopped or reversed.

## Section 5 — Session Data Model

Preserve the original variable names. The brief describes “approximately 60” variables but enumerates 38 individual names when the five temporaries are counted separately. The enumerated names below are the compatibility baseline. Additional names are explicitly proposed extensions, not claims about existing tool fields.

### Identity and authentication

| Variable | Source | Logical type | Rules |
|---|---|---|---|
| `clid` | Telephony | string | Incoming caller ID; may be withheld or malformed. Normalize valid numbers; never authenticate from it. |
| `tfn` | Telephony | string | Dialed service number; selects brand/channel configuration. |
| `cirn` | Identity backend after capture | string, PII | Customer reference; spoken/logged last four only. |
| `billing_account` | Identity backend after capture | string, PII | Selected billing account; spoken/logged last four only. |
| `customer_type` | Backend | `New` or `Existing` | Never invented from conversational appearance. |
| `user_id` | Backend | string | Internal customer identity, not a spoken identifier. |
| `auth_status` | Verification result handler | `Pass` / `Fail`; unset before evaluation | No model writes or seeded passes in end-to-end evaluation. Bound to account, session, and authorized actor. |
| `identification_status` | Profile result handler | `Pass` / `Fail`; unset before lookup | Identification permits only limited identity/routing work; not account-data disclosure. |
| `business_flag` | Backend | bool-str | Parse explicit `"True"`/`"False"`; unknown is not false. |

### Routing and conversation

| Variable | Source | Logical type | Rules |
|---|---|---|---|
| `route` | Classifier/routing | enum string | Validated intent/module code; model proposals cannot lower auth requirements. |
| `lob` | Caller selection and backend | `mobility`, `internet`, `tv`, `homephone`, `smarthome` | Must refer to the selected service. |
| `tv_sub_type` | Caller/backend | `streaming`, `satellite`, `streaming_only`, or null | Unknown until clarified; irrelevant outside TV. |
| `region` | Trusted routing/service backend | string or unset | Provenance required; Section 3 resolves startup versus account region. |
| `language` | Language policy | `primary` / `secondary` | Legacy role for configured launch locales; actual locale stored separately. |
| `utterance` | Caller capture | string | Sanitized current intent text, not a persistent credential-bearing transcript. |
| `dtmf_digits` | Secure preprocessing | secret string | Turn-scoped; never logged, put in model prompts, or handed off; cleared after authorized consumption. Payment capture bypasses this variable. |

### Counters and flags

| Variable | Source | Logical type | Rules |
|---|---|---|---|
| `local_noinput_counter` | Preprocessing | integer | Consecutive misses in current module. |
| `global_err_count` | Error handler | integer | Validation errors across the entire call; no module reset. |
| `no_match_confirmation_count` | Preprocessing | integer | Current unresolved disambiguation episode. |
| `misc_counter` | Flow handler | integer | Must have a named purpose; never a substitute for auth/security counters. |
| `mock_mode` | Trusted evaluation deployment | string | Exact `"True"` selects mocks only in an authorized evaluation environment. Caller/production values cannot enable it. |

### Payment, repair, messaging, and miscellaneous

| Variable | Source | Logical type | Rules |
|---|---|---|---|
| `last_pmt_amt` | Backend | float-str compatibility field | Parse as exact decimal/minor units, with currency; never binary-float authorization math. |
| `amount` | Caller capture | float-str compatibility field | Search/request input only; execution amount comes from authoritative decision. |
| `ban_type` | Backend | string | Billing account type. |
| `is_prepaid` | Backend | bool-str | Explicitly parsed; unknown blocks a prepaid/postpaid-specific action. |
| `loyalty_limit` | Backend | integer | Loyalty ceiling only; not a universal refund threshold. |
| `vr_task_count` | Repair capability | integer | Repair progress counter. |
| `ticket_state` | Backend | `open`, `in-progress`, `closed` | Describes a real ticket, not intent to create one. |
| `item_list` | Caller/backend | string | Equipment selection validated against the account. |
| `intent_type` | Classification | string | Sub-intent; warranty eligibility cannot be inferred from it. |
| `api_resp` | Response adapter | string | **A-12:** allowlisted, redacted summary only; never raw debug payload. |
| `sms_type` | Messaging policy | `Public` / `Private` | Selects approved template and permitted destination. |
| `sms_content` | Approved template plus verified fields | string | Sanitized display/audit representation; secret-bearing link payload stays in the messaging service. |
| `day_val`, `date_val`, `month_val`, `end_time`, `flag_val` | Flow handler | strings | Retained compatibility temporaries; validate and clear on flow exit. They cannot authorize transactions. |

If the framework serializes state as strings, adapters must enforce the logical types and reject unknown/invalid values. Do not treat the nonempty string `"False"` as true. Only validated tool result handlers may write protected facts, amounts, operation outcomes, identity, or auth state.

### Added state needed to remove ambiguity — assumptions A-01 through A-14

| Proposed field/group | Required meaning |
|---|---|
| `session_id`, `current_module`, `pending_intents` | Call identity, observable routing history, unfinished requests |
| `language_locale`, `language_locked`, `detected_language`, `region_source` | Concrete locale/provenance; unsupported detection is not stored as a supported `language` role |
| `authenticated_account_id`, `authorized_service_ids`, `auth_method`, `auth_time`, `auth_attempt_count` | Scope and history of verification; raw factors are excluded |
| `notice_key`, `notice_version`, `notice_locale`, `notice_playback_status` | `not_started`, `playing`, `completed`, or `incomplete`; callback-generated text alone is not completion |
| `operation_id`, `idempotency_key`, `operation_type`, `operation_status`, `operation_account_id` | Durable operation correlation and transaction state from Section 16; not model-created success claims |
| `eligibility_decision`, `restoration_decision` | Backend-issued authorization with account/service binding, policy/version, freshness, and permitted result fields |
| `handover_status`, `terminal_outcome`, `terminal_trigger`, `reason_code`, `safety_category` | Actual transport outcome, business cause, compatible reason code, and safety distinction |
| `sms_status`, `subscription_id`, `callback_status` | Backend evidence of message or future-notification registration; absent means not confirmed |

### Data exposure and handoff — Assumption A-12

Build handoff context in code from this allowlist: session identifier; brand/dialed number; selected locale; resolved account and service identifiers in the protected handoff argument only; identification provenance; actual auth method/time/account scope; whether the receiving desk must reverify; sanitized intent and summary; relevant service/region; approved transaction, ticket, appointment, and subscription references; operation status including unknown outcomes; nonsecret backend-confirmed amounts/currency needed for the case; terminal trigger, reason, and safety category.

Never include PINs, OTPs, attempted credentials, `dtmf_digits`, reset links, full card details, payment tokens, raw caller utterances, raw transcripts, raw `api_resp`, or complete tool payloads. Do not say an already verified caller was never authenticated: report the actual earlier verification and separately set `requires_reverification` for fraud/safety desks. Business actions remain disabled during a fraud escalation regardless of earlier verification.

Identifiers in ordinary logs/transcripts are masked. Sensitive digits received during credential capture are removed before transcript/utterance persistence and general model context where supported; any unavoidable model exposure must be part of the approved capture design. DLP/text redaction may assist but is not proof that recordings, streaming traces, or handoffs are protected. Audio retention, residency, access, sensitive-audio suppression, and caller objections are client/Legal requirements. Until validated, disable voice-secret capture and use a tested secure keypad path or human fallback. Every call still requires a recording artifact with approved protected segments; never claim text masking redacts audio.

## Section 6 — Per-Turn Preprocessing Requirements

Keep the original observable order: **DTMF capture → no-input accounting → tool-error classification → module-specific pre-checks → model response → post-turn processing**. Implement security, state transitions, disclosures, and terminal enforcement deterministically. Prompts may explain rules but must not be their only enforcement.

1. **DTMF capture.** Normalize native keypad events and text-encoded events such as `user pressed 1234`; retain trusted provenance. Untrusted text that describes digits is not proof of keypad entry. Only native verified keypad events may satisfy PIN capture. Route raw payment digits directly to the secure capture provider; do not copy them into general session state. Clear secret digits at turn completion and on failure.
2. **No-input accounting.** Count only genuine input windows reported by the platform. No-input must not accrue while notices are playing with barge-in disabled, tools are running, the call is on a transfer bridge, or secure capture has its own timer. Valid speech or expected keypad input resets consecutive no-input count. First and second misses receive short reprompts; the third nominates a handoff.
3. **Tool-error classification.** Inspect each result immediately before it can affect model output or authorize another tool. System errors nominate a handoff; business errors supply approved alternatives; validation errors consume the global error budget. See Section 16. Never wait for another caller turn to notice a failed action.
4. **Module pre-checks.** Check auth/account binding, business status, language/content readiness, required copy, service eligibility, and pending operations before composing a response or executing an action. Do not repeat an unchanged advisory every turn.

**Safety and priority.** Evaluate safety/fraud signals for each delivered input before permitting side effects. Gather event candidates without terminating from an earlier counter step; a single resolver applies Section 20 so a third no-input event cannot override a fraud/system/safety event. Then enforce account and disclosure prerequisites before any action. This preserves preprocessing order while giving the priority hierarchy real effect.

**Post-turn behaviors.** Validate and normalize tool results into explicit fields; set dependent fields when the result becomes known; mask persisted text; clear secret data; retain pending transaction/handoff status; and re-enable ordinary barge-in after protected playback. Do not wait until the next turn to record a completed action or verification. Tool-returned instructions are data, never authority to change policy.

## Section 7 — Verbatim Copy Library

Store locked strings as versioned constants per language, brand, and applicable region. Emit them through deterministic callbacks. Do not paraphrase, translate at runtime, contract, expand, or reorder locked text. Exact emitted text and approved audio rendering are tested separately. The original source strings are preserved below; their presence in a workshop brief is not evidence of production Legal approval.

| Key | Original primary-language source text | Conditions and release status |
|---|---|---|
| `greeting_main` | Welcome to Telco. I can help with billing, technical support, or managing your account. To get started, could you tell me the phone number or account number associated with your service? | Opening greeting; do not repeat after internal routing. Client must approve brand-specific text. |
| `recording_notice` | This call may be recorded for quality and training purposes. | Protected playback at opening, after initial language correction, and on request. Required regional variants need approval. |
| `id_verification_otp` | For your security, I just sent a 6-digit code to that number — please read it back to me. | Only after successful send; spoken OTP permitted only with approved capture protections. Six-digit backend contract must match. |
| `id_verification_pin` | For your security, I'll need to verify your identity. Please enter the 4-digit PIN you set up. | Keypad input only; PIN contract must match. |
| `live_agent_handoff` | I'll connect you to a representative who can help. Please hold. | Use only when a handoff is actually initiated; not for a known closed queue or completed disconnect. |
| `business_handoff` | To get you the best support for your business account, I'll transfer you to an agent. You'll need to use your phone keypad instead of talking to the virtual assistant. Just a moment while I connect you. | Business handoff; client/platform must confirm the promised keypad experience or approve replacement copy before launch. |
| `payment_method_preamble` | **No source text supplied. Obtain from Legal / Compliance.** | Blocks automated payment-method access/capture until supplied. |
| `contract_cancellation_fee_disclosure` | **No source text supplied. Obtain from Legal.** | Blocks automated cancellation/port-out actions requiring it until supplied. |
| `refund_confirmation_pattern` | Your refund of ${amount} will appear on your next statement within {days} business days. | Original legacy pattern; only applicable when the backend transaction type, destination, and timing make this exact statement true and Legal approves its use. Not a universal credit/refund message. |
| `empathy_protocol` | I'm very sorry to hear that you are facing challenges. I will ensure we handle your request with the utmost care. | Fraud and approved safety handoffs. |
| `outage_active` | I see there's an active outage in your area. We're working on it. Would you like me to text you when it's restored? | Only when active outage and a real restoration-notification capability are confirmed. |
| `transfer_to_specialist` | I'll connect you to a billing specialist now — they'll have everything we've already discussed. | Billing transfer with sanitized relevant context; never implies secrets are transferred. |

All secondary-language entries require approved translations. “Secondary” does not mean any language a model can speak; concrete locales and coverage must be configured. If a required locked string is unavailable, do not generate a substitute. Route to an approved human/legacy path with appropriate approved fallback audio. If even the language-specific handoff asset is missing, the affected language is not ready for automated launch; do not silently speak the primary-language line.

**Added copy requirements — Assumptions A-01, A-07, A-08, A-11, A-13.** The copy registry also needs approved text for restricted-caller deflection; ordinary success/declined-help closure; transfer unavailable/failed; next-business-day instructions; supported-language selection and unsupported-language fallback; outage advisory without an SMS offer; transaction pending/unknown; separate statement-credit and payment-refund confirmations; and threat/malicious closure. Names and wording are client copy assets, not existing backend tools. Until supplied, the corresponding branch uses a validated human/legacy fallback or remains disabled; the model must not invent locked legal text.

Financial templates must distinguish transaction type, destination, amount/currency, and estimated versus guaranteed timing. The agent uses no two-day default. A backend value that conflicts with locked copy is an integration mismatch: suppress the misleading copy and transfer with the actual state. It is not permission to rewrite a mandatory string. Apply the same rule to six-digit OTPs, four-digit PINs, and the original 30-minute reset-link requirement.

## Section 8 — Module M1: Session Lifecycle & Routing

M1 is the caller's entry and exit point. It owns greeting, identity capture, intent clarification, routing, re-entry, handoff, and caller-confirmed closing.

**Functional responsibilities.** Execute Section 3; capture language and intent; identify the account without exposing account information; invoke M2 when required; classify and route; preserve pending intents and account-bound auth across internal transitions; and accept specialist re-entry without re-greeting. State internal moves in a short natural sentence without exposing module names. Never demand completion of an irrelevant flow after a pivot.

**Backend tools consumed.** Profile lookup, routing evaluator, validated state handlers, safety classification, live-agent/IVR bridge, and the platform session-ending mechanism. Internal module routing is distinct from transferring the telephone call to a human.

### Terminal call outcomes — Assumption A-07

| Logical outcome | Customer experience | Required evidence |
|---|---|---|
| `self_service_completed` | Relevant tasks completed and caller agrees to close | Tool results or validated informational outcome, caller completion, no unhandled pending intent |
| `handover_accepted` | Human platform/queue assumes responsibility for the connected call | Transfer acceptance acknowledgement and handover reference; queue assignment alone is insufficient |
| `handover_failed` | Agent explains it cannot connect, offers only a real approved alternative, then closes if none is available | Failed/timed-out transfer outcome and any separately confirmed callback registration |
| `callback_registered` | Caller is given the backend-confirmed callback arrangement | Durable callback reference, consent, and supplied timing; never inferred from an SMS-send result |
| `next_business_day` | Caller is asked to contact the supplied channel at its verified next opening | Queue calendar/configuration; no promise that the company will call |
| `caller_disconnected` | Caller or network ended the phone call | Transport event; retain action/notice status and operation references |
| `restricted_caller` / `malicious_closed` / `caller_declined` | Approved applicable closing and disconnection | Classified reason/context and terminal transport acknowledgement |

The logical AI-session ending is not assumed to physically disconnect a telephone call. The telephony adapter must explicitly implement `handover_accepted` versus disconnect and verify that the caller is not dropped on escalation. A platform `end_session` call may participate in a configured escalation handler; its name alone does not prove whether a human transfer occurred. Integration must follow the current platform contract and pass the telephone-loop test.

### Handoff sequence

1. Freeze new account mutations, identify the winning trigger under Section 20, and snapshot the allowlisted context from Section 5. Preserve unknown/in-flight operation status.
2. Resolve queue availability and language through the platform's approved reason/context mapping. The model does not guess business hours or human language coverage.
3. If open, emit the applicable approved handoff line and initiate transfer. Stop self-service once initiated. Do not tell the caller a representative has accepted until the transport confirms it.
4. If status is unknown, attempt the configured transfer once; let the platform return its actual result. If a transfer times out, check transfer status using its reference if supported; do not initiate a second potentially duplicated bridge.
5. For an explicitly failed safety/fraud transfer only, permit one immediate retry if the transport guarantees the previous transfer did not connect and the request is idempotent. For other explicit failures, use the approved alternate channel/callback if available and accepted. Do not recursively hand off to the same failed path.
6. If no approved alternative can be established, give the approved unavailable message and close, recording `handover_failed`, the original trigger, and `system_unavailable` as the transport failure. This exception also applies to safety transfer failure; it is not successful safety resolution and blocks readiness if the required 24/7 path is unavailable.

**Closed queues.** Automated actions with available prerequisites may continue after hours. A necessary sales, plan-change, booking, cancellation, or porting handoff to a closed queue receives next-business-day instructions. Fraud and outage requests use the configured 24/7 destinations. Other intents use the verified queue schedule. Register a callback only if the capability exists, the caller agrees, and the backend confirms it. If next opening is unknown, provide only the approved contact alternative, not an invented date or promise.

**Recording objections.** Re-emit the applicable notice on request, explain only approved policy, and offer the configured representative/alternative. The agent does not claim it stopped recording. Consent, refusal, and any recording-off route must be provided by the client's approved recording policy before launch (A-12).

## Section 9 — Module M2: Authentication & Identity

Three states are retained: **Guest** (no resolved account), **Identified** (account resolved), and **Authenticated** (identity verified for that account and permitted role). Public information, language selection, public coverage/catalog browsing, and minimum identity resolution are exceptions to account-read authentication. No balance, personal profile, account-specific plan, or appointment details are disclosed under those exceptions.

**Lead guidance.** The contact on file belongs to the customer context of the account being authenticated. The lead did not confirm that password-reset dispatch may bypass authentication, nor name an actual lookup API.

**Assumption A-03: operative auth policy.** Require successful OTP or PIN verification before sending a password-reset link. Accept OTP as spoken digits or native keypad input when the capture channel meets Section 5. Accept PIN only from native verified keypad input. This explicitly replaces the routing-table “Identified only” entry and the original contradictory blanket statement that OTPs must not be spoken. Never read either credential back.

### Required identity and OTP flow

1. Resolve the caller-specified account/phone to one account through a client identity capability. A `clid` lookup may suggest an account, but cannot silently override a different account the caller intends to use. Disambiguate multiple accounts without revealing private details.
2. Obtain a protected challenge/destination reference bound to that account and its permitted actor. The destination must be the backend's on-file contact. Never send an OTP or reset link to an arbitrary caller-supplied number.
3. Confirm only the last four digits of the on-file destination and ask whether to send the code. Dispatch it using the bound challenge context.
4. Emit `id_verification_otp` only after successful dispatch with the matching code-length contract. A send error follows the error policy; a successful send is not authentication.
5. Capture the answer through the permitted channel, give native keypad input precedence only for the active challenge, and call validation. Delayed digits from an old challenge must not be reused.
6. The verified result handler records Pass/Fail for the exact account/session/challenge. Only Pass unlocks that account's authorized actions. Caller claims, model text, router output, and historical lookup results cannot create a Pass.

### PIN fallback and attempt limits

Use the account-supported PIN fallback when the caller reports they cannot access the on-file phone, when the phone is lost/stolen, or when the contact capability reports it unavailable. This is **Assumption A-03**; it broadens the earlier addendum's system-only reachability restriction. It never permits replacing the on-file destination. If PIN is not configured, the keypad channel is unavailable, or the policy does not allow fallback, hand off with `auth_failure_handoff`.

Emit `id_verification_pin`; require native keypad provenance; refuse spoken/text-described PINs without echoing them. A submitted invalid factor or refused factor-entry attempt consumes the auth attempt budget. Backend lockouts and a lower `attempts_remaining` prevail. Three failed attempts across OTP and PIN together cause handoff; resending an OTP or switching modules does not reset the limit. Silence uses the no-input counter, not a double-counted auth failure. Resend count, expiration, and throttling come from the auth backend, not invented constants.

**Account binding and step-up — A-04.** Auth survives topic/module changes only for the same account and authorized services during this call, subject to backend expiration/revocation. Choosing another account clears Pass and requires new verification. MFA and contact-channel changes require an explicitly defined step-up factor and freshness policy; merely repeating the original verification is not assumed sufficient. Until that contract exists, authenticate normally and transfer without making the change. The 30-minute reset-link lifetime, six-digit OTP, and four-digit PIN remain required backend/copy alignment targets; a mismatch is surfaced to the integration owner and not silently reworded.

Fraud skips new authentication and transfers immediately. Any earlier verification is reported accurately with a requirement for receiving-desk reverification. Business account detection transfers before consumer self-service.

## Section 10 — Module M3: Billing & Payment

M3 owns CUJ-2 and the payment portion of CUJ-6.

**Functional responsibilities.** Look up recent bills; identify a charge by date, amount, or line item; apply eligible adjustments or open a dispute; process payments; configure autopay; issue refunds within policy; offer payment arrangements; and answer deposit questions.

**Backend tools consumed.** Bill lookup, dispute creation, payment processing, eligibility evaluation, adjustment/refund execution, autopay configuration, arrangement options, and deposit information. Representative names are in Section 17; omitted contracts must be supplied rather than invented as existing APIs.

### Financial authorization — Lead guidance; contract details under A-08

The client backend owns eligibility and restoration policy. It may use delinquency, dunning group, product, account history, prior adjustments, and other conditions. Those are possible backend policy inputs, not rules for the agent to invent or evaluate from conversation. No numeric refund limit, delinquency cutoff, or approval criterion is specified by this PRD.

The proposed adapter contract for an eligibility decision must expose these meanings (field names are a proposed interface): `decision_id`, selected account/service/charge, `verdict` (`eligible`, `ineligible`, `review_required`), `operation_type` (`statement_credit` or `payment_refund`), allowed amount, currency, applicable limit, permitted destination, caller-safe reason, policy version, and validity/expiry. Monetary values are exact decimals or minor units. An eligibility decision and its execution must refer to the same account, charge, currency, and operation type.

- A caller's amount is a search key only. Look up the bill before naming a charge, then confirm the charge with the caller.
- Execute an adjustment only when the backend returns an affirmative decision and the requested action lies within it. Do not interpret “small-dollar,” `loyalty_limit`, or the example amount as a policy.
- If a limit/verdict is absent or inconsistent, or the request exceeds it, do not execute. Transfer to billing with `refund_threshold_exceeded` and a separate trigger distinguishing `limit_exceeded` from `eligibility_unknown`; the code is a compatibility category, not proof that a numeric threshold was exceeded.
- A successful ineligible result may lead to a dispute case if the backend permits it and the caller agrees. An eligible automatic adjustment must not also create a dispute for the same charge.
- Before submission, state the backend-provided action, amount/currency, destination, and any relevant conditions; obtain explicit confirmation. Section 16 governs submission and uncertain results.
- Execution must return operation reference/status and confirmed transaction details. “Eligible,” “accepted,” and “pending” are not completed credit/refund outcomes.

### Statement credit versus refund

A **statement credit** reduces the customer's account balance or future bill. A **payment refund** returns funds through a backend-approved payment route. The confirmation must identify the actual type and destination. Do not promise cash returned when only a bill credit occurred. Apply the approved type-specific template after a successful execution result, using its amount/currency and posting window. If timing is unknown or required copy is missing, do not invent it; transfer with the existing operation reference, and never re-execute to obtain a nicer response.

The original `refund_confirmation_pattern` remains in the copy library for traceability, but is used only when its exact statement is approved and true for the returned result. Type-specific templates are release dependencies. The original $12.50/two-business-day illustration is not financial policy.

**Illustrative corrected sequence.** Caller reports an unfamiliar charge → authenticate → look up and confirm the exact charge → obtain eligibility → explain the backend-authorized credit or refund → receive caller confirmation → execute once → read the result → emit the applicable approved confirmation. Do not announce a credit merely because eligibility succeeded.

### Payments, autopay, arrangements, and deposits

Emit `payment_method_preamble` before any payment-method access or capture. Raw card entry belongs to a secure upstream capture/tokenization path; never ask the caller to speak card details or place raw payment digits in `dtmf_digits`. A payment token is not logged or handed to the model. Missing disclosure or secure capture means billing handoff before payment entry. For autopay, obtain explicit agreement to backend-returned payment method, terms, and schedule before commit; do not infer consent from a request for information.

Arrangement options, deposits, prepaid/postpaid eligibility, amounts due, and payment outcomes come from the backend. Present only returned options. An arrangement counts as established only after a confirmed enrollment/commit result. Prepaid requests must not run a postpaid-only tool. A refused payment or arrangement does not automatically end all help: offer an appropriate representative without promising restoration.

### Restoration after non-payment

Payment submission, authorization, settlement, balance posting, and a permitted restoration are distinct states. After a relevant payment or arrangement, obtain a fresh backend restoration decision bound to the account and selected service. Proposed result meanings: `eligible`, `decision_id`, `service_id`, `decision_time`, `valid_until` or an equivalent atomic validity guarantee, unmet conditions, and permitted effective timing. A payment arrangement qualifies only if that decision explicitly allows it.

Return via M1 to M7 only when that decision permits restore, or return the explicit pending/ineligible outcome for explanation/handoff. No guessed zero-balance test, successful card authorization, or model inference can authorize restoration. The restoration executor must validate that permission atomically when committing. See Section 14.

## Section 11 — Module M4: Technical Support & Virtual Repair

M4 owns CUJ-3, the largest volume slice.

### Required diagnostic flow

1. Authenticate for account-specific technical service, identify the affected line of business/service, and obtain its trusted service region.
2. Check regional outage before diagnostics. A failed or unknown outage check is not “no outage.” The pre-call public advisory does not substitute for this service-specific check.
3. For an active outage, use `outage_active` only when a real restoration-text subscription exists. On consent, register it and confirm only after a subscription reference is returned. Without that capability, use an approved outage-only advisory. If such copy is missing, transfer rather than emit the original false SMS offer.
4. For no active outage, clarify TV subtype before TV diagnostics. Do not ask TV subtype for internet, mobile, homephone, or smarthome issues.
5. Start the supported virtual-repair session, capture diagnostic answers through its lifecycle capability, and follow backend/approved content steps. Do not invent repair instructions outside approved coverage.
6. Offer SMS first for more than two sequential troubleshooting steps. If declined, unavailable, or undelivered, speak at most two steps at a time and check progress. Two or fewer steps may be spoken directly.
7. If resolved, recap and check whether the caller needs anything else. If unresolved, offer a technician visit via M1 → M6 or create a ticket when the backend's disposition permits it. State a ticket reference only after confirmed creation.

**Backend tools consumed.** Outage lookup, repair lifecycle, diagnostic answer capture, ticket lookup/creation, localized content, SMS dispatch, and durable outage subscriptions. SMS dispatch alone is not an outage-subscription capability.

**Completion and boundaries — A-11.** Receiving an outage advisory does not mean service was restored. Record an informational outcome and any confirmed subscription separately. Do not end automatically before honoring another intent or a human request. Quote an ETA only when the outage backend supplies it. Stop diagnostics at the backend's terminal outcome or configured maximum repair steps; limits are supplied in the repair content/contract, not a guessed number. Missing limits/coverage block automated repair for that symptom and route to a human.

## Section 12 — Module M5: Sales & Equipment

M5 owns CUJ-5.

**Functional responsibilities.** Check coverage at the relevant address; present a small comparable set of plans; place an authorized order; return order reference and delivery timing; send a receipt; distinguish warranty statuses; route equipment returns, SIM requests, and transfer-in requests appropriately.

**Backend tools consumed.** Coverage, catalog, order placement/status, warranty decision/claim, returns, and transfer-in capability. Availability is gated under Section 17.

**Sales flow.** Public coverage/catalog can be served to a Guest with minimal caller-provided address information. Account-specific pricing and all changes to an existing account require authentication. A prospect with no authenticated account may receive public information and then a sales handoff; do not invent an identity/onboarding flow. Coverage must succeed before offering plans. Present two or three comparable eligible options when available; if only one exists, present one with an honest explanation, and if none exist say so. Never invent extra plans to meet a numeric minimum or read the whole catalog.

Selection alone is not final order consent. Confirm the selected service, backend price/currency, material terms/fees, target service/address, and relevant fulfillment timing before submission. Place once; announce order number and ETA only from confirmed results. A failed receipt SMS does not cancel the order or justify placing it again.

**Equipment policy — A-10.** Warranty eligibility, damage exclusions, replacement charges, return windows, and transfer eligibility are backend/client rules. Missing policy or capability means handoff. Proposed initial handling for SIM swaps/replacements/eSIM, PUK requests, carrier unlocks, returns, and number transfer-in is an authenticated human handoff for existing accounts. New prospects follow the Guest sales path. Diagnose “phone locked” versus carrier unlock with one question. Never read a PUK or other secret to the caller. These handoff defaults preserve intent coverage but require acceptance as launch scope.

Business accounts transfer immediately once identified, with no consumer sales attempt. Do not make unsolicited offers during outage, fraud, safety, or system-failure calls.

## Section 13 — Module M6: Appointment & Ticket Management

M6 owns CUJ-4.

**Functional responsibilities.** Find active appointments, offer availability, book/reschedule/cancel with consent, send confirmation, report technician status, and look up existing tickets.

**Backend tools consumed.** Active-appointment lookup, availability, booking/reschedule/cancellation commit and status, dispatch status, optional technician-note and waitlist capabilities, ticket lookup, and SMS confirmation.

| Situation | Required behavior |
|---|---|
| Single active appointment | Confirm its relevant details and the requested action after authentication. |
| Multiple appointments | Clarify by service/address without exposing unrelated accounts. |
| Booking/rescheduling | Offer two or three real slots when available; one is acceptable if only one exists. State date, window, and service-location timezone; resolve ambiguous dates before commit. |
| Caller chooses a slot | Read back the exact choice and obtain confirmation before committing. A slot offer is not a reservation. |
| Slot disappears before commit | Keep the prior appointment unchanged unless backend evidence says otherwise; fetch fresh options and reconfirm. |
| Same-day cancellation | Explain the backend-approved consequence and obtain two distinct confirmations before commit. |
| Technician dispatched or en-route | Do not cancel automatically. This resolves the original “no take-backs” ambiguity conservatively; use a human or a real note capability. |
| Dispatch state unknown | Do not assume cancellation is permitted; transfer. Unknown is not reported to the caller as dispatched. |
| No availability | Offer a slot-opening notification only if a durable waitlist capability exists; confirm registration only from its result. Otherwise offer verified alternatives/handoff. |
| Commit succeeds, confirmation SMS fails | State the confirmed appointment verbally; record messaging failure without repeating the appointment mutation. |

The dispatched/en-route restriction and same-day double confirmation are **Assumption A-10** where the original wording conflicts. Ticket status comes from a real lookup. “No tickets found” is a successful empty result, not a system outage. Never claim to have left a technician note without a confirmed write.

## Section 14 — Module M7: Account Management

M7 owns CUJ-1 and the account portion of CUJ-6.

**Functional responsibilities.** Send a password-reset SMS link, enable/disable MFA where allowed, route fraud, update permitted profile fields, send registration links, suspend/restore service, and route cancellation/port-out requests.

**Backend tools consumed.** Password-reset dispatch, approved step-up and MFA/profile capabilities, fraud handoff, registration messaging, suspension reason/status, restoration eligibility, and the suspend/restore executor.

**Password reset — A-03.** Authenticate before dispatching to the account's on-file number. The backend owns the one-time link and the original required 30-minute validity. Confirm dispatch and the matching validity only from its result. Never reset the password directly or expose the reset link in speech, model output, logs, or handoff. `sent` means submitted to messaging, not confirmed read by the caller. A mismatched lifetime is an integration failure handled without repeating dispatch blindly.

**MFA and profile — A-04.** Non-sensitive approved profile fields require authentication and a documented field allowlist. MFA and changes to account contact channels require named step-up policy. While it is absent, hand off after normal authentication and make no change. Do not let a caller replace their on-file phone as a way to receive an OTP elsewhere. Registration SMS uses a backend-generated link and the permitted messaging destination; never treat registration as account verification.

### Fraud and lost/stolen service — Assumption A-05; business lead explicitly deferred this decision

- A fraud claim at any stage emits `empathy_protocol` and transfers with `fraud_escalation`; do not request new auth, file a self-service fraud case, or perform account changes. The receiving desk owns investigation/verification.
- When theft/loss and fraud are reported together, use that fraud path without suspending first. This proposed choice follows the original priority hierarchy; it has not been approved by the business lead.
- For theft/loss without a fraud claim, authenticate using the approved alternate/PIN path, select the exact affected service, obtain confirmation, then suspend before unrelated conversation. Never suspend an unauthenticated caller's line.
- A prior verified account does not authorize new self-service after fraud is alleged. A mutation already submitted cannot be wished away; include its actual/unknown status and reference in the immediate handoff.

### Suspend / restore flow

1. Authenticate, select the service, and obtain current state and suspension reason from the backend. If already active, explain the confirmed state and do not execute restore.
2. For non-payment, route M7 → M1 with the payment intent → M3. M3 offers only backend-approved payments/arrangements and obtains a restoration decision under Section 10. Return M3 → M1 → M7; never restore merely because payment was attempted.
3. For travel/lost and other supported reasons, obtain the backend's restoration permission for that specific state; do not assume every non-payment-independent suspension can be reversed.
4. On explicit current permission, explain the action/effective timing, obtain confirmation, and commit through the executor with an idempotency key and decision reference. The backend must revalidate permission at commit.
5. Read the actual new service state and effective time. Only then confirm restoration and send the SMS confirmation. Pending/failed/unknown results are not restored service. A confirmation-text failure does not trigger a second restore.
6. If the caller refuses payment, explain the backend-returned unmet condition and offer a representative. Acceptance transfers; refusal closes normally after checking other requests. Record `refused_payment` as an outcome detail, not a fabricated backend error.

**Cancellation and port-out — A-10.** Proposed launch handling is authenticated human handoff. Do not cancel, provide a transfer credential, promise a fee waiver, or claim a port completed. If automated handling is later approved, require the named execution tools, effective-date and fee rules, necessary approved disclosure before commitment, and the transaction safeguards in Section 16. A closed specialist queue uses Section 8.

## Section 15 — Module M8: Secondary Language Fallback

M8 owns CUJ-7. It handles technical-support requests in a configured secondary language when M4 does not have approved localized content for the actual service/subtype/symptom.

**Lead guidance.** Platform-supported languages and client-supported languages are separate sets. Voice support must be verified for the selected model/channel; a language supported for chat is not automatically approved for this voice deployment.

**Client language contract — A-01.** Each supported voice locale requires approved legal/greeting/handoff assets, tested speech recognition and synthesis, localized or approved translatable ordinary content, and a verified human fallback route. The original `primary`/`secondary` roles map to concrete locale codes; expanding beyond two requires an explicit extension rather than silently assigning every language to `secondary`.

**Coverage decision.** Use a configured coverage matrix keyed by locale, service, subtype, symptom, and content/version. A missing approved result means unsupported coverage, not permission to translate repair instructions freely. If M4 lacks coverage and M8 has it, route via M1 to M8. If neither has it, transfer with `secondary_language_live_agent` and the actual requested locale. Billing, sales, appointments, and account management stay in their usual modules only when those modules' localized prerequisites are satisfied; otherwise use the same language-aware human fallback.

**Unsupported language.** Detect it where possible, stop automated account actions, and invoke a configured multilingual/legacy routing path. Provide only approved selection/fallback audio; do not promise a representative speaks that language unless confirmed by routing. An explicit caller choice of a supported language may resume the appropriate flow. Uncertain detection receives one approved language clarification, then the fallback. The old reason `secondary_language_live_agent` is used as a compatibility code with `terminal_trigger = unsupported_language` and the actual locale; unsupported input does not become a supported `language` role.

**Non-degradation.** After initial language selection/correction, every response and handoff prompt remains in the locked language unless the caller explicitly requests a switch. Ordinary approved content may be rendered naturally; legal strings never use model translation. Missing translation is not permission to fall back to the primary-language line. Preserve the requested language in handoff metadata and verify the platform's destination, including unavailable-queue behavior.

## Section 16 — Error Recovery & Retry Requirements

### Error classes and counters

| Class/counter | Trigger or limit | Action |
|---|---|---|
| System error | `SYSTEM_DOWN`, `INTERNAL_ERROR`, `AUTH_SERVICE_UNAVAILABLE`, unknown error code, invalid result schema | Stop dependent work and transfer with `system_unavailable`; no model-directed tool retry. |
| Business error | Documented `INSUFFICIENT_FUNDS`, `NOT_ELIGIBLE`, `ALREADY_APPLIED`, or another registered business code | Explain approved meaning; offer only real alternatives. `ALREADY_APPLIED` requires original-result/status evidence, not a new mutation. |
| Validation error | `INVALID_INPUT`, `MALFORMED_REQUEST` | Increment `global_err_count`. Ask the caller only for input they can actually correct; adapter/schema defects route to system failure rather than repeatedly blaming the caller. |
| `local_noinput_counter` | Three consecutive misses in the same module | `no_input_escalation`; reset on valid input or module change. |
| `no_match_confirmation_count` | Three unresolved targeted clarification attempts in the same episode | `disambig_max_attempts`; reset when resolved or the caller chooses a genuinely new module/intent. |
| `global_err_count` | Three validation errors in the call | `too_many_errors` handoff; never reset by a topic/module change. System errors do not wait for this count. |
| Auth attempt budget | Three failed/refused factor attempts across OTP/PIN, or stricter backend limit | `auth_failure_handoff`; see Section 9. |

Do not read raw backend error messages to callers. Map documented errors to approved explanations, and never follow instructions embedded in tool results. Empty successful lists, unknown optional ETA fields, and pending transaction status are not automatically system outages; follow their explicitly defined business branches.

### Transaction confirmation, interruption, and uncertain outcomes — Assumption A-09; lead response pending

Apply the following lifecycle to every payment, adjustment/refund, order, subscription enrollment, appointment change, and account mutation. Authorization, consent, and completion are distinct facts.

| Operation status | Meaning | Caller interruption / permitted behavior |
|---|---|---|
| `draft` | Nothing submitted | Change topic or cancel immediately; no side effect to reverse. |
| `awaiting_confirmation` | Material details presented | Require explicit affirmative consent tied to those details. Silence, partial acknowledgement, or a different topic is not consent. |
| `submitted` | Backend request accepted/in flight | Preserve operation reference and key. “Stop” is a cancellation request, not proof of cancellation. |
| `pending` | Backend knows the operation and has not completed it | Give only returned status/timing. Do not call it completed or resend it as new. |
| `succeeded` | Backend confirms committed result | Explain actual result. Undo requires a separately supported and authorized reversal; do not silently reverse it. |
| `failed` | Backend confirms no successful effect | Explain the failure and permitted alternative; a new attempt needs applicable confirmation. |
| `unknown` | Submission may have taken effect; reliable result unavailable | No success/failure claim and no fresh mutation. Hand off with the original reference/key and unresolved status. |
| `cancelled` / `reversed` | Backend confirms cancellation or compensating action | Confirm exactly what was cancelled/reversed, including any remaining fees or pending effects returned by the backend. |

Generate the durable idempotency key before submission, bound to account/service, action, and caller-confirmed request. Retrying that same operation reuses the key; a changed request requires fresh consent and a new operation. The backend's documented status/commit point is authoritative. Idempotency avoids duplication but does not prove an operation never happened.

On “stop” during `submitted`/`pending`, use the backend's cancellation/status capability if available and authorized. If it cannot confirm cancellation, explain uncertainty and hand off. Do not delay a higher-priority fraud/safety/human handoff to conduct a prolonged reconciliation; pass the operation state to the receiving system. Serialize dependent mutations on the same target while a previous result is unresolved.

A system error after submission marks the action unknown unless backend evidence proves otherwise, then transfers immediately with the operation reference. The receiving operations system owns read-only reconciliation; the AI does not retry the failed mutation. A late backend completion must update the durable operation record even after the call ends. A durable integration/operations owner must be able to find and resolve every unknown result. If that facility is absent, the mutation is not ready for production automation.

Caller disconnection does not automatically cancel a submitted operation. Complete or reconcile according to the backend contract; use only already authorized messaging, and never create a new payment/order because the call restarted. Human and agent continuations must refer to the same operation record. A delivery-message failure does not undo or duplicate the underlying action.

### Reason-code compatibility and truthful outcomes — Assumption A-07

Retain the original eleven codes. `terminal_outcome` and `terminal_trigger` capture detail without changing their meaning silently.

| Reason code | Normal logical action | Notes |
|---|---|---|
| `malicious_input` | Approved closing and disconnect | Requires actual classified malicious/threat behavior, not anger alone. |
| `fraud_escalation` | 24/7 human handoff | Fraud; legacy safety transport use requires `safety_category` and approved queue mapping under Section 20. |
| `system_unavailable` | Human/legacy handoff | Backend/capability failure or final transport failure; never recursive transfer loops. |
| `user_requested_agent` | Human handoff | Explicit request or acceptance of a representative offer. |
| `business_handoff` | Business human handoff | Selected account's business flag. |
| `no_input_escalation` | Human handoff | Third consecutive eligible no-input event. |
| `disambig_max_attempts` | Human handoff | Third unresolved clarification attempt. |
| `too_many_errors` | Human handoff | Third global validation error. |
| `auth_failure_handoff` | Human handoff | Verification exhausted/unavailable; caller not authorized for action. |
| `refund_threshold_exceeded` | Billing human handoff | Excess limit or unavailable eligibility/limit, distinguished by trigger. |
| `secondary_language_live_agent` | Language-appropriate human/legacy handoff | Supported-language content gap or unsupported-language routing, distinguished by trigger. |

For policy-only/manual launch paths, offer a representative: on acceptance use `user_requested_agent`; on decline use a normal close. A missing backend/copy dependency uses `system_unavailable` with the specific trigger unless the table provides a more specific category. Successful completion, restricted callers, caller disconnection, and declined assistance use terminal outcomes, not invented problem codes. If the platform requires its own transport reason, map it separately and retain the business code as metadata.

## Section 17 — Available Backend Tool Inventory

The original inventory describes capabilities that are or will be exposed. This draft does not verify any live integration. Register each actual tool/capability with owner, version, environment, availability, auth scope, inputs/outputs, errors, timeout, mutation/idempotency/status semantics, localization, and PII classification before wiring it to production.

### Representative tool contracts retained from the original

These are source-level examples, not sufficient authorization contracts. Any additions below must be implemented through a documented adapter or backend change; do not assume these sample payloads already return the new fields.

| Tool | Original input | Original output | Category |
|---|---|---|---|
| `fetch_customer_profile` | `{clid: string}` | `{identification_status, customer_type, business_flag, is_prepaid, ...}` | Identity |
| `send_authentication_otp` | `{clid: string}` | `{sent: bool, expires_in_sec: int}` | Auth |
| `validate_authentication_otp` | `{code: string}` | `{auth_status: Pass/Fail, attempts_remaining: int}` | Auth |
| `validate_authentication_pin` | `{pin: string}` | `{auth_status: Pass/Fail, attempts_remaining: int}` | Auth |
| `evaluate_routing_rules` | `{utterance: string, entities: object}` | `{route: string, confidence: float, requires_auth: bool}` | Routing |
| `fetch_recent_bills` | `{billing_account: string}` | `{bills: [{id, date, amount, line_items}]}` | Billing |
| `create_dispute_ticket` | `{charge_id, reason, notes}` | `{ticket_id: string, eta_business_days: int}` | Billing |
| `check_regional_outage` | `{region: string, lob: string}` | `{active: bool, restoration_eta_iso: string or null}` | Tech |
| `start_virtual_repair` | `{cirn, lob, symptom}` | `{session_id, first_diagnostic_question}` | Tech |
| `fetch_availability_slots` | `{zip, service_type}` | `{slots: [{date, window, technician_id}]}` | Appointments |
| `commit_appointment_reschedule` | `{appt_id, new_slot}` | `{confirmed: bool, new_date: string}` | Appointments |
| `fetch_plan_catalog` | `{lob, customer_type}` | `{plans: [{id, name, price, key_features}]}` | Sales |
| `send_password_reset_sms` | `{cirn}` | `{sent: bool, valid_minutes: int}` | Account |
| `execute_suspend_restore` | `{cirn, action: suspend/restore, reason}` | `{new_state: string, effective_iso: string}` | Account |
| `execute_live_agent_handover` | `{reason: string, session_context: object}` | `{handover_id: string, queue: string}` | Handoff |

**Necessary contract additions.** The sample `clid` input does not establish ownership of a caller-specified account. The identity/auth adapter must resolve that account and bind the OTP/PIN challenge to its on-file destination and session. Verification results must identify the bound account/authorized scope. Mutation adapters must expose operation reference/status and idempotency. Handoff needs acceptance/failure status, not merely a queue string. Slots/appointments need a service-location timezone and stable slot reference. Financial and restoration decisions need the result meanings defined in Section 10. These are required capabilities to be supplied by integration owners, not invented named tools.

### Approximate inventory by category

| Category | Original approximate count | Naming examples |
|---|---:|---|
| Identity & profile | 20 | `fetch_*`, `lookup_*`, `load_*_configs` |
| Auth | 10 | `send_authentication_*`, `validate_authentication_*` |
| Routing & disambiguation | 12 | `evaluate_routing_*`, `update_routing_state` |
| Billing & payments | 80 | `fetch_recent_bills_*`, `process_payment_*`, `create_dispute_*` |
| Tech & virtual repair | 35 | `check_*_outage`, `start_virtual_repair`, `lookup_*_ticket` |
| Sales & equipment | 18 | `fetch_plan_catalog`, `place_new_order`, `process_warranty_claim` |
| Appointments | 30 | `fetch_availability_*`, `commit_appointment_*` |
| SMS / messaging | 8 | `prepare_sms_payload`, `send_sms` |
| Handoff & escalation | 6 | `execute_live_agent_handover`, `execute_business_handover` |
| State mutation helpers | 25 | Validated state setters/context handlers |
| Content / RAG | 6 | Language-tagged content collections |

Counts describe the original expected surface; they are not evidence that roughly 250 live tools exist or must all be exposed to the model.

### Proposed launch capability matrix — Assumption A-10

Every row is recognized. “Conditional automation” means required for the intended automated scope but disabled until its prerequisites are confirmed. Actual availability is **unverified** for all rows in this draft. Product must approve any replacement of an original self-service journey with a handoff.

| Intent/capability | Proposed launch treatment | Required before automatic completion; fallback if absent |
|---|---|---|
| Opening, notices, restricted-caller checks | Mandatory intake | Brand/language/notice/blocklist and tested legacy intake; no production launch without safe intake |
| Identity, OTP/PIN, reset dispatch | Conditional automation, CUJ-1 | Account-bound auth, approved factor channels/copy, on-file SMS; auth/help handoff |
| Bills, eligible credits/refunds, disputes | Conditional automation, CUJ-2 | Lookup, eligibility, execution/status, type-specific copy, consent; billing handoff |
| Payments, autopay, arrangements, deposits | Conditional automation | Secure capture, policy/options, approved preamble, transaction/status tools; billing handoff |
| Outage, repair, technical tickets | Conditional automation, CUJ-3 | Service auth/region, outage/content/repair/status/ticket tools; tech handoff |
| Existing-customer sale/order | Conditional automation, CUJ-5 | Auth, coverage, comparable catalog, terms, order/status, receipt; sales handoff |
| Prospect/new-customer sale | Public information then human handoff | Coverage/catalog; do not build unsupplied onboarding/credit-check policy |
| Warranty claim | Conditional automation | Backend warranty verdict, permitted remedy, fees/consent and claim/status; equipment handoff |
| Returns, SIM replacement/swap/eSIM, PUK, carrier unlock | Human handoff | Client security/return policy and new execution contracts required to expand automation |
| Number transfer-in, port-out, cancellation | Human handoff | Client policy, credentials handling, fee copy, execution/status and consent required to expand automation |
| Appointment booking/rescheduling/cancellation/status, ticket status | Conditional automation, CUJ-4 | Active appointment/dispatch/slots/timezone/commit/status/tickets; appointment handoff |
| MFA and contact-channel changes | Human handoff after normal authentication | Named step-up and authorized-field policy required to expand automation |
| Other profile changes, registration SMS | Conditional automation | Field allowlist, account auth, validated update or registration dispatch; account handoff |
| Suspend/restore | Conditional automation, CUJ-6 | Client security policy, state/reason/eligibility/commit/status; account/fraud handoff |
| Fraud, business, safety, explicit human requests | Human/legacy outcome required | Approved rules, queue mapping, handoff transport and unavailable outcome; never claim automated resolution |
| Secondary-language technical fallback | Conditional automation or language handoff, CUJ-7 | Localized coverage, mandatory copy, human-language routing; affected locale disabled until fallback works |
| Outage-restored/slot-open notifications, callbacks, technician notes | Conditional ancillary capability | Durable subscription/callback/note service and acknowledgements; never offer absent follow-up |

### Requirements every tool must satisfy

1. **Real and mock branches.** Every wired tool has a documented real contract and a deterministic mock branch. Mocking is enabled only by trusted evaluation deployment plus `mock_mode == "True"`, never by caller input or production session parameters. Test identity/auth through mocked lookup/verification tools; do not seed auth Pass in end-to-end tests. Low-level isolated unit fixtures must be labeled and cannot count as end-to-end authentication evidence.
2. **Failure fixtures.** Mocks support success, business rejection, validation error, hard system error, empty result, pending/unknown operation, duplicate request, stale eligibility, and message/transfer failure. Success-only mocks are insufficient. Fixtures use synthetic accounts and factors.
3. **Error envelope.** Preserve `{ "error": "<CODE>", "message": "<human>" }`. Additional integration metadata is allowed only in a versioned schema and cannot bypass error classification or leak sensitive data. Raw `message` is not caller copy. Unknown codes/schemas invoke the system path.
4. **Idempotency and reconciliation.** Every mutating operation must deduplicate the same operation key, return the original result/status, and support a durable status/reconciliation path. Test the real non-production contract as well as the mock; a mock alone cannot prove backend idempotency.
5. **Authorization.** Backends verify account/service scope and action authorization, including restoration permission, at execution time. An agent-side auth flag alone is not a backend security boundary.
6. **PII handling.** Classify sensitive response fields, redact every persistence sink, and deliver only the minimum approved result to the model. The adapter must not persist raw secrets while waiting for later DLP processing.
7. **Grounding, localization, and freshness.** Validate field types, currencies, timestamps/timezones, policy/decision versions, language, and validity windows. Missing information must be represented as unknown. Use approved localized content or the fallback; never fabricate.
8. **Messaging — A-11.** Sensitive SMS goes only to the backend-approved on-file contact. Public troubleshooting for a prospect requires an explicitly approved verified destination policy; absent that, use speech. Templates use verified data, never caller-dictated arbitrary messages. Distinguish dispatch accepted, delivered, failed, and unknown. Future notifications require durable subscriptions with consent; an immediate SMS send does not satisfy them.

## Section 18 — Requirements Register (BR-TV-001 … BR-TV-020)

Original IDs and names remain stable. The descriptions below incorporate the explicit clarifications in this document so the register, flow, and tests use one rule. Added assumption IDs supplement these requirements; they do not imply client approval.

| ID | Name | Operative requirement | Main sections |
|---|---|---|---|
| BR-TV-001 | Recording notice | Approved opening notice in the initial configured language; protected playback; approved replay after startup language correction and on request; auditable completion | 3, 7 |
| BR-TV-002 | Restricted caller check | Check before greeting; restricted caller follows approved notice/deflection/disconnect path; missing check uses tested legacy intake | 3, 17 |
| BR-TV-003 | Regional service alert | Use trusted pre-call service region; active approved advisory precedes greeting; unknown region is not a clear result | 3, 11 |
| BR-TV-004 | Language locking | Detect/select supported language on first meaningful input, permit the defined startup correction, retain lock except explicit caller switch | 3, 15 |
| BR-TV-005 | Module coverage | Recognize every Section 4 intent and reach its approved automated or human path; scope reductions require acceptance | 4, 17 |
| BR-TV-006 | Retry strikes | Third consecutive no-input or third unresolved clarification attempt causes handoff with defined reset rules | 6, 16 |
| BR-TV-007 | DTMF capture | Normalize current-turn events with provenance; native-only PIN; payment isolation and secret clearing override general storage | 5, 6, 9 |
| BR-TV-008 | Auth ladder | Guest → Identified → Authenticated; scoped account verification before private reads/mutations, with explicit public/identity exceptions | 4, 9 |
| BR-TV-009 | PII redaction | Last-four permitted identifiers; never echo credentials; protect logs/transcripts, audio, and handoff under the approved data contract | 5, 7 |
| BR-TV-010 | Tool-error tri-state | System failure stops dependent work and transfers; business alternatives are grounded; caller-correctable validation errors use the retry budget | 6, 16 |
| BR-TV-011 | Verbatim compliance | Exact approved copy/version/locale, deterministic emission, truthful substitutions, no invented translations | 7 |
| BR-TV-012 | Business handoff | Business status on the resolved account triggers business transfer before consumer self-service | 1, 8, 12 |
| BR-TV-013 | Fraud escalation | Empathy and 24/7 fraud handoff; no new authentication or account actions; theft/fraud overlap follows A-05 | 14, 20 |
| BR-TV-014 | After-hours awareness | Verify queue availability; preserve fraud/outage 24/7 destinations; no unregistered callback promises | 8 |
| BR-TV-015 | Session-context handoff | Transfer the approved allowlisted context and actual operation/auth status; exclude secrets and raw payloads | 5, 8 |
| BR-TV-016 | Malicious utterance | Per-turn classification with separate safety, threat, fraud, and anger handling; no keyword-only malicious disconnects | 6, 20 |
| BR-TV-017 | No invented data | Private facts and action/eligibility/timing claims require the corresponding successful authoritative result | 10, 16, 17 |
| BR-TV-018 | Audio recording | Every connected call produces the required `.wav` recording artifact with approved sensitive-segment handling and access policy | 5, 21 |
| BR-TV-019 | Topic switch mid-call | Reclassify through M1; preserve unresolved operations; topic changes do not themselves cancel submitted actions | 4, 16 |
| BR-TV-020 | Language non-degradation | After startup selection/correction, responses and human-routing language remain consistent except caller-requested switches | 3, 15 |

## Section 19 — Example User Journeys (Test Scenarios)

Retain all seven original journeys and their relative emphasis. The original PDF contains clipped scenario lines; the complete specifications below replace those incomplete examples using the visible original requirements and this document's labeled assumptions. They are readable acceptance specifications, not a claim that runnable evaluation files already exist. Implement them in the actual runner schema and link their IDs to results.

Each fixture must specify account/service identity, on-file contact, auth factors, business/prepaid flags, locale/copy versions, queue state, deterministic tool results, mutation state, and SMS outcomes. Derive account/auth state through the fixture tools, not a seeded Pass. Each happy path requires the corresponding real capability to pass Section 17 contract tests before release. A fallback test passing cannot stand in for its happy path.

### CUJ-1 — `cuj_1_account_password_reset`

| Field | Specification |
|---|---|
| Primary module / volume | M7 / 15% |
| Caller goal | Obtain a portal password-reset link at the account's on-file contact |
| Fixture | Existing consumer account; reachable registered contact; valid six-digit OTP; successful reset dispatch with `valid_minutes = 30`; approved copy |
| Conversation | Caller says “I forgot my password”; identifies the intended account; verifies; agrees to receive the link |
| Original turn budget | 8 caller-response cycles; notice-only playback and tool events are not invented caller turns |
| Success | Correct account authenticated; link dispatched once to on-file contact; confirmed 30-minute validity stated; caller agrees to close |

Assertions: verification precedes reset dispatch; no direct password change; no reset-link/OTP/PIN echo; no caller-supplied alternate destination; no false claim that the SMS was read. Add PIN fallback, unreachable/stolen phone, wrong-account, auth failure, business account, disclosure/capture failure, and delivery-failure variants. A-03 is explicit in this journey and supersedes the original routing-table exception.

### CUJ-2 — `cuj_2_billing_dispute_auto_eligible`

| Field | Specification |
|---|---|
| Primary module / volume | M3 / 25% |
| Caller goal | Resolve an unfamiliar small charge through an authorized adjustment |
| Fixture | Authenticated through normal flow; one matching charge; backend eligible decision with amount/currency/limit and type; successful execution; approved type-specific confirmation with returned timing |
| Conversation | Caller reports a charge; confirms the identified bill item; hears the exact authorized remedy and confirms it |
| Original turn budget | 10 caller-response cycles |
| Success | Exactly one authorized adjustment is committed and correctly described using execution result fields |

Assertions: bill lookup before naming a charge; eligibility before execution; explicit consent; exact amount/type/destination/timing grounding; no dispute case for the eligible charge. Test statement credit and payment refund separately. Add missing-verdict/limit, excess threshold, ineligible-with-dispute, already-applied, unknown execution result, stale eligibility, fraud pivot, wrong currency, and missing approved-copy variants. Never use a hardcoded $12/$12.50 policy or two-day timing.

### CUJ-3 — `cuj_3_tech_support_tv_signal`

| Field | Specification |
|---|---|
| Primary module / volume | M4 / 30% |
| Caller goal | Resolve “TV says no signal” when no outage is active |
| Fixture | Verified account/service; correct region; successful no-outage result; initially unknown TV subtype; supported localized repair content; backend repair success |
| Conversation | Caller identifies symptom and TV subtype, answers diagnostics, and accepts or declines SMS steps |
| Original turn budget | 12 caller-response cycles |
| Success | Outage checked before repair; subtype known before TV-specific diagnostics; confirmed repair outcome and caller completion |

Assertions: no invented subtype/ETA; SMS offered first for more than two sequential steps; speech fallback remains available in short groups. Add active outage with/without subscription capability, null ETA, SMS failure, non-TV service, unresolved-to-ticket/appointment, unsupported symptom, and explicit-human-request variants. An outage notification subscription alone is not a repaired-service result.

### CUJ-4 — `cuj_4_appointment_reschedule`

| Field | Specification |
|---|---|
| Primary module / volume | M6 / 10% |
| Caller goal | Move an existing technician appointment |
| Fixture | Verified account; active appointment; known dispatch state; two or three valid slots with timezone; successful commit and messaging result |
| Conversation | Caller identifies the appointment, selects a real slot, and confirms the readback before commit |
| Original turn budget | 8 caller-response cycles |
| Success | Correct appointment committed once to the confirmed slot; actual new date/window/timezone stated; SMS dispatched after commit |

Assertions: active-appointment lookup before slots; no duplicate commit; SMS failure cannot duplicate the change. Add multiple appointments, one/no slot, slot conflict, unknown/en-route dispatch, same-day two confirmations, ambiguous date/timezone, and interruption-before/after-submit variants.

### CUJ-5 — `cuj_5_sales_add_tv_existing`

| Field | Specification |
|---|---|
| Primary module / volume | M5 / 15% |
| Caller goal | Add TV service to an existing account |
| Fixture | Verified consumer account; positive coverage; two or three eligible comparable plans; confirmed order result with reference and ETA; receipt dispatch |
| Conversation | Caller asks to add TV, selects a plan, hears the final order details/terms, and confirms |
| Original turn budget | 10 caller-response cycles |
| Success | Coverage precedes plan offer; authorized order committed once; actual reference/timing stated; receipt dispatched |

Assertions: no more than three plan options; account auth before billed mutation; order reference only after successful result. Add one/no plan, coverage failure, business account, Guest prospect handoff, caller “stop” during order submission, pending order, and receipt failure variants. Do not fabricate a second plan when only one exists.

### CUJ-6 — `cuj_6_restore_service_from_non_payment`

| Field | Specification |
|---|---|
| Primary module / volume | M7 with M3 / 5% |
| Caller goal | Restore a service suspended for non-payment |
| Fixture | Verified selected service; backend suspension reason; approved payment option; successful payment state; fresh explicit restoration permission; successful restore result; SMS dispatch |
| Conversation | Caller requests restoration, agrees to the specified payment, then confirms permitted restoration |
| Original turn budget | 14 caller-response cycles |
| Success | M7 → M1 → M3 → M1 → M7 routing; restoration occurs only under current backend permission; actual resulting state and timing stated |

Assertions: payment success alone cannot permit restoration; no restore before the eligibility decision; confirmation SMS follows real restore. Add authorization-but-not-posted, arrangement eligible/ineligible, pending eligibility, refused payment, unknown payment, already active, stale restore decision, wrong service, and lost/stolen-plus-fraud variants.

### CUJ-7 — `cuj_7_secondary_language_tech_fallback`

| Field | Specification |
|---|---|
| Primary module / volume | M8 / subset of CUJ-3 |
| Caller goal | Obtain technical help in a configured secondary language |
| Fixture | Named supported locale and all required approved copy; M4 coverage miss; M8 supported-content result or a matching human queue |
| Conversation | Caller speaks the secondary language, states symptom, and answers clarification/auth questions |
| Original turn budget | 10 caller-response cycles |
| Success | Correct startup language selection/correction; M8 self-service or a confirmed language-appropriate handoff |

Assertions: after language lock no primary-language response unless explicitly requested; if unsupported by M8, use `secondary_language_live_agent`; never invent translations of compliance strings. Add initial-language mismatch, ambiguous detection, unsupported language, explicit switch, no localized copy, wrong-language content, and unavailable language-queue variants. Transcript checks distinguish approved startup correction from unwanted later degradation.

### Cross-journey cases required in addition to the seven examples

Test billing → cancellation; any flow → fraud; lost phone with and without fraud; simultaneous fraud and human request; any flow → explicit human request; payment/order in flight → “stop”; account A → account B after verification; two intents in one utterance; notice playback with attempted barge-in; retry threshold plus higher-priority signal on the same event; and human-transfer failure after an unresolved financial operation. Assertions must inspect tool traces, final operation state, and transport outcomes, not only plausible dialogue.

## Section 20 — Priority Hierarchy

Retain the original ten levels, but make their interaction with playback, authentication, and transaction state explicit. The resolver chooses one winning conversation action per event. It never removes security requirements or changes an already submitted operation's factual state.

1. **Safety signals.** Apply the approved category-specific rule below. Stop new account actions.
2. **Fraud claim.** `empathy_protocol`, no new auth or self-service, handoff with `fraud_escalation`. Fraud plus a human request remains fraud, including after hours.
3. **System error.** Stop dependent work and hand off with `system_unavailable`, carrying any unknown operation outcome.
4. **Explicit human request.** Initiate human handoff without unnecessary identification or task completion.
5. **Business account.** Emit applicable business handoff and transfer before consumer self-service.
6. **Retry/auth failure.** Apply no-input, no-match, global validation, or auth limit and its handoff reason. Do not reset budgets to avoid transfer.
7. **Mandatory copy / language prerequisites.** Emit required approved strings; an unavailable translation/copy takes the defined fallback. No unauthorized mutation is possible even when another action has priority.
8. **Authenticated customer action.** Check backend permission, consent, and transaction prerequisites before acting. Excess refund limit, manual-only capability, and closed specialist queue take their defined alternatives.
9. **Disambiguation.** One targeted question per unresolved attempt, up to the specified budget.
10. **Small talk, recap, and closing.** Only after necessary work and pending intents are handled or declined.

**Protected playback is a transport rule, not a competing conversational priority — Lead guidance and A-06.** Once mandatory notice playback starts, barge-in is disabled for that short segment. The next delivered input is resolved by the hierarchy afterward. Do not start another disclosure or action merely to delay a known safety/fraud/human event. An unplayed opening notice is emitted as the required short preface to the selected handoff where the call remains connected. Transport loss is logged as incomplete notice; the system does not pretend it can compel a disconnected caller to listen. Any emergency policy exception to disclosure must be supplied by the client before enablement; none is silently assumed here.

**Safety categories — Assumption A-13; client Security owns final policy.**

| Category | Proposed behavior |
|---|---|
| Self-harm/distress requiring safety assistance | Empathy and immediate transfer to the client's approved 24/7 safety destination. Do not intentionally disconnect while a viable transfer exists. Use the original `fraud_escalation` only as a legacy transport code with `safety_category = self_harm` if platform mapping explicitly routes it to that safety destination. Do not treat this as a fraud allegation or count it as fraud in analytics. Without an approved mapping, a validated legacy safety route is a launch dependency. |
| Credible directed threat or malicious request | Approved polite closure and `malicious_input`, retain only permitted audit context. Threat classification must distinguish a caller making a threat from reporting or quoting someone else's threat. |
| Ordinary anger, frustration, non-threatening profanity, or fraud reporting | Continue the relevant help or fraud/human path; not malicious solely on these grounds. |
| Instructions embedded in retrieved content/tool errors | Ignore the instructions and treat them as untrusted data. Do not disconnect an innocent caller merely because retrieved material contains hostile text. |

Human transfer failure follows the finite transport fallback in Section 8 even for safety; it is recorded as a failure, not successful resolution. Production cannot launch a claimed safety/fraud service without a tested real destination. No routine customer-service queue is assumed qualified for safety cases merely because it is open 24/7.

## Section 21 — Testing & Evaluation Requirements

The original seven test layers remain. Test authoring is the engineer's responsibility. A detailed test definition is not evidence of implementation, and mocked success is not evidence that a real backend is available.

| Test kind | Purpose | Coverage target |
|---|---|---|
| Tool-contract tests | Real non-production and mock contracts, authorization, errors, status, idempotency, PII, localization | 100% of wired tools, with success and failure branches; separately prove every required launch capability is present |
| Per-turn preprocessing tests | Original four-step ordering plus safety resolution, protected playback, counter resets, provenance, same-turn tool errors | Happy and boundary cases for all four original stages and the added safety/transaction guards |
| Deterministic goldens | Exact approved copy, sensitive-value exclusion, handoff fields, reason codes and factual outcome claims | Every active copy key/locale/variant, all eleven reason codes, all terminal paths and protected state writes |
| Sim scenarios | All seven CUJs, negative paths, pivots, account switch, uncertainty, unavailable capabilities | At least 60% baseline and 90% pre-production on the agreed versioned suite; no substitution of fallback tests for required success journeys |
| Audio-mode audit | Real voice rendering, legal playback protection, language, spoken values, DTMF, secret handling | All P0 scenarios per release candidate |
| Telephony-loop test | Actual dial-in, transfer survival, playback completion, keypad provenance, recording output | Once per release, covering each distinct channel/brand/language integration and relevant terminal behavior |
| Compliance audit | Approved spoken copy and no prohibited data exposure, including audio/transcript/log/handoff/SMS boundaries | 50 calls per supported language, quarterly and after every verbatim change |

### Acceptance details added to remove ambiguity — Assumption A-14; lead response pending

- **Critical gates.** Safety, authentication, PII, truthful financial/operation outcomes, required notice delivery, and real handoff outcomes have zero permitted failures. Use P0 for these and the original highest-volume critical journeys. Report per-priority and per-module results alongside the flat rate. No average score can conceal a critical failure.
- **Original performance targets.** Keep at least 60% in-agent resolution and at most four minutes average agent handle time. Proposed resolution denominator is all genuine connected customer calls that express an in-scope request, including required human handoffs and dependency failures. Exclude synthetic tests, confirmed malicious/restricted calls, and disconnects before a request is understood; report these exclusions separately. Numerator requires every in-scope request in that call to be completed by the agent with backend evidence or a verified informational answer, no required transfer, and caller-confirmed completion. A restored-alert subscription does not resolve a “restore service” request, but can complete a caller's explicit “notify me” request. Report a secondary automation-eligible rate separately; do not use it to hide human-only scope.
- **Timing.** Measure agent handle time from connection/start of automated intake to confirmed queue/legacy takeover or call disconnection, including authentication, disclosures, tool latency, retries, and unresolved transfer attempts. Report mean plus tail latency and segment by outcome. Time spent in a human queue after confirmed takeover is outside AI handle time. Simulator turn counts are not elapsed-time measurements.
- **Compliance and recording.** Require 100% exact approved text for audited completed disclosures and truthful slot substitution. Report every incomplete/disconnected playback separately; it is not counted as a completed notice. Every connected call must yield its `.wav` audit artifact under approved sensitive-segment handling, including transferred and prematurely ended calls. Require zero prohibited PII/credential exposure across the audit set. Unexpected missing recordings or a missing required notice on a continuing call is a release failure.
- **Regression.** No P0 regression for two consecutive deploys, retaining the original target. Pin agent/model/config/copy/tool versions and evaluator versions in each result. Reset the regression baseline when those behavior-affecting components change.
- **Volume-weighted reporting.** In addition to the required flat pass rate, compute each module's eligible test pass rate and multiply by its fixed original volume share, then sum. Do not multiply every scenario by the module share without normalizing within its module. CUJ-7 is included within M4's slice; cross-cutting safety/auth requirements have separate gates and are not an extra traffic percentage.
- **Suite changes.** The earlier addendum proposes excluding 15 public simulations that conflict with its security handoffs. This draft does not silently apply those exclusions. Product/security and the evaluation owner must approve the exact IDs, conflicting clauses, replacement assertions, and revised denominator. Report original-suite and approved-suite results separately. Failed behavior is not relabeled infrastructure failure. Quota/infrastructure-blocked runs are reported and rerun; they do not count as passes or establish a release gate.
- **Mocks and reconstruction.** Version named success/failure fixtures. Prove no mock traffic reaches production and no production input enables mocks. Test auth through the tools. The clipped PDF examples have been completed in Section 19, but any disputed source detail requires an explicit assumption change rather than a silently invented expected answer.
- **Traceability.** Every BR-TV requirement, assumption, mandatory copy condition, enabled capability, negative transaction state, and handoff outcome must have a named check. Test tool ordering through traces/callback checks, not only an LLM reading the transcript. A feature blocked by missing policy/copy/tool stays visibly blocked until supplied or an explicit scope reduction is accepted.

### Assumptions and client-owned dependencies

The business lead answered platform language behavior, the relationship between account and on-file contact, callback-controlled barge-in, and backend ownership of financial conditions. The lead skipped theft/fraud, did not settle password-reset authentication, treated launch scope/copy/data questions as client discovery, and deferred transaction/evaluation answers. The following table prevents those unanswered items from being presented as business approval.

| ID | Proposed rule / what it closes | Authority and owner | Required before affected production use |
|---|---|---|---|
| A-01 | Configured initial locale; detect/correct first input; then lock; approved unsupported-language path | Platform detection is lead guidance; startup/scope/fallback details are assumptions. Product and language/Legal owners. | Actual voice locales and model/channel support; default per dialed number; approved translations/fallback; human-language coverage and startup exception approval |
| A-02 | Trusted pre-call service region or omit targeted advisory; account service region later; no blocklist fail-open | Proposed integration policy. Telephony/platform and client security. | Region provenance, legal-default mapping, blocklist/legacy intake contracts, public advisory behavior |
| A-03 | Authenticate password-reset dispatch; OTP speech/keypad; PIN native keypad; on-file contact only; shared attempt budget | On-file contact/account relationship clarified by lead; reset/modes/fallback policy remains proposed. Client security/identity owner. | Approval of reset auth exception removal, factor channels, PIN access policy, identity/account/challenge contracts, capture protection |
| A-04 | Verification bound to account/service; explicit step-up; handoff for undefined sensitive changes | Proposed security completion. Client security/platform. | Auth freshness, authorized actor/service scope, profile field allowlist, step-up policy and contracts |
| A-05 | Theft plus fraud transfers without suspension; theft alone suspends only after verification | Explicitly skipped by lead; proposed conservative behavior from hierarchy/addendum. Client fraud/security. | Written approval of protective-suspension and fraud overlap policy; verified fraud handoff |
| A-06 | Disable barge-in on legal notice; track completion; finite playback failure behavior | Non-interruptible callback is lead guidance; enforced via `root_agent` `handle_legal_notice` callback. Platform/Legal. | End-to-end playback-control proof, copy/notice regional approval, interruption/transport-loss tests |
| A-07 | Explicit AI/phone outcomes; closed-queue instructions; bounded handoff failures; compatible reason codes | Proposed operational policy, not answered by lead. Contact-center/platform/product. | Reason/context-to-queue map, acceptance/status signals, hours/timezones, alternate paths and approved terminal copy |
| A-08 | Backend authorizes eligible amount/type/limit/timing and restoration; no hardcoded dunning rules | Backend authority endorsed by lead; specific contract and copy details proposed. Billing/finance/platform/Legal. | Real eligibility/execution/restoration contracts, policy/version/freshness, type-specific copy, exact arrangement treatment |
| A-09 | Explicit consent; durable operation state; stop/reconcile behavior; no blind retry after uncertainty | Lead response pending. Product/backend operations/security. | Commit/cancel/status/idempotency contracts, durable reconciliation ownership, disconnect/late-result handling |
| A-10 | Recognize all intents; per-intent conditional automation/manual scope; no fictitious capabilities | Client discovery acknowledged, no launch scope approved. Product and each backend owner. | Signed launch matrix, real availability evidence, policies for appointment dispatch, equipment, porting/cancellation and Guest sales; revised targets if scope reduced |
| A-11 | SMS dispatch versus delivery; durable notification subscription; speech/handoff when unavailable | Proposed completion of original SMS journeys. Messaging/product. | Destination consent policy, delivery/status contract, subscription/waitlist/callback ownership and approved outage-only copy |
| A-12 | Explicit handoff allowlist, credential exclusion, immediate text masking, approved audio policy | Lead noted DLP for text but did not approve data policy. Client security/privacy/Legal. | Accepted allowlist and data-retention/access/residency rules; all-sink tests; secure audio/DTMF capture; recording-objection handling |
| A-13 | Separate distress/self-harm, threats, malicious inputs, fraud, and anger; tested appropriate human destinations | Proposed safety policy informed by addendum, not approved by this lead response. Client safety/security/contact center. | Category examples and approved actions/copy; qualified destination mapping; legacy reason-code compatibility; failure behavior |
| A-14 | Measurable resolution/AHT denominators, critical gates, honest exclusions, replacement tests, real idempotency proof | Lead response pending; original numeric targets retained. Product/QA/operations. | Metric definitions accepted, versioned complete suite, exact approved exclusions if any, real integration evidence and two-deploy regression history |

### Release readiness and definition of done

Development may proceed with synthetic fixtures and the stated assumptions. A client-owned missing value must be supplied through configuration/contract, not guessed by an agent. A missing approval for an account mutation keeps that mutation disabled and exercises its specified handoff. Missing global intake, legal notice, safety/transfer, or data-protection prerequisites block the affected deployment; no silent fail-open behavior is acceptable.

A production-ready Telco Voice Central meets the original targets: **at least 60% in-agent resolution; at most four minutes average handle time; 100% verbatim compliance on audited applicable strings; zero prohibited PII exposure in the audit set; 100% recording-artifact coverage; and no P0 regressions for two consecutive deploys.** It also has approved client language/security/financial/data policies, all required launch capabilities verified, and demonstrated handling of unknown transactions, real handoff failure, and unavailable messaging/copy. The team cannot mark these dependencies complete merely because this document assigns a fallback.

**What this draft closes.** Each previously ambiguous behavior now has an explicit proposed rule, deterministic fallback, test expectation, and owner where a client decision is still required. It does not claim that unprovided client decisions, approved copy, live tools, or production test evidence have been supplied.
