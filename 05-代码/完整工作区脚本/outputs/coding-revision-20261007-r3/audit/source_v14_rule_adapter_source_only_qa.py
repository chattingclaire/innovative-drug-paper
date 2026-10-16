"""Exercise v14 source-interface authentication only; do not run a classifier."""
from pathlib import Path
import copy
import hashlib
import json
import sys

B = Path(__file__).resolve().parents[1]
RUNTIME = B / 'rules-v34-audit/architecture/runtime-v34.1-source-interface'
sys.path.insert(0, str(RUNTIME))
from source_context_adapter_v34 import local_family_v14, component_v14
from context_validation import payload_digest

sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
DEST = B / 'audit/source_v14_rule_adapter_source_only_qa.json'
assert not DEST.exists()
hashes = {str(p): sha(p) for p in RUNTIME.glob('*.py')}
rows = {x['id']: x['input'] for x in map(json.loads, (B / 'rule_inputs_shared_v14.jsonl').read_text().splitlines())}
targets = json.loads((B / 'material_v14_manifest.json').read_text())['affected_ids']

def authenticate(record):
    typed, log = [], []
    shared = record['llm_v29_shared_context']
    local_family_v14(record, shared, typed, log)
    component_v14(record, shared, typed, log)
    return typed, log

positive = []
for rid in targets:
    row = copy.deepcopy(rows[rid]); before = copy.deepcopy(row)
    typed, log = authenticate(row)
    assert row == before and len(typed) == len(log) == 1
    assert typed[0]['labels_may_be_copied'] is False and log[0]['dimension_assignment'] is False
    assert 'labels' not in typed[0] and 'labels' not in log[0]
    assert log[0]['authenticated'] is True
    positive.append({'id': rid, 'field': typed[0]['field'], 'role': typed[0]['role'], 'source_authenticated': True, 'no_dimension_assignment': True})

def synced(record, field):
    record['llm_v29_shared_context'][field] = copy.deepcopy(record[field])

def mutation(case):
    row = copy.deepcopy(rows['RECODE25-04340' if case.startswith('list_') else 'RECODE25-02010'])
    field = 'source_local_list_family_v14' if case.startswith('list_') else 'source_component_boundary_v14'
    c = row[field]
    if case == 'list_current_text_digest':
        c['current_unit_sha256'] = '0' * 64
    elif case == 'list_source_sha':
        c['source_sha256'] = '0' * 64
    elif case == 'list_parent_text':
        c['actual_parent_predicate']['text'] += '额外内容'
    elif case == 'list_omit_sibling':
        c['contexts'].pop(1); c['contexts_sha256'] = payload_digest(c['contexts'])
    elif case == 'list_wrong_next_boundary':
        c['structure_boundary']['next_boundary']['text'] = '不存在的边界'
    elif case == 'component_wrong_heading':
        c['actual_component_heading']['text'] += '不存在的标题'
    elif case == 'component_omit_middle_item':
        c['contexts'].pop(3); c['contexts_sha256'] = payload_digest(c['contexts'])
    elif case == 'component_reverse_items':
        c['contexts'].reverse(); c['contexts_sha256'] = payload_digest(c['contexts'])
    elif case == 'component_omit_last_item':
        c['contexts'].pop(); c['contexts_sha256'] = payload_digest(c['contexts'])
    synced(row, field)
    return row

negative = []
for case in ['list_current_text_digest', 'list_source_sha', 'list_parent_text', 'list_omit_sibling', 'list_wrong_next_boundary', 'component_wrong_heading', 'component_omit_middle_item', 'component_reverse_items', 'component_omit_last_item']:
    try:
        authenticate(mutation(case))
    except (ValueError, AssertionError) as error:
        negative.append({'case': case, 'rejected': True, 'message': str(error)})
    else:
        negative.append({'case': case, 'rejected': False})
assert all(x['rejected'] for x in negative), negative
assert all(sha(p) == h for p, h in hashes.items()), 'Runtime changed during audit; rerun as a new audit version'
report = {'status': 'PASS', 'source_only': True, 'scope': 'Only local_family_v14/component_v14 source authenticators exercised; no classifier, predictions, confirmation, reference labels or PRIVATE review mappings used.', 'authentic_positive_n': len(positive), 'typed_parent_n': sum(x['field'] == 'source_local_list_family_v14' for x in positive), 'typed_component_n': sum(x['field'] == 'source_component_boundary_v14' for x in positive), 'positive_details': positive, 'negative_controls': negative, 'input_sha256': sha(B / 'rule_inputs_shared_v14.jsonl'), 'runtime_hashes': hashes, 'source_adapter_sha256': sha(RUNTIME / 'source_family_v14.py'), 'no_semantic_or_score_claim': True, 'audit_script_sha256': sha(Path(__file__))}
DEST.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'status': report['status'], 'authentic_positive_n': len(positive), 'typed_parent_n': report['typed_parent_n'], 'typed_component_n': report['typed_component_n'], 'negative_control_n': len(negative), 'source_adapter_sha256': report['source_adapter_sha256']}, ensure_ascii=False))
