"""One finite synthetic mechanical check; never imports or executes coder modules."""
import ast
import hashlib
import json
import sys
import tempfile
from pathlib import Path
import prepare_scope
import rule_driver

HERE = Path(__file__).resolve().parent
ORIGINAL = HERE.parent / 'human4-general-rule-repair-sol' / 'versions' / 'v4'


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False) + '\n', encoding='utf-8')


def rejected(scope, scope_path, reason):
    write(scope_path, scope)
    old_args = sys.argv
    sys.argv = ['rule_driver.py', '--scope', str(scope_path), '--scope-sha256',
        rule_driver.digest(scope_path), '--input', scope['source_packet']['path'],
        '--input-sha256', scope['source_packet']['sha256'], '--out', scope['output_directory']]
    try:
        rule_driver.main()
    except ValueError as error:
        assert reason in str(error), str(error)
        return str(error)
    finally:
        sys.argv = old_args
    raise AssertionError('expected mechanical rejection')


def main():
    checks = {}
    for name in ('interface_common.py', 'source_packet.py', 'source_receipts.py',
            'evidence.py', 'relations.py', 'dimensions.py', 'manual-candidate-binding.json'):
        assert (ORIGINAL / name).read_bytes() == (HERE / name).read_bytes(), name
    checks['six_implementation_files_and_candidate_binding_byte_identical'] = True
    original = (ORIGINAL / 'rule_driver.py').read_text()
    adapted = (HERE / 'rule_driver.py').read_text()
    old_tree, new_tree = ast.parse(original), ast.parse(adapted)
    names = [node.name for node in old_tree.body if isinstance(node, ast.FunctionDef) and node.name != 'main']
    for name in names:
        old_node = next(node for node in old_tree.body if isinstance(node, ast.FunctionDef) and node.name == name)
        new_node = next(node for node in new_tree.body if isinstance(node, ast.FunctionDef) and node.name == name)
        assert ast.get_source_segment(original, old_node) == ast.get_source_segment(adapted, new_node), name
    old_main = next(node for node in old_tree.body if isinstance(node, ast.FunctionDef) and node.name == 'main')
    new_main = next(node for node in new_tree.body if isinstance(node, ast.FunctionDef) and node.name == 'main')
    old_loop = next(node for node in old_main.body if isinstance(node, ast.For) and ast.unparse(node.target) == 'bundle')
    new_loop = next(node for node in new_main.body if isinstance(node, ast.For) and ast.unparse(node.target) == 'bundle')
    assert ast.get_source_segment(original, old_loop) == ast.get_source_segment(adapted, new_loop)
    assert original[original.index("if __name__=='__main__':"):] == adapted[adapted.index("if __name__=='__main__':"):]
    checks['original_helper_functions_inference_loop_and_terminal_failure_handler_unchanged'] = names
    with tempfile.TemporaryDirectory(prefix='synthetic-mechanical-', dir=HERE) as directory:
        temp = Path(directory)
        synthetic = {}
        for key, name in [('manual', 'manual.txt'), ('prompt', 'prompt.txt'),
                ('protocol', 'production-protocol.txt'), ('source_reading_protocol_code', 'source_reading_protocol_v12.py'), ('source_packet', 'source_input.jsonl'),
                ('source_package_seal', 'source_seal.json'), ('source_manifest', 'frame_bindings.jsonl')]:
            path = temp / name
            path.write_text('synthetic mechanical fixture only\n', encoding='utf-8')
            synthetic[key] = prepare_scope.binding(path)
        ids = temp / 'ids.json'
        write(ids, ['SYNTHETIC-' + str(index) for index in range(4481)])
        inventory = temp / 'inventory.json'
        write(inventory, {'material_bindings': [synthetic['source_packet']]})
        release_path = temp / 'release.json'
        release = {'status': 'released_for_production_provisional', 'execution_purpose': 'production_provisional',
            'authorization_id': 'SYNTHETIC-NOT-REAL-AUTHORIZATION', 'output_directory': str(temp / 'first-output'),
            'max_actual_cohort_inference_runs': 1, 'manual': synthetic['manual'], 'prompt': synthetic['prompt'],
            'protocol': synthetic['protocol'], 'source_input': synthetic['source_packet']}
        write(release_path, release)
        params = {**synthetic, 'release': str(release_path), 'material_inventory_file': str(inventory),
            'ordered_record_ids_file': str(ids), 'v12_source_base': str(temp),
            'complete_bundles_canonical_sha256': synthetic['source_packet']['sha256'],
            'manual_version': 'SYNTHETIC-MECHANICAL-ONLY', 'authorization_id': release['authorization_id'],
            'output_directory': release['output_directory']}
        scope = prepare_scope.build_scope(params)
        assert scope['expected_record_N'] == 4481 and scope['expected_dimension_N'] == 22405
        assert scope['max_actual_cohort_inference_runs'] == 1 and scope['status'] == 'prepared_not_released'
        assert synthetic['source_packet'] in scope['material_bindings']
        scope_path = temp / 'scope.json'
        checks['unreleased_scope_rejected'] = rejected(scope, scope_path, 'scope not released')
        frozen = {**scope, 'status': 'frozen_for_execution'}
        checks['wrong_purpose_rejected'] = rejected({**frozen, 'execution_purpose': 'development'}, scope_path, 'production_provisional execution only')
        checks['partial_count_rejected'] = rejected({**frozen, 'expected_record_N': 1}, scope_path, 'complete 4481-record')
        checks['false_blind_validation_rejected'] = rejected({**frozen, 'blind_validation': True}, scope_path, 'disclosed calibration provenance')
        write(release_path, {**release, 'manual': {**synthetic['manual'], 'sha256': '0' * 64}})
        mismatched = {**frozen, 'release': prepare_scope.binding(release_path)}
        checks['release_common_binding_mismatch_rejected'] = rejected(mismatched, scope_path, 'released common binding differs: manual')
        assert not Path(scope['output_directory']).exists()
        Path(scope['output_directory']).mkdir()
        sentinel = Path(scope['output_directory']) / 'sentinel.txt'
        sentinel.write_text('original first output bytes\n', encoding='utf-8')
        before = sentinel.read_bytes()
        checks['existing_first_output_rejected'] = rejected(scope, scope_path, 'first output exists')
        assert sentinel.read_bytes() == before
    assert not any(name in sys.modules for name in rule_driver.CODER_MODULES)
    checks['no_coder_imported'] = True
    checks['real_cohort_inference_runs'] = 0
    result = {'status': 'passed_one_finite_synthetic_mechanical_selfcheck',
        'contains_real_policy_or_reference_labels': False, 'checks': checks}
    with (HERE / 'mechanical-selfcheck.json').open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': result['status'], 'real_cohort_inference_runs': 0}, ensure_ascii=False))


if __name__ == '__main__':
    main()
