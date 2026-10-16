"""Read-only independent source, schema, equality and packaging checks for v14.

Never import the preparation script or a classifier, and never read labels.
"""
from pathlib import Path
from functools import lru_cache
from collections import Counter
import copy
import hashlib
import json
import subprocess
import tempfile
import unicodedata
from pypdf import PdfReader

B = Path(__file__).resolve().parents[1]
DEST = B / 'audit/independent_source_material_v14_qa.json'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
digest = lambda s: hashlib.sha256(s.encode()).hexdigest()
canonical = lambda x: json.dumps(x, ensure_ascii=False, sort_keys=True)
norm = lambda s: ''.join(c for c in unicodedata.normalize('NFKC', s) if c.isalnum())
jl = lambda p: [json.loads(s) for s in Path(p).read_text().splitlines()]
obj = lambda p: json.loads(Path(p).read_text())

@lru_cache(None)
def source_raw(path):
    p = Path(path)
    if p.suffix == '.txt':
        return p.read_text().splitlines()
    if p.suffix == '.pdf':
        return [page.extract_text() for page in PdfReader(p).pages]
    return subprocess.run(['textutil', '-convert', 'txt', '-stdout', str(p)], check=True, capture_output=True, text=True).stdout

@lru_cache(None)
def check_render(source, page, image, expected_sha):
    assert sha(image) == expected_sha
    with tempfile.TemporaryDirectory(prefix='v14-source-qa-') as directory:
        out = Path(directory) / 'page'
        subprocess.run(['pdftoppm', '-f', str(page), '-l', str(page), '-r', '130', '-singlefile', '-png', source, str(out)], check=True)
        assert sha(out.with_suffix('.png')) == expected_sha
    return True

def verify_literal(c, source, visual=None):
    raw = source_raw(source)
    if Path(source).suffix == '.txt':
        literal = '\n'.join(raw[int(line[1:]) - 1] for line in c['source_lines'])
        assert norm(c['text']) == norm(literal)
        return 'stated_original_lines_exact_normalized'
    if Path(source).suffix == '.pdf':
        literal = '\n'.join(raw[page - 1] for page in c['pages'])
        if not literal.strip():
            assert visual and visual['page'] == 17 and c['pages'] == [17]
            assert check_render(source, visual['page'], visual['path'], visual['sha256'])
            return 'source_bound_fresh_render_plus_recorded_visual_review'
        assert norm(c['text']) in norm(literal)
        return 'stated_original_pdf_pages_normalized_literal'
    assert norm(c['text']) in norm(raw)
    return 'original_word_textutil_literal'

