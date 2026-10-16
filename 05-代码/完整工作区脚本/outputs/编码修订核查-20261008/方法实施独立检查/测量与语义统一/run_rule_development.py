"""Run a fixed development packet once; keep every output and failure."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
import time
import traceback

sys.dont_write_bytecode = True
parser = argparse.ArgumentParser()
parser.add_argument('--runtime', type=Path, required=True)
parser.add_argument('--input', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--expected-n', type=int, required=True)
args = parser.parse_args()
runtime = args.runtime.resolve()
rows = [json.loads(s) for s in args.input.read_text().splitlines()]
assert len(rows) == args.expected_n
assert len({r['id'] for r in rows}) == len(rows)
assert not args.output.exists(), 'Refuse to overwrite a completed or partial execution.'
summary_path = args.output.with_suffix('.execution.json')
assert not summary_path.exists()
digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
freeze = {p.name: digest(p) for p in runtime.glob('*.py')}
sys.path.insert(0, str(runtime))
from policy_coding_v27 import code_unit

start = time.time()
results = []
with args.output.open('x') as output:
    for row in rows:
        try:
            result = code_unit(copy.deepcopy(row['input']))
            payload = {'id': row['id'], 'status': 'completed', 'result': result}
        except Exception as error:
            payload = {'id': row['id'], 'status': 'failed', 'error_type': type(error).__name__,
                       'error': str(error), 'traceback': traceback.format_exc()}
        output.write(json.dumps(payload, ensure_ascii=False) + '\n')
        output.flush()
        results.append(payload)
after = {p.name: digest(p) for p in runtime.glob('*.py')}
summary = {
    'purpose': 'fixed_development_packet_not_independent_validation',
    'python_executable': sys.executable, 'runtime': str(runtime),
    'input': str(args.input.resolve()), 'input_sha256': digest(args.input),
    'runtime_before_sha256': freeze, 'runtime_unchanged_during_execution': freeze == after,
    'output_sha256': digest(args.output), 'n': len(results),
    'completed': sum(r['status'] == 'completed' for r in results),
    'failed': sum(r['status'] == 'failed' for r in results),
    'unresolved': sum(r.get('result', {}).get('judgement_status') == 'undetermined' for r in results),
    'elapsed_seconds': time.time() - start,
    'reference_labels_used': False,
}
summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({k: summary[k] for k in ['n', 'completed', 'failed', 'unresolved',
      'runtime_unchanged_during_execution', 'elapsed_seconds']}, ensure_ascii=False))
sys.exit(0 if summary['failed'] == 0 and freeze == after else 1)
