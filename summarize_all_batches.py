import os
import glob
import json

base_dir = "eval-reports"
batch_dirs = sorted([d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))])

total_sims = 0
total_passed = 0
total_failed = 0

print(f"{'Batch Directory':<35} | {'Total':<6} | {'Passed':<6} | {'Failed':<6} | {'Pass Rate':<10}")
print("-" * 72)

for b_dir in batch_dirs:
    res_file = os.path.join(base_dir, b_dir, "sim_results.json")
    if not os.path.exists(res_file):
        continue
    try:
        with open(res_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            b_total = len(data)
            b_passed = sum(1 for s in data if s.get("passed", False))
            b_failed = b_total - b_passed
            total_sims += b_total
            total_passed += b_passed
            total_failed += b_failed
            rate = (b_passed / b_total * 100) if b_total > 0 else 0
            print(f"{b_dir:<35} | {b_total:<6} | {b_passed:<6} | {b_failed:<6} | {rate:>5.1f}%    ")
    except Exception as e:
        print(f"{b_dir:<35} | ERROR reading: {e}")

print("-" * 72)
overall_rate = (total_passed / total_sims * 100) if total_sims > 0 else 0
print(f"{'TOTAL':<35} | {total_sims:<6} | {total_passed:<6} | {total_failed:<6} | {overall_rate:>5.1f}%    ")

