"""Seal the authorized 78 source-only repairs, without touching prior versions."""
from pathlib import Path
import copy
import hashlib
import json

B = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
digest = lambda s: hashlib.sha256(s.encode()).hexdigest()
canonical = lambda x: json.dumps(x, ensure_ascii=False, sort_keys=True)
jl = lambda p: [json.loads(x) for x in Path(p).read_text().splitlines()]
P = B / 'audit/extended_fragment_source_proposal_v14.json'
REVIEW = B / 'audit/extended_fragment_source_review_v14.json'
for name in ['effective_blind_inputs_v14.jsonl', 'rule_inputs_shared_v14.jsonl', 'material_v14_manifest.json']:
    assert not (B / name).exists(), 'Never overwrite v14'
prop = json.loads(P.read_text()); review = json.loads(REVIEW.read_text())
assert review['status'] == 'PASS' and review['proposal_sha256'] == sha(P)
assert review['affected_ids'] == prop['affected_ids'] and len(prop['affected_ids']) == 78
reviewed = {x['family']: x for x in review['families']}
prior = {name: sha(B / name) for name in ['effective_blind_inputs_v13.jsonl', 'rule_inputs_shared_v13.jsonl', 'material_v13_manifest.json']}
assert prior['effective_blind_inputs_v13.jsonl'] == prop['v13_llm_sha256']
assert prior['rule_inputs_shared_v13.jsonl'] == prop['v13_rule_sha256']
old_manifest = json.loads((B / 'material_v13_manifest.json').read_text())
frozen = old_manifest['production_manual_freeze_hashes_verified']
assert all(sha(p) == h for p, h in frozen.items())
source_hashes = {f[k + '_path']: f[k + '_sha256'] for f in review['families'] for k in ['source', 'candidate']}
assert all(sha(p) == h for p, h in source_hashes.items())
ll = jl(B / 'effective_blind_inputs_v13.jsonl'); rr = jl(B / 'rule_inputs_shared_v13.jsonl')
old_ll = copy.deepcopy(ll); old_rr = copy.deepcopy(rr)
lb = {x['id']: x for x in ll}; rb = {x['id']: x['input'] for x in rr}
usage = '仅补充本单位实际来源的对象、控制谓词、资格条件或组件关系。父段、兄弟段和标题均不得向当前单位自动传递任何维度标签；不增加分析单位。'
for x in prop['proposals']:
    rid = x['id']; row = lb[rid]; r = rb[rid]; ctx = row['contexts']
    assert row['text'] == r['unit_text'] == x['current_unit']
    assert digest(row['text']) == x['current_unit_sha256']
    assert digest(canonical(ctx)) == x['old_context_sha256']
    if x['repair_type'] == 'actual_local_list_parent_predicate':
        f = reviewed[x['family_head_unit']]
        contexts = copy.deepcopy(x['complete_local_family_contexts'])
        parent = copy.deepcopy(x['actual_parent_context'])
        parent.update(repair_version='v14-source-local-list-predicate', context_role='actual_local_list_parent_predicate', unit_id=r['unit_id'], original_unit_sha256=digest(row['text']), text_sha256=digest(parent['text']), usage=usage)
        if 'fresh_visual_evidence' in f:
            parent['source_visual_evidence_v14'] = copy.deepcopy(f['fresh_visual_evidence'])
        ctx.setdefault('verified_parent_context', []).append(copy.deepcopy(parent))
        ctx.setdefault('verified_context_certificates', {}).setdefault('verified_parent_context', []).append(copy.deepcopy(parent))
        r.setdefault('verified_parent_context', []).append(copy.deepcopy(parent))
        cert = {'repair_version': 'v14-source-local-list-family', 'context_role': 'actual_local_list_family', 'current_unit_id': r['unit_id'], 'current_unit_sha256': digest(row['text']), 'source_path': f['source_path'], 'source_sha256': f['source_sha256'], 'candidate_path': f['candidate_path'], 'candidate_sha256': f['candidate_sha256'], 'actual_parent_predicate': copy.deepcopy(parent), 'contexts': contexts, 'contexts_sha256': digest(canonical(contexts)), 'structure_boundary': {'first_paragraph': contexts[0]['paragraph_id'], 'last_paragraph': contexts[-1]['paragraph_id'], 'all_paragraphs_in_interval_included': True, 'next_boundary': copy.deepcopy(x['next_boundary'])}, 'usage': usage, 'verification': {'verified': True, 'method': 'v14_independent_original_source_family_review', 'review_path': str(REVIEW), 'review_sha256': sha(REVIEW)}, 'frozen_rule_validation_or_consumption_not_claimed': True}
        if 'fresh_visual_evidence' in f:
            cert['source_visual_evidence_v14'] = copy.deepcopy(f['fresh_visual_evidence'])
        ctx['source_local_list_family_v14'] = copy.deepcopy(cert)
        r['source_local_list_family_v14'] = copy.deepcopy(cert)
    else:
        assert x['repair_type'] == 'actual_source_component_heading_and_boundary'
        f = reviewed['independent_original_word_attachment_material_requirements']
        heading = copy.deepcopy(x['actual_component_heading'])
        heading.update(repair_version='v14-source-component-heading', context_role='actual_independent_attachment_heading', text_sha256=digest(heading['text']), usage=usage)
        assert 'paragraph_id' not in heading
        actual_heading = {'text': heading['text'], 'pages': []}
        ctx['nearest_preceding_heading'] = copy.deepcopy(actual_heading)
        r['nearest_preceding_heading'] = copy.deepcopy(actual_heading)
        if x['first_item_wrong_cross_component_immediate_previous_requires_replacement']:
            ctx['immediately_preceding_paragraph'] = copy.deepcopy(actual_heading)
            r['immediately_preceding_paragraph'] = copy.deepcopy(actual_heading)
        items = copy.deepcopy(x['complete_actual_attachment_items'])
        cert = {'repair_version': 'v14-source-component-boundary', 'context_role': 'actual_independent_attachment_component', 'current_unit_id': r['unit_id'], 'current_unit_sha256': digest(row['text']), 'actual_component_heading': heading, 'source_path': f['source_path'], 'source_sha256': f['source_sha256'], 'candidate_path': f['candidate_path'], 'candidate_sha256': f['candidate_sha256'], 'contexts': items, 'contexts_sha256': digest(canonical(items)), 'structure_boundary': {'first_paragraph': items[0]['paragraph_id'], 'last_paragraph': items[-1]['paragraph_id'], 'all_nine_actual_attachment_items_included': True, 'next_boundary': 'end_of_original_word_attachment', 'first_item_previous_is_real_source_title': x['first_item_wrong_cross_component_immediate_previous_requires_replacement']}, 'verification': {'verified': True, 'method': 'original_word_textutil_title_all_nine_items_and_end_verified', 'attachment_extracted_text_sha256': f['attachment_extracted_text_sha256'], 'review_path': str(REVIEW), 'review_sha256': sha(REVIEW)}, 'no_fake_candidate_heading_paragraph': True, 'usage': usage, 'frozen_rule_validation_or_consumption_not_claimed': True}
        ctx['source_component_boundary_v14'] = copy.deepcopy(cert)
        r['source_component_boundary_v14'] = copy.deepcopy(cert)
    r['llm_v29_shared_context'] = copy.deepcopy(ctx)
    assert 'RECODE25-' not in json.dumps(ctx, ensure_ascii=False), 'Source contexts must not disclose global review IDs'
