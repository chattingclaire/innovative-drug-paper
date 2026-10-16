#!/bin/bash
set -euo pipefail
if [ "$#" -ne 1 ]; then
  echo 'Usage: reproduce_v36_2.sh /absolute/path/to/new-output.jsonl' >&2
  exit 2
fi
TASK_RULE_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
TASK_R3_DIR="$(dirname -- "$TASK_RULE_DIR")"
exec /Users/rainbow/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  "$TASK_RULE_DIR/runtime/predict_batch.py" \
  --module-dir "$TASK_RULE_DIR/runtime" \
  --input "$TASK_R3_DIR/rule_inputs_shared_v14.jsonl" \
  --output "$1" \
  --version-expected v36.2-two-bounded-omissions-development \
  --freeze "$TASK_RULE_DIR/candidate_freeze.json"
