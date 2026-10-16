"""Read-only field-consumption trace; no predictions, labels, or metrics written.

Only final shared material and the frozen automatic-rule runtime are read.
The runtime's 57 v8-added-context rows are executed with transparent mapping
wrappers. Field access is logged independently of classifier output. No code,
source material, prediction, reference, or frozen QA is modified.
"""
import collections
import hashlib
import inspect
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / 'rules-v32/material-adapter-v32.1/runtime'
sys.path.insert(0, str(RUNTIME))
import policy_coding_v27 as coding

WATCH = {'verified_scope_context_v8', 'verified_parent_list_v8',
         'verified_parent_context', 'verified_scope_qualifications_v28',
         'verified_innovation_scope_v27', 'llm_v29_shared_context'}
EVENTS = []
CURRENT_ID = None


def location():
    frame = inspect.currentframe().f_back.f_back
    return (Path(frame.f_code.co_filename).name, frame.f_code.co_name,
            frame.f_lineno)


class Record(dict):
    def get(self, key, default=None):
        if key in WATCH:
            EVENTS.append((CURRENT_ID, 'record.get', key, *location()))
        return super().get(key, default)

    def __getitem__(self, key):
        if key in WATCH:
            EVENTS.append((CURRENT_ID, 'record.__getitem__', key, *location()))
        return super().__getitem__(key)

    def items(self):
        EVENTS.append((CURRENT_ID, 'record.items', '*', *location()))
        return super().items()

    def __iter__(self):
        EVENTS.append((CURRENT_ID, 'record.__iter__', '*', *location()))
        return super().__iter__()


class Parent(dict):
    def get(self, key, default=None):
        if key in {'text', 'repair_version'}:
            EVENTS.append((CURRENT_ID, 'parent.get', key, *location()))
        return super().get(key, default)

    def __getitem__(self, key):
        if key in {'text', 'repair_version'}:
            EVENTS.append((CURRENT_ID, 'parent.__getitem__', key, *location()))
        return super().__getitem__(key)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    global CURRENT_ID
    input_path = ROOT / 'rule_inputs_shared_v8.jsonl'
    rows = [json.loads(line) for line in input_path.read_text().splitlines()]
    affected = [r for r in rows if r['input'].get('verified_scope_context_v8')
                or r['input'].get('verified_parent_list_v8')]
    assert len(rows) == 4924 and len(affected) == 57
    result_checks = []
    for row in affected:
        CURRENT_ID = row['id']
        original = row['input']
        record = Record(original)
        if record.get('verified_parent_context'):
            record['verified_parent_context'] = [Parent(p) for p in
                                                 original['verified_parent_context']]
        start = len(EVENTS)
        traced = coding.code_unit(record)
        event_end = len(EVENTS)
        # Transparent wrappers must not alter any result. The plain run is only
        # compared in memory; neither result nor its labels are saved.
        plain = coding.code_unit(original)
        assert traced == plain, row['id']
        result_checks.append({'id': row['id'], 'unmodified_result_equal': True,
                              'trace_events': event_end-start})
    counts = collections.Counter(tuple(e[1:]) for e in EVENTS
                                 if e[4] not in {'main', '<listcomp>'}
                                 or e[3] != Path(__file__).name)
    # Retain only the source-runtime trace, excluding this harness's own get.
    runtime_events = [e for e in EVENTS if e[3] != Path(__file__).name]
    grouped = collections.Counter(tuple(e[1:]) for e in runtime_events)
    field_counts = collections.Counter(e[2] for e in runtime_events)
    by_id = []
    for row in affected:
        ev = [e for e in runtime_events if e[0] == row['id']]
        r = row['input']
        by_id.append({
            'id': row['id'],
            'scope_field_present': bool(r.get('verified_scope_context_v8')),
            'full_parent_list_field_present': bool(r.get('verified_parent_list_v8')),
            'parent_field_present': bool(r.get('verified_parent_context')),
            'v28_qualifications_present': bool(r.get('verified_scope_qualifications_v28')),
            'source_scope_field_accesses': sum(e[2]=='verified_scope_context_v8' for e in ev),
            'full_parent_list_field_accesses': sum(e[2]=='verified_parent_list_v8' for e in ev),
            'parent_text_read_call_sites': sorted(set(
                f'{e[3]}:{e[5]}:{e[4]}' for e in ev
                if e[1].startswith('parent.') and e[2]=='text')),
        })
    report = {
        'status': 'passed_readonly_field_access_trace',
        'scope': 'Execution field-consumption audit only; not semantic accuracy or validation metrics.',
        'prohibited_reference_or_metric_inputs_read': [],
        'input_path': str(input_path), 'input_sha256': sha(input_path),
        'runtime_path': str(RUNTIME),
        'runtime_code_sha256': {p.name: sha(p) for p in sorted(RUNTIME.glob('*.py'))
                               if not p.name.startswith('test')},
        'rows_in_shared_material': len(rows), 'v8_context_rows_traced': len(affected),
        'transparent_wrapper_result_equality': result_checks,
        'source_scope_count': sum(bool(r['input'].get('verified_scope_context_v8')) for r in rows),
        'full_parent_list_count': sum(bool(r['input'].get('verified_parent_list_v8')) for r in rows),
        'runtime_field_access_counts': dict(field_counts),
        'runtime_access_call_sites': [dict(operation=k[0], field=k[1], file=k[2],
                                           function=k[3], line=k[4], count=v)
                                      for k,v in sorted(grouped.items())],
        'by_id': by_id,
        'no_prediction_or_label_values_written': True,
        'no_runtime_or_material_edits': True,
    }
    target = Path(__file__).with_name('actual_field_access_trace.json')
    assert not target.exists(), 'Do not overwrite an existing audit.'
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({'status': report['status'], 'output': str(target),
                      'output_sha256':sha(target), 'trace_rows':len(affected),
                      'runtime_field_access_counts':dict(field_counts)},
                     ensure_ascii=False))


if __name__ == '__main__':
    main()
