"""Freeze a source-only v15 development77 scope; never import or execute a coder."""
import ast
import copy
import datetime
import hashlib
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CANDIDATE = ROOT / '06-coding/human4-general-rule-repair-sol/versions/v2'
SOURCE = ROOT / '01-review/source-interface-v15-price-context-sol'
BASE = ROOT / '01-review/context-projection-sol/full-frame-preflight'
ALGORITHM_VERSION = 'rule-v19-human4-general-repair-development-candidate-2'
DRIVER_VERSION = 'formal-freeze-rule-driver-human4-general-repair-candidate-2'
MANUAL_VERSION = 'v1.3F-human4-clarification-candidate'
SOURCE_SHA = '6c8623909a30566fd5348df3679f14c74cba1b86ccda5602b45707dd55fcb16a'
WHITELIST_SHA = 'cacc5a8d037ce26c7b2b13a9ef06e3a7913610dd3c971b5312e4aa188e6dc46d'
MANUAL_SHA = '7bb13ef1a5ad3d230abe5e786eb3dccd1ef4dfdc17a8f8ae4cbf2958d7229a65'


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def binding(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}


def verify(expected):
    actual = binding(expected['path'])
    if any(actual[key] != expected[key] for key in ('path', 'sha256', 'bytes')):
        raise ValueError('exact frozen file SHA/bytes/path differs: ' + expected['path'])
    return copy.deepcopy(expected)


def read_json(path):
    return json.loads(Path(path).read_bytes())


def write_json(name, value):
    with (HERE / name).open('x', encoding='utf8') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def driver_constants():
    tree = ast.parse((CANDIDATE / 'rule_driver.py').read_bytes())
    found = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id in ('VERSION', 'INFERENCE_FILES', 'CODER_MODULES'):
                found[target.id] = ast.literal_eval(node.value)
    if found.get('VERSION') != DRIVER_VERSION:
        raise ValueError('driver version is not the exact v2 candidate')
    return found


