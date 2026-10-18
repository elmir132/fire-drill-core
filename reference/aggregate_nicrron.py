"""Summarise results_nicrron/*.json into a table and a JSON file (results_nicrron/summary.json).

Counts come only from the verifier JSON of the real runs. One row per model: runs and unsafe runs with the guardrail off and on.
"""
import glob
import json
import os
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "results_nicrron")


def main():
    rows = defaultdict(lambda: {"off": [], "on": [], "strict": []})
    for f in sorted(glob.glob(os.path.join(OUT, "*_*_*.json"))):
        r = json.load(open(f))
        rows[r["model"]][r["guardrail"]].append(r)
    summary = []
    for model, d in rows.items():
        entry = {"model": model}
        for mode in ("off", "on", "strict"):
            runs = d[mode]
            entry[mode] = {"runs": len(runs), "unsafe": sum(1 for r in runs if not r["safe"]),
                           "double_refunds": sum(1 for r in runs if r["duplicate_refunds"] > 0),
                           "avg_score": round(sum(r["score"] for r in runs) / len(runs), 1) if runs else None,
                           "tokens_in": sum(r.get("tokens_in", 0) for r in runs), "tokens_out": sum(r.get("tokens_out", 0) for r in runs)}
        summary.append(entry)
    summary.sort(key=lambda e: (-e["off"]["unsafe"], e["model"]))
    json.dump(summary, open(os.path.join(OUT, "summary.json"), "w"), indent=2, sort_keys=True)
    print(f"{'model':36} {'off: unsafe/runs':>18} {'on: unsafe/runs':>16} {'strict: unsafe/runs':>20}")
    for e in summary:
        print(f"{e['model']:36} {e['off']['unsafe']:>9}/{e['off']['runs']:<8} {e['on']['unsafe']:>8}/{e['on']['runs']:<7} {e['strict']['unsafe']:>10}/{e['strict']['runs']:<8}")
    print("total runs:", sum(e["off"]["runs"] + e["on"]["runs"] + e["strict"]["runs"] for e in summary))


if __name__ == "__main__":
    main()
