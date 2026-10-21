"""One real source04 row through the frozen candidate12 function; no retry."""
from pathlib import Path
import copy
import datetime
import hashlib
import importlib.metadata
import json
import platform
import sys
import time
import traceback


OUT = Path(__file__).resolve().parent
CANDIDATE = OUT.parent
RUNTIME = CANDIDATE / 'attempt01' / 'runtime'
FREEZE = CANDIDATE / 'attempt01' / 'candidate12_freeze.json'
WORK = CANDIDATE.parents[2]
INPUT = WORK / 'LLM编码' / '统一判据编码准备' / '共用纯来源材料04' / 'rule_inputs_material04.jsonl'
TARGET = 'RECODE25-03894'
EXPECTED = {
    'input': 'bab2da6586fade4a5fc6b188b3fee9cbfbf4099579b9205fee93639c3d7af960',
    'manual': '5abee1f2448cd8a54403d2ac615fea8ebc3c162e78c907029322ec0e85a9556c',
    'freeze': 'a6d45e3a74f213194a900a9a65b47392f201bea3f09ceefdcbeb14239c95d209',
    'python': 'ac60cfe0268614638d0ffa35f3b0284fc7b3a11482723793455e17eeb278509e',
}
BUNDLED_PYTHON = Path('/LOCAL_HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3')
VERSION = 'common-definitions-development-candidate12'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def text_sha(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def now():
    return datetime.datetime.now().astimezone().isoformat()


def save_json(path, value):
    with Path(path).open('x', encoding='utf-8') as handle:
        handle.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main():
    assert sys.dont_write_bytecode, 'Use bundled Python with -B.'
    assert not (OUT / 'preexecution_lock04.json').exists(), 'Never rerun this one-call wrapper.'
    assert not (OUT / 'actual1.jsonl').exists()
    assert sha(FREEZE) == EXPECTED['freeze']
    freeze = json.loads(FREEZE.read_text(encoding='utf-8'))
    manual = Path(freeze['manual_path'])
    assert freeze['manual_sha256'] == EXPECTED['manual'] == sha(manual)
    assert sha(INPUT) == EXPECTED['input']
    locked_code = freeze['production_code_sha256']
    actual_code = {str(path.resolve()): sha(path) for path in RUNTIME.glob('*.py')}
    assert len(actual_code) == len(locked_code) == 51
    assert actual_code == locked_code, 'Frozen runtime file set or bytes differ.'
    assert Path(sys.executable).resolve() == BUNDLED_PYTHON.resolve()
    assert sha(Path(sys.executable).resolve()) == EXPECTED['python']
    import pypdf
    pypdf_dir = Path(pypdf.__file__).resolve().parent
    pypdf_hashes = {name: sha(pypdf_dir / name) for name in ('__init__.py', '_reader.py', '_page.py')}
    assert importlib.metadata.version('pypdf') == '6.10.0'
    environment = {
        'python_executable': sys.executable,
        'python_executable_realpath': str(Path(sys.executable).resolve()),
        'python_executable_sha256': sha(Path(sys.executable).resolve()),
        'python_version': sys.version,
        'python_implementation': platform.python_implementation(),
        'platform': platform.platform(),
        'bytecode_writes_disabled': sys.dont_write_bytecode,
        'pypdf_version': importlib.metadata.version('pypdf'),
        'pypdf_directory': str(pypdf_dir),
        'pypdf_file_sha256': pypdf_hashes,
    }
    rows = INPUT.read_bytes().splitlines(keepends=True)
    selected = [(i, line, json.loads(line)) for i, line in enumerate(rows, 1)
                if json.loads(line)['id'] == TARGET]
    assert len(rows) == 4924 and len(selected) == 1
    line_number, raw_line, row = selected[0]
    assert line_number == 3894
    record = row['input']
    source_hashes = {str(Path(record[key]).resolve()): sha(record[key])
                     for key in ('source', 'unit_source', 'candidate_file') if record.get(key)}
    assert sha(record['unit_source']) == record['unit_source_sha256']
    assert sha(record['source']) == record['source_sha256']
    assert sha(record['candidate_file']) == record['candidate_sha256']
    assert record['nearest_preceding_heading']['text'] == '二中药'
    refs = record['explicitly_cited_qualifications_v12']['references']
    assert [len(group['contexts']) for group in refs] == [3, 3, 5]
    assert len(record['source_application_scope04']) == 4
    scope_field_occurrences = [str(path) for path in RUNTIME.glob('*.py')
                               if 'source_application_scope04' in path.read_text(encoding='utf-8')]
    lock = {
        'created_before_coder_import_and_call': now(),
        'target_id': TARGET,
        'original_id': row['original_id'],
        'input_path': str(INPUT),
        'input_sha256': sha(INPUT),
        'input_line_1based': line_number,
        'exact_input_line_sha256_including_newline': hashlib.sha256(raw_line).hexdigest(),
        'current_unit_sha256': text_sha(record['unit_text']),
        'manual_path': str(manual),
        'manual_sha256': sha(manual),
        'candidate_freeze_path': str(FREEZE),
        'candidate_freeze_sha256': sha(FREEZE),
        'frozen_runtime_path': str(RUNTIME),
        'production_code_sha256': actual_code,
        'actual_source_and_candidate_sha256': source_hashes,
        'environment': environment,
        'entrypoint': 'policy_coding_v27.code_unit',
        'component_settings': {'source_adapter': True, 'substantive_rules': True},
        'max_actual_calls': 1,
        'semantic_retry_allowed': False,
        'wrapper_path': str(Path(__file__).resolve()),
        'wrapper_sha256': sha(__file__),
        'source_application_scope04_input_paragraph_ids': [c['paragraph_id'] for c in record['source_application_scope04']],
        'source_application_scope04_occurrences_in_frozen_runtime': scope_field_occurrences,
        'reference_labels_loaded': False,
        'other_unit_predictions_loaded': False,
        'model_called': False,
        'metrics_computed': False,
    }
    save_json(OUT / 'preexecution_lock04.json', lock)
    call_count = 0
    result = None
    error = None
    started = now()
    timer = time.perf_counter()
    try:
        sys.path.insert(0, str(RUNTIME))
        import policy_coding_v27 as coder
        assert Path(coder.__file__).resolve().parent == RUNTIME
        assert coder.VERSION == VERSION
        call_count += 1
        result = coder.code_unit(copy.deepcopy(record), source_adapter=True, substantive_rules=True)
        assert isinstance(result, dict)
        actual = {'id': row['id'], 'original_id': row['original_id'], 'prediction': result}
        with (OUT / 'actual1.jsonl').open('x', encoding='utf-8') as handle:
            handle.write(json.dumps(actual, ensure_ascii=False) + '\n')
    except Exception as exc:
        error = {'type': type(exc).__name__, 'message': str(exc), 'traceback': traceback.format_exc()}
        save_json(OUT / 'actual1_error.json', error)
    elapsed = time.perf_counter() - timer
    unchanged = {
        'input_bytes_unchanged': sha(INPUT) == lock['input_sha256'],
        'manual_bytes_unchanged': sha(manual) == lock['manual_sha256'],
        'freeze_bytes_unchanged': sha(FREEZE) == lock['candidate_freeze_sha256'],
        'all_51_runtime_code_bytes_unchanged':
            {str(p.resolve()): sha(p) for p in RUNTIME.glob('*.py')} == actual_code,
        'source_and_candidate_bytes_unchanged': all(sha(p) == digest for p, digest in source_hashes.items()),
    }
    loaded_runtime = {str(Path(module.__file__).resolve()): sha(module.__file__)
                      for module in list(sys.modules.values())
                      if getattr(module, '__file__', None)
                      and Path(module.__file__).suffix == '.py'
                      and Path(module.__file__).resolve().parent == RUNTIME}
    interface = None
    if result is not None:
        groups = result.get('typed_contexts_v34', [])
        interface = {
            'id': TARGET,
            'judgement_status': result.get('judgement_status'),
            'input_assessment_status': result.get('input_assessment_status'),
            'source_field_consumption_v34': result.get('source_field_consumption_v34', []),
            'source_context_adaptation_log_v33': result.get('source_context_adaptation_log_v33', []),
            'typed_reference_groups': [
                {**{key: group.get(key) for key in ('field', 'role', 'reference_address',
                   'complete_interval_authenticated', 'labels_may_be_copied')},
                 'contexts': [{key: context.get(key) for key in (
                     'paragraph_id', 'text', 'pages', 'source_lines', 'source_path', 'source_sha256',
                     'candidate_path', 'candidate_sha256', 'authentication_v34')}
                     for context in group.get('contexts', [])]}
                for group in groups],
            'source_application_scope04': {
                'input_paragraph_ids': lock['source_application_scope04_input_paragraph_ids'],
                'occurrences_in_frozen_runtime': scope_field_occurrences,
                'named_field_in_actual_consumption_log': any(
                    item.get('field') == 'source_application_scope04'
                    for item in result.get('source_field_consumption_v34', [])),
                'named_field_in_actual_typed_contexts': any(
                    item.get('field') == 'source_application_scope04' for item in groups),
                'interpretation': 'Only named-field consumption is checked; other existing scope logic is not certified by this check.',
            },
            'existing_scope_diagnostics': {key: value for key, value in result.items()
                                           if ('scope' in key or 'gate' in key) and 'labels' not in key},
            'independent_validity_evidence': False,
        }
        save_json(OUT / 'actual_source_interface04.json', interface)
    metadata = {
        'version': VERSION,
        'started_at': started,
        'completed_at': now(),
        'elapsed_seconds': elapsed,
        'status': 'returned' if error is None else 'exception_preserved_no_retry',
        'actual_code_unit_call_count': call_count,
        'n': 1 if error is None else 0,
        'target_id': TARGET,
        'input_path': str(INPUT),
        'input_sha256': lock['input_sha256'],
        'manual_sha256': lock['manual_sha256'],
        'candidate_freeze_path': str(FREEZE),
        'candidate_freeze_sha256': lock['candidate_freeze_sha256'],
        'preexecution_lock_path': str(OUT / 'preexecution_lock04.json'),
        'preexecution_lock_sha256': sha(OUT / 'preexecution_lock04.json'),
        'runtime_code_sha256': loaded_runtime,
        'environment': environment,
        'component_settings': lock['component_settings'],
        'checks_after_call': unchanged,
        'prediction_path': str(OUT / 'actual1.jsonl') if error is None else None,
        'prediction_sha256': sha(OUT / 'actual1.jsonl') if error is None else None,
        'error_path': str(OUT / 'actual1_error.json') if error is not None else None,
        'error_sha256': sha(OUT / 'actual1_error.json') if error is not None else None,
        'interface_path': str(OUT / 'actual_source_interface04.json') if interface is not None else None,
        'interface_sha256': sha(OUT / 'actual_source_interface04.json') if interface is not None else None,
        'reference_labels_loaded': False,
        'other_unit_predictions_loaded': False,
        'other_unit_dimension_labels_used': False,
        'model_called': False,
        'metrics_computed': False,
        'independent_validity_evidence': False,
        'semantic_retry_performed': False,
    }
    save_json(OUT / 'actual1.run.json', metadata)
    print(json.dumps({'status': metadata['status'], 'actual_code_unit_call_count': call_count,
                      'checks_after_call': unchanged,
                      'prediction_sha256': metadata['prediction_sha256'],
                      'interface_sha256': metadata['interface_sha256'],
                      'error': None if error is None else {'type': error['type'], 'message': error['message']}},
                     ensure_ascii=False))
    if not all(unchanged.values()):
        raise RuntimeError('Post-call byte preservation check failed; artifacts have been retained.')


if __name__ == '__main__':
    main()