def prepare():
    if any((HERE / name).exists() for name in (
            'preparation-start-record.json', 'preparation-failure.json', 'source-scope.json',
            'preflight.json', 'pre-run-seal.json', 'root-go.json', 'actual-launch-record.json',
            'run77-first')):
        raise ValueError('fresh never-prepared and never-executed first-output directory required')
    write_json('preparation-start-record.json', {
        'status': 'scope_preparation_only_started', 'started_at_utc': now(),
        'actual_driver_process_launch_N': 0, 'actual_cohort_inference_runs': 0,
        'coder_import_N': 0, 'ROOT_GO_received': False})

    whitelist_path = SOURCE / 'common-material-bindings-v15.json'
    whitelist_binding = binding(whitelist_path)
    if whitelist_binding['sha256'] != WHITELIST_SHA:
        raise ValueError('ROOT-specified v15 source whitelist hash differs')
    whitelist = read_json(whitelist_path)
    if whitelist.get('material_binding_N') != 112 or len(whitelist['material_bindings']) != 112:
        raise ValueError('ROOT-specified exact 112-source-material whitelist differs')
    if whitelist.get('no_reference_label_input') is not True:
        raise ValueError('v15 whitelist is not explicitly source-only')
    base_materials = [verify(item) for item in whitelist['material_bindings']]
    if len({item['path'] for item in base_materials}) != 112:
        raise ValueError('duplicate source-material whitelist path')

    source_packet = binding(SOURCE / 'development77/common-source-bundles-v15.jsonl')
    if source_packet['sha256'] != SOURCE_SHA:
        raise ValueError('ROOT-specified unique development77 source hash differs')
    if source_packet not in base_materials:
        raise ValueError('unique actual source packet absent from exact whitelist')
    manifest_path = SOURCE / 'development77/delivery-manifest.json'
    manifest_binding = binding(manifest_path)
    manifest = read_json(manifest_path)
    ids = manifest['global_order']
    batches = [{'batch_id': item['batch_id'], 'source_ids': item['source_ids'],
                'expected_N': item['expected_N']} for item in manifest['batches']]
    if (len(ids) != 77 or len(set(ids)) != 77 or len(batches) != 13
            or [rid for item in batches for rid in item['source_ids']] != ids
            or [len(item['source_ids']) for item in batches] != manifest['batch_sizes']
            or manifest['record_N'] != 77 or manifest['source77_JSONL'] != source_packet):
        raise ValueError('v15 source-only delivery77 ID count/order/batch metadata differs')
    if manifest['v12_source_base'] != str(BASE) or whitelist['v12_source_base'] != str(BASE):
        raise ValueError('frozen source identity resolver base differs')
    bundles = [json.loads(line) for line in Path(source_packet['path']).read_bytes().splitlines()]
    if [item['source_record']['id'] for item in bundles] != ids:
        raise ValueError('actual v15 source packet count/order differs from delivery manifest')
    snapshot_paths = sorted({str(Path(leaf['locator']['snapshot_absolute_path']).resolve())
        for item in bundles for leaf in item['source_full_text_resources']
        if leaf.get('kind') == 'verbatim_UTF8_snapshot_text'})
    if not set(snapshot_paths).issubset({item['path'] for item in base_materials}):
        raise ValueError('literal source snapshot outside whitelist')

    candidate_manual_manifest_path = CANDIDATE / 'manual-candidate-binding.json'
    candidate_manual_manifest = read_json(candidate_manual_manifest_path)
    manual = verify(candidate_manual_manifest['manual'])
    if manual['sha256'] != MANUAL_SHA or candidate_manual_manifest['manual_version'] != MANUAL_VERSION:
        raise ValueError('ROOT-specified disclosed-label candidate manual differs')
    materials = copy.deepcopy(base_materials)
    if manual not in materials:
        if any(item['path'] == manual['path'] for item in materials):
            raise ValueError('candidate manual conflicts with exact source-material whitelist')
        materials.append(manual)

    constants = driver_constants()
    algorithm_path = CANDIDATE / 'algorithm-bindings.json'
    algorithm_manifest = read_json(algorithm_path)
    if algorithm_manifest['algorithm_version'] != ALGORITHM_VERSION:
        raise ValueError('algorithm manifest version differs')
    if [item['module'] for item in algorithm_manifest['modules']] != list(constants['CODER_MODULES']):
        raise ValueError('algorithm manifest/driver frozen coder module order differs')
    implementation = [binding(CANDIDATE / name) for name in constants['INFERENCE_FILES']]
    implementation += [verify(item) for item in algorithm_manifest['modules']]
    if len(implementation) != 10 or len({item['path'] for item in implementation}) != 10:
        raise ValueError('v2 requires five inference dependencies plus five coder modules')
    implementation_seal = binding(CANDIDATE / 'seal.json')
    source_package_seal = binding(SOURCE / 'seal.json')

    scope = {
        'runtime_version': DRIVER_VERSION, 'driver_version': DRIVER_VERSION,
        'algorithm_version': ALGORITHM_VERSION, 'status': 'frozen_for_execution',
        'execution_release_status': 'pending_ROOT_GO_after_independent_controls',
        'execution_purpose': 'development', 'output_directory': str(HERE / 'run77-first'),
        'source_packet': source_packet, 'source_package_seal': source_package_seal,
        'source_version': 'v15 price-context shared-source exact development77',
        'source_manifest': manifest_binding, 'source_manifest_sha256': manifest_binding['sha256'],
        'complete_bundles_canonical_sha256': source_packet['sha256'],
        'source_material_whitelist': whitelist_binding, 'source_material_whitelist_N': 112,
        'material_bindings': materials, 'material_binding_N': len(materials),
        'candidate_manual_additional_to_source_whitelist': manual,
        'manual': manual, 'manual_version': MANUAL_VERSION,
        'algorithm_bindings': binding(algorithm_path), 'implementation_bindings': implementation,
        'implementation_binding_N': len(implementation), 'candidate_implementation_seal': implementation_seal,
        'manual_candidate_manifest': binding(candidate_manual_manifest_path),
        'approved_record_ids': ids, 'expected_record_N': 77, 'expected_dimension_N': 385,
        'original_native_batch_ID_order_metadata_only': batches, 'original_native_batch_N': 13,
        'original_native_coding_read': False, 'v12_source_base': str(BASE),
        'max_actual_cohort_inference_runs': 1, 'actual_cohort_inference_runs_at_freeze': 0,
        'actual_cohort_inference_runs_authorized_at_freeze': 0,
        'ROOT_explicit_GO_required': True, 'ROOT_authorization_record_filename': 'root-go.json',
        'candidate_and_source_status_bytes_unchanged': True,
        'scope_preparation_coder_import_N': 0, 'scope_preparation_inference_N': 0,
        'historically_exposed_AI_development': True, 'calibration_labels_already_disclosed': True,
        'blind_validation': False, 'formal_validation_complete': False,
        'human_validation_complete': False, 'human_independent_label_N': 0,
        'not_human_or_formal_validation': True, 'no_reference_read_in_inference': True,
        'reference_or_Gold_input': None, 'accuracy_computation_authorized': False,
        'actual_image_pixel_reads_expected': 0,
        'requested_model': 'gpt-6.1-sol', 'requested_reasoning_effort': 'ultra',
        'provider_identity_status': 'Requested orchestrating role declared; deterministic Python rules use no model inference calls.',
        'execution_scope': 'One disclosed-label development regression over the exact v15 77-source packet; no new800 or all4481 release.',
        'source_extension_scope': 'Uniform same-PDF four-full-physical-page context; source delivery alone makes no actual read/use claim.',
        'version_change': 'The immutable v2 general semantic repair candidate and clarification manual applied to the immutable v15 source packet.'}
    write_json('source-scope.json', scope)
    argv = [sys.executable, '-B', str(CANDIDATE / 'rule_driver.py'),
        '--scope', str(HERE / 'source-scope.json'), '--scope-sha256', binding(HERE / 'source-scope.json')['sha256'],
        '--input', source_packet['path'], '--input-sha256', source_packet['sha256'],
        '--out', scope['output_directory']]
    preflight = {
        'status': 'prepared_frozen_waiting_ROOT_GO_not_executed', 'prepared_at_utc': now(),
        'scope_binding': binding(HERE / 'source-scope.json'), 'argv': argv,
        'source_packet': source_packet, 'source_package_seal': source_package_seal,
        'source_delivery_manifest': manifest_binding, 'source_material_whitelist': whitelist_binding,
        'source_whitelist_exact_checks': base_materials, 'material_bindings': materials,
        'manual': manual, 'implementation_files': implementation,
        'candidate_implementation_seal': implementation_seal,
        'algorithm_version': ALGORITHM_VERSION, 'driver_version': DRIVER_VERSION,
        'manual_version': MANUAL_VERSION, 'source_record_N': 77, 'dimension_N': 385,
        'exact_source_order_matches_v15_delivery_manifest': True,
        'exact_13_batch_ID_order_retained': True,
        'source_whitelist_N': 112, 'runtime_material_binding_N': len(materials),
        'additional_material_binding_reason': 'v15 source whitelist retains original formal manual; v2 driver also requires the candidate clarification manual.',
        'implementation_binding_N': len(implementation),
        'implementation_binding_count_resolution': 'ROOT accepted 10: actual v2 INFERENCE_FILES five entries plus five algorithm modules; old nine-item wording not reused.',
        'source_asset_snapshot_paths_bound': snapshot_paths,
        'coder_import_N': 0, 'actual_driver_process_launch_N': 0,
        'actual_cohort_inference_runs': 0, 'maximum_actual_cohort_inference_runs': 1,
        'ROOT_GO_received': False, 'independent_controls_release': 'pending_ROOT_evidence',
        'Gold_or_reference_read': False, 'old_predictions_or_metrics_read': False,
        'calibration_labels_already_disclosed': True, 'blind_validation': False,
        'formal_validation_complete': False, 'human_validation_complete': False,
        'accuracy_computed': False,
        'launch_authorization_required_fields': ['decision=GO', 'authorized_by=ROOT',
            'scope_sha256', 'pre_run_seal_sha256', 'algorithm_version', 'source_packet_sha256',
            'candidate_manual_sha256', 'independent_controls_passed=true',
            'independent_control_binding', 'max_actual_cohort_inference_runs=1',
            'actual_cohort_inference_runs_before_release=0', 'authorization_basis']}
    write_json('preflight.json', preflight)
    write_json('pre-run-seal.json', {
        'status': 'scope_and_launcher_frozen_waiting_ROOT_GO', 'sealed_at_utc': now(),
        'files': [binding(HERE / name) for name in ('prepare_dev77_scope.py', 'launch_dev77_once.py',
            'README.md', 'preparation-start-record.json', 'source-scope.json', 'preflight.json')],
        'implementation_files': implementation, 'material_bindings': materials,
        'other_frozen_bindings': [whitelist_binding, manifest_binding, source_package_seal, implementation_seal],
        'actual_driver_process_launch_N_at_seal': 0, 'actual_cohort_inference_runs_at_seal': 0,
        'max_actual_cohort_inference_runs': 1, 'ROOT_GO_received': False,
        'formal_validation_complete': False, 'human_validation_complete': False,
        'calibration_labels_already_disclosed': True, 'blind_validation': False,
        'first_output_directory': scope['output_directory']})
    print(json.dumps({'status': preflight['status'], 'source_record_N': 77,
        'source_whitelist_N': 112, 'runtime_material_binding_N': len(materials),
        'implementation_binding_N': len(implementation), 'scope_sha256': preflight['scope_binding']['sha256'],
        'actual_driver_process_launch_N': 0}, ensure_ascii=False))


if __name__ == '__main__':
    try:
        prepare()
    except BaseException as error:
        if (HERE / 'preparation-start-record.json').exists() and not (HERE / 'preparation-failure.json').exists():
            write_json('preparation-failure.json', {'status': 'preparation_failure_preserved_no_inference',
                'finished_at_utc': now(), 'error_type': type(error).__name__, 'message': str(error),
                'actual_driver_process_launch_N': 0, 'actual_cohort_inference_runs': 0})
        raise
