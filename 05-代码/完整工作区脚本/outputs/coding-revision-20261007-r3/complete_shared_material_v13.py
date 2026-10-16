"""Apply the approved actual clinical-safety list-family source repair.

v12 is immutable. No analysis unit, classifier, prompt, coding standard or
label is changed. New v13 certificates make no frozen-validator claim.
"""
from pathlib import Path
import copy
import hashlib
import json

B = Path(__file__).resolve().parent
P = B / 'audit/local_list_parent_priority_proposal_v13.json'
TARGETS = ['RECODE25-02869', 'RECODE25-02870', 'RECODE25-02871']


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def digest(s):
    return hashlib.sha256(s.encode()).hexdigest()


def jl(p):
    return [json.loads(s) for s in Path(p).read_text().splitlines() if s.strip()]


for name in ['effective_blind_inputs_v13.jsonl', 'rule_inputs_shared_v13.jsonl', 'material_v13_manifest.json']:
    assert not (B / name).exists(), 'Never overwrite v13'
preserved = {name: sha(B / name) for name in ['effective_blind_inputs_v12.jsonl', 'rule_inputs_shared_v12.jsonl', 'material_v12_manifest.json']}
freeze = json.loads((B / 'rules-v33/candidate_freeze.json').read_text())
frozen = freeze['production_code_sha256'] | freeze['all_runtime_py_sha256'] | freeze['basis_files_sha256']
assert all(sha(p) == h for p, h in frozen.items())
ll = jl(B / 'effective_blind_inputs_v12.jsonl')
rr = jl(B / 'rule_inputs_shared_v12.jsonl')
before_ll = copy.deepcopy(ll)
before_rr = copy.deepcopy(rr)
lb = {x['id']: x for x in ll}
rb = {x['id']: x['input'] for x in rr}
proposal = json.loads(P.read_text())
assert proposal['affected_ids'] == TARGETS and proposal['affected_unit_n'] == 3
for x in proposal['proposals']:
    rid = x['id']
    r = rb[rid]
    assert x['current_unit'] == lb[rid]['text'] == r['unit_text']
    assert digest(r['unit_text']) == x['current_unit_sha256']
    assert lb[rid]['contexts']['nearest_preceding_heading'] == x['old_nearest_preceding_heading']
    assert r['nearest_preceding_heading'] == x['old_nearest_preceding_heading']
    contexts = copy.deepcopy(x['full_subsection_contexts'])
    cp = Path(r['candidate_file'])
    cd = json.loads(cp.read_text())
    paragraphs = cd['paragraphs']
    idx = {p['id']: i for i, p in enumerate(paragraphs)}
    assert [c['paragraph_id'] for c in contexts] == [p['id'] for p in paragraphs[idx['p0048']:idx['p0052'] + 1]]
    assert paragraphs[idx['p0052'] + 1]['id'] == x['next_boundary']['paragraph_id'] == 'p0052h1'
    for c in contexts:
        p = paragraphs[idx[c['paragraph_id']]]
        assert c['verification']['verified'] is True
        assert c['text'] == p['text'] and c['pages'] == p['pages']
        assert c['source_lines'] == (p.get('line_ids') or [])
        assert sha(c['candidate_path']) == c['candidate_sha256'] == r['candidate_sha256']
        assert sha(c['source_path']) == c['source_sha256'] == (r.get('unit_source_sha256') or r['source_sha256'])
        assert Path(p.get('source_file') or cd['source']).resolve() == Path(c['source_path']).resolve()
    head = x['correct_actual_heading']
    actual_heading = {'text': head['text'], 'pages': head['pages']}
    lb[rid]['contexts']['nearest_preceding_heading'] = copy.deepcopy(actual_heading)
    r['nearest_preceding_heading'] = copy.deepcopy(actual_heading)
    parent = copy.deepcopy(x['local_controlling_parent_predicate'])
    parent.update({
        'repair_version': 'v13-source-local-list-predicate',
        'original_unit_sha256': digest(r['unit_text']),
        'unit_id': r['unit_id'],
        'text_sha256': digest(parent['text']),
        'context_role': 'actual_clinical_safety_subsection_local_list_predicate',
        'usage': '提供原PDF当前小节的实际父谓词。仅消解来源子项的对象与语境；不从父段或全局DRMP目的自动传递任何维度标签。',
    })
    lb[rid]['contexts'].setdefault('verified_parent_context', []).append(copy.deepcopy(parent))
    r.setdefault('verified_parent_context', []).append(copy.deepcopy(parent))
    lb[rid]['contexts'].setdefault('verified_context_certificates', {}).setdefault('verified_parent_context', []).append(copy.deepcopy(parent))
    cert = {
        'repair_version': 'v13-source-local-list-family',
        'current_unit_id': r['unit_id'],
        'current_unit_sha256': digest(r['unit_text']),
        'source_path': contexts[0]['source_path'],
        'source_sha256': contexts[0]['source_sha256'],
        'candidate_path': str(cp),
        'candidate_sha256': sha(cp),
        'actual_heading': copy.deepcopy(head),
        'actual_parent_predicate': copy.deepcopy(x['local_controlling_parent_predicate']),
        'actual_list_siblings': copy.deepcopy(x['actual_list_siblings']),
        'contexts': contexts,
        'contexts_sha256': digest(json.dumps(contexts, ensure_ascii=False, sort_keys=True)),
        'structure_boundary': {
            'first_paragraph': 'p0048', 'last_paragraph': 'p0052',
            'all_paragraphs_in_interval_included': True,
            'next_boundary': copy.deepcopy(x['next_boundary']),
            'actual_source_bullet_count': 3,
            'source_bullets_without_analysis_units': ['p0050', 'p0051'],
        },
        'source_image_evidence': copy.deepcopy(proposal['source_image_evidence']),
        'usage': '当前临床安全性信息小节的完整实际源结构：标题、父谓词和三个来源子项。兄弟段仅为语境，不增加分析单位，不继承标签；不以全局政策目的代替当前父谓词。',
        'frozen_rule_validation_or_consumption_not_claimed': True,
    }
    lb[rid]['contexts']['source_local_list_family_v13'] = copy.deepcopy(cert)
    r['source_local_list_family_v13'] = copy.deepcopy(cert)
    r['llm_v29_shared_context'] = copy.deepcopy(lb[rid]['contexts'])

