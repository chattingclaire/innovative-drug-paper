"""Finite ROOT reception: sealed artifacts and real blank-sheet interoperability.

This reads metadata and derived blanks only. It does not release packages,
authenticate participants, adjudicate labels or calculate research results.
"""
import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / '05-validation/formal800-xlsx-reception-adapter-sol'
BRIDGE = ROOT / '07-statistics/formal800-v15-statistics-input-bridge-sol'


def binding(path):
    raw = Path(path).read_bytes()
    return {'path': str(Path(path).resolve()), 'bytes': len(raw),
            'sha256': hashlib.sha256(raw).hexdigest()}


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def check_seal(path):
    checks, errors = [], []
    def walk(value):
        if isinstance(value, dict):
            name = value.get('absolute_path', value.get('path'))
            if name is not None and 'sha256' in value and 'bytes' in value:
                target = Path(name)
                if not target.is_absolute():
                    target = path.parent / target
                try:
                    got = binding(target)
                    if got['sha256'] != value['sha256'] or got['bytes'] != value['bytes']:
                        errors.append({'path': str(target), 'reason': 'byte/SHA mismatch'})
                except OSError as error:
                    errors.append({'path': str(target), 'reason': str(error)})
                checks.append(str(target))
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)
    walk(read_json(path))
    return {'seal': binding(path), 'checked_binding_N': len(checks), 'errors': errors}


def main():
    seals = [ADAPTER / 'seal.json',
             ADAPTER / 'checks/final-blank-dry-run/seal.json',
             BRIDGE / 'input-seal.json', BRIDGE / 'output-seal.json']
    verified = [check_seal(path) for path in seals]
    assert all(not item['errors'] for item in verified), verified
    spec = importlib.util.spec_from_file_location('received_formal800_bridge', BRIDGE / 'bridge.py')
    bridge = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bridge)
    rows, design, management = bridge.load_management()
    reception = ADAPTER / 'checks/final-blank-dry-run'
    report = read_json(reception / 'report.json')
    assert report['command'] == 'dry-run'
    assert report['formal_validation_complete'] is False
    statuses, side_summaries = [], {}
    for side in 'AB':
        records = [json.loads(line) for line in
                   (reception / ('derived-' + side + '.jsonl')).read_text(encoding='utf-8').splitlines()]
        assert len(records) == 4000
        assert report['sides'][side]['content_valid'] is True
        assert report['sides'][side]['counts'] == {'unfilled': 4000}
        assert report['sides'][side]['qualification']['eligible_for_downstream_content_handoff'] is False
        outputs, ledger = bridge.project_xlsx_derived_cells(records, side, rows)
        assert len(outputs) == 800 and len(ledger) == 4000
        assert all(item['state'] == 'blank' and item['value'] is None for item in ledger)
        assert all(item['completion_status'] == 'unfilled' and item['value'] is None for item in records)
        assert all(item['derived_record'] is True and item['not_original_human_file'] is True for item in records)
        assert binding(reception / ('original-' + side + '.xlsx'))['sha256'] == report['sides'][side]['input_original']['sha256']
        statuses.extend(ledger)
        side_summaries[side] = {'assigned_records_N': 800, 'dimension_slots_N': 4000,
                                'binary_N': 0, 'blank_N': 4000, 'content_errors_N': 0,
                                'actual_submission_received': False}
    todo = [json.loads(line) for line in (reception / 'coordinator-private/adjudication-todo.jsonl').read_text().splitlines()]
    assert len(todo) == 4000
    assert (reception / 'coordinator-private/disagreements.jsonl').read_bytes() == b''
    assert report['alignment_rows'] == 4000 and report['pending_todo_rows'] == 4000
    finite = read_json(ADAPTER / 'finite-checks.json')
    assert finite['checks_N'] == 16 and all(item['passed'] is True for item in finite['checks'])
    assert finite['actual_human_submissions_N'] == 0
    result = {'artifact_type': 'ROOT_finite_actual_blank_XLSX_statistics_bridge_reception',
              'at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
              'verified_seals': verified, 'side_actual_blank_readback': side_summaries,
              'management_readback': management,
              'coverage_projection': bridge.coverage_summary(statuses, rows),
              'adapter_finite_checks_N': 16, 'adapter_finite_checks_pass_N': 16,
              'actual_independent_submissions_N': 0, 'formal_release_completed': False,
              'human_identity_or_independence_authenticated': False,
              'automatic_adjudication_performed': False, 'research_statistics_computed': False,
              'source_body_semantic_coding_performed': False,
              'all800_holdout_claimed': False, 'current77_originals_modified': False}
    dest = ROOT / 'logs/root-formal800-xlsx-statistics-bridge-reception-20261010.json'
    with dest.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps({'saved_receipt': str(dest), 'verified_binding_N': sum(x['checked_binding_N'] for x in verified),
                      'actual_blank_slots_N': 8000, 'real_labels_or_statistics_generated_N': 0}, ensure_ascii=False))


if __name__ == '__main__':
    main()
