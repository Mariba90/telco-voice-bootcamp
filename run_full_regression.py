import argparse
import json
import os
import subprocess
import sys
import time

BATCHES = [
    (1, "Fraud handling"),
    (2, "Human handoff"),
    (3, "Password reset"),
    (4, "Multi-factor authentication"),
    (5, "Billing and payments"),
    (6, "Service restoration"),
    (7, "Technical support and SIM/device access"),
    (8, "Appointment booking and changes"),
    (9, "Technician and ticket status"),
    (10, "Sales and upgrades"),
    (11, "Warranty"),
    (12, "Cancellation and retention"),
    (13, "Number transfer"),
    (14, "Additional edge & hard scenarios"),
]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-batch", type=int, default=1, help="Starting batch number (1-14)")
    parser.add_argument("--end-batch", type=int, default=14, help="Ending batch number (1-14)")
    parser.add_argument("--rpm", type=float, default=5.0, help="RPM pacing for evaluations")
    parser.add_argument("--batches", nargs="+", type=int, help="Specific batch numbers to run")
    args = parser.parse_args()

    python_exe = sys.executable

    if args.batches:
        selected_batches = [b for b in BATCHES if b[0] in args.batches]
    else:
        selected_batches = [b for b in BATCHES if args.start_batch <= b[0] <= args.end_batch]

    print(f"=== FULL REGRESSION AUDIT SWEEP ===")
    print(f"Batches to execute: {[b[0] for b in selected_batches]}")
    print(f"Pacing: {args.rpm} RPM")
    print(f"Python interpreter: {python_exe}\n")

    summary_results = {}
    total_start = time.time()

    for batch_num, batch_name in selected_batches:
        print(f"\n==================================================")
        print(f"Executing Batch {batch_num}: {batch_name}")
        print(f"==================================================")
        cmd = [
            python_exe,
            "run_batch.py",
            "--batch", str(batch_num),
            "--rpm", str(args.rpm)
        ]
        batch_start = time.time()
        result = subprocess.run(cmd, capture_output=False)
        duration = time.time() - batch_start
        passed = (result.returncode == 0)
        summary_results[batch_num] = {
            "name": batch_name,
            "passed": passed,
            "duration": duration,
            "returncode": result.returncode
        }
        print(f"\nBatch {batch_num} completed in {duration:.1f}s. Result: {'PASS' if passed else 'FAIL'}")

    total_duration = time.time() - total_start
    print(f"\n\n==================================================")
    print(f"FULL REGRESSION AUDIT SUMMARY")
    print(f"Total Sweep Duration: {total_duration/60:.1f} minutes")
    print(f"==================================================")
    all_passed = True
    for b_num, b_name in selected_batches:
        info = summary_results[b_num]
        status = "PASSED" if info["passed"] else "FAILED"
        if not info["passed"]:
            all_passed = False
        print(f"Batch {b_num:02d} ({b_name}): [{status}] ({info['duration']:.1f}s)")

    print(f"==================================================")
    if all_passed:
        print("ALL BATCHES PASSED 100%! Regression sweep complete.")
        sys.exit(0)
    else:
        print("Some batches had failures. Please check individual batch reports.")
        sys.exit(1)

if __name__ == "__main__":
    main()

