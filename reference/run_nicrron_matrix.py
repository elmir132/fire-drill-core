"""Run the Fire Drill matrix on many models behind the Nicrron gateway: N runs per model per guardrail mode, a few in parallel,
each in its own fresh Daytona sandbox. Results go to results_nicrron/<label>_<off|on>_<n>.json (existing files are skipped,
so an interrupted run can be resumed).

    python reference/run_nicrron_matrix.py [--runs 8] [--workers 4]
"""
import argparse
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results_nicrron"
RUNNER = ROOT / "reference" / "nicrron_agent_runner.py"
# openai/gpt-6-astra was tried and left out: through this gateway it only accepts tools on /v1/responses, which the gateway does not offer.
MODELS = [
    "anthropic/claude-fable-5-1", "anthropic/claude-opus-5-5", "openai/gpt-6-sol", "deepseek/deepseek-v4-pro",
    "moonshot/kimi-k3", "xai/grok-4.7", "z-ai/glm-5.3", "mistral/mistral-large-4", "anthropic/claude-haiku-5-5", "openai/gpt-6-luna",
]


def label(model):
    return model.split("/")[1].replace(".", "")


def one(job):
    model, mode, n = job
    out = OUT / f"{label(model)}_{mode}_{n}.json"
    if out.exists():
        return job, "skipped"
    for attempt in (1, 2):
        r = subprocess.run([sys.executable, str(RUNNER), "--guardrail", mode, "--model", model, "--out", str(out)], capture_output=True, text=True, timeout=900)
        if out.exists():
            return job, "ok"
    return job, "FAILED: " + (r.stderr.strip().splitlines() or ["?"])[-1][:160]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=8)
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    OUT.mkdir(exist_ok=True)
    jobs = [(m, mode, n) for n in range(1, a.runs + 1) for m in MODELS for mode in ("off", "on")]
    done = 0
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        for job, status in ex.map(one, jobs):
            done += 1
            print(f"[{done}/{len(jobs)}] {job[0]} {job[1]} #{job[2]}: {status}", flush=True)


if __name__ == "__main__":
    main()
