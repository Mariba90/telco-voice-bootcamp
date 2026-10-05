import json

with open("eval-reports/canary_guardrails/sim_results.json") as f:
    data = json.load(f)

for s in data:
    if not s.get("passed"):
        print("="*60)
        print(f"FAILED: {s['name']}")
        if not s.get("expectation_details"):
            print("  NO EXPECTATION DETAILS (possibly 429 or error)")
            continue
        for e in s.get("expectation_details", []):
            if e.get("status") != "Met":
                print(f"  [NOT MET] {e.get('expectation')}")
                print(f"    Reason: {e.get('justification')}")