assert len(ll) == len(rr) == 4924
assert all(a['id'] == b['id'] and a['text'] == b['text'] for a, b in zip(ll, before_ll))
assert all(a['id'] == b['id'] and a['input']['unit_id'] == b['input']['unit_id'] and a['input']['unit_text'] == b['input']['unit_text'] for a, b in zip(rr, before_rr))
assert all(a['id'] == b['id'] and a['contexts'] == b['input']['llm_v29_shared_context'] for a, b in zip(ll, rr))
changed = [a['id'] for a, b in zip(ll, before_ll) if a != b]
assert changed == TARGETS
assert [a['id'] for a, b in zip(rr, before_rr) if a != b] == TARGETS
for name, rows in [('effective_blind_inputs_v13.jsonl', ll), ('rule_inputs_shared_v13.jsonl', rr)]:
    (B / name).write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows))
manifest = {
    'material_version': 'v13', 'status': 'sealed_root_approved_source_only_repair',
    'source_only': True, 'n': 4924, 'affected_ids': changed,
    'incremental_context_changed_n': 3, 'unit_text_changes': 0,
    'unit_id_changes': 0, 'unit_order_changes': 0, 'new_analysis_units': 0,
    'reason': 'Actual PDF p16 local clinical-safety source list: repair the misidentified heading and supply its controlling paragraph and all three source siblings.',
    'actual_heading': '2.1.2临床安全性信息',
    'actual_parent_predicate_paragraph': 'p0049',
    'actual_source_siblings': ['p0050', 'p0051', 'p0052'],
    'complete_source_interval': ['p0048', 'p0049', 'p0050', 'p0051', 'p0052'],
    'excluded_next_boundary': 'p0052h1:2.1.3同类药物重要临床安全性信息',
    'two_methods_same_text_and_context': True,
    'coding_standard_unchanged': 'CAL-5D-v1.3 + operational-v1.4',
    'classification_code_unchanged': True, 'manual_unchanged': True,
    'new_parent_certificate_version': 'v13-source-local-list-predicate',
    'new_local_list_field': 'source_local_list_family_v13',
    'new_fields_available_byte_equally_to_both_methods': True,
    'frozen_rule_validation_or_consumption_of_new_fields_not_claimed': True,
    'no_labels_transferred': True,
    'global_drmp_purpose_not_substituted_for_local_predicate': True,
    'references_or_predictions_read_by_preparation_script': False,
    'prior_v12_files_preserved_sha256': preserved,
    'production_manual_freeze_hashes_verified': frozen,
    'proposal_path': str(P), 'proposal_sha256': sha(P),
    'new_llm_sha256': sha(B / 'effective_blind_inputs_v13.jsonl'),
    'new_rule_sha256': sha(B / 'rule_inputs_shared_v13.jsonl'),
    'actual_model_rerun_required_on_changed_context_payloads': True,
}
(B / 'material_v13_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
assert all(sha(B / name) == h for name, h in preserved.items())
assert all(sha(p) == h for p, h in frozen.items())
print(json.dumps({k: manifest[k] for k in ['n', 'affected_ids', 'new_llm_sha256', 'new_rule_sha256']}, ensure_ascii=False))