assert not DEST.exists(), 'Never overwrite an audit'
old = jl(B / 'effective_blind_inputs_v13.jsonl'); new = jl(B / 'effective_blind_inputs_v14.jsonl')
rold = jl(B / 'rule_inputs_shared_v13.jsonl'); rnew = jl(B / 'rule_inputs_shared_v14.jsonl')
m = obj(B / 'material_v14_manifest.json'); proposal = obj(B / 'audit/extended_fragment_source_proposal_v14.json'); review = obj(m['review_path'])
targets = proposal['affected_ids']; pby = {x['id']: x for x in proposal['proposals']}
checks = {
    'all_4924_unique_ids_order_original_text_unchanged': len(new) == len(rnew) == len({r['id'] for r in new}) == 4924 and all(a['id'] == b['id'] and a['text'] == b['text'] for a, b in zip(old, new)) and all(a['id'] == b['id'] and a['input']['unit_id'] == b['input']['unit_id'] and a['input']['unit_text'] == b['input']['unit_text'] for a, b in zip(rold, rnew)),
    'exactly_78_approved_context_and_rule_records_changed': [a['id'] for a, b in zip(old, new) if a != b] == targets == [a['id'] for a, b in zip(rold, rnew) if a != b] and len(targets) == 78,
    'all_4924_two_methods_exact_context_bytes': all(a['id'] == b['id'] and a['text'] == b['input']['unit_text'] and json.dumps(a['contexts'], ensure_ascii=False) == json.dumps(b['input']['llm_v29_shared_context'], ensure_ascii=False) for a, b in zip(new, rnew)),
    'v13_frozen_files_unchanged': all(sha(B / p) == h for p, h in m['prior_v13_files_preserved_sha256'].items()),
    'v14_input_manifest_shas_match': sha(B / 'effective_blind_inputs_v14.jsonl') == m['new_llm_sha256'] and sha(B / 'rule_inputs_shared_v14.jsonl') == m['new_rule_sha256'],
    'all_original_source_candidate_files_unchanged': all(sha(p) == h for p, h in m['original_source_and_candidate_sha256'].items()),
    'prior_frozen_classifier_and_manual_bytes_unchanged': all(sha(p) == h for p, h in m['production_manual_freeze_hashes_verified'].items()),
    'proposal_review_build_shas_authentic': sha(m['proposal_path']) == m['proposal_sha256'] == review['proposal_sha256'] and sha(m['review_path']) == m['review_sha256'] and sha(B / 'complete_shared_material_v14.py') == m['build_script_sha256'],
    'only_approved_source_fields_changed': True,
}
details = []; family_verified = {}; type_counts = Counter()
for prev, row, rprev, rrow in zip(old, new, rold, rnew):
    rid = row['id']
    if rid not in pby:
        continue
    x = pby[rid]; ctx = row['contexts']; r = rrow['input']
    restored = copy.deepcopy(row); restored_r = copy.deepcopy(rrow)
    assert row['context_usage'] == prev['context_usage'] and 'do not inherit labels' in row['context_usage']
    assert 'RECODE25-' not in json.dumps(ctx, ensure_ascii=False)
    if x['repair_type'] == 'actual_local_list_parent_predicate':
        type_counts['parent'] += 1
        c = ctx['source_local_list_family_v14']; parent = ctx['verified_parent_context'][-1]
        assert c == r['source_local_list_family_v14']
        assert parent == r['verified_parent_context'][-1] == ctx['verified_context_certificates']['verified_parent_context'][-1] == c['actual_parent_predicate']
        assert parent['repair_version'] == 'v14-source-local-list-predicate' and parent['context_role'] == 'actual_local_list_parent_predicate'
        assert parent['unit_id'] == c['current_unit_id'] == r['unit_id']
        assert parent['original_unit_sha256'] == c['current_unit_sha256'] == digest(row['text'])
        assert parent['text_sha256'] == digest(parent['text'])
        assert c['repair_version'] == 'v14-source-local-list-family' and c['context_role'] == 'actual_local_list_family'
        assert c['contexts'] == x['complete_local_family_contexts'] and c['contexts_sha256'] == digest(canonical(c['contexts']))
        assert parent['text'] == c['contexts'][0]['text'] and parent['paragraph_id'] == c['contexts'][0]['paragraph_id']
        assert parent['usage'] == c['usage'] and '不得' in parent['usage'] and '标签' in parent['usage']
        assert parent['verification']['verified'] is True
        cp = obj(c['candidate_path']); ps = cp['paragraphs']; ix = {p['id']: i for i, p in enumerate(ps)}
        cs = c['contexts']; first, last = cs[0]['paragraph_id'], cs[-1]['paragraph_id']
        assert [a['paragraph_id'] for a in cs] == [a['id'] for a in ps[ix[first]:ix[last] + 1]]
        boundary = c['structure_boundary']['next_boundary']
        assert boundary == x['next_boundary'] and ps[ix[last] + 1]['id'] == boundary['paragraph_id']
        assert {p['paragraph_id'] for p in ctx['paragraph_context']} <= {a['paragraph_id'] for a in cs[1:]}
        for a in cs + [boundary]:
            p = ps[ix[a['paragraph_id']]]
            assert a['text'] == p['text'] and a['pages'] == p.get('pages', []) and a['source_lines'] == p.get('line_ids', [])
            assert Path(p.get('source_file') or cp['source']).resolve() == Path(c['source_path']).resolve()
            verify_literal(a, c['source_path'], c.get('source_visual_evidence_v14'))
        assert parent['source_sha256'] == sha(c['source_path']) == c['source_sha256'] == (r.get('unit_source_sha256') or r['source_sha256'])
        assert parent['candidate_sha256'] == sha(c['candidate_path']) == c['candidate_sha256'] == r['candidate_sha256']
        family_verified[x['family_head_unit']] = {'source_path': c['source_path'], 'parent': first, 'continuous_paragraph_n': len(cs), 'next_boundary': boundary['paragraph_id'], 'all_original_source_paragraphs_verified': True}
        restored['contexts'].pop('source_local_list_family_v14')
        restored['contexts']['verified_parent_context'].pop()
        restored['contexts']['verified_context_certificates']['verified_parent_context'].pop()
        if 'verified_parent_context' not in prev['contexts']['verified_context_certificates']:
            restored['contexts']['verified_context_certificates'].pop('verified_parent_context')
        restored_r['input'].pop('source_local_list_family_v14'); restored_r['input']['verified_parent_context'].pop()
        if 'verified_parent_context' not in rprev['input']:
            restored_r['input'].pop('verified_parent_context')
        field = 'source_local_list_family_v14'
    else:
        type_counts['attachment_heading'] += 1
        c = ctx['source_component_boundary_v14']; heading = c['actual_component_heading']
        assert c == r['source_component_boundary_v14']
        assert c['repair_version'] == 'v14-source-component-boundary' and heading['repair_version'] == 'v14-source-component-heading'
        assert heading['context_role'] == 'actual_independent_attachment_heading'
        assert 'paragraph_id' not in heading and heading['source_key'] == 'original_word_attachment_title_paragraphs'
        assert heading['text'] == x['actual_component_heading']['text'] and heading['text_sha256'] == digest(heading['text'])
        actual = {'text': heading['text'], 'pages': []}
        assert ctx['nearest_preceding_heading'] == r['nearest_preceding_heading'] == actual
        raw = source_raw(c['source_path']); assert isinstance(raw, str)
        assert digest(raw) == c['verification']['attachment_extracted_text_sha256'] and norm(heading['text']) in norm(raw)
        cp = obj(c['candidate_path']); ps = [p for p in cp['paragraphs'] if p.get('origin') == 'verified_local_attachment' and p.get('attachment_title') == '试点工作申报资料要求']
        cs = c['contexts']; assert len(ps) == len(cs) == 9 and cs == x['complete_actual_attachment_items']
        assert c['contexts_sha256'] == digest(canonical(cs)) and c['structure_boundary']['next_boundary'] == 'end_of_original_word_attachment'
        assert [a['paragraph_id'] for a in cs] == [p['id'] for p in ps]
        pos = -1
        for a, p in zip(cs, ps):
            assert a['text'] == p['text'] and a['source_lines'] == p['line_ids'] and a['pages'] == []
            verify_literal(a, c['source_path'])
            here = norm(raw).index(norm(a['text'])); assert here > pos; pos = here
        assert norm(raw).endswith(norm(cs[-1]['text']))
        assert not any(norm(p['text']) == norm(heading['text']) for p in cp['paragraphs'])
        assert heading['source_sha256'] == c['source_sha256'] == sha(c['source_path']) == r['unit_source_sha256']
        assert heading['candidate_sha256'] == c['candidate_sha256'] == sha(c['candidate_path']) == r['candidate_sha256']
        if x['first_item_wrong_cross_component_immediate_previous_requires_replacement']:
            type_counts['attachment_previous'] += 1
            assert ctx['immediately_preceding_paragraph'] == r['immediately_preceding_paragraph'] == actual
            restored['contexts']['immediately_preceding_paragraph'] = prev['contexts']['immediately_preceding_paragraph']
            restored_r['input']['immediately_preceding_paragraph'] = rprev['input']['immediately_preceding_paragraph']
        restored['contexts']['nearest_preceding_heading'] = prev['contexts']['nearest_preceding_heading']
        restored_r['input']['nearest_preceding_heading'] = rprev['input']['nearest_preceding_heading']
        restored['contexts'].pop('source_component_boundary_v14'); restored_r['input'].pop('source_component_boundary_v14')
        field = 'source_component_boundary_v14'
    assert c['verification']['verified'] is True and c['verification']['review_sha256'] == sha(m['review_path'])
    assert c['frozen_rule_validation_or_consumption_not_claimed'] is True
    restored_r['input']['llm_v29_shared_context'] = rprev['input']['llm_v29_shared_context']
    checks['only_approved_source_fields_changed'] &= restored == prev and restored_r == rprev
    details.append({'id': rid, 'original_text_sha256': digest(row['text']), 'typed_source_field': field, 'authentic_v14_certificate': True, 'source_candidate_sha_and_current_unit_binding_verified': True, 'parent_or_component_relationship_verified': True, 'no_label_inheritance': True})
