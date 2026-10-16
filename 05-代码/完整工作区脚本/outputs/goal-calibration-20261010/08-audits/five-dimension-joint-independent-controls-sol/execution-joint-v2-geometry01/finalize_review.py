#!/usr/bin/env python3
"""Read back and seal the existing first execution; never import or run judge."""
from pathlib import Path
import datetime
import hashlib
import json

OUT = Path(__file__).resolve().parent
PREP = OUT.parent
ROOT = PREP.parents[1]
CANDIDATE = ROOT / '06-coding/rule-five-dimension-joint-root/versions/joint-v2-geometry01'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def binding(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': sha(raw)}


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(name, data):
    with (OUT / name).open('x', encoding='utf-8') as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def verify(member):
    actual = binding(member['path'])
    assert actual['bytes'] == member['bytes'] and actual['sha256'] == member['sha256'], member['path']
    return actual


assert not (OUT / 'output-seal.json').exists()
prep_seal = load(PREP / 'preparation-seal.json')
candidate_seal = load(CANDIDATE / 'pre-execution-seal.json')
prep_members = [verify(x) for x in prep_seal['output_members']]
candidate_members = [verify(x) for x in candidate_seal['output_members']]
builder = verify(candidate_seal['builder'])
execution_binding = load(OUT / 'execution-input-and-code-seal.json')
for item in execution_binding['snapshots']:
    verify(item['candidate'])
    verify(item['executed_snapshot'])
manual = verify(prep_seal['manual_binding'])
manual_raw = Path(manual['path']).read_text(encoding='utf-8')
manual_lines = manual_raw.splitlines(keepends=True)
fixed = load(PREP / 'controls20-fixed-before-execution.json')
cases = fixed['cases']
execution = load(OUT / 'execution-results.json')
records = execution['cases']
summary = load(OUT / 'execution-summary.json')
assert len(cases) == len(records) == 20
assert summary['candidate_judge_attempts_N'] == execution['candidate_judge_attempts_N'] == 20
assert [x['name'] for x in cases] == [x['name'] for x in records]
for case, result in zip(cases, records):
    assert case['expected_values_fixed_before_execution'] == result['expected_values_fixed_before_execution']


def quotes(numbers):
    answer = []
    for number in numbers:
        literal = manual_lines[number-1]
        start = sum(map(len, manual_lines[:number-1]))
        assert manual_raw[start:start+len(literal)] == literal
        answer.append({'manual': manual, 'line_1based': number,
                       'unicode_span_half_open': [start, start+len(literal)], 'quote': literal})
    return answer


interpretations = {
    'current_named_feedback_does_not_copy_parallel_conditions': {
        'category': 'direct_current_innovation_support_missed',
        'confirmed_algorithm_problem_dimensions': ['I'],
        'explanation': '当前实际开放具名研发反馈服务；已供同版第一条明确创新药上市前研发对象及专门团队反馈。当前对象、可用安排与阶段关系均有文字，未生成必要关系，I漏判。并行第六条五维条件不适用于本次仅开放服务的命题。',
        'missing_material': False,
    },
    'current_operational_standard_in_same_feedback_plan': {
        'category': 'complete_same_version_standard_consumers_incomplete',
        'confirmed_algorithm_problem_dimensions': ['I', 'F'],
        'explanation': '当前第八条以第六条全部实质条件维持实际反馈资格；已供并闭合的第六条包含技术新颖性与收入较低患者持续获得药物的独立内容。cited_standard仅路由S/E/Ec，I/F未生成其他消费路径。完整来源在场不意味着并行当前服务条文继承五维，但本例当前确指全部条件，不能只消费前三维。',
        'missing_material': False,
    },
    'innovation_timed_review_not_other_object_supply_gap': {
        'category': 'direct_current_relative_time_support_missed',
        'confirmed_algorithm_problem_dimensions': ['I'],
        'explanation': '当前明确为创新药研发项目把普通程序六十日缩为四十日，具体相对时限支持直接成立；I漏判。另一受益对象的现实供药缺口未映射到本命题，F=0正确，不以可见完整程序跨对象捐献F。',
        'missing_material': False,
    },
    'article10_supplied_article12_still_stopped': {
        'category': 'known_positive_preserved_and_other_exact_dependency_unresolved',
        'confirmed_algorithm_problem_dimensions': ['I', 'F'],
        'explanation': '原五维NULL预期完整保留。第十条已供并闭合，核验过敏风险是独立安全性依据，实际S=1应保持，不能为匹配原NULL擦除已知正类。第十二条未交付仍stopped，S决策details保留该未解请求，S阳性不能将其解掉。E/Ec=NULL正确保存缺材；未供全部实质条件只把未知路由到S/E/Ec，I/F直接为0存在消费者路由问题，未知不能记0。并不据独立保存但未交付的第十二条内容硬判I/F=1。',
        'original_expected_interpretation_boundary': {'S': '原NULL过宽；同维存在独立实质阳性应为1，并保留另条未解请求。原固定预期不可回写。'},
        'not_a_confirmed_false_positive_dimension': ['S'],
        'missing_material': True,
        'material_scope': '第十二条及第十三条边界仅存在独立合成原件，未作为bundle资源交付；只用于审查输入缺口定位，不进入候选消费。',
    },
    'formal_filename_inference_explicitly_denied': {
        'category': 'attachment_names_and_denied_inference_misused_as_evaluation',
        'confirmed_algorithm_problem_dimensions': ['I', 'F'],
        'explanation': '完整当前明确五栏目仅作附件文件名，否定从文件名推定任何评价或支持，实际仅签章核验。generic路径将否定推断中的评价词当成真实评价要求，I/F过度纳入。该否定不同于真正要求评价某药属性是否成立。',
        'missing_material': False,
    },
}

bindings = []
reviews = []
failures = []
for case, result in zip(cases, records):
    packet = case['synthetic_bundle']
    canonical = json.dumps(packet, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
    documents = [verify(x['binding']) for x in case['synthetic_documents']]
    bindings.append({'name': case['name'], 'source_only_bundle_canonical_sha256': sha(canonical),
                     'source_only_bundle_canonical_bytes': len(canonical),
                     'current_text': packet['source_record']['text'],
                     'current_source_ref': packet['source_record']['source_ref'],
                     'documents': documents,
                     'candidate_visible_full_text_resources_N': len(packet['source_full_text_resources']),
                     'expected_unchanged': True})
    detail = interpretations.get(case['name'], {
        'category': 'finite_independent_control_matched',
        'confirmed_algorithm_problem_dimensions': [],
        'explanation': case['manual_reason'],
        'missing_material': False,
    })
    reviews.append({'name': case['name'], 'current_text': packet['source_record']['text'],
                    'original_expected_values': case['expected_values_fixed_before_execution'],
                    'first_actual_values': result['actual_values'],
                    'original_expectation_mismatches': result['mismatched_dimensions'],
                    'interpretation': detail,
                    'manual_quotes': quotes(case['manual_lines']),
                    'actual_read': {'complete_current_proposition': True,
                                    'complete_saved_synthetic_original': True,
                                    'all_supplied_context_text_and_geometry': True,
                                    'candidate_visible_and_undelivered_material_distinguished': True},
                    'formal_reference_validation': False})
    if not result['values_matched']:
        failures.append({'name': case['name'], 'unchanged_presealed_case': case,
                         'unchanged_first_execution_record': result,
                         'semantic_review': reviews[-1]})

write('case-input-bindings.json', {'control_file': binding(PREP / 'controls20-fixed-before-execution.json'),
                                 'case_N': 20, 'cases': bindings})
write('failure-full-inputs-and-paths.json', {'first_failed_case_N': 5, 'all_first_failures_preserved': True,
                                          'original_expectations_unchanged': True, 'cases': failures})
write('semantic-review.json', {'status': 'independent_source_and_manual_review_of_first_execution',
                               'cases': reviews, 'no_algorithm_or_expected_change': True})

case13 = records[12]
case14 = records[13]
assert case13['actual_values']['S'] == 1
assert case13['stopped_requests']
assert case13['full_five_decisions_first_execution']['S']['details']['unresolved_material_requests']
coverage = {
    'consumer_route': {'observed_positive_route_violations_N': summary['accepted_positive_consumer_route_violations_N'],
                       'only_IF_observed_units_N': summary['only_IF_observed_units_N'],
                       'static_affected_intersection_with_IF_present': True,
                       'actual_only_IF_gate_dynamic_coverage': 'not_exercised_no_natural_units_with_flag',
                       'abstract_preparation_vectors_not_dynamic_tests': True,
                       'no_injected_relation_or_resolved_receipt': True},
    'boundary_and_current_scope': {'boundary_same_literal_and_current_occurrence_pair_matched': True,
                                   'exact_current_anaphor_and_brother_member_pairs_matched': True,
                                   'different_recipient_supply_gap_not_donated_to_innovation_branch': True},
    'dependency_receipts': {'case13_stopped_requests_first_output': case13['stopped_requests'],
                            'case13_exact_closed_relation_traces': case13['source_relation_traces'],
                            'case13_explicit_resolved_request_receipts': case13['resolved_receipts'],
                            'case14_separate_closed_relation_traces': case14['source_relation_traces'],
                            'case14_explicit_resolved_request_receipts': case14['resolved_receipts'],
                            'scope_closure_traces_are_not_claimed_as_explicit_resolved_request_receipts': True,
                            'resolved_request_receipt_dynamic_branch': 'not_exercised_by_these_controls',
                            'known_S_positive_kept_with_other_reference_still_unresolved': True},
    'quote_validation': {'literal_validation': binding(OUT / 'literal-quote-first-execution-validation.json'),
                         '36_literal_matches_do_not_establish_semantic_applicability': True},
}
write('interface-constraint-coverage.json', coverage)
report = {'status': 'sealed_finite_first_execution_review_not_formal_validation',
          'summary': summary, 'original_preparation_seal': binding(PREP / 'preparation-seal.json'),
          'candidate_pre_execution_seal': binding(CANDIDATE / 'pre-execution-seal.json'),
          'preparation_at_utc': prep_seal['prepared_at_utc'],
          'candidate_algorithm_at_utc': load(CANDIDATE / 'algorithm-bindings.json')['at_utc'],
          'hidden20_prepared_before_final_algorithm_seal': True,
          'five_failed_cases_nine_fixed_expected_dimension_mismatches_preserved': True,
          'known_S1_vs_original_NULL_is_expected_interpretation_boundary_not_confirmed_FP': True,
          'confirmed_problem_groups': ['direct_innovation_service_miss', 'relative_time_innovation_support_miss',
                                       'complete_standard_IF_consumer_gap', 'unprovided_standard_IF_unknown_as_zero',
                                       'attachment_name_denied_inference_as_generic_IF_evaluation'],
          'only_IF_gate_naturally_generated_test_units_N': 0,
          'explicit_resolved_request_receipt_branch_not_exercised': True,
          'actual_read_and_check_boundary': ['all20 complete current propositions',
                                           'all saved synthetic originals and supplied context geometry',
                                           'first decisions/relation traces/requests/observed units/accepted positives',
                                           'five candidate modules read-only; candidate membership SHA checks',
                                           'frozen manual exact quoted line spans',
                                           'candidate parent regression/function-selection bytes hashed only, no test content read'],
          'parent75_or235_answers_read': False, 'main_LLM_partial_or_owner800_labels_read': False,
          'new_candidate_judge_attempts_from_finalize_N': 0,
          'actual_human_reference_results_N': 0, 'formal_statistics_or_year_metrics_N': 0}
write('report.json', report)

readme = '''联合 joint-v2-geometry01 隐藏20独立控制：首次执行与语义封存

原20输入与预期于最终算法封存前固定，ROOT仅先收数量和预封存SHA。每项只执行一次：15项匹配、5项不符，共9维与原固定预期不符，20次证据校验通过、36条独立字面与源定位校验通过，零异常。算法和预期均未改写。

直接漏判：具名创新研发反馈开放、相对普通程序缩短审评时限，各漏I。完整同版第六条标准已供并被当前第八条确指，S/E/Ec消费成立而I/F无消费路径。附件名案例当前否定由文件名推定评价并仅核签章，generic误记I/F。

部分缺材案例原五维NULL预期保留，第十条独立安全性证据使S=1成立，应保持；第十二条另一个确指条件未供仍stopped，S决策亦保留未解请求，不能凭S阳性解掉它。E/Ec=NULL保存；未供全部实质条件只路由前三维而I/F记0需修正未知消费范围。S与原NULL的不符属于原预期解释边界，不称确定FP，不修改原预期或将已知1擦除。

only_IF交集门静态存在，但20项实际生成此flag单位为0，未将六个预备抽象向量冒充动态测试。精确条范围closure trace可核对，不冒充不存在的resolved source_request receipt；相应显式receipt分支未实测。边界引用不捐献标签、当前明确指示排除兄弟、OR分支的有限通过仅覆盖本20控制。

case-input-bindings.json绑定全部输入；failure-full-inputs-and-paths.json逐项保存五处完整原固定输入、所有上下文、源几何、首次五维输出、误接/缺接路径及手册原句；semantic-review.json给20逐项解释。literal校验是必要机械核对，不替代实质关系审查。

此次为合成源结构的有限独立代码审查，没有真人参照、正式准确率、年度指标或整批77/800/4481运行。缺材原件虽为审查定位保存，未向候选交付的段落不进入候选判断。所有新文件仅写本execution子目录；原准备、候选、手册与旧输出不改。
'''
with (OUT / 'README.txt').open('x', encoding='utf-8') as stream:
    stream.write(readme)
write('final-readback.json', {'status': 'pass', 'original16_preparation_members': prep_members,
                             'candidate8_members': candidate_members, 'builder': builder,
                             'manual': manual, 'fixed_inputs_expected_equal_to_first_execution': True,
                             'first_execution_attempts_N': 20, 'additional_judge_attempts_N': 0,
                             'new_outputs_before_seal': [binding(p) for p in sorted(OUT.rglob('*')) if p.is_file()]})
members = [binding(p) for p in sorted(OUT.rglob('*')) if p.is_file()]
write('output-seal.json', {'status': 'sealed_independent_finite_first_execution',
                          'at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                          'output_members': members, 'seal_self_excluded': True,
                          'first_execution_attempts_N': 20, 'candidate_and_fixed_expected_unchanged': True,
                          'formal_human_validation': False})
for member in members:
    verify(member)
print(json.dumps({'seal': binding(OUT / 'output-seal.json'), 'members_N': len(members),
                  'case_N': 20, 'matched_N': 15, 'failed_N': 5, 'mismatched_dimensions_N': 9,
                  'known_S_expected_boundary_preserved': True}, ensure_ascii=False))
