"""Bind a single authorized development77 attempt without changing source bytes."""
import copy, datetime, hashlib, json, os, sys
from pathlib import Path
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CANDIDATE = ROOT / '05-validation/rule-request-routing-repair-sol'
BASE = ROOT / '06-coding/rule-v18-overall-health-boundary-development-root'
def binding(path):
    p = Path(path).resolve()
    raw = p.read_bytes()
    return {'path': str(p), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
def read_json(path):
    return json.loads(Path(path).read_bytes())
def write_json(path, obj):
    with Path(path).open('x', encoding='utf8') as f:
        f.write(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
def verify(b):
    actual = binding(b['path'])
    if any(actual[key] != b[key] for key in ('path', 'sha256', 'bytes')):
        raise ValueError('actual SHA/bytes differs: ' + b['path'])
    return copy.deepcopy(b)
scope_path, out = HERE / 'development77-source-scope.json', HERE / 'run77-once'
if scope_path.exists() or out.exists() or (HERE / 'preflight.json').exists():
    raise ValueError('distinct never-executed scope and output required')
controls = read_json(HERE / 'independent-control-results-attempt01.json')
if not controls['passed']:
    raise ValueError('independent controls failed; no development run release')
candidate_seal = read_json(CANDIDATE / 'seal.json')
candidate_checks = []
for item in candidate_seal['files']:
    candidate_checks.append(verify(item))
parent = read_json(BASE / 'source-scope.json')
materials = [verify(b) for b in parent['material_bindings']]
for key in ('source_packet', 'source_package_seal', 'manual'):
    verify(parent[key])
algorithms = read_json(CANDIDATE / 'algorithm-bindings.json')
code = [binding(CANDIDATE / n) for n in ('rule_driver.py', 'interface_common.py', 'algorithm-bindings.json', 'formal-manual-binding.json')]
code += [verify(b) for b in algorithms['modules']]
manual_component = read_json(CANDIDATE / 'formal-manual-binding.json')
if manual_component['manual'] != parent['manual'] or manual_component['manual_version'] != '1.3F':
    raise ValueError('development source manual differs from candidate bound manual component')
# Complete material bindings were inherited from the existing 77 scope. JSON
# parsing below checks identity/order only; text contents are not emitted.
raw = Path(parent['source_packet']['path']).read_bytes()
bundles = [json.loads(line) for line in raw.splitlines()]
ids = [b['source_record']['id'] for b in bundles]
if ids != parent['approved_record_ids'] or len(ids) != 77 or len(set(ids)) != 77:
    raise ValueError('development77 packet identity/count/order mismatch')
if any(b.get('common_source_bundle_version') != bundles[0].get('common_source_bundle_version') for b in bundles):
    raise ValueError('mixed source bundle schema versions')
paths = {b['path'] for b in materials}
asset_paths = sorted({str(Path(leaf['locator']['snapshot_absolute_path']).resolve()) for b in bundles for leaf in b['source_full_text_resources'] if leaf.get('kind') == 'verbatim_UTF8_snapshot_text'})
if any(p not in paths for p in asset_paths):
    raise ValueError('literal source asset absent from exact material bindings')
scope = copy.deepcopy(parent)
scope.update(runtime_version='formal-freeze-rule-driver-request-routing-candidate-1', driver_version='formal-freeze-rule-driver-request-routing-candidate-1', status='frozen_for_execution', output_directory=str(out), execution_purpose='development', algorithm_bindings=binding(CANDIDATE / 'algorithm-bindings.json'), manual_version='1.3F', max_actual_cohort_inference_runs=1, actual_cohort_inference_runs_authorized=1, semantic_change='request routing/null propagation only; original positive predicates unchanged', version_change='Isolated request-routing candidate, independent development77 regression only; source/manual/assets exact bytes inherited from v18 development77.', human_independent_label_N=0, formal_validation_complete=False, human_validation_complete=False, not_human_or_formal_validation=True, source_scope_origin=binding(BASE / 'source-scope.json'), candidate_seal_binding=binding(CANDIDATE / 'seal.json'), independent_control_binding=binding(HERE / 'independent-control-results-attempt01.json'), requested_model='gpt-6.1-sol', requested_reasoning_effort='ultra', actual_provider_model_id=None, actual_provider_reasoning_setting=None, provider_identity_status='AI technical role; requested model/effort declared, actual provider configuration not independently observable', authorization='ROOT explicit authorization for one independent development77 candidate regression; no real800/4481 cohort, no Gold or independent-human validation; subsequent human calibration feedback does not alter this scope', semantic_calibration_status='Any human semantic calibration is outside this sealed technical regression and is not read or applied')
write_json(scope_path, scope)
argv = [sys.executable, '-B', str(CANDIDATE / 'rule_driver.py'), '--scope', str(scope_path), '--scope-sha256', binding(scope_path)['sha256'], '--input', parent['source_packet']['path'], '--input-sha256', parent['source_packet']['sha256'], '--out', str(out)]
preflight = {'status': 'passed_frozen_development77_once_only', 'created_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'candidate_seal_actual_file_binding_checks': candidate_checks, 'implementation_files': code, 'exact_material_bindings': materials, 'source_packet': parent['source_packet'], 'source_package_seal': parent['source_package_seal'], 'manual': parent['manual'], 'scope_binding': binding(scope_path), 'parent_scope_binding': binding(BASE / 'source-scope.json'), 'independent_control_binding': binding(HERE / 'independent-control-results-attempt01.json'), 'source_record_N': len(ids), 'dimension_N': len(ids)*5, 'source_order_exactly_matches_parent': True, 'source_packet_bytes_unchanged': True, 'source_semantic_content_added': False, 'source_asset_snapshot_paths_bound': asset_paths, 'source_reading_protocol_binding': next(b for b in materials if Path(b['path']).name == 'source_reading_protocol_v12.py'), 'manual_component_manifest_binding': binding(CANDIDATE / 'formal-manual-binding.json'), 'source_interface_translation': 'No data transformation. Existing complete bare v14 bundles accepted by candidate interface_common.unpack_packet; finite_protocol reuses unchanged v12 protocol with source-only finite lookup.', 'argv': argv, 'max_actual_cohort_inference_runs': 1, 'formal_validation_complete': False, 'human_validation_complete': False, 'human_independent_label_N': 0, 'Gold_or_reference_read': False, 'new_calibration_applied': False}
write_json(HERE / 'preflight.json', preflight)
write_json(HERE / 'pre-run-seal.json', {'status': 'sealed_before_actual_development77_driver_attempt', 'sealed_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'files': [binding(HERE / n) for n in ('independent_controls.py', 'independent-control-results-attempt01.json', 'prepare_dev77_scope.py', 'development77-source-scope.json', 'preflight.json')], 'implementation_files': code, 'material_bindings': materials, 'output_directory': str(out), 'execution_purpose': 'development', 'max_actual_cohort_inference_runs': 1, 'actual_cohort_inference_runs_at_seal': 0, 'formal_validation_complete': False, 'human_validation_complete': False, 'human_independent_label_N': 0, 'new_calibration_applied': False})
print(json.dumps({'status': preflight['status'], 'record_N': len(ids), 'material_binding_N': len(materials), 'implementation_binding_N': len(code), 'scope_sha256': binding(scope_path)['sha256']}, ensure_ascii=False))