assert len(ll) == len(rr) == 4924
assert all(a['id'] == b['id'] and a['text'] == b['text'] for a, b in zip(ll, old_ll))
assert all(a['id'] == b['id'] and a['input']['unit_id'] == b['input']['unit_id'] and a['input']['unit_text'] == b['input']['unit_text'] for a, b in zip(rr, old_rr))
assert all(a['id'] == b['id'] and a['contexts'] == b['input']['llm_v29_shared_context'] for a, b in zip(ll, rr))
changed = [a['id'] for a, b in zip(ll, old_ll) if a != b]
assert changed == prop['affected_ids'] == [a['id'] for a, b in zip(rr, old_rr) if a != b]
for name, rows in [('effective_blind_inputs_v14.jsonl', ll), ('rule_inputs_shared_v14.jsonl', rr)]:
    (B / name).write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows))
manifest = {'material_version': 'v14', 'status': 'sealed_authorized_source_only_repair', 'source_only': True, 'n': 4924, 'base_material_version': 'v13', 'affected_ids': changed, 'incremental_context_changed_n': 78, 'source_family_n': 20, 'parent_repair_unit_n': 69, 'attachment_heading_unit_n': 9, 'attachment_cross_component_previous_n': 1, 'unit_text_changes': 0, 'unit_id_changes': 0, 'unit_order_changes': 0, 'new_analysis_units': 0, 'two_methods_same_text_and_context': True, 'coding_standard_unchanged': 'CAL-5D-v1.3 + operational-v1.4', 'classification_code_unchanged': True, 'manual_unchanged': True, 'new_parent_certificate_version': 'v14-source-local-list-predicate', 'new_typed_source_fields': ['source_local_list_family_v14', 'source_component_boundary_v14'], 'new_fields_available_byte_equally_to_both_methods': True, 'frozen_rule_validation_or_consumption_of_new_fields_not_claimed': True, 'no_labels_transferred': True, 'references_or_predictions_read_by_preparation_script': False, 'prior_v13_files_preserved_sha256': prior, 'production_manual_freeze_hashes_verified': frozen, 'original_source_and_candidate_sha256': source_hashes, 'proposal_path': str(P), 'proposal_sha256': sha(P), 'review_path': str(REVIEW), 'review_sha256': sha(REVIEW), 'build_script_sha256': sha(Path(__file__)), 'new_llm_sha256': sha(B / 'effective_blind_inputs_v14.jsonl'), 'new_rule_sha256': sha(B / 'rule_inputs_shared_v14.jsonl'), 'actual_model_rerun_required_on_changed_context_payloads': True, 'scope': [{'family': f['family'], 'n': f['affected_n'], 'affected_ids': f['affected_ids'], 'reason': f['reason']} for f in review['families']]}
(B / 'material_v14_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
assert all(sha(B / p) == h for p, h in prior.items())
assert all(sha(p) == h for p, h in (frozen | source_hashes).items())
print(json.dumps({k: manifest[k] for k in ['material_version', 'n', 'incremental_context_changed_n', 'new_llm_sha256', 'new_rule_sha256']}, ensure_ascii=False))
