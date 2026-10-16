"""One bounded new B request using immutable09 A; offline preparation by default.

No runtime copies, new A call, semantic retry, corpus expansion or adoption.
"""
import argparse
import datetime
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
C09 = HERE.parent / '候选09-分步判读'
PRIVATE09 = HERE.parent / '候选09-独立检查'
MODEL = 'gpt-5.6-sol'
EFFORT = 'medium'
SCOPE = 'candidate10-initial11-newB-reusing-immutable09A'
MAX_ATTEMPTS = 3

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def read(p):
    return json.loads(Path(p).read_text())

def bind(p):
    p = Path(p).resolve()
    return {'path': str(p), 'sha256': sha(p), 'bytes': p.stat().st_size}

def write_new(p, data):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('xb') as f:
        f.write(data if isinstance(data, bytes) else data.encode())

def dump_new(p, obj):
    write_new(p, json.dumps(obj, ensure_ascii=False, indent=2) + '\n')

def verify(o):
    p = Path(o['path'])
    assert p.is_absolute() and p.is_file() and sha(p) == o['sha256'], str(p)
    if 'bytes' in o:
        assert p.stat().st_size == o['bytes'], str(p)
    return p

def load(name, p):
    spec = importlib.util.spec_from_file_location(name, p)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

def original_packet():
    ip = PRIVATE09 / 'known11_inputs_ORIGINAL_FIELDS_PRIVATE_FROZEN.jsonl'
    ap = C09 / 'runs/initial11-stageA-first-run/all_stageA_records.json'
    assert sha(ip) == '386d17fbe0fb45d6ebcbf8d0b3e834c18953c13b726f29d051b242662d9a0a9c'
    assert sha(ap) == '8f87de605448a7e4295d6deb166ae99b94a46437e1c954934c60432374625ef5'
    rows = [json.loads(s) for s in ip.read_text().splitlines() if s.strip()]
    a = read(ap)
    assert len(rows) == len(a['rows']) == len({r['id'] for r in rows}) == 11
    pure = load('c10_pure_packet_assembler', C09 / 'run_candidate09.py')
    return pure.assemble_stageB_packet(rows, a), pure

def preparation():
    lock = read(HERE / 'prompt_lock_and_sources.json')
    assert lock['model'] == MODEL and lock['reasoning_effort'] == EFFORT
    for b in [lock['prompt'], lock['manual_suffix'], lock['unchanged_B_schema'], lock['previous09_B_prompt'], *lock['manual_sources'], *[v for v in lock['immutable_previous09_A_source'].values() if isinstance(v, dict)]]:
        verify(b)
    packet, pure = original_packet()
    gate = read(PRIVATE09 / 'root-execution/stageA_semantic_gate.json')
    assert gate['approved_for_stageB'] and gate['confirmed_semantic_errors'] == 0
    assert gate['stageA_output_sha256'] == sha(C09 / 'runs/initial11-stageA-first-run/all_stageA_records.json')
    prompt = (HERE / 'stageB_prompt.txt').read_text()
    request = pure.make_request('B', packet, prompt)
    dump_new(HERE / 'prepared_input_packet.json', packet)
    write_new(HERE / 'prepared_request.txt', request)
    dependencies = [
        HERE / 'stageB_prompt.txt', HERE / 'prompt_lock_and_sources.json',
        Path(__file__), C09 / 'run_candidate09.py',
        C09 / 'runtime/run_production_v32.py', C09 / 'runtime/validate_binary_output.py',
        C09 / 'runtime/output_schema_codex_compatible.json',
        PRIVATE09 / 'known11_inputs_ORIGINAL_FIELDS_PRIVATE_FROZEN.jsonl',
        C09 / 'runs/initial11-stageA-first-run/all_stageA_records.json',
        C09 / 'runs/initial11-stageA-first-run/stageA_seal.json',
        PRIVATE09 / 'root-execution/stageA_semantic_gate.json',
        PRIVATE09 / 'root-execution/stageB_semantic_gate.json',
        C09 / 'runs/initial11-stageB-first-run/attempts/attempt-01/run_metadata.json',
        HERE / 'prepared_input_packet.json', HERE / 'prepared_request.txt',
        *[Path(b['path']) for b in lock['manual_sources']],
    ]
    freeze = {
        'scope': SCOPE, 'n': 11, 'model': MODEL, 'reasoning_effort': EFFORT,
        'logical_requests': 1, 'max_identical_technical_attempts': MAX_ATTEMPTS,
        'first_technical_valid_only': True, 'new_A_calls': 0,
        'semantic_retries_or_expansion_or_adoption': False,
        'old09_B_FAIL_preserved': True, 'only_packet_keys': ['rows', 'stageA_records'],
        'dependencies': [bind(p) for p in dependencies],
        'source_type': 'New B implementation; reuses sealed09 A and unchanged original materials. Not09 retry or a new full A/B run.',
    }
    dump_new(HERE / 'initial11_execution_freeze.json', freeze)
    print(json.dumps({'status': 'PREPARED_OFFLINE_NOT_RUN', 'freeze': bind(HERE / 'initial11_execution_freeze.json'), 'new_model_calls': 0}, ensure_ascii=False))