checks['69_typed_parents_9_component_headings_1_previous'] = type_counts == {'parent': 69, 'attachment_heading': 9, 'attachment_previous': 1}
checks['19_distinct_actual_list_families_and_1_attachment'] = len(family_verified) == 19 and len(review['families']) == 20
checks['all_78_certificates_source_authenticated'] = len(details) == 78
checks['source_certificates_use_true_v14_no_legacy_version_impersonation'] = all(x['authentic_v14_certificate'] for x in details)
sample = obj(B / 'admin/future_human_v4_sampling_PRIVATE.json'); sample5 = obj(B / 'admin/future_human_v5_sampling_PRIVATE.json')
nb = {x['id']: x for x in new}; ob = {x['id']: x for x in old}
future = []
for coder in ['A', 'C']:
    map4 = {x['blind_id']: x['original_id'] for x in sample['mapping'] if x['coder'] == coder}
    map5 = {x['blind_id']: x['original_id'] for x in sample5['mapping'] if x['coder'] == coder}
    p4 = obj(B / f'future-human-validation-v4/真人{coder}-无答案材料.json'); p5 = obj(B / f'future-human-validation-v5/真人{coder}-无答案材料.json')
    assert len(p4['rows']) == len(p5['rows']) == 240
    differences = []
    for a, b in zip(p4['rows'], p5['rows']):
        rid = map4[a['id']]; assert rid == map5[b['id']]
        assert a['text'] == b['text'] == nb[rid]['text'] and a['contexts'] == ob[rid]['contexts'] and b['contexts'] == nb[rid]['contexts']
        assert all(v == '' for v in b['coding'].values())
        if a['contexts'] != b['contexts']:
            differences.append({'original_id': rid, 'v4_blind_id': a['id'], 'v5_blind_id': b['id']})
    assert {x['original_id'] for x in differences} == {'RECODE25-04371', 'RECODE25-04390'}
    future.append({'coder': coder, 'all_240_v4_contexts_equal_v13': True, 'all_240_v5_contexts_equal_v14': True, 'exactly_two_actual_unit_context_changes': differences})
