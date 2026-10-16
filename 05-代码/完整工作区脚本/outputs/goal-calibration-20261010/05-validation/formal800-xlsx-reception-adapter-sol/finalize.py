"""Seal only adapter-owned artifacts and verify unchanged bound inputs."""
import datetime
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def binding(path):
    raw = path.read_bytes()
    return {'path': str(path.resolve()), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


# Exporter-generated whole-workbook inspections duplicate source prose. They were
# neither semantically inspected nor needed for this finite D/E verification.
for p in (HERE / 'checks/constructed-fixtures').glob('*.xlsx.inspect.ndjson'):
    p.unlink()
originals = json.loads((HERE / 'bindings.json').read_text())
for b in [*originals['inputs'].values(), *originals['dependencies'].values()]:
    if binding(Path(b['path'])) != b:
        raise ValueError('old input changed: ' + b['path'])
for p in HERE.glob('*.py'):
    compile(p.read_text(), str(p), 'exec')
members = [binding(p) for p in sorted(HERE.rglob('*')) if p.is_file() and p.name != 'seal.json']
seal = {'version': 'formal800-xlsx-reception-adapter-delivery-1',
        'created_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'input_bindings': originals['inputs'], 'reused_dependency_bindings': originals['dependencies'],
        'all_bound_old_files_unchanged': True, 'output_members': members,
        'output_member_N': len(members), 'self_hash_policy': 'all seal.json files individually own their output members; top seal excludes all seal.json to avoid self recursion',
        'actual_human_submissions_N': 0, 'actual_formal_release_created_N': 0,
        'statistics_or_CI_calculated': False, 'source_prose_semantically_read': False,
        'finite_checks': binding(HERE / 'finite-checks.json'),
        'final_blank_dry_run_report': binding(HERE / 'checks/final-blank-dry-run/report.json')}
# Individual run seals are referenced independently, including their exact bytes.
seal['run_seals'] = [binding(p) for p in sorted((HERE / 'checks').rglob('seal.json'))]
with (HERE / 'seal.json').open('x') as f:
    f.write(json.dumps(seal, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'sealed_members_N': len(members), 'old_inputs_unchanged': True}))
