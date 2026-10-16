"""Read-only checks of frozen source-only inputs, without any coded result."""
from pathlib import Path
from collections import defaultdict
import copy
import hashlib
import json
import unicodedata
from pypdf import PdfReader

B = Path(__file__).resolve().parents[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
digest = lambda s: hashlib.sha256(s.encode()).hexdigest()
norm = lambda s: ''.join(c for c in unicodedata.normalize('NFKC', s) if c.isalnum())
jl = lambda p: [json.loads(s) for s in Path(p).read_text().splitlines() if s.strip()]
old = jl(B / 'effective_blind_inputs_v12.jsonl')
new = jl(B / 'effective_blind_inputs_v13.jsonl')
rold = jl(B / 'rule_inputs_shared_v12.jsonl')
rnew = jl(B / 'rule_inputs_shared_v13.jsonl')
m = json.loads((B / 'material_v13_manifest.json').read_text())
targets = ['RECODE25-02869', 'RECODE25-02870', 'RECODE25-02871']
checks = {}
checks['all_4924_unit_ids_order_and_original_text_unchanged'] = len(new) == len(rnew) == 4924 and all(a['id'] == b['id'] and a['text'] == b['text'] for a, b in zip(old, new)) and all(a['id'] == b['id'] and a['input']['unit_id'] == b['input']['unit_id'] and a['input']['unit_text'] == b['input']['unit_text'] for a, b in zip(rold, rnew))
checks['exactly_three_changed_contexts_and_rule_records'] = [a['id'] for a, b in zip(old, new) if a != b] == targets and [a['id'] for a, b in zip(rold, rnew) if a != b] == targets
checks['all_4924_two_methods_share_exact_context_bytes'] = all(a['id'] == b['id'] and json.dumps(a['contexts'], ensure_ascii=False) == json.dumps(b['input']['llm_v29_shared_context'], ensure_ascii=False) for a, b in zip(new, rnew))
checks['v12_all_manifest_bound_bytes_preserved'] = all(sha(B / p) == h for p, h in m['prior_v12_files_preserved_sha256'].items())
checks['v13_manifest_sha_matches_inputs'] = sha(B / 'effective_blind_inputs_v13.jsonl') == m['new_llm_sha256'] and sha(B / 'rule_inputs_shared_v13.jsonl') == m['new_rule_sha256']
checks['frozen_classifier_runtime_manual_bytes_unchanged'] = all(sha(p) == h for p, h in m['production_manual_freeze_hashes_verified'].items())
checks['only_approved_source_fields_changed'] = True
details = []
for a, b, ra, rb in zip(old, new, rold, rnew):
    if a['id'] not in targets:
        continue
    c = b['contexts']['source_local_list_family_v13']
    original = copy.deepcopy(b)
    original['contexts'].pop('source_local_list_family_v13')
    original['contexts']['nearest_preceding_heading'] = a['contexts']['nearest_preceding_heading']
    parent = original['contexts']['verified_parent_context'].pop()
    cert_parent = original['contexts']['verified_context_certificates']['verified_parent_context'].pop()
    assert parent == cert_parent
    checks['only_approved_source_fields_changed'] &= original == a
    original_rule = copy.deepcopy(rb)
    original_rule['input'].pop('source_local_list_family_v13')
    original_rule['input']['nearest_preceding_heading'] = ra['input']['nearest_preceding_heading']
    original_rule['input']['verified_parent_context'].pop()
    original_rule['input']['llm_v29_shared_context'] = ra['input']['llm_v29_shared_context']
    checks['only_approved_source_fields_changed'] &= original_rule == ra
    assert parent['repair_version'] == 'v13-source-local-list-predicate'
    assert parent['original_unit_sha256'] == c['current_unit_sha256'] == digest(b['text'])
    assert parent['unit_id'] == c['current_unit_id'] == rb['input']['unit_id']
    assert parent['text_sha256'] == digest(parent['text'])
    assert c['contexts_sha256'] == digest(json.dumps(c['contexts'], ensure_ascii=False, sort_keys=True))
    source = Path(c['source_path'])
    candidate = Path(c['candidate_path'])
    assert sha(source) == c['source_sha256'] and sha(candidate) == c['candidate_sha256']
    cd = json.loads(candidate.read_text())
    pp = cd['paragraphs']
    idx = {p['id']: i for i, p in enumerate(pp)}
    assert [x['paragraph_id'] for x in c['contexts']] == [p['id'] for p in pp[idx['p0048']:idx['p0052'] + 1]] == ['p0048', 'p0049', 'p0050', 'p0051', 'p0052']
    assert pp[idx['p0052'] + 1]['id'] == c['structure_boundary']['next_boundary']['paragraph_id'] == 'p0052h1'
    pdf_text = norm(PdfReader(source).pages[15].extract_text())
    for x in c['contexts']:
        p = pp[idx[x['paragraph_id']]]
        assert x['text'] == p['text'] and x['pages'] == p['pages'] == [16]
        assert x['source_lines'] == (p.get('line_ids') or [])
        assert norm(x['text']) in pdf_text
        assert Path(p.get('source_file') or cd['source']).resolve() == source.resolve()
    assert c['actual_heading']['paragraph_id'] == 'p0048'
    assert c['actual_parent_predicate']['paragraph_id'] == 'p0049'
    assert [x['paragraph_id'] for x in c['actual_list_siblings']] == ['p0050', 'p0051', 'p0052']
    assert b['contexts']['nearest_preceding_heading'] == rb['input']['nearest_preceding_heading'] == {'text': '2.1.2临床安全性信息', 'pages': [16]}
    assert sha(c['source_image_evidence']['path']) == c['source_image_evidence']['sha256']
    actual_analysis_paragraphs = {p['paragraph_id'] for r in new if r['source_title'] == b['source_title'] for p in r['contexts']['paragraph_context']}
    assert 'p0050' not in actual_analysis_paragraphs and 'p0051' not in actual_analysis_paragraphs
    details.append({'id': b['id'], 'original_text_sha256': digest(b['text']), 'actual_heading': 'p0048', 'actual_parent_predicate': 'p0049', 'source_siblings': ['p0050', 'p0051', 'p0052'], 'actual_pdf_page': 16, 'printed_page': 13, 'all_five_paragraphs_original_pdf_literal_verified': True, 'next_heading_excluded': True, 'new_parent_cert_is_authentic_v13_not_v28': True, 'all_previous_source_fields_preserved': True})
checks['three_local_subsections_bound_to_actual_pdf_and_candidate'] = len(details) == 3
signature = lambda row: json.dumps({k: row[k] for k in ['text', 'source_title', 'pages', 'contexts', 'context_usage']}, ensure_ascii=False, sort_keys=True)
old_by_signature = defaultdict(list)
new_by_id = {row['id']: row for row in new}
for row in old:
    old_by_signature[signature(row)].append(row['id'])
future = []
for coder in ['A', 'C']:
    p = B / f'future-human-validation-v4/真人{coder}-无答案材料.json'
    package = json.loads(p.read_text())
    rows = package['rows']
    all_ids = []
    assert len(rows) == 240
    assert package['coder_name'] == package['professional_background'] == package['execution_date'] == ''
    for row in rows:
        ids = old_by_signature[signature(row)]
        assert len(ids) == 1
        rid = ids[0]
        assert row['contexts'] == new_by_id[rid]['contexts']
        assert row['text'] == new_by_id[rid]['text']
        assert all(v == '' for v in row['coding'].values())
        all_ids.append(rid)
    assert len(set(all_ids)) == 240 and not set(all_ids) & set(targets)
    future.append({'coder': coder, 'json_path': str(p), 'sha256': sha(p), 'rows': 240, 'distinct_actual_ids': 240, 'changed_unit_intersection': [], 'all_240_contexts_equal_v13': True, 'all_identity_coding_reason_evidence_fields_blank': True})
assert future[0]['sha256'] != future[1]['sha256']
checks['future_v4_both_240_contexts_already_exactly_v13_no_update_required'] = len(future) == 2
assert all(checks.values()), checks
report = {'qa_version': 'independent-source-v13', 'status': 'PASS', 'scope': 'actual source-only local list family; no labels, confirmation results, or machine outputs read', 'checks': checks, 'affected_ids': targets, 'details': details, 'future_human_v4_readonly_same_material_verification': future, 'no_frozen_rule_validation_or_consumption_claim_for_new_v13_fields': True, 'source_pdf_sha256': c['source_sha256'], 'candidate_sha256': c['candidate_sha256'], 'v13_llm_sha256': m['new_llm_sha256'], 'v13_rule_sha256': m['new_rule_sha256'], 'v13_manifest_sha256': sha(B / 'material_v13_manifest.json')}
(B / 'audit/independent_source_material_v13_qa.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'status': report['status'], 'checks': checks, 'affected_ids': targets}, ensure_ascii=False))
