"""Independent follow-up review. Only synthetic tests; no CLI/model calls."""
from pathlib import Path
import copy
import datetime
import hashlib
import importlib.util
import json
import sys

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
BASE = OUT.parent

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def read(path):
    return json.loads(Path(path).read_text())

def dump_new(path, obj):
    assert not path.exists(), 'Do not overwrite independent prior reviews.'
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')

def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result

def binding(paths):
    return [{'path': str(p), 'sha256': sha(p), 'bytes': p.stat().st_size} for p in paths]

def synthetic_change_tests(audit):
    old = {'id': 'SYNTHETIC', 'labels': {'S': 0, 'E': 0, 'Ec': 0, 'I': 0, 'F': 0},
           'dimension_reasons': {'S': 'reason'}, 'evidence': [], 'fairness_subtypes': [],
           'innovation_subtypes': [], 'safety_quality_basis': 'no_quality_basis'}
    tests = []
    edits = [('dimension_reasons', {'S': 'changed reason'}), ('evidence', [{'quote': 'synthetic'}]),
             ('fairness_subtypes', ['access']), ('innovation_subtypes', ['attribute']),
             ('safety_quality_basis', 'quality_only')]
    for field, value in edits:
        new = copy.deepcopy(old)
        new[field] = value
        assert new['labels'] == old['labels']
        assert audit.changed_fields(old, new) == [field]
        tests.append({'test': 'same_labels_changed_' + field, 'selected_for_review': True, 'PASS': True})
    new = copy.deepcopy(old)
    del new['evidence']
    assert audit.changed_fields(old, new) == ['evidence']
    tests.append({'test': 'field_missing', 'selected_for_review': True, 'PASS': True})
    new = copy.deepcopy(old)
    new['future_field'] = {'x': 1}
    assert audit.changed_fields(old, new) == ['future_field']
    tests.append({'test': 'field_added', 'selected_for_review': True, 'PASS': True})
    new = {key: old[key] for key in reversed(list(old))}
    assert audit.changed_fields(old, new) == []
    tests.append({'test': 'object_key_order_only', 'selected_for_review': False, 'PASS': True})
    old_issues = [{'id': 'SYNTHETIC', 'issue_type': 'boundary_note', 'description': 'A'}]
    new_issues = [{'id': 'SYNTHETIC', 'issue_type': 'boundary_note', 'description': 'B'}]
    assert audit.canonical(old_issues) != audit.canonical(new_issues)
    tests.append({'test': 'same_rows_changed_issue_records', 'selected_for_review': True, 'PASS': True})
    return tests

