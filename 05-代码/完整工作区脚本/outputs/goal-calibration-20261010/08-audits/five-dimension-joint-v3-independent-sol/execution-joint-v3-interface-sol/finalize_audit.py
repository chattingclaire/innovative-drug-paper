#!/usr/bin/env python3
"""Seal both technical attempts and review readable outputs; never run judge."""
from pathlib import Path
import datetime
import hashlib
import json

OUT = Path(__file__).resolve().parent
PREP = OUT.parent
ROOT = PREP.parents[1]
CANDIDATE = ROOT / '06-coding/rule-five-dimension-joint-root/versions/joint-v3-interface-sol'
RETRY = OUT / 'attempt02'


def bind(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def verify(item):
    assert bind(item['path']) == item, item['path']
    return item


def write(name, data):
    with (OUT/name).open('x', encoding='utf-8') as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


assert not (OUT/'output-seal.json').exists()
preseal = load(PREP/'preparation-seal.json')
assert bind(PREP/'preparation-seal.json')['sha256'] == 'c2f2033647918ae48c2dbea6bd960c1830b9b4588a5f5272787487eae260cec9'
prep_members = [verify(item) for item in preseal['output_members']]
cseal = load(CANDIDATE/'pre-execution-seal.json')
assert bind(CANDIDATE/'pre-execution-seal.json')['sha256'] == '909f4aaa1cbdd1f2222284f56bdffae458438b61b90a828a90ae0c1918916f93'
active_bindings = cseal['modules'] + cseal['common_frozen_input_bindings'] + [cseal['manual'], cseal['algorithm_bindings']]
candidate_members = [verify(item) for item in active_bindings]
capture_seal = load(OUT/'attempt01-capture-reception-seal.json')
capture_members = [verify(item) for item in capture_seal['output_members']]
for seal_path in (OUT/'execution-input-and-code-seal.json', RETRY/'execution-input-and-code-seal.json'):
    for item in load(seal_path)['snapshots']:
        verify(item['candidate']); verify(item['executed_snapshot'])
cases = load(PREP/'controls12-fixed-before-execution.json')['cases']
results = load(RETRY/'execution-results.json')['cases']
summary = load(RETRY/'execution-summary.json')
assert len(cases) == len(results) == 12
assert summary['source_construction_attempts_N'] == 12 and summary['candidate_judge_attempts_N'] == 9
assert summary['saved_case_results_N'] == 12
events = [json.loads(line) for line in (RETRY/'immediate-events.jsonl').read_text().splitlines()]
assert sum(e['event'] == 'case_start' for e in events) == 12
assert sum(e['event'] == 'RelationView_enter' for e in events) == 12
assert sum(e['event'] == 'RelationView_exception' for e in events) == 3
assert sum(e['event'] == 'judge_enter' for e in events) == 9
assert sum(e['event'] == 'judge_return' for e in events) == 9
assert sum(e['event'] == 'case_result_saved' for e in events) == 12
manual = verify(cseal['manual'])
manual_raw = Path(manual['path']).read_text(encoding='utf-8')
lines = manual_raw.splitlines(keepends=True)


def manual_quotes(numbers):
    out = []
    for number in numbers:
        start = sum(map(len, lines[:number-1])); text = lines[number-1]
        assert manual_raw[start:start+len(text)] == text
        out.append({'line_1based': number, 'unicode_span_half_open': [start,start+len(text)],
                    'quote': text, 'manual_binding': manual})
    return out


def current_literal_check(case, result):
    row = case['synthetic_bundle']['source_record']
    doc = case['synthetic_documents'][0]
    verify(doc['binding'])
    raw = Path(doc['binding']['path']).read_bytes()
    original = raw.decode('utf-8')
    ref = row['source_ref']; locator = ref['locator']
    a,b = locator['unicode_code_point_interval_half_open']
    ba,bb = locator['utf8_byte_interval_half_open']
    assert original[a:b] == row['text'] and raw[ba:bb].decode('utf-8') == row['text']
    assert ref['sha256'] == doc['binding']['sha256']
    decisions = result['full_five_decisions_first_execution']
    quotes = []
    if decisions is not None:
        for dim, decision in decisions.items():
            for role in ('current_anchor', 'current_proposition'):
                quote = decision[role]
                if quote is None:
                    assert decision['value'] != 1
                    continue
                assert row['text'][quote['start']:quote['end']] == quote['text']
                ga,gb = a+quote['start'],a+quote['end']
                assert original[ga:gb] == quote['text']
                quotes.append({'dimension': dim, 'role': role, 'quote': quote,
                               'source_global_unicode_span': [ga,gb],
                               'physical_line_interval': [original[:ga].count('\n')+1,original[:gb].count('\n')+1],
                               'source_ref': ref, 'literal_valid': True})
    return {'name': case['name'], 'input_current_literal_valid': True,
            'actual_decision_current_quotes': quotes,
            'construction_exception_has_no_synthetic_decision_quote': decisions is None,
            'candidate_unavailable_original_paragraphs_not_consumed': True}


explanations = {
    'admitted_projects_current_feedback': {
        'category': 'current_I3_support_relation_missed', 'actual_error_dimension': 'I',
        'explanation': '当前允许已纳入本计划项目预约该团队的上市前研究方案书面反馈；已供同版第一条明确该计划对象为创新药上市前研发并有专门团队预约反馈。对象、可用服务与当前阶段直接联系完整，未生成关系且I=0，属漏判；并非仅沟通形式或档案身份。'},
    'relative_ordinary_review_time_shortened': {
        'category': 'direct_relative_time_support_missed', 'actual_error_dimension': 'I',
        'explanation': '完整当前先给创新研发申请专门通道，再以其承接同一对象，明示相对同版第一条普通三十日缩至二十日。两分句不是互不相关背景，I3实际申请便利成立；I=0漏判。不能只按单个时限数字推支持，负例普通共同期限保持0。'},
    'negative_novelty_and_actual_supply_obstacle_information': {
        'category': 'specific_continuous_drug_access_obstacle_information_missed', 'actual_error_dimension': 'F',
        'explanation': '技术新颖性的否定评价I=1正确。另一当前分句实质要求核验目标患者因药物供应不稳无法持续得到所需治疗这一具体保障障碍，符合五维统一的实质讨论/信息核验门槛及患者持续治疗保障缺口，不是一般物流栏目。F=0漏判；没有据此声称障碍已经证实或支持措施已生效，也未补写费用/疗效。'},
}
current_checks = []
reviews = []
failures = []
bindings = []
for case, result in zip(cases, results):
    assert case['name'] == result['name']
    assert case['expected_values_fixed_before_execution'] == result['expected_values_fixed_before_execution']
    current_checks.append(current_literal_check(case, result))
    canonical = json.dumps(case['synthetic_bundle'],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
    bindings.append({'name': case['name'], 'source_only_input_canonical_sha256': hashlib.sha256(canonical).hexdigest(),
                     'source_only_input_canonical_bytes': len(canonical),
                     'current_source_ref': case['synthetic_bundle']['source_record']['source_ref'],
                     'synthetic_originals': [verify(d['binding']) for d in case['synthetic_documents']]})
    if result['execution_error'] is not None:
        interpretation = {'category': 'candidate_neutral_article_number_type_construction_error',
                          'numeric_values_not_available': True,
                          'explanation': '中性structure.article整数保持原样传入；v3 _se_operational_references对该值直接norm，matching_view要求文字，因此RelationView构造异常，尚未judge。不是语义NULL，也不是五维判0，不将缺失五维输出计成15个科学FP/FN。标准和缺材预期原样留存。',
                          'integer_articles_in_supplied_contexts': sorted({c['structure']['article'] for c in case['synthetic_bundle']['source_record']['contexts'] if type(c['structure'].get('article')) is int}),
                          'missing_material_independent_of_this_technical_failure': any(not d['delivered_complete_literal_snapshot'] for d in case['synthetic_documents'])}
    elif result['values_matched']:
        interpretation = {'category': 'limited_readable_control_matched', 'explanation': case['manual_reason']}
    else:
        interpretation = explanations[case['name']]
    review = {'name': case['name'], 'complete_current_text': case['synthetic_bundle']['source_record']['text'],
              'fixed_original_expected': case['expected_values_fixed_before_execution'],
              'attempt02_actual': result['actual_values'],
              'actual_output_unavailable_not_semantic_NULL': result['actual_values'] is None,
              'interpretation': interpretation, 'manual_quotes': manual_quotes(case['manual_lines']),
              'original_expected_interpretation_boundary': 'none identified in readable three numeric discrepancies; fixed expectations retained; construction failures prevent scope/NULL consumer evaluation',
              'complete_current_and_supplied_source_text_and_geometry_read': True,
              'saved_but_unprovided_original_sections_not_given_to_candidate': True}
    reviews.append(review)
    if not result['values_matched']:
        failures.append({'name': case['name'], 'unchanged_presealed_full_case': case,
                         'complete_readable_attempt02_record': result, 'review': review})
write('all12-input-bindings.json', {'original_plan': bind(PREP/'controls12-fixed-before-execution.json'),
                                   'cases': bindings, 'inputs_and_expected_unchanged': True})
write('current-quote-and-source-location-validation.json', {'input_current_quote_N': 12,
       'readable_decision_current_quote_N': sum(len(x['actual_decision_current_quotes']) for x in current_checks),
       'context_quote_N': summary['independent_literal_quote_N'], 'context_quotes_naturally_emitted': False,
       'context_zero_not_claimed_as_completed_relation_quote_coverage': True, 'cases': current_checks,
       'literal_match_does_not_establish_semantic_applicability': True})
write('semantic-and-interface-review.json', {'case_N': 12, 'reviews': reviews,
      'technical_attempt01_not_reconstructed': True, 'all_readable_values_are_attempt02': True})
write('failure-full-inputs-and-paths.json', {'unmatched_cases_N': 6, 'construction_failure_cases_N': 3,
      'readable_numeric_discrepancy_cases_N': 3, 'readable_numeric_discrepancy_dimensions_N': 3,
      'original_runner_raw_mismatch_count18_includes15_unavailable_construction_dimensions': True,
      'no_constructed_failure_outputs_or_NULL_fill': True, 'cases': failures})
write('consumer-coverage.json', {'source_relation_traces_N': sum(len(r['source_relation_traces']) for r in results),
      'only_IF_observed_units_N': summary['only_IF_observed_units_N'],
      'typed_subset_observed_units_N': summary['typed_subset_observed_units_N'],
      'only_IF_actual_positive_events_N': summary['only_IF_accepted_positive_events_N'],
      'typed_subset_actual_positive_events_N': summary['typed_subset_accepted_positive_events_N'],
      'actual_positive_consumer_violations_N': summary['accepted_positive_consumer_route_violations_N'],
      'coverage': 'not_exercised_no_naturally_generated_only_IF_or_typed_subset_units',
      'no_injected_unit_relation_route_or_resolved_receipt': True,
      'zero_violations_with_zero_restricted_units_is_not_proof_of_consumer_gate_correctness': True})
report = {'status': 'completed_bounded_audit_with_preserved_technical_failure_and_one_authorized_retry',
          'original_hidden12_preseal': bind(PREP/'preparation-seal.json'),
          'final_candidate_preseal': bind(CANDIDATE/'pre-execution-seal.json'),
          'attempt01_failed_capture_seal': bind(OUT/'attempt01-failed-capture/output-seal.json'),
          'attempt01_capture_corrected_external_reception_seal': bind(OUT/'attempt01-capture-reception-seal.json'),
          'attempt01_original_capture_seal_self_entry_error_preserved': True,
          'attempt01_first_values_not_saved_and_cannot_reconstruct': True,
          'attempt01_judge_attempt_count_not_logged': True,
          'postfailure_SourcePacket_RelationView_diagnostic_calls_N': 12,
          'postfailure_diagnostic_judge_calls_N': 0,
          'attempt02_authorized_technical_retry': True,
          'attempt02_source_construction_attempts_N': 12, 'attempt02_judge_calls_N': 9,
          'attempt02_readable_saved_case_results_N': 12,
          'matched_readable_cases_N': 6, 'readable_numeric_discrepancy_cases_N': 3,
          'readable_numeric_discrepancy_dimensions_N': 3, 'constructor_exception_cases_N': 3,
          'three_constructor_errors_are_not_semantic_NULL_or_15_scientific_FP_FN': True,
          'total_judge_calls_across_both_processes_not_exactly_logged': True,
          'cannot_claim_total_execution_only12': True, 'third_retry_performed_N': 0,
          'only_IF_and_typed_subset_dynamic_coverage': 'not_exercised_actual_units0',
          '9_evidence_validators_passed': True,
          'actual_nonnull_current_decision_quotes_N': sum(len(x['actual_decision_current_quotes']) for x in current_checks),
          'actual_nonnull_current_decision_quotes_exact': True,
          'zero_decision_optional_null_anchors_not_counted_as_quotes': True,
          'context_quotes_N': 0, 'all12_source_current_quotes_exact': True,
          'source_rows_and_original_EXPECTED_NULL_preserved': True,
          'candidate_5_modules_and_manual_unchanged': True,
          'actual_policy_new_IDs_or_cohort_runs_N': 0, 'actual_human_reference_or_statistics_N': 0,
          'parent75_235_answers_or_mainLLM_partial_labels_read': False,
          'historical_control_files_listed_in_algorithm_bindings_not_consumed': True,
          'not_formal_human_validation': True}
write('report.json', report)
with (OUT/'README.txt').open('x',encoding='utf-8') as stream:
    stream.write('v3隐藏12独审：技术失败与一次授权重试均保留。\n\n'
                 'attempt01原runner在循环后、结果写盘前断言judge数等于12；3项构造异常使进程结束，内存中逐项结果无法恢复。原runner、tool退出异常、输入/代码绑定及事后仅SourcePacket/RelationView的诊断已不可覆盖封存。事后诊断不是首次judge结果。\n\n'
                 'ROOT允许仅修审计保存机制后的attempt02一次重试，候选五模块/源接口/原12输入与预期均不改。每项开始、构造异常、judge进入与返回、完整结果即时JSONL并flush。attempt02构造12项，9次judge，12条可读结果：6匹配、3项/3维数值不符、3项构造异常。不能称两次过程总执行只有12次；attempt01确切judge次数未记录。无第三次重试。\n\n'
                 '构造异常均为structure.article整数4或21被v3直接交给norm/matching_view，后者要求原文str。这是中性结构编号接口异常，不是语义NULL，更不是15个科学FP/FN。缺材预期仍保留，不以异常填0/1/null。\n\n'
                 '可读数值不符：具名纳入后可预约反馈与明示相对普通时限缩短各漏I；当前要求核验供药不稳造成患者持续治疗障碍漏F。否定技术新颖性评价I=1正确。对应完整当前、全部供给语境、源几何和手册依据逐项保存。\n\n'
                 '自然linked relation、only_IF、typed子集单位均为0，消费者限制动态未实测；不注入关系/单位/路径/假resolved。9项返回均通过evidence校验，12当前源定位和实际非空当前anchor/proposition逐字校验通过；0决策允许空anchor，不将其计成引文。context引用0不能冒充完整关系引用测试。\n\n'
                 '所有原始不符、NULL预期、source-only输入和代码快照可追溯。该12已暴露给后续开发，不再作为未来v4独立控制。无真实policy新增ID、cohort、真人参照、正式准确率或统计验证。\n')
write('final-readback.json', {'original14_preparation_members': [verify(x) for x in prep_members],
      'active_candidate_and_common_freeze_bindings': [verify(x) for x in candidate_members],
      'attempt01_capture_members': [verify(x) for x in capture_members],
      'immediate_event_counts_verified': True, 'no_extra_judge_from_finalize': True,
      'own_outputs_before_seal': [bind(p) for p in sorted(OUT.rglob('*')) if p.is_file()]})
members = [bind(p) for p in sorted(OUT.rglob('*')) if p.is_file()]
write('output-seal.json', {'status': 'sealed_independent_v3_12_with_first_failure_and_authorized_retry',
      'at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
      'output_members': members, 'seal_self_excluded': True, 'actual_human_validation': False,
      'first_attempt_output_loss_disclosed': True, 'only_one_authorized_retry': True})
for item in members:
    verify(item)
print(json.dumps({'output_seal': bind(OUT/'output-seal.json'), 'members_N': len(members),
      'attempt02_constructed_attempts_N': 12, 'attempt02_judge_N': 9,
      'readable_N': 12, 'match_N': 6, 'numeric_discrepancy_N': 3, 'construction_exception_N': 3,
      'third_retry_N': 0},ensure_ascii=False))
