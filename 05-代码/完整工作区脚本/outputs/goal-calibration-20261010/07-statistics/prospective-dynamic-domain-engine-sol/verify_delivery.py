"""Read-only byte verification against an externally supplied delivery SHA."""
import argparse
import hashlib
import json
from pathlib import Path


def binding(path):
    p = Path(path).resolve()
    raw = p.read_bytes()
    return {'path': str(p), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected-seal-sha', required=True)
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    seal_path = here / 'output-seal.json'
    if binding(seal_path)['sha256'] != args.expected_seal_sha:
        raise ValueError('Delivery seal differs from ROOT/external expected SHA')
    seal = json.loads(seal_path.read_text())
    checks = [{'path': b['path'], 'equal': binding(b['path']) == b} for b in seal['output_members']]
    if not all(c['equal'] for c in checks):
        raise ValueError('Sealed delivery member changed')
    frozen = json.loads((here / 'input-bindings.json').read_text())['frozen_inputs']
    if not all(binding(b['path']) == b for b in frozen.values()):
        raise ValueError('Frozen upstream input changed')
    print(json.dumps({'delivery_seal_sha256': args.expected_seal_sha,
                      'members_checked': len(checks), 'all_equal': True,
                      'frozen_inputs_checked': len(frozen), 'actual_statistics_executed_N': 0,
                      'main_LLM_output_files_accessed_N': 0}))


if __name__ == '__main__':
    main()