def execute(auth_path):
    freeze_path = HERE / 'initial11_execution_freeze.json'
    freeze = read(freeze_path)
    assert freeze['scope'] == SCOPE and freeze['n'] == 11
    assert freeze['max_identical_technical_attempts'] == MAX_ATTEMPTS
    for b in freeze['dependencies']:
        verify(b)
    auth = read(auth_path)
    assert auth['scope'] == SCOPE and auth['approved_by'] == '/root'
    assert auth['execution_freeze_sha256'] == sha(freeze_path)
    assert auth['n'] == 11 and auth['logical_requests'] == 1
    preflight_path = verify(auth['independent_preflight'])
    assert read(preflight_path)['approved_for_bounded_execution'] is True
    packet, pure = original_packet()
    assert packet == read(HERE / 'prepared_input_packet.json')
    request = pure.make_request('B', packet, (HERE / 'stageB_prompt.txt').read_text())
    assert request.encode() == (HERE / 'prepared_request.txt').read_bytes()
    base = load('c10_existing_frozen_runtime', C09 / 'runtime/run_production_v32.py')
    assert base.MODEL == MODEL and base.EFFORT == EFFORT
    old_meta = read(C09 / 'runs/initial11-stageB-first-run/attempts/attempt-01/run_metadata.json')
    assert sha(base.CLI) == old_meta['cli_binary_sha256']
    run = HERE / 'runs/initial11-newB-reusing09A'
    run.mkdir(parents=True, exist_ok=False)
    dump_new(run / 'start_receipt.json', {'scope': SCOPE, 'created_at_UTC': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'authorization': bind(auth_path), 'freeze': bind(freeze_path), 'n': 11, 'new_A_calls': 0})
    attempts = []
    summary = {'scope': SCOPE, 'status': 'STOPPED_TECHNICAL_OR_MATERIAL_FAILURE', 'n': 11, 'logical_requests': 1, 'new_A_calls': 0, 'attempts': attempts, 'semantic_review_required': True, 'expansion_or_adoption': False}
    for number in range(1, MAX_ATTEMPTS + 1):
        for b in freeze['dependencies']:
            verify(b)
        dest = run / 'attempts' / f'attempt-{number:02d}'
        meta = base.run_attempt(dest, packet, request, sha(HERE / 'stageB_prompt.txt'), old_meta['cli_version'], old_meta['cli_binary_sha256'], 900)
        entry = {'attempt': number, 'metadata': bind(dest / 'run_metadata.json'), 'status': meta['status'], 'errors': meta['errors'], 'tool_event_count': meta['tool_event_count']}
        attempts.append(entry)
        raw = read(dest / 'raw_output.json') if (dest / 'raw_output.json').exists() else None
        material = [i for i in raw.get('issue_records', []) if isinstance(i, dict) and i.get('status') == 'material_issue'] if isinstance(raw, dict) else []
        if meta['status'] == 'accepted_structural_literal_zero_tools':
            for b in freeze['dependencies']:
                verify(b)
            write_new(run / 'all_predictions.json', (dest / 'raw_output.json').read_bytes())
            write_new(run / 'all_predictions.jsonl', ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in raw['rows']))
            summary.update(status='TECHNICAL_COMPLETE_SEMANTIC_REVIEW_REQUIRED', first_technical_valid_only=True, selected_attempt=number, output_JSON=bind(run / 'all_predictions.json'), output_JSONL=bind(run / 'all_predictions.jsonl'))
            break
        if material:
            summary['status'] = 'STOPPED_MATERIAL_FLAG_NO_SEMANTIC_RETRY'
            summary['material_issue_count'] = len(material)
            break
    summary['actual_model_attempts'] = len(attempts)
    dump_new(run / 'technical_summary.json', summary)
    print(json.dumps(summary, ensure_ascii=False), flush=True)
    return 0 if summary['status'] == 'TECHNICAL_COMPLETE_SEMANTIC_REVIEW_REQUIRED' else 2

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--authorization', type=Path)
    args = parser.parse_args()
    assert args.prepare != args.execute, 'Choose preparation or bounded execution explicitly.'
    if args.prepare:
        preparation()
    else:
        assert args.authorization is not None
        raise SystemExit(execute(args.authorization))
