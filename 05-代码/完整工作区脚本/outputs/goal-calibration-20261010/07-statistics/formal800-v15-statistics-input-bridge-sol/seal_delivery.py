"""Seal only owned delivery files and authorized read-only implementation inputs."""
from pathlib import Path
import hashlib
import json
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def item(path):
    path = Path(path).resolve()
    return {'absolute_path': str(path), 'bytes': path.stat().st_size,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def write_exclusive(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def main():
    paths = [ROOT / p for p in (
        '02-methods/prospective-statistical-contract-v2/validation-design-v2.json',
        '05-validation/full800-common-v15-prerelease-sol/coordinator-private/draw-contract.json',
        '05-validation/full800-common-v15-prerelease-sol/coordinator-private/mapping.json',
        '07-statistics/prospective-engine-domain-sol/metrics_engine.py',
        '07-statistics/prospective-engine-domain-sol/input-contract.json',
        '07-statistics/prospective-engine-year-independent-audit-sol/metrics_engine_repaired.py',
        '07-statistics/prospective-engine-year-independent-audit-sol/input-contract-repaired.json',
        '07-statistics/prospective-engine-year-independent-audit-sol/README.md',
        '05-validation/formal800-xlsx-reception-adapter-sol/adapter.py',
        '05-validation/formal800-xlsx-reception-adapter-sol/derived-row.schema.json')]
    write_exclusive(HERE / 'input-seal.json', {'status': 'read_only_management_and_existing_interfaces',
                    'inputs': [item(path) for path in paths],
                    'prohibited_materials_not_read': ['policy body', 'human coding values', 'machine coding values', 'development77 results'],
                    'hashes_authenticate_human_identity': False, 'new_submissions_received': 0})
    members = [item(path) for path in sorted(HERE.rglob('*')) if path.is_file() and
               path.name != 'output-seal.json' and '__pycache__' not in path.parts]
    write_exclusive(HERE / 'output-seal.json', {'status': 'prepared_unfilled_bridge_delivery_not_a_result',
                    'members': members, 'self_excluded': True, 'overwrite_allowed': False})
    print(json.dumps({'sealed_members': len(members), 'output_seal': str(HERE / 'output-seal.json')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
