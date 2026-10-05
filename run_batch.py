import argparse
import json
import os
import sys
import time
from cxas_scrapi.evals.runner import run_all_evals
from cxas_scrapi.evals.simulation_evals import SimulationEvals
from cxas_scrapi.utils.rate_limiter import RateLimiter
from cxas_scrapi.utils.reporting import generate_combined_report_from_dir
from cxas_scrapi.utils.gemini import GeminiGenerate

def _robust_generate(self, prompt=None, audio_path=None, audio_bytes=None, system_prompt=None, model_name=None, response_mime_type=None, response_schema=None, temperature=1.0, thinking_level=None):
    max_retries = 6
    for attempt in range(max_retries):
        try:
            target_model = model_name or self.model_name
            config = self._build_generation_config(
                system_prompt=system_prompt,
                response_mime_type=response_mime_type,
                response_schema=response_schema,
                temperature=temperature,
                thinking_level=thinking_level,
            )
            contents = self._build_contents(prompt, audio_path, audio_bytes)
            response = self.client.models.generate_content(
                model=target_model, contents=contents, config=config
            )
            if response_mime_type == "application/json" and response_schema:
                return response.parsed
            return response.text
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                wait_time = (attempt + 1) * 15
                print(f"\n[RateLimit 429] Encountered quota limit. Backing off {wait_time}s (retry {attempt+1}/{max_retries})...")
                time.sleep(wait_time)
                continue
            raise e
    return None

GeminiGenerate.generate = _robust_generate

