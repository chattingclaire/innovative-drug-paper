"""Write an integrity inventory, not an external timestamp/authenticity certificate."""
import hashlib
import importlib.metadata
import json
import platform
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def main():
    inputs = json.loads((ROOT / 'authorized-inputs.json').read_text(encoding='utf-8'))
    for item in inputs:
        if hashlib.sha256(Path(item['path']).read_bytes()).hexdigest() != item['sha256']:
            raise ValueError('authorized input changed; do not seal this version')
    checks = json.loads((ROOT / 'toy-verification.json').read_text(encoding='utf-8'))
    if not checks['passed'] or checks['actual_model_calls'] != 0 or checks['real_policy_units_coded'] != 0:
        raise ValueError('toy verification failed or claims real execution')
    files = []
    for path in sorted(ROOT.rglob('*')):
        if not path.is_file() or '__pycache__' in path.parts or path.name == '封存清单.json':
            continue
        raw = path.read_bytes()
        files.append({'path': str(path.relative_to(ROOT)), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
    manifest = {'status': 'protocol_and_offline_toy_verified_real_execution_pending',
                'sealed_at_utc': datetime.now(timezone.utc).isoformat(),
                'assigned_model': 'GPT-6.1 Sol', 'assigned_reasoning': 'ultra',
                'assignment_evidence': 'task instruction, not actual provider verification',
                'actual_provider_model_identity': None, 'actual_model_calls': 0, 'real_policy_units_coded': 0,
                'primary_repeats_executed': 0, 'perturbations_executed': 0,
                'toy_tests_passed': checks['tests_run'],
                'runtime': {'python': platform.python_version(), 'jsonschema': importlib.metadata.version('jsonschema')},
                'write_scope': str(ROOT), 'authorized_inputs': inputs,
                'files': files, 'external_timestamp_or_storage_authentication': None}
    from runner import implementation_sha256
    manifest['implementation_sha256'] = implementation_sha256()
    destination = ROOT / '封存清单.json'
    with destination.open('x', encoding='utf-8') as stream:
        json.dump(manifest, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps({'files': len(files), 'toy_tests_passed': checks['tests_run'], 'actual_model_calls': 0}, ensure_ascii=False))

if __name__ == '__main__':
    main()
