#!/bin/bash
# Measured runs: 3 per mode for two Claude models on Bedrock, each in a fresh Daytona sandbox, each traced to Arize.
# Writes results/<model>_<mode>_<n>.json. Needs .env (Daytona, AWS, Arize). Costs a few cents of Bedrock tokens.
cd "$(dirname "$0")/.."
PY="${PYTHON:-python3}"
for pair in "haiku45:us.anthropic.claude-haiku-4-5-20251001-v1:0" "sonnet55:us.anthropic.claude-sonnet-5-5"; do
  tag="${pair%%:*}"; model="${pair#*:}"
  for mode in off on; do
    for n in 1 2 3; do
      echo "== $tag $mode $n"
      "$PY" reference/bedrock_agent_runner.py --guardrail $mode --model "$model" --out "results/${tag}_${mode}_${n}.json" 2>&1 | grep -E '^\{"guardrail"|FAILED|arize:|deleted'
    done
  done
done
echo MATRIX_DONE
