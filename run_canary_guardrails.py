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

TARGET_FILES = [
    "sim__report_fraud_identity_theft.yaml",
    "sim__report_fraud_stolen_phone.yaml",
    "sim__report_fraud_unauthorized_charges.yaml",
    "sim__warranty_claim_fraud_pivot.yaml",
    "sim__request_secondary_language.yaml",
    "sim__request_during_troubleshooting.yaml",
    "sim__request_after_billing_query.yaml",
    "sim__enable_mfa_secondary_language.yaml",
    "sim__restore_service_non_payment.yaml",
    "sim__restore_service_already_active.yaml",
    "sim__reschedule_technician_appointment.yaml",
    "sim__cancel_service_moving.yaml",
    "sim__hard_04_system_down_degradation.yaml",
]

BASELINE_FILES = [
    "sim__report_fraud_mid_call_discovery.yaml",
    "sim__immediate_request.yaml",
    "sim__password_reset_happy_path.yaml",
    "sim__enable_mfa_happy_path.yaml",
    "sim__pay_my_bill.yaml",
    "sim__restore_service_lost_stolen_found.yaml",
    "sim__troubleshoot_internet_tv_phone_service_issues.yaml",
    "sim__book_technician_appointment.yaml",
    "sim__tech_status_happy_path.yaml",
    "sim__upgrade_my_plan_add_new_services.yaml",
    "sim__file_warranty_claim_defective_device.yaml",
    "sim__transfer_number_happy_path.yaml",
]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--targets-only", action="store_true", help="Run only the 13 target regression tests")
    parser.add_argument("--baselines-only", action="store_true", help="Run only the 12 baseline regression tests")
    parser.add_argument("--rpm", type=float, default=5.0, help="Requests per minute")
    parser.add_argument("--files", nargs="+", help="Specific YAML files to run")
    args = parser.parse_args()

    if args.files:
        files = args.files
        mode_desc = f"Custom ({len(files)} files)"
    elif args.targets_only:
        files = TARGET_FILES
        mode_desc = f"Targets Only ({len(files)} files)"
    elif args.baselines_only:
        files = BASELINE_FILES
        mode_desc = f"Baselines Only ({len(files)} files)"
    else:
        files = TARGET_FILES + BASELINE_FILES
        mode_desc = f"Full Canary Suite ({len(files)} files: 13 targets + 12 baselines)"

    output_dir = "eval-reports/canary_guardrails"
    os.makedirs(output_dir, exist_ok=True)

    print(f"=== Starting Canary Guardrail Suite: {mode_desc} ===")
    print(f"Target files: {files}")
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

    new_sims = run_results.get("simulation", [])
    for s in new_sims:
        existing_sims[s.get("name")] = s

    all_merged = list(existing_sims.values())
    with open(sim_json_path, "w") as f:
        json.dump(all_merged, f, indent=2)

    generate_combined_report_from_dir(
        output_dir=output_dir,
        app_name=app_name,
        run=False,
    )

    print(f"\n=== Canary Guardrails Results Summary ===")
    target_names = [os.path.splitext(f)[0] for f in files]
    filtered_sims = [s for s in all_merged if s.get("name") in target_names]
    passed = [s for s in filtered_sims if s.get("passed") is True]
    failed = [s for s in filtered_sims if s.get("passed") is False and "429" not in str(s.get("error", ""))]
    quota_failed = [s for s in filtered_sims if "429" in str(s.get("error", ""))]

    print(f"Total Evaluated in this run: {len(filtered_sims)}")
    print(f"Passed: {len(passed)}")
    print(f"Failed (Behavioral): {len(failed)}")
    print(f"Incomplete (Quota 429): {len(quota_failed)}")

    for s in filtered_sims:
        status = "PASSED" if s.get("passed") else ("QUOTA_429" if "429" in str(s.get("error", "")) else "FAILED")
        print(f"  [{status}] {s.get('name')}: {s.get('error', 'All expectations met')}")

    if len(failed) > 0 or len(quota_failed) > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
