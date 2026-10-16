"""Create material04 for one verified decimal-section reference, without coding."""
from pathlib import Path
import copy
import hashlib
import json
from datetime import datetime
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent
MODEL_BASE = BASE / '共用纯来源材料03/source_only_with_scope03.jsonl'
RULE_BASE = BASE / '共用纯来源材料03/rule_inputs_material03.jsonl'
PROPOSAL = BASE / 'runtime/actual_reference03894_source01/suggested_complete_reference_patch01.json'
ORIGINAL_BATCH = BASE / 'runtime/full-common-source02/batches/batch-0156/input.json'
TARGET = 'RECODE25-03894'
REFERENCE_FIELD = 'explicitly_cited_qualifications_v12'
SCOPE_FIELD = 'source_application_scope04'
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
text_sha = lambda value: hashlib.sha256(value.encode('utf-8')).hexdigest()
payload_sha = lambda value: text_sha(json.dumps(value, ensure_ascii=False, sort_keys=True))


def new_json(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    assert sha(MODEL_BASE) == '578739c66f6d44dd31d5315b318985b5ee7260b473842330c15674c254463fe9'
    assert sha(RULE_BASE) == 'ef5170455630bda8b32b547dd681be569e919a74d8bfec420acef3df25fc6f9f'
    assert sha(PROPOSAL) == '2fc6e02f162e1c99a79629cacdd1cc4f9570fbdc65ea5a4274a15843c05a9922'
    proposal = json.loads(PROPOSAL.read_text())
    assert proposal['status'] == 'SUGGESTED_ONLY_NOT_APPLIED' and proposal['target_id'] == TARGET
    for key in ('source_pdf', 'source_candidate'):
        assert sha(proposal[key]['path']) == proposal[key]['sha256']
    candidate = json.loads(Path(proposal['source_candidate']['path']).read_text())
    paragraphs = candidate['paragraphs']
    by_paragraph = {p['id']: p for p in paragraphs}
    model_lines = MODEL_BASE.read_bytes().splitlines(keepends=True)
    rule_lines = RULE_BASE.read_bytes().splitlines(keepends=True)
    model_rows = [json.loads(line) for line in model_lines]
    rule_rows = [json.loads(line) for line in rule_lines]
    assert len(model_rows) == len(rule_rows) == 4924
    assert [r['id'] for r in model_rows] == [r['id'] for r in rule_rows]
    index = next(i for i, r in enumerate(model_rows) if r['id'] == TARGET)
    assert index == 3893
    model = copy.deepcopy(model_rows[index])
    rule = copy.deepcopy(rule_rows[index])
    current = rule['input']
    shared = current['llm_v29_shared_context']
    assert model['text'] == current['unit_text'] == proposal['target_current_text_unchanged']
    target_candidates = [u for u in candidate['unit_candidates'] if u['id'] == current['unit_id']]
    assert len(target_candidates) == 1 and target_candidates[0]['text'] == model['text']
    assert current['unit_source'] == proposal['source_pdf']['path']
    assert current['unit_source_sha256'] == proposal['source_pdf']['sha256']
    assert current['candidate_file'] == proposal['source_candidate']['path']
    assert current['candidate_sha256'] == proposal['source_candidate']['sha256']

    heading = by_paragraph['p0018']
    assert heading['text'] == '二中药' and heading['pages'] == [4]
    heading_positions = [i for i, c in enumerate(model['contexts']) if c['kind'] == 'heading']
    assert len(heading_positions) == 1
    hp = heading_positions[0]
    old_heading = copy.deepcopy(model['contexts'][hp])
    assert old_heading['text'] == '一、化学药品与生物制品'
    model['contexts'][hp] = {
        'context_id': 'CTX-' + text_sha('|'.join((TARGET, current['unit_source_sha256'], 'current_heading', 'p0018')))[:20],
        'kind': 'heading', 'source_document': 'D-' + current['unit_source_sha256'][:16],
        'structure': {'paragraph_id': 'p0018', 'pages': heading['pages'], 'source_lines': heading['line_ids']},
        'text': heading['text']}
    nearest = {'text': heading['text'], 'pages': copy.deepcopy(heading['pages'])}
    current['nearest_preceding_heading'] = copy.deepcopy(nearest)
    shared['nearest_preceding_heading'] = copy.deepcopy(nearest)

    section_contexts = copy.deepcopy(proposal['model_source_contexts_to_append_complete_sections'])
    scope_contexts = copy.deepcopy(proposal['model_source_contexts_to_append_scope_separately'])
    assert len(section_contexts) == 11 and len(scope_contexts) == 4
    for context in section_contexts + scope_contexts:
        source_paragraph = by_paragraph[context['structure']['paragraph_id']]
        assert context['text'] == source_paragraph['text']
        assert context['structure']['pages'] == source_paragraph['pages']
        assert context['structure']['source_lines'] == source_paragraph['line_ids']
    model['contexts'].extend(section_contexts + scope_contexts)
    assert len({c['context_id'] for c in model['contexts']}) == len(model['contexts'])

    assert REFERENCE_FIELD not in current and REFERENCE_FIELD not in shared
    assert SCOPE_FIELD not in current and SCOPE_FIELD not in shared
    raw_sections = proposal['rule_source_sections_to_append']
    raw_by_paragraph = {p['paragraph_id']: p for p in raw_sections}
    references = []
    for section in proposal['complete_sections']:
        ids = section['complete_paragraph_ids']
        start = next(i for i, p in enumerate(paragraphs) if p['id'] == ids[0])
        assert [p['id'] for p in paragraphs[start:start + len(ids)]] == ids
        following = paragraphs[start + len(ids)]
        assert following['id'] == section['exclusive_next_boundary']['paragraph_id']
        contexts = [copy.deepcopy(raw_by_paragraph[pid]) for pid in ids]
        assert all('article' not in c and 'authentication_v34' not in c and 'verification' not in c for c in contexts)
        for context in contexts:
            assert context['text'] == by_paragraph[context['paragraph_id']]['text']
            assert context['source_path'] == current['unit_source']
            assert context['source_sha256'] == current['unit_source_sha256']
            assert context['candidate_path'] == current['candidate_file']
            assert context['candidate_sha256'] == current['candidate_sha256']
        references.append({
            'reference_address': '化学药品与生物制品资料要求 ' + section['section'] + ' 项下',
            'contexts': contexts,
            'structure_boundary': {
                'first_paragraph_id': ids[0], 'last_paragraph_id': ids[-1],
                'next_candidate_paragraph_id': following['id'],
                'next_candidate_paragraph_text': following['text'],
                'all_paragraphs_in_interval_included': True}})
    reference_packet = {
        'current_unit_sha256': text_sha(current['unit_text']),
        'current_unit_id': current['unit_id'],
        'current_unit_source_path': current['unit_source'],
        'current_unit_source_sha256': current['unit_source_sha256'],
        'current_unit_candidate_path': current['candidate_file'],
        'current_unit_candidate_sha256': current['candidate_sha256'],
        'references': references, 'references_sha256': payload_sha(references)}
    current[REFERENCE_FIELD] = copy.deepcopy(reference_packet)
    shared[REFERENCE_FIELD] = copy.deepcopy(reference_packet)
    raw_scope = []
    for scope in proposal['actual_source_scope']:
        pid = scope['paragraph_id']
        assert scope['text'] == by_paragraph[pid]['text']
        raw_scope.append({
            'paragraph_id': pid, 'text': scope['text'], 'pages': scope['pages'],
            'source_lines': scope['source_line_ids'], 'source_path': current['unit_source'],
            'source_sha256': current['unit_source_sha256'], 'candidate_path': current['candidate_file'],
            'candidate_sha256': current['candidate_sha256'],
            'role': 'source_application_scope' if pid in ('p0001', 'p0002') else 'source_chapter_heading'})
    current[SCOPE_FIELD] = copy.deepcopy(raw_scope)
    shared[SCOPE_FIELD] = copy.deepcopy(raw_scope)

    model_new = list(model_lines)
    rule_new = list(rule_lines)
    model_new[index] = (json.dumps(model, ensure_ascii=False) + '\n').encode('utf-8')
    rule_new[index] = (json.dumps(rule, ensure_ascii=False) + '\n').encode('utf-8')
    model_output = ROOT / 'source_only_with_scope04.jsonl'
    rule_output = ROOT / 'rule_inputs_material04.jsonl'
    for path, lines in ((model_output, model_new), (rule_output, rule_new)):
        with path.open('xb') as stream:
            stream.write(b''.join(lines))

    original = json.loads(ORIGINAL_BATCH.read_text())['rows']
    original_ids = [r['id'] for r in original]
    assert len(original_ids) == 25 and original_ids == [r['id'] for r in model_rows[3875:3900]]
    assert [json.loads(line)['id'] for line in model_new[3875:3900]] == original_ids
    subset = ROOT / 'source_recovery_original_batch156.jsonl'
    with subset.open('xb') as stream:
        stream.write(b''.join(model_new[3875:3900]))
    mapping = {
        'purpose': 'Complete original semantic batch 156 restored from material04; no output, label, or metric selection.',
        'source_material': str(model_output), 'source_material_sha256': sha(model_output),
        'recovery_input': str(subset), 'recovery_input_sha256': sha(subset), 'n': 25,
        'original_batch_input': {'path': str(ORIGINAL_BATCH), 'sha256': sha(ORIGINAL_BATCH)},
        'mapping': [{'recovery_batch': 1, 'original_batch': 156, 'ids': original_ids}],
        'record_mapping': [{'id': rid, 'recovery_row_1_based': i + 1,
                            'material04_row_1_based': 3876 + i, 'original_batch': 156,
                            'original_position_in_batch_1_based': i + 1} for i, rid in enumerate(original_ids)],
        'model_or_coder_called': False, 'recovery_run_not_started_by_builder': True}
    mapping_path = ROOT / 'source_recovery_original_batch156_mapping04.json'
    new_json(mapping_path, mapping)

    actual_model_lines = model_output.read_bytes().splitlines(keepends=True)
    actual_rule_lines = rule_output.read_bytes().splitlines(keepends=True)
    for old, actual in ((model_lines, actual_model_lines), (rule_lines, actual_rule_lines)):
        assert len(actual) == 4924
        assert [i for i, (a, b) in enumerate(zip(old, actual)) if a != b] == [3893]
        assert [json.loads(line)['id'] for line in old] == [json.loads(line)['id'] for line in actual]
        assert old[63] == actual[63]
    assert sha(MODEL_BASE) == '578739c66f6d44dd31d5315b318985b5ee7260b473842330c15674c254463fe9'
    assert sha(RULE_BASE) == 'ef5170455630bda8b32b547dd681be569e919a74d8bfec420acef3df25fc6f9f'
    assert json.loads(actual_model_lines[index]) == model and json.loads(actual_rule_lines[index]) == rule
    assert model['text'] == model_rows[index]['text'] and current['unit_text'] == rule_rows[index]['input']['unit_text']
    assert all(model['contexts'][i] == old for i, old in enumerate(model_rows[index]['contexts']) if i != hp)
    assert len(model['contexts']) - len(model_rows[index]['contexts']) == 15
    assert payload_sha(shared[REFERENCE_FIELD]['references']) == shared[REFERENCE_FIELD]['references_sha256']

    coder_dir = BASE.parent.parent / '自动规则编码/共同定义候选/candidate11/runtime'
    interfaces = ['source_context_adapter_v34.py', 'common_definition_stage.py', 'referenced_relations_v34.py']
    interface_note = {
        'existing_reference_container': REFERENCE_FIELD,
        'reference_address_type': 'Actual decimal module section address; no law article field or fake article number.',
        'source_adapter_generic_references_support_complete_candidate_intervals': True,
        'scope_source_only_field': SCOPE_FIELD,
        'scope_field_not_consumed_by_existing_adapter': True,
        'semantic_bridge_has_no_explicit_decimal_same_requirement_pattern': True,
        'no_claim_that_source_delivery_changes_rule_semantic_support': True,
        'authentication_fields_not_prefilled': True, 'coder_not_modified_or_executed': True,
        'inspected_interface_files': [{'path': str(coder_dir / name), 'sha256': sha(coder_dir / name)} for name in interfaces]}
    report = {
        'status': 'complete_actual_source_material04_not_label_validation',
        'created_at': datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(timespec='seconds'),
        'builder_sha256': sha(Path(__file__)),
        'base_model': {'path': str(MODEL_BASE), 'sha256': sha(MODEL_BASE)},
        'base_rule': {'path': str(RULE_BASE), 'sha256': sha(RULE_BASE)},
        'source_proposal': {'path': str(PROPOSAL), 'sha256': sha(PROPOSAL)},
        'source_pdf': proposal['source_pdf'], 'source_candidate': proposal['source_candidate'],
        'n': 4924, 'changed_ids': [TARGET], 'changed_lines_1_based': [3894],
        'current_text_changed': False, 'old_model_heading': old_heading,
        'new_model_heading': model['contexts'][hp], 'other_existing_model_contexts_preserved': True,
        'full_cited_sections': [{'section': s['section'], 'paragraph_ids': s['complete_paragraph_ids']} for s in proposal['complete_sections']],
        'complete_section_paragraph_n': 11, 'complete_scope_paragraph_ids': ['p0001', 'p0002', 'p0003', 'p0018'],
        'interface_difference': interface_note,
        'outputs': {k: {'path': str(p), 'sha256': sha(p)} for k, p in {
            'model_inputs': model_output, 'rule_inputs': rule_output,
            'recovery_subset': subset, 'original_mapping': mapping_path}.items()},
        'all_other_4923_lines_byte_identical': True,
        'RECODE25_00064_unresolved_and_byte_unchanged': True,
        'manual_prompt_run_prediction_files_unchanged': True,
        'labels_human_references_metrics_not_read': True, 'model_or_coder_called': False,
        'does_not_claim_whole_corpus_material_or_semantic_validity': True}
    new_json(ROOT / 'material_patch_execution04.json', report)
    qa = {
        'status': 'PASS_actual_reopened_material_files_mechanical_QA_only',
        'changed_ids_both_methods': [TARGET], 'n_both_methods': 4924,
        'other_4923_lines_byte_identical_to03_both_methods': True,
        'current_text_unchanged_both_methods': True, 'ID_count_order_unchanged': True,
        'heading_corrected_to_actual_Chinese_chapter_both_methods': True,
        'old_nonheading_model_contexts_unchanged': True,
        'complete_three_sections_11_paragraphs_and_four_scope_paragraphs_source_bound': True,
        'rule_top_and_shared_reference_packets_identical': current[REFERENCE_FIELD] == shared[REFERENCE_FIELD],
        'rule_top_and_shared_scope_identical': current[SCOPE_FIELD] == shared[SCOPE_FIELD],
        'decimal_section_addresses_not_faked_as_law_articles': True,
        'authentication_not_prefilled_or_falsely_claimed': True,
        'subset_matches_complete_original_156_ID_order_and_material04_bytes': subset.read_bytes() == b''.join(actual_model_lines[3875:3900]),
        'RECODE25_00064_remains_unresolved_unchanged': True,
        'source_SHA_and_candidate_texts_checked': True,
        'coder_models_predictions_human_labels_metrics_not_executed_or_read': True,
        'outputs': report['outputs']}
    new_json(ROOT / 'mechanical_material_QA04.json', qa)
    print(json.dumps({'status': report['status'], 'changed_ids': report['changed_ids'],
                      'outputs': report['outputs'], 'QA': str(ROOT / 'mechanical_material_QA04.json')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
