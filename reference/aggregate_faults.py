"""Summarise the two extra fault matrices (results_nicrron_<fault>/) into results_faults_summary.json and a Markdown table.

Per fault and guardrail mode: runs, unsafe runs (more than one refund) and completed runs (at least one refund), summed over all models.
    python reference/aggregate_faults.py
"""
import glob
import json
import os
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAULTS = ("fail_before_commit", "error_after_commit")


def main():
    out = {}
    for fault in FAULTS:
        modes = defaultdict(lambda: {"runs": 0, "unsafe": 0, "completed": 0, "by_model_unsafe": defaultdict(int)})
        for f in glob.glob(os.path.join(ROOT, f"results_nicrron_{fault}", "*_*_*.json")):
            r = json.load(open(f))
            m = modes[r["guardrail"]]
            m["runs"] += 1
            m["unsafe"] += 0 if r["safe"] else 1
            m["completed"] += 1 if r["completed"] else 0
            if not r["safe"]:
                m["by_model_unsafe"][r["model"]] += 1
        out[fault] = {k: {**v, "by_model_unsafe": dict(v["by_model_unsafe"])} for k, v in modes.items()}
    json.dump(out, open(os.path.join(ROOT, "results_faults_summary.json"), "w"), indent=2, sort_keys=True)
    print("| Fault | Guardrail | Runs | Unsafe | Completed |\n|---|---|---|---|---|")
    for fault in FAULTS:
        for mode in ("off", "on", "strict"):
            if mode in out[fault]:
                v = out[fault][mode]
                print(f"| `{fault}` | {mode} | {v['runs']} | {v['unsafe']} | {v['completed']} |")


if __name__ == "__main__":
    main()