def main():
    previous = read(OUT / 'candidate07_independent_preflight_v1.json')
    assert sha(OUT / 'candidate07_independent_preflight_v1.json') == '4ba3ebc821ffbc978bc18b195c5f6e503e3bbcc0aa9d0cd80217109d6bb92d11'
    reviewer = module('independent07_v1_reusable_mechanics', OUT / 'review_candidate07_v1.py')
    paths = [BASE / name for name in ['execution_layer_PROPOSED.txt', 'candidate07_prompt_PROPOSED.txt',
        'candidate06_to_07_prompt.diff', 'synthetic20_pairs_PRIVATE_PROPOSED.json', 'synthetic20_inputs_PROPOSED.jsonl',
        'synthetic106_expected_PRIVATE_PROPOSED.json', 'predeclared_acceptance_PROPOSED.json',
        'candidate07_execution_plan_PROPOSED.json', 'run_bounded_candidate07.py', 'audit_candidate07.py',
        'prompt_conflict_and_mechanism_audit_PRIVATE.json', '候选07方案说明.txt']]
    start = binding(paths)
    declared_sha = {'candidate07_prompt_PROPOSED.txt': 'd2e0483fad5b08cbe3298a23acfb418aa274e3969bf0aa51b26fd79bf9bb127f',
                    'execution_layer_PROPOSED.txt': '397bfdffb341ca1862515545fc523541135424533224804abb469a5c93728aa9',
                    'synthetic20_pairs_PRIVATE_PROPOSED.json': '1bfc60747322cc4dc5cee4cc1526b676a8a65f4b9a5d6699f58c594b0cbe640e',
                    'synthetic20_inputs_PROPOSED.jsonl': '1b33992e76c60de4eca4f9cfe401832d778b33cd72dff73523d286e4bb698c0f',
                    'audit_candidate07.py': 'fc1dc2e3dc9ff15e8377144a4e531bd1ef267af19227c9ca1835356ebb9f5aa8',
                    'predeclared_acceptance_PROPOSED.json': '825e3334d936993ed8f4256056e840b08217ee4b882aff724e3571a27b744c37'}
    assert all(sha(BASE / name) == value for name, value in declared_sha.items())
    archived = BASE / 'preflight-revisions/v1-before-independent-corrections'
    preserved = []
    archived_manifest = read(archived / 'snapshot_manifest.json')
    for item in archived_manifest['files']:
        assert sha(item['history_copy']) == item['sha256']
    for old in previous['source_bindings']:
        name = Path(old['path']).name
        if (archived / name).is_file():
            preserved.append({'name': name, 'archived_path': str(archived / name),
                              'v1_report_bound_sha256': old['sha256'], 'author_archived_sha256': sha(archived / name),
                              'same_timepoint_as_v1_report_binding': sha(archived / name) == old['sha256']})
    correction = {'status': 'V1_TIMING_ERROR_TRANSPARENTLY_CORRECTED_NOT_OVERWRITTEN',
        'finding': 'v1 bound a stable snapshot, but its20-control files already contained the06-B correction while its semantic opinion still described the earlier new-indication sentence. Stable before/after SHA was incorrectly described as an old-draft freeze.',
        'v1_bound20pairs_sha256': next(x['sha256'] for x in previous['source_bindings'] if Path(x['path']).name == 'synthetic20_pairs_PRIVATE_PROPOSED.json'),
        'current20pairs_sha256': sha(BASE / 'synthetic20_pairs_PRIVATE_PROPOSED.json'),
        'archived_original20pairs_sha256': sha(archived / 'synthetic20_pairs_PRIVATE_PROPOSED.json'),
        'effect': 'Do not use the v1 99-cell statistic or the06-B opinion as proof about its bound controls. The current v2 conclusions follow a new complete read of all20 current texts/contexts/labels/subtypes, separate explicit independent judgments and fresh current-file mechanical checks.',
        'preservation': 'v1 report/seal and first v2 failed assertion are preserved; no SHA force-match or overwrite.'}
    mechanical = reviewer.mechanics()
    oldpairs = read(archived / 'synthetic20_pairs_PRIVATE_PROPOSED.json')
    pairs = read(BASE / 'synthetic20_pairs_PRIVATE_PROPOSED.json')
    expected = copy.deepcopy(oldpairs)
    corrected = expected['pairs'][5]['members'][1]['input']
    assert corrected['id'] == 'C07-PAIR-06-B'
    assert corrected['text'] == '本年度拟将该药的新增适应症纳入保障范围。'
    corrected['text'] = '本年度拟将该药纳入保障范围。'
    assert expected == pairs, 'Only the prereviewed ambiguous constructed sentence may differ.'
    oldlayer = (archived / 'execution_layer_PROPOSED.txt').read_text()
    newlayer = (BASE / 'execution_layer_PROPOSED.txt').read_text()
    expected_layer = oldlayer.replace('原样完整v1.3手册与v1.4操作说明', '原样完整v1.3手册与v1.4共用实质操作说明')
    expected_layer = expected_layer.replace('具体产品改变不另要求优效。', '相对既有产品的具体属性变化不另要求优效或出现“创新”字样。')
    assert expected_layer == newlayer
    independently_read_values = {'01-A': '00000', '01-B': '00010', '02-A': '00100', '02-B': '00101',
        '03-A': '00000', '03-B': '10000', '04-A': '00001', '04-B': '00101',
        '05-A': '00000', '05-B': '00100', '06-A': '00000', '06-B': '00001',
        '07-A': '00000', '07-B': '00001', '08-A': '00000', '08-B': '00001',
        '09-A': '00101', '09-B': '00101', '10-A': '01010', '10-B': '10010'}
    independent_F = {'02-B': ['access'], '04-A': ['access'], '04-B': ['access'], '06-B': ['access'],
                     '07-B': ['access'], '08-B': ['clinical_management'], '09-A': ['access'], '09-B': ['access', 'affordability']}
    independent_I = {key: ['research_support'] for key in ['01-B', '10-A', '10-B']}
    prior_reason_wording = {r['id']: r['independent_per_dimension_reason'] for r in previous['controls']}
    controls = []
    for pair in pairs['pairs']:
        for member in pair['members']:
            ident = member['input']['id']
            key = ident.removeprefix('C07-PAIR-')
            reasons = copy.deepcopy(prior_reason_wording[ident])
            if key == '06-B':
                reasons['I'] = '当前仅提出该药纳入保障范围，无产品创新/改良/属性变化、创新资格比较或研发支持；不由保障纳入补创新。'
                reasons['F'] = '当前明确拟将具体药品纳入保障范围，支持access；不要求已实施或另写患者承诺。'
            controls.append({'id': ident, 'constructed_input': member['input'],
                'author_expected_labels': member['labels'],
                'independent_labels': dict(zip(reviewer.DIMS, [int(x) for x in independently_read_values[key]])),
                'independent_per_dimension_reason': reasons, 'independent_F_subtypes': independent_F.get(key, []),
                'independent_I_subtypes': independent_I.get(key, []), 'independent_S_quality_basis': 'no_quality_basis',
                'manual_basis': pair['manual_basis'], 'status': 'SUPPORTED_AFTER_COMPLETE_CURRENT20_READ',
                'current_text_context_and_all_five_dimensions_read_again_in_v2': True,
                'actual_model_output_read': False})
            assert controls[-1]['independent_F_subtypes'] == member['fairness_subtypes']
            assert controls[-1]['independent_I_subtypes'] == member['innovation_subtypes']
            assert controls[-1]['independent_S_quality_basis'] == member['safety_quality_basis']
    assert len(controls) == 20 and all(r['independent_labels'] == r['author_expected_labels'] for r in controls)
    audit = module('independent07_output_changes_synthetic_tests', BASE / 'audit_candidate07.py')
    tests = synthetic_change_tests(audit)
    source = (BASE / 'audit_candidate07.py').read_text()
    assert 'if any(output_fields.values()) or any(issue_changes.values()):' in source
    assert 'changed_output_fields_vs_each_history' in source and 'changed_dimensions_vs_each_history' in source
    assert 'older03_04_issue_records_not_available_in_row_snapshot' in source
    for name in ['run_bounded_candidate07.py']:
        old = next(b for b in previous['source_bindings'] if Path(b['path']).name == name)
        assert old['sha256'] == sha(BASE / name)
    acceptance = read(BASE / 'predeclared_acceptance_PROPOSED.json')
    required = acceptance['additional_independently_identified_known_items_NOT_GOLD']
    assert {x['id'] for x in required} == {'RECODE25-01955', 'RECODE25-02220'}
    assert all(x['mandatory_all_five_dimension_review_even_if_all_histories_same'] is True and x['working_judgment_not_gold'] == 1 for x in required)
    assert {x['id']: x['expected_innovation_subtype'] for x in required} == {'RECODE25-01955': 'attribute', 'RECODE25-02220': 'research_support'}
    assert any('任一完整输出字段变化' in line and '理由/证据变化即使标签相同' in line for line in acceptance['real_development'])
    expected_mandatory = set(acceptance['always_review_additional_ids'])
    for group in ['eight_clear06_error_cells_WORKING_NOT_GOLD', 'nine_fixed06_working_cells_to_preserve',
                  'additional_independently_identified_known_items_NOT_GOLD', 'boundary_cells_NOT_FORCED']:
        for record in acceptance[group]:
            expected_mandatory.add(record['id'])
    mandatory_ids = audit.mandatory_review_ids(acceptance)
    assert mandatory_ids == expected_mandatory and len(mandatory_ids) == 30
    assert {'RECODE25-01955', 'RECODE25-02220'} <= mandatory_ids
    current_ids_only = {json.loads(line)['id'] for line in (BASE / 'exposed240_inputs_UNCHANGED.jsonl').read_text().splitlines() if line.strip()}
    assert mandatory_ids <= current_ids_only
    assert "mandatory = [entry for entry in all240 if entry['id'] in mandatory_ids]" in source
    assert "candidate07_mandatory_known_items_REDACTED_PRIVATE.json" in source
    assert binding(paths) == start, 'Package changed during follow-up review.'
    result = {'status': 'PASS_INDEPENDENT_PREFLIGHT_SEMANTIC_AND_STATIC_TECHNICAL_NO_EXECUTION_AUTHORIZATION',
        'reviewed_at_UTC': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'reviewer': 'AI subagent validation_state_oct8; independent of07 design author, not a new blind human coder',
        'source_bindings': start, 'blocking_findings': [],
        'previous_review': {'path': str(OUT / 'candidate07_independent_preflight_v1.json'), 'sha256': sha(OUT / 'candidate07_independent_preflight_v1.json'),
            'file_preserved_unchanged_but_semantic_opinion_outdated': True, 'author_archive_vs_v1_timepoint_comparison': preserved},
        'v1_timing_error_correction': correction,
        'mechanical_checks_repeated_on_final_proposal': mechanical,
        'blocking_findings_closed_before_any_model_output': [
            {'id': 'SEM-01', 'status': 'CURRENT_AMBIGUITY_ABSENT_OLD_OPINION_CORRECTED', 'evidence': 'New full current20 read and exact author-archived original/new pair comparison: only06-B text changed to proposed inclusion of that medicine; all20 expected labels and subtypes unchanged. v1 report had already bound this corrected input, so its contrary opinion was stale.'},
            {'id': 'AUDIT-01', 'status': 'CLOSED', 'evidence': 'changed_fields compares every row field with type-preserving canonical JSON; selection combines any output-field change and available05/06 issue changes. Label-only difference list remains separate. Nine no-model synthetic tests pass.'}],
        'controls_all20_full_five_dimensions_and_subtypes': controls,
        'new_controls_summary': {'units': 20, 'pairs': 10, 'dimension_cells': 100, 'supported_dimension_cells': 100, 'unsupported_or_forced_expectations': 0,
            'subtypes': 'F and I sources independently reviewed; S quality absent for all20. No target score used.'},
        'pair_symmetry_review': {'status': 'SUPPORTED',
            'pairs01_03_05_07_08': 'Negative examples retain the neighboring theme/object but omit the actual target relation; positive examples add substantive support, evaluation, drug-payment relation, access channel, or management burden.',
            'pair02': 'Same economic child and drug-agreement object; verified parent distinguishes application from an actual extension outcome.',
            'pair04': 'Both planned coverage; onlyB adds independent fee responsibility. Planning tense is not the gate.',
            'pair06': 'Both planned;A imposes appointment on intended applicants,B proposes concrete drug coverage. No product-change confound remains.',
            'pair09': 'Both coverage/Ec;B independently adds patient affordability. Insurance responsibility alone does not force a patient-burden subtype.',
            'pair10': 'Same innovative-team support;A contains efficacy-evidence use,B contains toxicity monitoring. Support does not automatically add attribute, monitoring does not automatically add management difficulty.'},
        'prompt_conflict_and_extra_gate_review': {'status': 'NO_BLOCKING_CONFLICT_FOUND',
            'manual_suffix': 'Fullv1.3 and v1.4 substantive part plus schema/footer are exactly06 suffix; inherited validation-discipline omission is now accurately described.',
            'no_extra_implementation_or_positive_result_requirement': True, 'no_extra_fee_amount_or_new_target_requirement': True,
            'no_blanket_procedure_plan_or_guideline_exclusion': True,
            'I_attribute_wording_change': 'The final layer explicitly says relative concrete product-attribute change need not prove superiority or literally say innovation. This implements v1.3:142/v1.4:14 and does not make generic new submissions or category names innovative.',
            'explanation_interpretation_note': 'Who gives what support helps explain a relationship; it does not require every actor to be explicitly named when supplied context resolves it.',
            'reasoning_causality_limit': 'Prompt-conflict mechanism remains a development hypothesis, not demonstrated causality from a single previous output.'},
        'complete_output_change_tracking': {'status': 'PASS_STATIC_AND_SYNTHETIC_TESTS', 'tests': tests,
            'label_changes_tracked_separately': True, 'all_row_fields_in_change_review': True, 'available05_06_issue_changes_tracked': True,
            'older03_04_issue_record_limit': 'Original row snapshots lack issue_records; audit explicitly marks this unavailable, not unchanged.',
            'semantic_correctness_not_inferred_from_fields_or_agreement': True},
        'predeclared_additional_known_checks': required,
        'mandatory_review_queue_test': {'status': 'PASS_METADATA_ONLY', 'n_units': 30,
            'ids': sorted(mandatory_ids), 'exact_independent_union_of_error_fixed_boundary_additional_groups': True,
            'all_current_old240_IDs_and_no_reserved_current_unit': True,
            'separate_redacted_projection_even_if_no_fields_change': True, 'boundaries_not_forced': True},
        'unchanged_runtime_and_wrapper_test_binding': {'wrapper_sha256': sha(BASE / 'run_bounded_candidate07.py'),
            'previous_actual_no_model_test_report_sha256': sha(OUT / 'candidate07_independent_preflight_v1.json'),
            'v1_event_binding_cases': 8, 'v1_wrapper_intercept_cases': 5, 'tests_reused_only_after_hash_equality': True,
            'gpt_model': 'gpt-5.6-sol', 'reasoning_effort': 'medium', 'logical_requests': 15, 'max_identical_pure_technical_attempts': 45,
            'technical_first_valid_only': True, 'real_CLI_invocations': 0, 'real_model_calls': 0},
        'execution_conditions_remaining': ['Root must review and authorize the actual final dependency-closed freeze; this preflight is not authorization.',
            'After one bounded complete run, independently audit actual events/raw/selection and all106 control semantics plus all changed real outputs and forced known checks. Any confirmed error or unresolved required gate blocks adoption.',
            'No automatic full corpus, production or manuscript adoption.'],
        'read_boundaries': previous['read_boundaries'], 'source_files_modified': False, 'real_CLI_invocations': 0, 'real_model_calls': 0,
        'limits': ['Development controls and old240 remeasurement do not establish new human reliability or independent machine validity.',
            'Prior protected-context exposures remain registered. Full normalized matching does not exclude partial quotations/paraphrases.',
            'This does not recertify the semantic correctness of all86 inherited controls or earlier model outputs; those remain subject to the declared post-run review.',
            'Original first A/B outputs, user-confirmed retrospective human review, and current agent opinions remain separate; no label overwritten.',
            'No journal-acceptance or metric-target guarantee.']}
    dump_new(OUT / 'candidate07_independent_preflight_v2.json', result)
    note = '# 候选07独立执行前审查 v2\n\n独立预检通过；这不是模型执行授权或采纳意见。当前方案没有未闭合阻断，v1报告及作者旧稿分别保留。\n\n'
    note += '更正v1留痕错误：v1绑定时20控制已经完成06-B改句，但报告仍写旧句的创新性歧义，99维统计不能证明其绑定控制。v1前后SHA稳定只证明该时点未变，不能等同旧稿。首次v2旧稿强匹配断言失败已保存。本v2已重新完整读取当前全部20原句、contexts、五维及子类，并独立列出100个判断，未以旧意见冒称新实读。\n\n'
    note += '新20条控制全100维、F/I子类及S质量依据均有固定手册支持。06-B现为“本年度拟将该药纳入保障范围”，仅提出具体保障纳入，F1/access成立，未陈述产品属性改变，I0成立。其余19条原文与全部20期望/子类未变。\n\n'
    note += 'audit已逐字段跟踪完整输出差异，包括各维理由、证据、F/I子类和S质量依据，并另跟踪可得05/06 issue变化；标签差异单列，任何完整输出变化均进入全五维复审。9个无模型合成反例验证标签相同的非标签变化不再漏掉。03/04行快照没有issue记录，明确未知，未声称不变。\n\n'
    note += '完整v1.3、v1.4实质操作部分、schema及footer相对06字节一致；runner、validator、schema相对05v2/06一致。旧240/62/24、继承86预期字节一致。新20完整归一预留原文命中0、240当前ID与267交集0。此前共享语境暴露与机械遮蔽的局限继续保留。\n\n'
    note += '01955I/attribute、02220I/research_support已在预声明中列为即使所有历史标签相同也必须全五维复审的已知检查项；仍是工作判断，不是真人新标签。\n\n'
    note += '真实CLI/模型调用0次。范围346条、15逻辑请求、最多45纯技术尝试；默认wrapper无CLI调用，另行root授权须绑定最终freeze。实际运行后仍须核查首个技术有效响应、全部106控制和完整变化范围语义，不能由机械PASS或历史一致代替。\n'
    (OUT / '候选07独立执行前审查-v2.md').write_text(note)
    dump_new(OUT / 'preflight_v2_seal.json', {'reports': binding([OUT / 'candidate07_independent_preflight_v2.json', OUT / '候选07独立执行前审查-v2.md', Path(__file__).resolve()]), 'real_model_calls': 0})
    print(json.dumps({'status': result['status'], 'report': str(OUT / 'candidate07_independent_preflight_v2.json'), 'sha256': sha(OUT / 'candidate07_independent_preflight_v2.json'), 'controls': 20, 'dimension_cells': 100, 'real_model_calls': 0}, ensure_ascii=False))

if __name__ == '__main__':
    main()
