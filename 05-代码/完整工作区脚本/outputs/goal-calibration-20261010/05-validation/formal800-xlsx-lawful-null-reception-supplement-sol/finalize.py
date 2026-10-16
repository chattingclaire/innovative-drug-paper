"""Close this finite supplement and keep all old files frozen."""
import datetime
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PACKAGE = ROOT / '09-delivery/formal800-human-final-release-v2-20261010-sol'


def binding(path):
    raw = path.read_bytes()
    return {'path': str(path.resolve()), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def save(path, value):
    with path.open('x') as f:
        f.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


dependencies = json.loads((HERE / 'supplement-bindings.json').read_text())['dependencies']
for item in dependencies.values():
    assert binding(Path(item['path'])) == item
for p in HERE.rglob('*.py'):
    compile(p.read_text(), str(p), 'exec')
schema = json.loads((HERE / 'derived-row.schema.json').read_text())
schema['allOf'] = [
    {'if': {'properties': {'completion_status': {'const': 'lawful_null'}}}, 'then': {'properties': {'value': {'type': 'null'}, 'finished_judgment': {'const': True}, 'reason': {'type': 'string', 'minLength': 1}}}},
    {'if': {'properties': {'completion_status': {'const': 'filled'}}}, 'then': {'properties': {'value': {'type': 'integer', 'enum': [0, 1]}, 'finished_judgment': {'const': True}}}},
    {'if': {'properties': {'completion_status': {'enum': ['unfilled', 'incomplete']}}}, 'then': {'properties': {'value': {'type': 'null'}, 'finished_judgment': {'const': False}}}},
    {'if': {'properties': {'completion_status': {'const': 'invalid'}}}, 'then': {'properties': {'finished_judgment': {'const': False}}}},
]
(HERE / 'derived-row.schema.json').write_text(json.dumps(schema, ensure_ascii=False, indent=2) + '\n')
entries = {'adapter': binding(HERE / 'adapter.py'), 'bridge': binding(HERE / 'bridge.py'),
           'human_first_driver': binding(HERE / 'human_first_driver.py'),
           'derived_schema': binding(HERE / 'derived-row.schema.json'),
           'input_representation_supplement': binding(HERE / 'input-representation-supplement.txt'),
           'release_v2': binding(PACKAGE / 'release.json'),
           'release_v2_seal': binding(PACKAGE / 'seal.json'),
           'actual_human_submissions_N': 0, 'engine_analyze_called': False,
           'runtime_parameters': {'reception': 'receive --xlsx-a --xlsx-b --release --release-sha256 --declaration-a --declaration-b --out',
                                  'human_first': '--convert/--calculate --upstream-reception --statistics-metadata --statistics-metadata-sha256 --output-dir'}}
save(HERE / 'entrypoints.json', entries)
members = [binding(p) for p in sorted(HERE.rglob('*')) if p.is_file() and p.name != 'seal.json']
save(HERE / 'seal.json', {'version': 'formal800-lawful-null-input-supplement-seal-1',
                        'created_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                        'original_dependencies': dependencies, 'original_dependencies_unchanged': True,
                        'members': members, 'run_seals': [binding(p) for p in sorted((HERE / 'checks').rglob('seal.json'))],
                        'final_release_v2': binding(PACKAGE / 'release.json'), 'final_release_v2_seal': binding(PACKAGE / 'seal.json'),
                        'self_hash_policy': 'self excluded; run seal hashes separately retained',
                        'actual_human_submissions_N': 0, 'formal_validation_complete': False,
                        'engine_analyze_called': False, 'semantic_rules_or_statistics_scheme_changed': False})
print(json.dumps(entries, ensure_ascii=False))