future_qa = obj(B / 'audit/future_human_v5_source_only_qa.json')
checks['future_v4_to_v5_all_480_source_contexts_verified'] = len(future) == 2
checks['future_v5_independent_full_240x2_qa_all_pass'] = future_qa['all_checks_pass'] is True and all(future_qa['checks'].values())
checks['future_same_sample_probabilities_weights_and_order'] = sample['sample'] == sample5['sample'] and sample5['prior_v4_mapping'] == sample['mapping']
assert all(checks.values()), checks
report = {'qa_version': 'independent-source-v14', 'status': 'PASS', 'scope': 'Source-only: no labels, reference answers, confirmation, statistics, LLM/rule predictions or review PRIVATE mappings read. Only future-human sampling PRIVATE files used to preserve sample.', 'checks': checks, 'affected_ids': targets, 'details': details, 'source_family_checks': family_verified, 'fresh_image_only_render_regenerated_and_sha_compared': True, 'future_human_v4_to_v5_full_population_verification': future, 'no_frozen_classifier_new_field_consumption_claim': True, 'v14_llm_sha256': sha(B / 'effective_blind_inputs_v14.jsonl'), 'v14_rule_sha256': sha(B / 'rule_inputs_shared_v14.jsonl'), 'v14_manifest_sha256': sha(B / 'material_v14_manifest.json'), 'source_review_sha256': sha(m['review_path']), 'future_v5_source_qa_sha256': sha(B / 'audit/future_human_v5_source_only_qa.json'), 'qa_script_sha256': sha(Path(__file__))}
DEST.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'status': report['status'], 'checks': checks, 'counts': dict(type_counts), 'future_changes': future}, ensure_ascii=False, indent=2))
