"""Turn results/*.json into the scoreboard data files (scoreboard/data/*.js and *.json).

Main comparison: the agent model in MAIN below (guardrail off vs on). Optional second model for the side note.
Counts come only from the verifier JSON of the real runs in results/.
"""
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN, OTHER = "haiku45", "sonnet55"


def load(tag, mode):
    runs = []
    for f in sorted(glob.glob(os.path.join(ROOT, "results", f"{tag}_{mode}_*.json"))):
        runs.append(json.load(open(f)))
    return runs


def summarize(runs):
    return {"runs_total": len(runs), "runs_unsafe": sum(1 for r in runs if not r["safe"])}


def main():
    out = os.path.join(ROOT, "scoreboard", "data")
    os.makedirs(out, exist_ok=True)
    for mode, var in (("off", "RESULTS_OFF"), ("on", "RESULTS_ON")):
        runs = load(MAIN, mode)
        if not runs:
            sys.exit(f"no results for {MAIN} {mode}")
        rep = dict(max(runs, key=lambda r: (not r["safe"]) == (mode == "off")))   # a representative run
        rep.update(summarize(runs))
        rep["note"] = f"{rep['model']} on Amazon Bedrock; real Daytona sandboxes; mock payment service; {len(runs)} runs per mode"
        json.dump(rep, open(os.path.join(out, f"results_{mode}.json"), "w"), indent=2, sort_keys=True)
        open(os.path.join(out, f"results_{mode}.js"), "w").write(f"window.{var} = " + json.dumps(rep, indent=2, sort_keys=True) + ";\n")
    other = {}
    for mode in ("off", "on"):
        runs = load(OTHER, mode)
        if runs:
            other[mode] = dict(summarize(runs), model=runs[0]["model"])
    open(os.path.join(out, "results_other.js"), "w").write("window.RESULTS_OTHER = " + json.dumps(other, indent=2, sort_keys=True) + ";\n")
    print("scoreboard data written:", {m: summarize(load(MAIN, m)) for m in ("off", "on")}, "other:", other)


if __name__ == "__main__":
    main()