BATCHES = {
    1: {
        "name": "Fraud handling",
        "dir": "eval-reports/batch_01_fraud",
        "files": [
            "sim__report_fraud_identity_theft.yaml",
            "sim__report_fraud_stolen_phone.yaml",
            "sim__report_fraud_unauthorized_charges.yaml",
            "sim__report_fraud_mid_call_discovery.yaml",
            "sim__report_fraud_upset.yaml",
            "sim__warranty_claim_fraud_pivot.yaml",
        ],
    },
    2: {
        "name": "Human handoff",
        "dir": "eval-reports/batch_02_human_handoff",
        "files": [
            "sim__immediate_request.yaml",
            "sim__request_dtmf.yaml",
            "sim__request_secondary_language.yaml",
            "sim__request_during_troubleshooting.yaml",
            "sim__request_after_billing_query.yaml",
            "sim__request_after_hours_fraud.yaml",
        ],
    },
    3: {
        "name": "Password reset",
        "dir": "eval-reports/batch_03_password_reset",
        "files": [
            "sim__password_reset_happy_path.yaml",
            "sim__password_reset_mobile_fallback.yaml",
            "sim__password_reset_otp_failure.yaml",
            "sim__password_reset_business_account.yaml",
            "sim__password_reset_mid_call_pivot.yaml",
        ],
    },
    4: {
        "name": "Multi-factor authentication",
        "dir": "eval-reports/batch_04_mfa",
        "files": [
            "sim__enable_mfa_happy_path.yaml",
            "sim__disable_mfa_happy_path.yaml",
            "sim__disable_mfa_auth_failure.yaml",
            "sim__mfa_vague_request.yaml",
            "sim__enable_mfa_secondary_language.yaml",
        ],
    },
    5: {
        "name": "Billing and payments",
        "dir": "eval-reports/batch_05_billing_payments",
        "files": [
            "sim__dispute_charge_my_bill.yaml",
            "sim__pay_my_bill.yaml",
            "sim__request_refund_credit.yaml",
            "sim__set_up_autopay.yaml",
        ],
    },
    6: {
        "name": "Service restoration",
        "dir": "eval-reports/batch_06_service_restoration",
        "files": [
            "sim__restore_service_non_payment.yaml",
            "sim__restore_service_lost_stolen_found.yaml",
            "sim__restore_service_refuse_payment.yaml",
            "sim__restore_service_already_active.yaml",
            "sim__restore_service_business_account.yaml",
        ],
    },
    7: {
        "name": "Technical support and SIM/device access",
        "dir": "eval-reports/batch_07_tech_sim",
        "files": [
            "sim__troubleshoot_internet_tv_phone_service_issues.yaml",
            "sim__phone_locked_puk_code.yaml",
            "sim__sim_issue_input_retry.yaml",
            "sim__resolve_sim_card_locked_phone_issues.yaml",
            "sim__damaged_sim_replacement.yaml",
            "sim__carrier_unlock_request.yaml",
            "sim__hard_01_blocklist_deflection.yaml",
        ],
    },
    8: {
        "name": "Appointment booking and changes",
        "dir": "eval-reports/batch_08_appointments",
        "files": [
            "sim__book_technician_appointment.yaml",
            "sim__reschedule_technician_appointment.yaml",
            "sim__cancel_appointment_en_route.yaml",
            "sim__cancel_appointment_same_day.yaml",
            "sim__appointment_availability_sms_callback.yaml",
            "sim__hard_02_disambiguation_ladder.yaml",
        ],
    },
    9: {
        "name": "Technician and ticket status",
        "dir": "eval-reports/batch_09_tech_status",
        "files": [
            "sim__tech_status_happy_path.yaml",
            "sim__tech_status_multiple_appointments.yaml",
            "sim__tech_status_en_route_cancel.yaml",
            "sim__check_status_technician_visit_ticket.yaml",
            "sim__ticket_status_happy_path.yaml",
            "sim__ticket_status_found.yaml",
        ],
    },
    10: {
        "name": "Sales and upgrades",
        "dir": "eval-reports/batch_10_sales_upgrades",
        "files": [
            "sim__upgrade_my_plan_add_new_services.yaml",
            "sim__add_streaming_service_addon.yaml",
            "sim__upgrade_plan_business_handoff.yaml",
            "sim__upgrade_plan_after_hours.yaml",
            "sim__add_tv_service_existing.yaml",
            "sim__upgrade_mobile_plan_data.yaml",
        ],
    },
    11: {
        "name": "Warranty",
        "dir": "eval-reports/batch_11_warranty",
        "files": [
            "sim__file_warranty_claim_defective_device.yaml",
            "sim__warranty_claim_defective_battery.yaml",
            "sim__warranty_claim_out_warranty.yaml",
            "sim__warranty_claim_physical_damage_rejection.yaml",
        ],
    },
    12: {
        "name": "Cancellation and retention",
        "dir": "eval-reports/batch_12_cancellation",
        "files": [
            "sim__cancel_service_moving.yaml",
            "sim__cancel_service_auth_retry.yaml",
            "sim__cancel_business_account_redirection.yaml",
            "sim__cancel_service_after_hours.yaml",
            "sim__port_out_mobile_number.yaml",
            "sim__bill_dispute_cancellation_pivot.yaml",
        ],
    },
    13: {
        "name": "Number transfer",
        "dir": "eval-reports/batch_13_number_transfer",
        "files": [
            "sim__transfer_my_phone_number_another_carrier.yaml",
            "sim__transfer_number_missing_pin.yaml",
            "sim__transfer_number_business_block.yaml",
            "sim__transfer_number_happy_path.yaml",
        ],
    },
    14: {
        "name": "Additional edge & hard scenarios",
        "dir": "eval-reports/batch_14_edge_hard",
        "files": [
            "sim__sim_working_happy_path.yaml",
            "sim__book_reschedule_cancel_technician_appointment.yaml",
            "sim__hard_03_silence_timeout_ladder.yaml",
            "sim__hard_04_system_down_degradation.yaml",
            "sim__hard_05_interrupted_recording_notice_replay.yaml",
        ],
    },
}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", type=int, required=True, help="Batch number (1-14)")
    parser.add_argument("--rpm", type=float, default=6.0, help="Requests per minute")
    parser.add_argument("--test-single", action="store_true", help="Run only the first file in the batch")
    parser.add_argument("--files", nargs="+", help="Specific YAML file names to run")
    args = parser.parse_args()

    batch_info = BATCHES[args.batch]
    output_dir = batch_info["dir"]
    os.makedirs(output_dir, exist_ok=True)
    if args.files:
        files = args.files
    elif args.test_single:
        files = batch_info["files"][:1]
    else:
        files = batch_info["files"]

    print(f"=== Starting Batch {args.batch}: {batch_info['name']} ===")
    print(f"Target files ({len(files)}): {files}")
    print(f"Output directory: {output_dir}")
    print(f"Rate limiter pacing: {args.rpm} RPM (1 request every {60.0/args.rpm:.1f}s)")

    limiter = RateLimiter(requests_per_minute=args.rpm)
    SimulationEvals.max_retries = 5
    SimulationEvals.retry_delay_base = 3

    app_name = "projects/gcp-i-and-d-practitioners/locations/us/apps/maryam-telco-voice-central"

    sim_json_path = os.path.join(output_dir, "sim_results.json")
    existing_sims = {}
    if os.path.exists(sim_json_path):
        try:
            with open(sim_json_path, "r") as f:
                for item in json.load(f):
                    existing_sims[item.get("name")] = item
        except Exception:
            pass

    run_results = run_all_evals(
        app_name=app_name,
        simulation_dir="evals/simulations",
        output_dir=output_dir,
        filter_files=files,
        include=["sims"],
        parallel=1,
        rate_limiter=limiter,
        use_tool_fakes=True,
    )

    # Merge new results into existing_sims
    new_sims = run_results.get("simulation", [])
    for s in new_sims:
        existing_sims[s.get("name")] = s

    all_merged = list(existing_sims.values())
    with open(sim_json_path, "w") as f:
        json.dump(all_merged, f, indent=2)

    # Generate combined report HTML
    generate_combined_report_from_dir(
        output_dir=output_dir,
        app_name=app_name,
        run=False,
    )

    print(f"\n=== Batch {args.batch} Results Summary ===")
    sims = all_merged
    passed = [s for s in sims if s.get("passed") is True]
    failed = [s for s in sims if s.get("passed") is False and "429" not in str(s.get("error", ""))]
    quota_failed = [s for s in sims if "429" in str(s.get("error", ""))]

    print(f"Total Evaluations: {len(sims)}")
    print(f"Passed: {len(passed)}")
    print(f"Failed (Behavioral): {len(failed)}")
    print(f"Incomplete (Quota 429): {len(quota_failed)}")

    for s in sims:
        status = "PASSED" if s.get("passed") else ("QUOTA_429" if "429" in str(s.get("error", "")) else "FAILED")
        print(f"  [{status}] {s.get('name')}: {s.get('error', 'All expectations met')}")

    if len(failed) > 0 or len(quota_failed) > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()

